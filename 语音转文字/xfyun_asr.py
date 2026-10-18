#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞开放平台「录音文件转写大模型」(Ifasr_llm) 语音转文字工具

文档: https://www.xfyun.cn/doc/spark/asr_llm/Ifasr_llm.html

接口要点（全部按文档实现）:
  * 协议   : HTTPS，仅 POST
  * 域名   : https://office-api-ist-dx.iflyaisol.com
  * 鉴权   : HMAC-SHA1(secret, baseString) -> Base64，放在请求头 signature
             baseString = 参数按名字典序排序 -> key/value 均 URL 编码 -> k=v 用 & 连接
             空值不参与签名；签名参数用未编码原始值
  * 上传   : POST /v2/upload   Content-Type: application/octet-stream   body=音频二进制
             -> 返回 content.orderId
  * 查询   : POST /v2/getResult Content-Type: application/json          body={}
             参数 signatureRandom 必须与上传时相同，dateTime 必须重新生成
  * 状态   : orderInfo.status  0 已创建 / 3 处理中 / 4 完成 / -1 失败
  * 音频   : 16kHz 或 8kHz、16bit、单声道；mp3/wav/pcm/opus/flac/ogg/speex
             时长 ≤ 5 小时，文件 ≤ 500MB
  * 结果   : content.orderResult 是 JSON 字符串
             {lattice:[{json_1best:"{st:{bg,ed,rl,rt:[{ws:[{wb,we,cw:[{w,wp,wc}]}]}]}}"}]}
             wp: n 正常词 / s 顺滑 / p 标点 / g 分段

本工具额外解决工程问题:
  * 任意采样率/声道/位深的音频自动转成 16k(或8k) 单声道 16bit PCM WAV
  * 超出 500MB / 5 小时的音频自动按段切分，转写后按时间偏移拼接回完整时间轴
  * orderId + 分段结果落盘（state.json），中断后可 --resume 续跑，不重复计费
  * 输出 txt / srt / json / subtitle.json（与项目内既有字幕格式一致）/ md

用法:
  python xfyun_asr.py run  录音.wav                # 完整流程
  python xfyun_asr.py run 录音.wav --role-type 1    # 开启角色分离
  python xfyun_asr.py probe 录音.wav                # 只看音频信息
  python xfyun_asr.py split 录音.wav                # 只做转码切分
  python xfyun_asr.py upload 录音.wav               # 只上传，打印 orderId
  python xfyun_asr.py result --order-id xxx --signature-random yyy
  python xfyun_asr.py selftest                      # 离线自检（无需密钥）

凭证（任选其一，优先级从高到低）:
  --appid / --api-key / --api-secret
  环境变量 XF_APPID / XF_API_KEY / XF_API_SECRET（也兼容 IFLYTEK_* / APPID/APIKEY/APISECRET）
  配置文件 .env（脚本同目录、当前目录或 --env 指定）
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import shutil
import ssl
import string
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# 常量
# --------------------------------------------------------------------------- #
API_HOST = "https://office-api-ist-dx.iflyaisol.com"
UPLOAD_PATH = "/v2/upload"
RESULT_PATH = "/v2/getResult"

MAX_UPLOAD_BYTES = 500 * 1024 * 1024      # 文档: 音频文件大小不超过 500MB
MAX_AUDIO_MS = 5 * 3600 * 1000           # 文档: 时长不超过 5 小时
SAFE_BYTES = 480 * 1024 * 1024           # 留 20MB 余量
SAFE_MS = 5 * 3600 * 1000 - 60_000       # 留 60s 余量

ERROR_CODES = {
    "000000": "成功",
    "999999": "未知异常",
    "000001": "参数错误或不完整",
    "000002": "accessKeyId不存在",
    "1000000": "不支持的操作",
    "100001": "订单不存在或状态异常",
    "100002": "订单音频未上传",
    "100003": "参数错误",
    "100004": "查询订单错误",
    "100005": "查询音频为空",
    "100006": "上传音频异常",
    "100007": "权限错误",
    "100008": "签名异常-请求时间超过限制",
    "100009": "签名校验不通过",
    "100012": "请求超过频率限制",
    "100013": "订单未完成",
    "100015": "热词必须是中文",
    "100020": "语言验证失败",
    "100026": "时间格式必须为: yy-MM-dd",
    "100029": "文件已存在",
    "100030": "未知的文件格式",
    "100033": "无效的角色分离个数，角色分离个数范围: [0-10]",
    "100037": "非法的订单号",
    "100039": "订单为空",
    "100040": "订单个数超出限制",
    "100042": "外链地址无效",
    "100044": "通道类型不存在",
}

FAIL_TYPES = {
    0: "音频正常执行",
    1: "音频上传失败",
    2: "音频转码失败",
    3: "音频识别失败",
    4: "音频时长超限（最大音频时长为5小时）",
    5: "音频校验失败（duration 与真实音频时长不符）",
    6: "静音文件",
    7: "翻译失败",
    8: "账号无翻译权限",
    9: "转写质检失败",
    10: "转写质检未匹配出关键词",
    11: "创建任务时未开启质检/翻译能力",
    12: "音频语种分析失败",
    99: "其他",
}

PD_DOMAINS = {
    "court": "法律", "finance": "金融", "medical": "医疗", "tech": "科技",
    "sport": "体育", "edu": "教育", "isp": "运营商", "gov": "政府",
    "game": "游戏", "ecom": "电商", "mil": "军事", "com": "企业",
    "life": "生活", "ent": "娱乐", "culture": "人文历史", "car": "汽车",
}


# --------------------------------------------------------------------------- #
# 小工具
# --------------------------------------------------------------------------- #
class AsrError(RuntimeError):
    """业务/网络异常"""


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr, flush=True)


def log(msg: str = "", prefix: str = "·") -> None:
    print(f"{prefix} {msg}" if msg else "", flush=True)


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}B"
        n /= 1024.0
    return f"{n:.1f}TB"


def human_dur(ms: float) -> str:
    total = max(0, int(round(ms / 1000.0)))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def srt_ts(ms: float) -> str:
    ms = max(0, int(round(ms)))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def now_datetime_str() -> str:
    """文档格式: yyyy-MM-dd'T'HH:mm:ss±HHmm，例如 2025-09-08T22:58:29+0800"""
    local = datetime.now().astimezone()
    return local.strftime("%Y-%m-%dT%H:%M:%S") + local.strftime("%z")


def random_str(n: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def url_encode(value: Any) -> str:
    """标准 URL 编码，不保留特殊字符（: -> %3A, + -> %2B）"""
    return urllib.parse.quote(str(value), safe="")


def http_post(url: str, headers: Dict[str, str], body: Any,
              timeout: float, insecure: bool = False) -> Tuple[int, bytes]:
    """POST 请求；body 可以是 bytes 或已打开的文件对象（需自行带 Content-Length）"""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    ctx = ssl._create_unverified_context() if insecure else None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:          # 4xx/5xx 也把 body 带回来
        return exc.code, exc.read()
    except urllib.error.URLError as exc:
        raise AsrError(f"网络请求失败: {exc.reason}") from exc
    except OSError as exc:
        raise AsrError(f"网络请求失败: {exc}") from exc


# --------------------------------------------------------------------------- #
# 鉴权
# --------------------------------------------------------------------------- #
def build_base_string(params: Dict[str, Any]) -> str:
    """按文档 3.1 生成 baseString：剔除 signature/null/空值，字典序，key 与 value 都编码"""
    items = []
    for key, value in params.items():
        if key == "signature" or value is None:
            continue
        text = str(value)
        if text.strip() == "":
            continue
        items.append((key, text))
    items.sort(key=lambda kv: kv[0])
    return "&".join(f"{url_encode(k)}={url_encode(v)}" for k, v in items)


def make_signature(access_key_secret: str, params: Dict[str, Any]) -> str:
    """HMAC-SHA1(baseString, key=APISecret) -> Base64"""
    base_string = build_base_string(params)
    digest = hmac.new(access_key_secret.encode("utf-8"),
                      base_string.encode("utf-8"),
                      hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def encode_query(params: Dict[str, Any]) -> str:
    """最终拼到 URL 上的查询串（与签名同样的编码规则）"""
    return "&".join(f"{url_encode(k)}={url_encode(v)}"
                    for k, v in params.items() if v is not None)


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    appid: str = ""
    api_key: str = ""
    api_secret: str = ""

    # 接口参数
    language: str = "autodialect"        # autodialect | autominor
    pd: str = ""                         # 领域参数
    role_type: Optional[int] = None      # 0 不分离 / 1 通用 / 3 声纹
    role_num: Optional[int] = None       # 0-10
    feature_ids: str = ""                # roleType=3 时的声纹 id，逗号分隔
    smooth: Optional[bool] = None        # eng_smoothproc, 默认 True
    colloq: Optional[bool] = None         # eng_colloqproc, 默认 False
    vad_mode: Optional[int] = None       # eng_vad_mdn 1 远场 / 2 近场
    rlang: Optional[int] = None          # eng_rlang 0 简体 / 1 繁体
    analysis: Optional[int] = None       # 0 关闭 / 1 语种识别
    result_type: str = "transfer"        # getResult 的 resultType
    duration_check_disable: bool = False

    # 音频处理
    sample_rate: int = 16000
    channel: str = "mix"                 # mix | left | right
    audio_track: int = 0                 # 视频容器里取第几条音轨
    chunk_seconds: Optional[int] = None  # None=自动（能整段传就整段传）
    no_normalize: bool = False           # 不合规也原样上传
    keep_chunks: bool = False
    mux_subs: bool = False               # 视频：把字幕封装进视频（流拷贝，很快）
    burn_subs: bool = False              # 视频：把字幕烧进画面（需重编码，很慢）
    srt_alongside: bool = False          # 视频：把 srt 复制到视频同目录同名，播放器自动加载
    sub_language: str = "chi"            # 字幕轨语言标记

    # 轮询
    poll_interval: float = 10.0
    poll_timeout: float = 7200.0

    # 网络
    host: str = API_HOST
    insecure: bool = False
    upload_timeout: float = 3600.0

    # 输出
    out_dir: str = "asr_out"
    formats: Tuple[str, ...] = ("txt", "srt", "json", "subtitle")
    cue_chars: int = 32                  # 字幕单条最大字符数
    cue_seconds: float = 8.0             # 字幕单条最大时长
    punct_auto: bool = True              # 英文行全角标点转半角
    out_name: str = ""
    save_raw: bool = False
    resume: bool = True
    dry_run: bool = False


ENV_KEYS = {
    "appid": ("XF_APPID", "IFLYTEK_APPID", "APPID"),
    "api_key": ("XF_API_KEY", "XF_APIKEY", "IFLYTEK_API_KEY", "APIKEY"),
    "api_secret": ("XF_API_SECRET", "XF_APISECRET", "IFLYTEK_API_SECRET", "APISECRET"),
}


def load_env_file(path: Path) -> Dict[str, str]:
    """极简 .env 解析：KEY=VALUE / # 注释 / 允许引号"""
    data: Dict[str, str] = {}
    if not path.is_file():
        return data
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            data[key] = value
    return data


def resolve_credentials(cfg: Config, env_path: Optional[str]) -> None:
    """按 命令行 > 环境变量 > .env 的优先级补齐凭证"""
    candidates: List[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    here = Path(__file__).resolve().parent
    candidates += [Path.cwd() / ".env", here / ".env"]
    file_env: Dict[str, str] = {}
    for candidate in candidates:
        if candidate.is_file():
            file_env = load_env_file(candidate)
            break

    for attr, names in ENV_KEYS.items():
        if getattr(cfg, attr):
            continue
        for name in names:
            value = os.environ.get(name) or file_env.get(name)
            if value:
                setattr(cfg, attr, value.strip())
                break


# --------------------------------------------------------------------------- #
# 音频探测与切分
# --------------------------------------------------------------------------- #
def _find_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def require_ffmpeg() -> Tuple[str, str]:
    ffmpeg, ffprobe = _find_tool("ffmpeg"), _find_tool("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AsrError("未找到 ffmpeg/ffprobe，请先安装并加入 PATH（Windows: winget install Gyan.FFmpeg）")
    return ffmpeg, ffprobe


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".ts", ".m4v",
              ".wmv", ".mpg", ".mpeg", ".3gp", ".mts", ".m2ts", ".vob", ".rmvb"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".amr",
              ".pcm", ".wma", ".aiff", ".aif", ".speex", ".slk"}
MEDIA_EXTS = VIDEO_EXTS | AUDIO_EXTS

MP4_FAMILY = {".mp4", ".mov", ".m4v", ".3gp"}


def ffprobe_media(path: Path) -> Dict[str, Any]:
    """读取任意媒体文件（音频或视频容器）的音轨/视频轨信息"""
    _, ffprobe = require_ffmpeg()
    cmd = [ffprobe, "-v", "error",
           "-show_entries",
           "stream=index,codec_type,codec_name,sample_rate,channels,bits_per_sample,"
           "width,height,r_frame_rate,duration,bit_rate",
           "-show_entries", "format=duration,size,format_name",
           "-of", "json", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise AsrError(f"ffprobe 读取失败: {path.name} / {(proc.stderr or '').strip()[:300]}")
    data = json.loads(proc.stdout or "{}")
    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video_streams = [s for s in streams if s.get("codec_type") == "video"]

    audio = audio_streams[0] if audio_streams else {}
    try:
        audio_dur = float(audio.get("duration") or 0.0)
    except (TypeError, ValueError):
        audio_dur = 0.0
    try:
        fmt_dur = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        fmt_dur = 0.0
    duration_s = audio_dur or fmt_dur          # 视频容器优先用音轨时长做切分依据
    if duration_s <= 0:
        raise AsrError(f"无法读取时长: {path.name}")

    video_info: Dict[str, Any] = {}
    if video_streams:
        v = video_streams[0]
        try:
            num, _, den = str(v.get("r_frame_rate") or "0/1").partition("/")
            fps = round(float(num) / float(den or 1), 3)
        except (ValueError, ZeroDivisionError):
            fps = 0.0
        video_info = {
            "codec": str(v.get("codec_name") or ""),
            "width": int(v.get("width") or 0),
            "height": int(v.get("height") or 0),
            "fps": fps,
            "count": len(video_streams),
        }

    return {
        "duration_s": duration_s,
        "duration_ms": int(round(duration_s * 1000)),
        "codec": str(audio.get("codec_name") or ""),
        "sample_rate": int(audio.get("sample_rate") or 0),
        "channels": int(audio.get("channels") or 0),
        "bits": int(audio.get("bits_per_sample") or 0),
        "size": int(fmt.get("size") or path.stat().st_size),
        "format": str(fmt.get("format_name") or ""),
        "audio_stream_count": len(audio_streams),
        "has_video": bool(video_streams),
        "video": video_info,
    }


# 兼容旧名
ffprobe_audio = ffprobe_media


@dataclass
class Chunk:
    index: int
    path: str
    offset_ms: int
    duration_ms: int
    size: int
    temp: bool = True
    order_id: str = ""
    sig_random: str = ""
    status: str = "pending"          # pending | uploaded | done | failed
    fail_reason: str = ""
    segments: List[Dict[str, Any]] = field(default_factory=list)
    language: str = ""

    def to_json(self) -> Dict[str, Any]:
        return {
            "index": self.index, "path": self.path, "offset_ms": self.offset_ms,
            "duration_ms": self.duration_ms, "size": self.size, "temp": self.temp,
            "order_id": self.order_id, "sig_random": self.sig_random,
            "status": self.status, "fail_reason": self.fail_reason,
            "segments": self.segments, "language": self.language,
        }

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Chunk":
        return Chunk(
            index=int(data.get("index", 0)), path=str(data.get("path", "")),
            offset_ms=int(data.get("offset_ms", 0)), duration_ms=int(data.get("duration_ms", 0)),
            size=int(data.get("size", 0)), temp=bool(data.get("temp", True)),
            order_id=str(data.get("order_id", "")), sig_random=str(data.get("sig_random", "")),
            status=str(data.get("status", "pending")), fail_reason=str(data.get("fail_reason", "")),
            segments=list(data.get("segments") or []), language=str(data.get("language", "")),
        )


def _filter_chain(cfg: Config) -> List[str]:
    if cfg.channel == "left":
        return ["-af", "pan=mono|c0=c0"]
    if cfg.channel == "right":
        return ["-af", "pan=mono|c1=c0"]
    return ["-ac", "1"]


def convert_segment(src: Path, out: Path, start_s: float, dur_s: float, cfg: Config) -> None:
    """从任意媒体（含视频）里只取指定音轨，转成 16bit 单声道 PCM WAV 片段"""
    ffmpeg, _ = require_ffmpeg()
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
           "-ss", f"{start_s:.3f}", "-t", f"{dur_s:.3f}", "-i", str(src),
           "-vn", "-sn", "-dn", "-map", f"0:a:{cfg.audio_track}"]
    cmd += _filter_chain(cfg)
    cmd += ["-ar", str(cfg.sample_rate), "-c:a", "pcm_s16le", "-f", "wav", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not out.is_file():
        raise AsrError(f"ffmpeg 转码失败: {out.name} / {(proc.stderr or '').strip()[:300]}")


def prepare_chunks(src: Path, workdir: Path, cfg: Config) -> List[Chunk]:
    """把任意音频/视频变成「每片都符合接口要求」的清单（必要时提取音轨 + 转码 + 切分）"""
    info = ffprobe_media(src)
    total_ms = info["duration_ms"]
    size = src.stat().st_size

    if info["audio_stream_count"] == 0:
        kind = "视频文件里没有音轨" if info["has_video"] else "文件里没有音轨"
        raise AsrError(f"{src.name}：{kind}，无法转写")
    if cfg.audio_track >= info["audio_stream_count"]:
        raise AsrError(f"{src.name} 只有 {info['audio_stream_count']} 条音轨，"
                       f"--audio-track {cfg.audio_track} 越界（从 0 开始）")

    if info["has_video"]:
        video = info["video"]
        log(f"检测到视频容器：{video.get('codec')} {video.get('width')}x{video.get('height')}"
            f"@{video.get('fps')}fps，共 {info['audio_stream_count']} 条音轨，"
            f"将提取第 {cfg.audio_track + 1} 条音轨（{info['codec']} "
            f"{info['sample_rate']}Hz/{info['channels']}ch）转写")

    # 视频容器即使内含 PCM 音轨也不能整文件上传（服务端只认音频格式）
    conformant = (not info["has_video"]
                  and info["codec"] == "pcm_s16le"
                  and info["sample_rate"] == cfg.sample_rate
                  and info["channels"] == 1
                  and info["bits"] in (16, 0))

    if conformant and size <= SAFE_BYTES and total_ms <= SAFE_MS:
        log(f"音频已符合接口要求（{info['sample_rate']}Hz/16bit/单声道），直接上传",
            "√")
        return [Chunk(0, str(src), 0, total_ms, size, temp=False)]

    if cfg.no_normalize and not info["has_video"]:
        if size > MAX_UPLOAD_BYTES or total_ms > MAX_AUDIO_MS:
            raise AsrError("指定了 --no-normalize，但文件本身已超过 500MB / 5 小时限制，必须转码切分")
        log(f"--no-normalize：原样上传（{info['sample_rate']}Hz/{info['channels']}ch/"
            f"{info['bits']}bit），接口要求 16k/8k、16bit、单声道，可能识别失败", "!")
        return [Chunk(0, str(src), 0, total_ms, size, temp=False)]

    bytes_per_sec = cfg.sample_rate * 2                      # 16bit 单声道 wav
    max_sec_by_size = int(SAFE_BYTES // bytes_per_sec)
    hard_limit_s = min(max_sec_by_size, SAFE_MS // 1000)
    # 未显式指定 chunk-seconds 时：只要整段转码后仍在限制内就整段上传（订单更少、无切片边界影响）
    chunk_s = max(60, min(cfg.chunk_seconds, hard_limit_s)) if cfg.chunk_seconds else hard_limit_s

    workdir.mkdir(parents=True, exist_ok=True)
    pieces = max(1, math.ceil(total_ms / 1000.0 / chunk_s))
    log(f"需要转码：{info['sample_rate']}Hz/{info['channels']}ch/{info['bits']}bit "
        f"{human_size(size)} {human_dur(total_ms)} → {cfg.sample_rate}Hz/16bit/单声道，"
        f"共 {pieces} 片" + (f"（每片 {chunk_s}s）" if pieces > 1 else "（整段上传）"))

    chunks: List[Chunk] = []
    stem = src.stem
    for index in range(pieces):
        start_s = index * chunk_s
        remain_s = total_ms / 1000.0 - start_s
        dur_s = min(chunk_s, remain_s)
        if dur_s <= 0.2:
            break
        out = workdir / f"{stem}_part{index + 1:03d}.wav"
        need_convert = True
        if out.is_file() and out.stat().st_size > 0:
            try:                                    # 复用前校验时长，避免用到参数变更后的旧切片
                need_convert = abs(ffprobe_audio(out)["duration_ms"] - dur_s * 1000) > 1500
                if need_convert:
                    log(f"  已有切片 {out.name} 时长与本次不一致，重新生成", "!")
            except AsrError:
                need_convert = True
        if need_convert:
            t0 = time.time()
            convert_segment(src, out, start_s, dur_s, cfg)
            log(f"  切片 {index + 1}/{pieces} 完成 "
                f"[{human_dur(start_s * 1000)} ~ {human_dur((start_s + dur_s) * 1000)}] "
                f"{human_size(out.stat().st_size)} 用时 {time.time() - t0:.0f}s")
        out_info = ffprobe_audio(out)
        chunks.append(Chunk(
            index=index, path=str(out), offset_ms=int(round(start_s * 1000)),
            duration_ms=out_info["duration_ms"], size=out.stat().st_size, temp=True,
        ))
    if not chunks:
        raise AsrError("音频切分结果为空，请检查源文件是否有效")
    return chunks


# --------------------------------------------------------------------------- #
# API 客户端
# --------------------------------------------------------------------------- #
class XfyunAsrClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    # -- 公共参数 ---------------------------------------------------------- #
    def _base_params(self, sig_random: str) -> Dict[str, Any]:
        return {
            "appId": self.cfg.appid,
            "accessKeyId": self.cfg.api_key,
            "dateTime": now_datetime_str(),
            "signatureRandom": sig_random,
        }

    def _task_params(self) -> Dict[str, Any]:
        """上传接口的业务参数（值为 None 的自动不参与签名/URL）"""
        cfg = self.cfg
        params: Dict[str, Any] = {"language": cfg.language}
        if cfg.duration_check_disable:
            params["durationCheckDisable"] = "true"
        if cfg.pd:
            params["pd"] = cfg.pd
        if cfg.role_type is not None:
            params["roleType"] = str(cfg.role_type)
        if cfg.role_num is not None:
            params["roleNum"] = str(cfg.role_num)
        if cfg.feature_ids:
            params["featureIds"] = cfg.feature_ids
        if cfg.smooth is not None:
            params["eng_smoothproc"] = "true" if cfg.smooth else "false"
        if cfg.colloq is not None:
            params["eng_colloqproc"] = "true" if cfg.colloq else "false"
        if cfg.vad_mode is not None:
            params["eng_vad_mdn"] = str(cfg.vad_mode)
        if cfg.rlang is not None:
            params["eng_rlang"] = str(cfg.rlang)
        if cfg.analysis is not None:
            params["analysis"] = str(cfg.analysis)
        return params

    def _post_json(self, path: str, params: Dict[str, Any], body: bytes,
                   content_type: str, timeout: float,
                   accept_codes: Iterable[str] = (),
                   retry_codes: Iterable[str] = ("100012",),
                   max_retries: int = 6) -> Dict[str, Any]:
        last_error = ""
        for attempt in range(max_retries + 1):
            # 每次尝试都重新签名（dateTime 会过期）
            signature = make_signature(self.cfg.api_secret, params)
            url = f"{self.cfg.host}{path}?{encode_query(params)}"
            headers = {
                "Content-Type": content_type,
                "signature": signature,
                "Charset": "UTF-8",
                "Content-Length": str(len(body)),
            }
            status, raw = http_post(url, headers, body, timeout, self.cfg.insecure)
            text = raw.decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                raise AsrError(f"接口返回非 JSON（HTTP {status}）：{text[:400]}")
            code = str(data.get("code", "")).strip()
            if code == "000000" or code in accept_codes:
                return data
            desc = data.get("descInfo") or ERROR_CODES.get(code, "未知错误")
            last_error = (f"接口返回错误 code={code} ({ERROR_CODES.get(code, desc)}) desc={desc}"
                          f"\n  签名串: {build_base_string(params)[:300]}")
            if code in retry_codes and attempt < max_retries:
                wait = min(30, 5 * (attempt + 1))
                log(f"服务端限流 {code}，{wait}s 后重试（{attempt + 1}/{max_retries}）", "!")
                time.sleep(wait)
                continue
            raise AsrError(last_error)
        raise AsrError(last_error or "接口调用失败")

    # -- 上传 -------------------------------------------------------------- #
    def upload_file(self, path: Path, duration_ms: int) -> Dict[str, Any]:
        cfg = self.cfg
        if not path.is_file():
            raise AsrError(f"要上传的音频不存在: {path}（若为切片缓存被清理，请删除状态文件后重跑或用 --no-resume）")
        sig_random = random_str(16)
        size = path.stat().st_size
        if size > MAX_UPLOAD_BYTES:
            raise AsrError(f"{path.name} 大小 {human_size(size)} 超过接口上限 500MB")
        params = self._base_params(sig_random)
        params.update({"fileSize": str(size), "fileName": path.name})
        if not cfg.duration_check_disable:
            params["duration"] = str(int(duration_ms))
        params.update(self._task_params())

        signature = make_signature(cfg.api_secret, params)
        url = f"{cfg.host}{UPLOAD_PATH}?{encode_query(params)}"
        headers = {
            "Content-Type": "application/octet-stream",
            "signature": signature,
            "Charset": "UTF-8",
            "Content-Length": str(size),
        }
        log(f"上传 {path.name} ({human_size(size)}, {human_dur(duration_ms)}) …")
        t0 = time.time()
        with open(path, "rb") as handle:
            status, raw = http_post(url, headers, handle, cfg.upload_timeout, cfg.insecure)
        text = raw.decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise AsrError(f"上传返回非 JSON（HTTP {status}）：{text[:400]}")
        code = str(data.get("code", "")).strip()
        if code == "100012":                     # 限流：等待后重试一次（上传体较大，只重试一次）
            log("服务端限流 100012，20s 后重试上传", "!")
            time.sleep(20)
            params = self._base_params(sig_random)
            params.update({"fileSize": str(size), "fileName": path.name})
            if not cfg.duration_check_disable:
                params["duration"] = str(int(duration_ms))
            params.update(self._task_params())
            signature = make_signature(cfg.api_secret, params)
            url = f"{cfg.host}{UPLOAD_PATH}?{encode_query(params)}"
            headers = {"Content-Type": "application/octet-stream", "signature": signature,
                       "Charset": "UTF-8", "Content-Length": str(size)}
            with open(path, "rb") as handle:
                status, raw = http_post(url, headers, handle, cfg.upload_timeout, cfg.insecure)
            text = raw.decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                raise AsrError(f"上传返回非 JSON（HTTP {status}）：{text[:400]}")
            code = str(data.get("code", "")).strip()
        if code != "000000":
            desc = data.get("descInfo") or ERROR_CODES.get(code, "未知错误")
            raise AsrError(f"上传失败 code={code} ({ERROR_CODES.get(code, desc)}) desc={desc}"
                           f"\n  签名串: {build_base_string(params)[:300]}")
        content = data.get("content") or {}
        order_id = content.get("orderId") or ""
        if not order_id:
            raise AsrError(f"上传成功但未返回 orderId：{text[:300]}")
        estimate = int(content.get("taskEstimateTime") or 0)
        log(f"上传成功 orderId={order_id}，预计转写 {human_dur(estimate)}，耗时 {time.time() - t0:.0f}s", "√")
        data["_signature_random"] = sig_random
        return data

    def create_task_by_url(self, audio_url: str, signature_random: str = "") -> Dict[str, Any]:
        """audioMode=urlLink 外链转写（音频已在公网可访问时使用）"""
        cfg = self.cfg
        sig_random = signature_random or random_str(16)
        params = self._base_params(sig_random)
        params.update({"audioMode": "urlLink", "audioUrl": audio_url})
        params.update(self._task_params())
        data = self._post_json(UPLOAD_PATH, params, b"", "application/octet-stream", 120)
        data["_signature_random"] = sig_random
        return data

    # -- 查询 -------------------------------------------------------------- #
    def probe_auth(self) -> Tuple[str, str]:
        """鉴权探测：用不存在的 orderId 调 getResult，只验证签名是否通过。
        不会创建订单、不消耗转写额度。返回 (code, descInfo)。"""
        params = self._base_params(random_str(16))
        params.update({"ts": str(int(time.time())),
                       "orderId": "AUTHPROBE0000000000",
                       "resultType": "transfer"})
        signature = make_signature(self.cfg.api_secret, params)
        url = f"{self.cfg.host}{RESULT_PATH}?{encode_query(params)}"
        headers = {"Content-Type": "application/json", "signature": signature,
                   "Charset": "UTF-8", "Content-Length": "2"}
        status, raw = http_post(url, headers, b"{}", 30, self.cfg.insecure)
        text = raw.decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return (f"HTTP{status}", text[:200])
        return (str(data.get("code", "")).strip(), str(data.get("descInfo", "")))

    def get_result_once(self, order_id: str, sig_random: str) -> Dict[str, Any]:
        cfg = self.cfg
        params = self._base_params(sig_random)          # dateTime 每次重新生成
        params.update({
            "ts": str(int(time.time())),
            "orderId": order_id,
            "resultType": cfg.result_type,
        })
        return self._post_json(RESULT_PATH, params, b"{}", "application/json", 120,
                               accept_codes=("100013",))

    def wait_result(self, order_id: str, sig_random: str,
                    label: str = "") -> Dict[str, Any]:
        cfg = self.cfg
        started = time.time()
        tag = f"[{label}] " if label else ""
        last_note = ""
        while True:
            data = self.get_result_once(order_id, sig_random)
            if str(data.get("code")) == "100013":        # 订单未完成：按处理中继续等
                content: Dict[str, Any] = {}
                info: Dict[str, Any] = {"status": 3}
            else:
                content = data.get("content") or {}
                info = content.get("orderInfo") or {}
            status = info.get("status")
            fail_type = info.get("failType")
            estimate = int(content.get("taskEstimateTime") or 0)
            if status == 4:
                sys.stdout.write("\r" + " " * 78 + "\r")
                sys.stdout.flush()
                log(f"{tag}转写完成 orderId={order_id}", "√")
                return data
            if status == -1:
                sys.stdout.write("\r" + " " * 78 + "\r")
                sys.stdout.flush()
                reason = FAIL_TYPES.get(int(fail_type or 99), f"failType={fail_type}")
                raise AsrError(f"{tag}转写失败 orderId={order_id}：{reason}")
            waited = time.time() - started
            status_text = {0: "已创建", 3: "处理中"}.get(status, str(status))
            note = (f"{tag}转写中 已等待 {human_dur(waited * 1000)}"
                    f"/ 预估 {human_dur(estimate)} [{status_text}]")
            if note != last_note:
                sys.stdout.write("\r" + note.ljust(78))
                sys.stdout.flush()
                last_note = note
            if waited > cfg.poll_timeout:
                sys.stdout.write("\r" + " " * 78 + "\r")
                raise AsrError(f"{tag}等待超时（{human_dur(waited * 1000)}），orderId={order_id} 可稍后用 result 命令续查")
            time.sleep(cfg.poll_interval + secrets.randbelow(2000) / 1000.0)  # 加抖动，多任务并行时避开限流


# --------------------------------------------------------------------------- #
# 结果解析
# --------------------------------------------------------------------------- #
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
# 该接口会输出半角中文标点（官方样例中即为 ｡），统一成全角以便阅读与翻译
_HALFWIDTH_PUNCT = str.maketrans({
    "｡": "。", "､": "、", "｢": "「", "｣": "」", "･": "・", "｢": "「",
})


def _loads_lenient(text: str) -> Any:
    """容错解析：兼容官方示例里多一层反斜杠转义的情况"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(re.sub(r"\\\\", r"\\", text))


def _sentence_from_st(st: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """把单个 st（一个 VAD 句子）转成 {start,end,speaker,text,words}
    words 保留词级时间戳（ws.wb/ws.we 为相对 bg 的帧数，1 帧 = 10ms），供字幕切条使用"""
    try:
        bg = int(float(st.get("bg") or 0))
        ed = int(float(st.get("ed") or 0))
    except (TypeError, ValueError):
        bg = ed = 0
    speaker = st.get("rl")
    words: List[Dict[str, Any]] = []
    for rt in st.get("rt") or []:
        for ws in rt.get("ws") or []:
            candidates = ws.get("cw") or []
            if not candidates:
                continue
            best = candidates[0]
            word = best.get("w") or ""
            wp = best.get("wp") or "n"
            if wp == "g":                      # 分段标识，不参与文本
                continue
            word = re.sub(r"[ \t\u00a0]+", " ", word).translate(_HALFWIDTH_PUNCT)
            if not word:
                continue
            try:
                wb = float(ws.get("wb") or 0.0)
                we = float(ws.get("we") or 0.0)
            except (TypeError, ValueError):
                wb = we = 0.0
            start = bg + int(round(wb * 10))
            end = bg + int(round(we * 10))
            if wp == "p" and words:            # 标点是独立 token，并回前一个词，词级时间才不会割裂
                words[-1]["w"] += word
                words[-1]["e"] = max(words[-1]["e"], end)
            else:
                words.append({"w": word, "s": start, "e": end})
    fix_filler_spacing(words)
    text = re.sub(r"[ \t\u00a0]+", " ", "".join(w["w"] for w in words)).strip()
    if not text and ed <= bg:
        return None
    return {
        "start": bg, "end": ed,
        "speaker": str(speaker) if speaker not in (None, "") else "",
        "text": text,
        "words": words,
    }


def parse_order_result(content: Dict[str, Any], prefer: str = "lattice") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """解析 getResult 响应 content -> (句子列表, 附加信息)"""
    raw = content.get("orderResult") or ""
    info = content.get("orderInfo") or {}
    meta: Dict[str, Any] = {
        "order_id": info.get("orderId", ""),
        "original_duration_ms": int(info.get("originalDuration") or 0),
        "expire_time": info.get("expireTime"),
        "language": info.get("language") or content.get("language") or "",
        "status": info.get("status"),
        "fail_type": info.get("failType"),
    }
    if not raw:
        return [], meta

    try:
        data = _loads_lenient(raw)
    except json.JSONDecodeError:
        return [], meta

    keys = ["lattice", "lattice2"] if prefer == "lattice" else ["lattice2", "lattice"]
    items: List[Dict[str, Any]] = []
    for key in keys:
        cand = data.get(key)
        if isinstance(cand, list) and cand:
            items = cand
            meta["result_key"] = key
            break
    if isinstance(data.get("label"), dict):
        meta["label"] = data["label"]

    sentences: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        blob = item.get("json_1best") or item.get("onebest") or ""
        if not blob:
            continue
        try:
            parsed = _loads_lenient(blob)
        except json.JSONDecodeError:
            continue
        st = (parsed or {}).get("st") or parsed
        if isinstance(st, dict):
            sentence = _sentence_from_st(st)
            if sentence:
                sentences.append(sentence)
    sentences.sort(key=lambda s: (s["start"], s["end"]))
    return sentences, meta


def merge_segments(chunks: Iterable[Chunk], role_separation: bool = False) -> List[Dict[str, Any]]:
    """把各分片结果按 offset 拼回完整时间轴"""
    merged: List[Dict[str, Any]] = []
    for chunk in sorted(chunks, key=lambda c: c.offset_ms):
        for seg in chunk.segments:
            start = int(seg.get("start") or 0) + chunk.offset_ms
            end = int(seg.get("end") or 0) + chunk.offset_ms
            if end < start:
                end = start
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            words = [{"w": w.get("w", ""),
                      "s": int(w.get("s") or 0) + chunk.offset_ms,
                      "e": int(w.get("e") or 0) + chunk.offset_ms}
                     for w in (seg.get("words") or [])]
            merged.append({
                "start": start, "end": end,
                "speaker": seg.get("speaker") or "",
                "text": text,
                "words": words,
            })
    merged.sort(key=lambda s: (s["start"], s["end"]))
    # 相邻完全重复的句子（切片边界偶发）去重
    deduped: List[Dict[str, Any]] = []
    for seg in merged:
        if deduped and seg["text"] == deduped[-1]["text"] and abs(seg["start"] - deduped[-1]["start"]) < 300:
            continue
        deduped.append(seg)
    # 未开启角色分离时，接口仍可能回 rl="0"，只有一个说话人就不显示
    speakers = {s["speaker"] for s in deduped if s["speaker"]}
    if not role_separation and len(speakers) <= 1:
        for seg in deduped:
            seg["speaker"] = ""
    for idx, seg in enumerate(deduped, 1):
        seg["index"] = idx
    return deduped


_CUE_PUNCT = "，。！？；：、,.!?;:）)」』"

# 停顿词常被接口输出成紧贴后词的 token（如 uhWe、umAnother），补一个空格
_FILLER_WORDS = {"uh", "uhh", "um", "umm", "er", "erm", "ah", "eh", "oh", "hmm", "mm", "mmm"}


def fix_filler_spacing(words: List[Dict[str, Any]]) -> None:
    """原地修正：停顿词（uh/um…）与前/后词之间缺失的空格"""
    for prev, cur in zip(words, words[1:]):
        prev_text = prev.get("w") or ""
        cur_text = cur.get("w") or ""
        if not prev_text or not cur_text:
            continue
        if prev_text.endswith((" ", "\t")) or cur_text.startswith((" ", "\t")):
            continue                                  # 已有空格边界，不用处理
        if prev_text.strip().lower() in _FILLER_WORDS:
            prev["w"] = prev_text + " "
        elif cur_text.strip().lower() in _FILLER_WORDS:
            cur["w"] = " " + cur_text

# 英文行里出现全角标点很扎眼，按行判断语种后转换为半角
_FW_TO_HW = str.maketrans({"，": ",", "。": ".", "？": "?", "！": "!", "：": ":",
                           "；": ";", "（": "(", "）": ")", "、": ",",
                           "“": '"', "”": '"', "‘": "'", "’": "'"})
_FW_PUNCT_RE = re.compile(r"([，。？！；：、])(?=[^\s，。？！；：、）)」』])")
_FW_PUNCT_MAP = {"，": ",", "。": ".", "？": "?", "！": "!", "：": ":", "；": ";", "、": ","}


def fix_punct(text: str) -> str:
    """纯英文/拉丁字符行（中文占比 <20%）把全角标点转半角并补空格；中文行原样保留"""
    if not text:
        return text
    latin = sum(1 for ch in text if ch.isascii() and (ch.isalnum() or ch.isspace()))
    cjk = sum(1 for ch in text if _CJK_RE.match(ch))
    if latin and latin >= (latin + cjk) * 0.8:
        text = _FW_PUNCT_RE.sub(lambda m: _FW_PUNCT_MAP[m.group(1)] + " ", text)
        return text.translate(_FW_TO_HW)
    return text


def _split_one_segment(seg: Dict[str, Any], max_chars: int, min_chars: int,
                       max_ms: int) -> List[Dict[str, Any]]:
    """按词级时间戳把长句切成字幕条"""
    words = [(w.get("w", ""), int(w.get("s") or 0), int(w.get("e") or 0))
             for w in (seg.get("words") or []) if (w.get("w") or "").strip()]
    if not words:
        return [{"start": seg["start"], "end": seg["end"],
                 "speaker": seg.get("speaker", ""), "text": seg["text"]}]
    has_timing = any(s != e for _, s, e in words)
    out: List[Dict[str, Any]] = []
    buf: List[Tuple[str, int, int]] = []
    buf_chars = 0
    cue_start = words[0][1]

    def flush() -> None:
        nonlocal buf, buf_chars
        if not buf:
            return
        text = "".join(item[0] for item in buf).strip()
        if text:
            start = buf[0][1] if has_timing else seg["start"]
            end = buf[-1][2] if has_timing else seg["end"]
            out.append({"start": start, "end": max(end, start + 200),
                        "speaker": seg.get("speaker", ""), "text": text})
        buf, buf_chars = [], 0

    punct_floor = max(min_chars, int(max_chars * 0.4))
    for word, ws_, we_ in words:
        length = len(word)                       # 含词间空格，保证切出的文本不超上限
        if buf and (buf_chars + length > max_chars
                    or (has_timing and we_ - cue_start > max_ms)):
            flush()
        if not buf:                              # 新的一条从当前词开始计时
            cue_start = ws_
        buf.append((word, ws_, we_))
        buf_chars += length
        stripped = word.strip()
        if stripped and stripped[-1] in _CUE_PUNCT and buf_chars >= punct_floor:
            flush()
    flush()

    if not has_timing and len(out) > 1:            # 没有词级时间：按字符数比例分配
        span = max(1, seg["end"] - seg["start"])
        total = sum(len(c["text"]) for c in out) or 1
        cursor = seg["start"]
        for cue in out:
            dur = max(200, span * len(cue["text"]) // total)
            cue["start"] = cursor
            cue["end"] = min(seg["end"], cursor + dur)
            cursor = cue["end"]
        out[-1]["end"] = seg["end"]
    if not out:
        return [{"start": seg["start"], "end": seg["end"],
                 "speaker": seg.get("speaker", ""), "text": seg["text"]}]
    return out


def split_into_cues(segments: List[Dict[str, Any]], max_chars: int = 32,
                    max_seconds: float = 8.0, min_chars: int = 8,
                    punct_auto: bool = True) -> List[Dict[str, Any]]:
    """字幕粒度：长句切条，短句保持原样"""
    max_ms = int(max_seconds * 1000)
    cues: List[Dict[str, Any]] = []
    for seg in segments:
        if len(seg["text"]) <= max_chars and seg["end"] - seg["start"] <= max_ms:
            cues.append({"start": seg["start"], "end": seg["end"],
                         "speaker": seg.get("speaker", ""), "text": seg["text"]})
        else:
            cues.extend(_split_one_segment(seg, max_chars, min_chars, max_ms))
    if punct_auto:                            # 整行判断语种后规整标点（标点是独立 token，必须拼完再判）
        for cue in cues:
            cue["text"] = fix_punct(cue["text"])
    for idx, cue in enumerate(cues, 1):
        cue["index"] = idx
    return cues


def smart_join(parts: List[str]) -> str:
    out = ""
    for part in parts:
        if not part:
            continue
        if not out:
            out = part
            continue
        if _CJK_RE.search(out[-1:]) or _CJK_RE.search(part[:1]):
            out += part
        else:
            out += " " + part
    return out


def build_paragraphs(segments: List[Dict[str, Any]], gap_ms: int = 2000) -> List[Dict[str, Any]]:
    paragraphs: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for seg in segments:
        speaker = seg.get("speaker") or ""
        if (current is None
                or current["speaker"] != speaker
                or seg["start"] - current["end"] > gap_ms):
            if current:
                current["text"] = smart_join(current.pop("_parts"))
                paragraphs.append(current)
            current = {"start": seg["start"], "end": seg["end"],
                       "speaker": speaker, "_parts": [seg["text"]]}
        else:
            current["_parts"].append(seg["text"])
            current["end"] = max(current["end"], seg["end"])
    if current:
        current["text"] = smart_join(current.pop("_parts"))
        paragraphs.append(current)
    return paragraphs


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #
def _speaker_prefix(speaker: str) -> str:
    return f"说话人{speaker}: " if speaker else ""


def render_txt(segments: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    lines = [
        f"文件: {meta.get('source', '')}",
        f"时长: {human_dur(meta.get('duration_ms', 0))}",
        f"引擎: 讯飞录音文件转写大模型 ({meta.get('language', '')})",
        f"订单: {', '.join(meta.get('orders') or [])}",
        "=" * 70,
        "",
    ]
    for para in build_paragraphs(segments):
        lines.append(f"{_speaker_prefix(para['speaker'])}{para['text']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_md(segments: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    lines = [
        f"# {meta.get('source', '')}",
        "",
        f"- 时长：{human_dur(meta.get('duration_ms', 0))}",
        f"- 引擎：讯飞录音文件转写大模型（{meta.get('language', '')}）",
        f"- 订单：{', '.join(meta.get('orders') or []) or '-'}",
        f"- 句子数：{len(segments)}",
        "",
        "## 转写文本",
        "",
    ]
    for para in build_paragraphs(segments):
        stamp = f"[{human_dur(para['start'])} - {human_dur(para['end'])}]"
        lines.append(f"**{stamp}**{(' ' + _speaker_prefix(para['speaker']).strip()) or ''}")
        lines.append("")
        lines.append(para["text"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_srt(cues: List[Dict[str, Any]]) -> str:
    blocks = []
    for idx, seg in enumerate(cues, 1):
        text = f"{_speaker_prefix(seg['speaker'])}{seg['text']}"
        blocks.append(f"{idx}\n{srt_ts(seg['start'])} --> {srt_ts(seg['end'])}\n{text}\n")
    return "\n".join(blocks)


def render_subtitle_json(cues: List[Dict[str, Any]]) -> str:
    """与项目内既有【原始字幕】格式一致：{"1": {start_time, end_time, original_subtitle, translated_subtitle}}"""
    payload = {}
    for idx, seg in enumerate(cues, 1):
        payload[str(idx)] = {
            "start_time": int(seg["start"]),
            "end_time": int(seg["end"]),
            "original_subtitle": seg["text"],
            "translated_subtitle": "",
        }
    return json.dumps(payload, ensure_ascii=False, indent=1)


def render_json(segments: List[Dict[str, Any]], meta: Dict[str, Any],
                cues: Optional[List[Dict[str, Any]]] = None) -> str:
    payload = {
        "source": meta.get("source", ""),
        "duration_ms": meta.get("duration_ms", 0),
        "language": meta.get("language", ""),
        "orders": meta.get("orders") or [],
        "chunks": meta.get("chunks") or [],
        "text": smart_join([s["text"] for s in segments]),
        "segments": [
            {"index": s["index"], "start": s["start"], "end": s["end"],
             "speaker": s["speaker"], "text": s["text"]}
            for s in segments
        ],
    }
    if cues is not None:
        payload["cues"] = [
            {"index": c["index"], "start": c["start"], "end": c["end"],
             "speaker": c["speaker"], "text": c["text"]}
            for c in cues
        ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def write_outputs(segments: List[Dict[str, Any]], meta: Dict[str, Any], cfg: Config,
                  stem: str) -> List[Path]:
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = cfg.out_name or stem
    if cfg.punct_auto:                       # 英文行全角标点转半角（仅影响输出，不改状态文件）
        for seg in segments:
            seg["text"] = fix_punct(seg["text"])
            for word in seg.get("words") or []:
                word["w"] = fix_punct(word.get("w", ""))
    cues = split_into_cues(segments, cfg.cue_chars, cfg.cue_seconds,
                           punct_auto=cfg.punct_auto)
    written: List[Path] = []
    writers = {
        "txt": (".txt", lambda: render_txt(segments, meta)),
        "md": (".md", lambda: render_md(segments, meta)),
        "srt": (".srt", lambda: render_srt(cues)),
        "json": (".json", lambda: render_json(segments, meta, cues)),
        "subtitle": (".subtitle.json", lambda: render_subtitle_json(cues)),
    }
    for fmt in cfg.formats:
        if fmt not in writers:
            raise AsrError(f"未知输出格式: {fmt}（可选 {', '.join(writers)}）")
        suffix, builder = writers[fmt]
        path = out_dir / f"{base}{suffix}"
        path.write_text(builder(), encoding="utf-8")
        written.append(path)
    return written


def render_from_state(src: Path, cfg: Config) -> List[Path]:
    """只根据已保存的状态文件重新生成输出（不再调用接口，不重复计费）"""
    state_file = state_path_for(cfg, src)
    state = load_state(state_file, src)
    if not state:
        raise AsrError(f"未找到可用的状态文件：{state_file}（先跑一次 run）")
    chunks = [Chunk.from_json(raw) for raw in state.get("chunks") or []]
    if not any(c.segments for c in chunks):
        raise AsrError(f"状态文件里还没有转写结果：{state_file}")
    missing = [c.index + 1 for c in chunks if not c.segments]
    if missing:
        log(f"分片 {missing} 还没有结果，输出只包含已完成部分", "!")
    segments = merge_segments(chunks, role_separation=bool(cfg.role_type))
    duration = int(state.get("duration_ms") or 0)
    meta = {
        "source": src.name,
        "duration_ms": max(duration, max((s["end"] for s in segments), default=0)),
        "language": next((c.language for c in chunks if c.language), cfg.language),
        "orders": [c.order_id for c in chunks if c.order_id],
        "chunks": [{"index": c.index + 1, "offset_ms": c.offset_ms,
                    "duration_ms": c.duration_ms, "order_id": c.order_id} for c in chunks],
    }
    written = write_outputs(segments, meta, cfg, src.stem)
    log(f"已从状态文件重新生成：{len(segments)} 句", "√")
    for path in written:
        log(f"  → {path}")
    return written


def refresh_from_orders(src: Path, cfg: Config) -> List[Path]:
    """用状态文件里的 orderId 重新拉取结果并重新解析（查询不产生新订单、不计费）"""
    state_file = state_path_for(cfg, src)
    state = load_state(state_file, src)
    if not state:
        raise AsrError(f"未找到可用的状态文件：{state_file}")
    chunks = [Chunk.from_json(raw) for raw in state.get("chunks") or []]
    usable = [c for c in chunks if c.order_id and c.sig_random]
    if not usable:
        raise AsrError(f"状态文件里没有可用的 orderId/signatureRandom：{state_file}")
    client = XfyunAsrClient(cfg)
    raw_dir = Path(cfg.out_dir) / "_raw" / (cfg.out_name or src.stem)
    for chunk in usable:
        label = f"#{chunk.index + 1}/{len(chunks)}"
        data = client.wait_result(chunk.order_id, chunk.sig_random, label)
        segments, meta = parse_order_result(data.get("content") or {})
        chunk.segments = segments
        chunk.language = meta.get("language", "")
        chunk.status = "done"
        chunk.fail_reason = ""
        save_state(state_file, src, chunks)
        if cfg.save_raw:
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"part{chunk.index + 1:03d}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"{label} 重新解析到 {len(segments)} 句", "√")
    written = render_from_state(src, cfg)
    save_state(state_file, src, chunks,
               {k: v for k, v in (state or {}).items()
                if k in ("finished_at", "segment_count", "duration_ms")})
    return written


# --------------------------------------------------------------------------- #
# 视频：字幕封装 / 烧录
# --------------------------------------------------------------------------- #
def _video_subtitle_target(video: Path, cfg: Config, burn: bool) -> Path:
    out_dir = Path(cfg.out_dir)
    suffix = f".{'烧录' if burn else ''}字幕"
    ext = ".mp4" if (video.suffix.lower() in MP4_FAMILY and not burn) else ".mkv"
    return out_dir / f"{cfg.out_name or video.stem}{suffix}{ext}"


def mux_subtitles(video: Path, srt: Path, cfg: Config) -> Optional[Path]:
    """把字幕作为独立字幕轨封装进视频（视频/音频流拷贝，画质无损、几乎不耗时）"""
    ffmpeg, _ = require_ffmpeg()
    target = _video_subtitle_target(video, cfg, burn=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    sub_codec = "mov_text" if target.suffix.lower() == ".mp4" else "srt"
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
           "-i", str(video), "-i", str(srt),
           "-map", "0:v:0", "-map", "0:a?", "-map", "1:0",
           "-c:v", "copy", "-c:a", "copy", "-c:s", sub_codec,
           "-metadata:s:s:0", f"language={cfg.sub_language}",
           "-metadata:s:s:0", f"title={cfg.sub_language}",
           "-disposition:s:0", "default", str(target)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not target.is_file():
        log(f"字幕封装失败（可改用 --burn-subs）：{(proc.stderr or '').strip()[:200]}", "×")
        return None
    return target


def burn_subtitles(video: Path, srt: Path, cfg: Config) -> Optional[Path]:
    """把字幕烧进画面（需要重编码视频，4K 素材会很慢）"""
    ffmpeg, _ = require_ffmpeg()
    target = _video_subtitle_target(video, cfg, burn=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    # 中文路径在 subtitles 滤镜里转义很脆弱：先把字幕拷到纯 ASCII 临时目录，再用相对路径引用
    tmp_dir = Path(tempfile.mkdtemp(prefix="asr_sub_"))
    try:
        local_srt = tmp_dir / "sub.srt"
        shutil.copyfile(srt, local_srt)
        style = ("FontName=Microsoft YaHei,FontSize=18,Outline=1,Shadow=0,"
                 "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,"
                 "BorderStyle=1,Outline=1,Shadow=0,MarginV=24")
        cmd = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
               "-i", str(video.resolve()),
               "-vf", f"subtitles=sub.srt:force_style='{style}'",
               "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "20", "-c:a", "copy", str(target.resolve())]
        proc = subprocess.run(cmd, cwd=str(tmp_dir), capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0 or not target.is_file():
            log(f"字幕烧录失败：{(proc.stderr or '').strip()[:200]}", "×")
            return None
        return target
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def add_subtitles_to_video(src: Path, srt: Optional[Path], cfg: Config) -> List[Path]:
    """视频输入处理完后，按需生成带字幕的视频 / 旁挂字幕"""
    produced: List[Path] = []
    if not srt or not srt.is_file():
        log("没有生成 srt，跳过视频字幕处理", "!")
        return produced
    if cfg.mux_subs:
        log("正在把字幕封装进视频（流拷贝，画质无损）…")
        path = mux_subtitles(src, srt, cfg)
        if path:
            produced.append(path)
            log(f"  → {path}（{human_size(path.stat().st_size)}）", "√")
    if cfg.burn_subs:
        log("正在把字幕烧进画面（需重编码，请耐心等待）…")
        t0 = time.time()
        path = burn_subtitles(src, srt, cfg)
        if path:
            produced.append(path)
            log(f"  → {path}（{human_size(path.stat().st_size)}，用时 {time.time() - t0:.0f}s）", "√")
    if cfg.srt_alongside:
        target = src.with_suffix(".srt")
        try:
            shutil.copyfile(srt, target)
            produced.append(target)
            log(f"字幕已放到视频旁（播放器会自动加载）：", "√")
            log(f"  → {target}")
        except OSError as exc:
            log(f"复制 srt 到视频目录失败：{exc}", "×")
    return produced


# --------------------------------------------------------------------------- #
# 状态文件（断点续跑）
# --------------------------------------------------------------------------- #
def state_path_for(cfg: Config, src: Path) -> Path:
    out_dir = Path(cfg.out_dir)
    return out_dir / f"{cfg.out_name or src.stem}.state.json"


def load_state(path: Path, src: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    try:
        st = src.stat()
    except OSError:
        return None
    if data.get("size") != st.st_size or int(data.get("mtime", 0)) != int(st.st_mtime):
        log(f"状态文件与源文件不一致，忽略旧状态：{path.name}", "!")
        return None
    return data


def save_state(path: Path, src: Path, chunks: List[Chunk], extra: Optional[Dict[str, Any]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    st = src.stat()
    payload = {
        "source": str(src),
        "name": src.name,
        "size": st.st_size,
        "mtime": int(st.st_mtime),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "chunks": [c.to_json() for c in chunks],
    }
    if extra:
        payload.update(extra)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def transcribe_file(src: Path, cfg: Config) -> Dict[str, Any]:
    if not src.is_file():
        raise AsrError(f"文件不存在: {src}")
    require_ffmpeg()
    client = XfyunAsrClient(cfg)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_path_for(cfg, src)
    workdir = out_dir / "_chunks" / (cfg.out_name or src.stem)

    info = ffprobe_media(src)
    kind = "视频" if info["has_video"] else "音频"
    log(f"源{kind}: {src.name} | {human_size(info['size'])} | {human_dur(info['duration_ms'])} | "
        f"{info['sample_rate']}Hz/{info['channels']}ch/{info['bits']}bit/{info['codec']}"
        + (f" | 视频 {info['video'].get('codec')} "
           f"{info['video'].get('width')}x{info['video'].get('height')}" if info["has_video"] else ""))

    chunks: Optional[List[Chunk]] = None
    previous: Dict[int, Chunk] = {}
    if cfg.resume:
        state = load_state(state_file, src)
        if state and state.get("chunks"):
            for raw in state["chunks"]:
                prev = Chunk.from_json(raw)
                previous[prev.index] = prev
            reused = [c for c in previous.values() if c.order_id]
            if reused:
                log(f"断点续跑：{len(reused)} 个分片已有订单号，将直接续查而不再上传", "√")
    chunks = prepare_chunks(src, workdir, cfg)
    # 把历史 orderId / 结果并回新清单（同样的参数切出来的分片 index 一一对应）
    restored = 0
    for chunk in chunks:
        prev = previous.get(chunk.index)
        if prev and (prev.order_id or prev.segments):
            chunk.order_id = prev.order_id
            chunk.sig_random = prev.sig_random
            chunk.segments = prev.segments
            chunk.language = prev.language
            chunk.fail_reason = prev.fail_reason
            chunk.status = "done" if prev.segments else "uploaded"
            restored += 1
    if restored and not any(c.order_id for c in previous.values()):
        log("历史状态里没有可用订单号，需重新上传", "!")
    save_state(state_file, src, chunks)

    if cfg.dry_run:
        log("--dry-run：不发起网络请求。分片清单如下：")
        for chunk in chunks:
            log(f"  #{chunk.index + 1} {Path(chunk.path).name} "
                f"[{human_dur(chunk.offset_ms)} ~ {human_dur(chunk.offset_ms + chunk.duration_ms)}] "
                f"{human_size(chunk.size)}")
        return {"dry_run": True, "chunks": [c.to_json() for c in chunks]}

    # 1) 上传（状态文件里已有 orderId 的跳过）
    for chunk in chunks:
        if chunk.status in ("uploaded", "done") and chunk.order_id:
            log(f"#{chunk.index + 1} 已上传，orderId={chunk.order_id}", "√")
            continue
        data = client.upload_file(Path(chunk.path), chunk.duration_ms)
        chunk.order_id = (data.get("content") or {}).get("orderId", "")
        chunk.sig_random = data["_signature_random"]
        chunk.status = "uploaded"
        save_state(state_file, src, chunks)

    # 2) 轮询结果
    raw_dir = out_dir / "_raw" / (cfg.out_name or src.stem)
    for chunk in chunks:
        if chunk.status == "done" and chunk.segments:
            log(f"#{chunk.index + 1} 已有转写结果，跳过", "√")
            continue
        label = f"#{chunk.index + 1}/{len(chunks)}"
        try:
            data = client.wait_result(chunk.order_id, chunk.sig_random, label)
        except AsrError as exc:
            # 订单已创建，绝不能丢掉它能续查的信息：保留 uploaded，只记录原因
            chunk.status = "done" if chunk.segments else "uploaded"
            chunk.fail_reason = str(exc)[:500]
            save_state(state_file, src, chunks)
            raise
        segments, meta = parse_order_result(data.get("content") or {}, prefer="lattice")
        chunk.segments = segments
        chunk.language = meta.get("language", "")
        chunk.status = "done"
        save_state(state_file, src, chunks)
        if cfg.save_raw:
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"part{chunk.index + 1:03d}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"{label} 解析到 {len(segments)} 句（{human_dur(chunk.duration_ms)}）", "√")

    # 3) 合并 + 输出
    segments = merge_segments(chunks, role_separation=bool(cfg.role_type))
    meta = {
        "source": src.name,
        "duration_ms": max(info["duration_ms"],
                           max((s["end"] for s in segments), default=0)),
        "language": next((c.language for c in chunks if c.language), cfg.language),
        "orders": [c.order_id for c in chunks if c.order_id],
        "chunks": [{"index": c.index + 1, "offset_ms": c.offset_ms,
                    "duration_ms": c.duration_ms, "order_id": c.order_id} for c in chunks],
    }
    written = write_outputs(segments, meta, cfg, src.stem)
    save_state(state_file, src, chunks, {"finished_at": datetime.now().isoformat(timespec="seconds"),
                                         "segment_count": len(segments),
                                         "duration_ms": info["duration_ms"]})

    if not cfg.keep_chunks:
        for chunk in chunks:
            if chunk.temp:
                try:
                    Path(chunk.path).unlink(missing_ok=True)
                except OSError:
                    pass
        try:
            if workdir.is_dir() and not any(workdir.iterdir()):
                workdir.rmdir()
        except OSError:
            pass

    log(f"完成：{len(segments)} 句 / {len(smart_join([s['text'] for s in segments]))} 字", "√")
    for path in written:
        log(f"  → {path}")

    # 4) 视频输入：按需产出「带字幕的视频 / 旁挂字幕」
    outputs = [str(p) for p in written]
    if info["has_video"]:
        if cfg.mux_subs or cfg.burn_subs or cfg.srt_alongside:
            srt_path = next((p for p in written if p.suffix.lower() == ".srt"), None)
            if srt_path:
                outputs += [str(p) for p in add_subtitles_to_video(src, srt_path, cfg)]
            else:
                log("本次未生成 srt（--format 里没有 srt），无法封装字幕；"
                    "先加 srt 重新生成：render 加 --format srt", "!")
        else:
            log("提示：这是视频文件，加 --mux-subs 另存一份带字幕的视频（流拷贝，很快）、"
                "--srt-alongside 把字幕放到视频旁让播放器自动加载、"
                "--burn-subs 把字幕烧进画面", "·")

    return {"segments": segments, "meta": meta, "outputs": outputs}


# --------------------------------------------------------------------------- #
# 凭证自检
# --------------------------------------------------------------------------- #
AUTH_OK_CODES = {"100001", "100004", "100037", "100039", "100002"}
AUTH_BAD_CODES = {"100009", "100008", "000002", "100007"}


def check_auth(cfg: Config, quiet: bool = False) -> bool:
    """验证 AppID/APIKey/APISecret 是否正确（不消耗转写额度）"""

    def mask(value: str) -> str:
        return value if len(value) <= 8 else f"{value[:4]}…{value[-4:]}"

    if not quiet:
        log(f"AppID={cfg.appid} APIKey={mask(cfg.api_key)} APISecret={mask(cfg.api_secret)}")
    candidates: List[Tuple[str, str]] = [("原样", cfg.api_secret)]
    try:                                        # 控制台有时显示 base64 形式的 secret，兜底再试一次
        decoded = base64.b64decode(cfg.api_secret, validate=True).decode("utf-8")
        if decoded != cfg.api_secret and decoded.strip():
            candidates.append(("base64 解码后", decoded))
    except Exception:
        pass

    for label, secret in candidates:
        probe = Config(**{**cfg.__dict__, "api_secret": secret})
        code, desc = XfyunAsrClient(probe).probe_auth()
        if code in AUTH_OK_CODES:
            if not quiet:
                log(f"凭证有效（APISecret 按「{label}」使用）", "√")
                log(f"  服务端响应 code={code} {ERROR_CODES.get(code, '')}——说明签名已通过，仅订单号不存在")
            if secret != cfg.api_secret:
                log(f"  注意：APISecret 应使用 base64 解码后的值：{secret}", "!")
            return True
        if code in AUTH_BAD_CODES:
            if not quiet:
                log(f"APISecret 按「{label}」试算未通过：code={code} {ERROR_CODES.get(code, '')} {desc}", "×")
            continue
        if not quiet:
            log(f"未知响应 code={code} desc={desc}", "!")
        return False
    return False


# --------------------------------------------------------------------------- #
# 自检
# --------------------------------------------------------------------------- #
DOC_SAMPLE_ORDER_RESULT = (
    '{"lattice":[{"json_1best":"{\\"st\\":{\\"pa\\":\\"0\\",\\"rt\\":[{\\"ws\\":[{\\"cw\\":'
    '[{\\"w\\":\\"为\\",\\"wp\\":\\"n\\",\\"wc\\":\\"0.7511\\"}],\\"wb\\":22,\\"we\\":75}]}],'
    '\\"bg\\":\\"880\\",\\"rl\\":\\"1\\",\\"ed\\":\\"1680\\"}}"}'
    ',{"json_1best":"{\\"st\\":{\\"pa\\":\\"0\\",\\"rt\\":[{\\"ws\\":[{\\"cw\\":'
    '[{\\"w\\":\\"喂\\",\\"wp\\":\\"s\\",\\"wc\\":\\"0.9806\\"}],\\"wb\\":19,\\"we\\":52},'
    '{\\"cw\\":[{\\"w\\":\\"你好\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":53,\\"we\\":111},'
    '{\\"cw\\":[{\\"w\\":\\"｡\\",\\"wp\\":\\"p\\",\\"wc\\":\\"0.0000\\"}],\\"wb\\":111,\\"we\\":111}]}],'
    '\\"bg\\":\\"2390\\",\\"rl\\":\\"1\\",\\"ed\\":\\"3640\\"}}"}'
    ',{"json_1best":"{\\"st\\":{\\"pa\\":\\"0\\",\\"rt\\":[{\\"ws\\":[{\\"cw\\":'
    '[{\\"w\\":\\"舒\\",\\"wp\\":\\"n\\",\\"wc\\":\\"0.8630\\"}],\\"wb\\":20,\\"we\\":44},'
    '{\\"cw\\":[{\\"w\\":\\"高\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":45,\\"we\\":65},'
    '{\\"cw\\":[{\\"w\\":\\"生\\",\\"wp\\":\\"n\\",\\"wc\\":\\"0.2461\\"}],\\"wb\\":66,\\"we\\":79},'
    '{\\"cw\\":[{\\"w\\":\\"先生\\",\\"wp\\":\\"n\\",\\"wc\\":\\"0.9709\\"}],\\"wb\\":80,\\"we\\":109},'
    '{\\"cw\\":[{\\"w\\":\\"是\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":110,\\"we\\":118},'
    '{\\"cw\\":[{\\"w\\":\\"吧\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":119,\\"we\\":138},'
    '{\\"cw\\":[{\\"w\\":\\"?\\",\\"wp\\":\\"p\\",\\"wc\\":\\"0.0000\\"}],\\"wb\\":138,\\"we\\":138},'
    '{\\"cw\\":[{\\"w\\":\\"喂\\",\\"wp\\":\\"s\\",\\"wc\\":\\"0.9078\\"}],\\"wb\\":139,\\"we\\":144}]}],'
    '\\"bg\\":\\"5130\\",\\"rl\\":\\"1\\",\\"ed\\":\\"7200\\"}}"}'
    ',{"json_1best":"{\\"st\\":{\\"pa\\":\\"0\\",\\"rt\\":[{\\"ws\\":[{\\"cw\\":'
    '[{\\"w\\":\\"为\\",\\"wp\\":\\"n\\",\\"wc\\":\\"0.7511\\"}],\\"wb\\":3,\\"we\\":115},'
    '{\\"cw\\":[{\\"w\\":\\"｡\\",\\"wp\\":\\"p\\",\\"wc\\":\\"0.0000\\"}],\\"wb\\":115,\\"we\\":115}]}],'
    '\\"bg\\":\\"7200\\",\\"rl\\":\\"1\\",\\"ed\\":\\"8650\\"}}"}'
    ',{"json_1best":"{\\"st\\":{\\"pa\\":\\"0\\",\\"rt\\":[{\\"ws\\":[{\\"cw\\":'
    '[{\\"w\\":\\"喂\\",\\"wp\\":\\"s\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":64,\\"we\\":88},'
    '{\\"cw\\":[{\\"w\\":\\"听\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":89,\\"we\\":106},'
    '{\\"cw\\":[{\\"w\\":\\"得到\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":107,\\"we\\":128},'
    '{\\"cw\\":[{\\"w\\":\\"吗\\",\\"wp\\":\\"n\\",\\"wc\\":\\"1.0000\\"}],\\"wb\\":129,\\"we\\":166},'
    '{\\"cw\\":[{\\"w\\":\\"?\\",\\"wp\\":\\"p\\",\\"wc\\":\\"0.0000\\"}],\\"wb\\":166,\\"we\\":166},'
    '{\\"cw\\":[{\\"w\\":\\"一\\",\\"wp\\":\\"n\\",\\"wc\\":\\"0.8993\\"}],\\"wb\\":167,\\"we\\":169},'
    '{\\"cw\\":[{\\"w\\":\\"｡\\",\\"wp\\":\\"p\\",\\"wc\\":\\"0.0000\\"}],\\"wb\\":169,\\"we\\":169},'
    '{\\"cw\\":[{\\"w\\":\\"\\",\\"wp\\":\\"g\\",\\"wc\\":\\"0.0000\\"}],\\"wb\\":169,\\"we\\":169}]}],'
    '\\"bg\\":\\"9330\\",\\"rl\\":\\"1\\",\\"ed\\":\\"11240\\"}}"}'
    ']}'
)

# 文档 3.1 签名算法交叉校验向量（期望值由独立实现 .NET HMACSHA1 计算得出）
SIGNATURE_VECTOR = {
    "secret": "b7d3f8a1c2e94f0d9a6b5c4e3d2f1a0b",
    "params": {
        "appId": "37f3f2b5",
        "accessKeyId": "a296be0df88f701ec2e4882be7727568",
        "dateTime": "2025-09-08T22:58:29+0800",
        "signatureRandom": "moI5WkopgjL1EL5Y",
        "fileSize": "3136940",
        "fileName": "lfasr_涉政.wav",
        "language": "autodialect",
        "duration": "56352",
    },
    "base_string": (
        "accessKeyId=a296be0df88f701ec2e4882be7727568"
        "&appId=37f3f2b5"
        "&dateTime=2025-09-08T22%3A58%3A29%2B0800"
        "&duration=56352"
        "&fileName=lfasr_%E6%B6%89%E6%94%BF.wav"
        "&fileSize=3136940"
        "&language=autodialect"
        "&signatureRandom=moI5WkopgjL1EL5Y"
    ),
    "signature": "zi1hnWQXOkogxPFy4RoaLt/KtLc=",
}


def run_selftest(netcheck: bool = False) -> int:
    failures: List[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        log(f"{'PASS' if ok else 'FAIL'}  {name}{(' :: ' + detail) if (detail and not ok) else ''}",
            "√" if ok else "×")
        if not ok:
            failures.append(name)

    # 1) baseString 构造
    vector = SIGNATURE_VECTOR
    got_base = build_base_string(vector["params"])
    check("baseString 排序 + key/value 双端 URL 编码", got_base == vector["base_string"], got_base)

    # 2) HMAC-SHA1 + Base64
    got_sig = make_signature(vector["secret"], vector["params"])
    check("signature = Base64(HMAC-SHA1(baseString, APISecret))",
          got_sig == vector["signature"], got_sig)

    # 3) 空值 / signature 字段剔除
    dirty = dict(vector["params"])
    dirty.update({"signature": "should-be-ignored", "pd": "", "callbackUrl": None})
    check("空值/None/signature 不参与签名",
          build_base_string(dirty) == vector["base_string"])
    check("签名与参数顺序无关",
          make_signature(vector["secret"], dict(reversed(list(vector["params"].items())))) == got_sig)

    # 4) 文档样例解析
    content = {
        "orderResult": DOC_SAMPLE_ORDER_RESULT,
        "orderInfo": {"orderId": "DKHJQ202003171520031715109E1FF5E50001D",
                      "status": 4, "failType": 0, "originalDuration": 14000},
    }
    segments, meta = parse_order_result(content)
    expected = ["为", "喂你好。", "舒高生先生是吧?喂", "为。", "喂听得到吗?一。"]
    check("官方样例解析出 5 句", len(segments) == 5, str(len(segments)))
    check("句子文本正确（wp=g 空分段不进入文本）",
          [s["text"] for s in segments] == expected, str([s["text"] for s in segments]))
    check("句子时间轴正确",
          [(s["start"], s["end"]) for s in segments]
          == [(880, 1680), (2390, 3640), (5130, 7200), (7200, 8650), (9330, 11240)],
          str([(s["start"], s["end"]) for s in segments]))
    check("角色编号 rl 解析为 speaker", all(s["speaker"] == "1" for s in segments))
    check("orderInfo 解析", meta["order_id"].endswith("0001D") and meta["original_duration_ms"] == 14000)

    # 5) 分片合并
    c1 = Chunk(0, "a", 0, 10000, 1, segments=segments)
    c2 = Chunk(1, "b", 10000, 10000, 1, segments=[{"start": 0, "end": 500, "speaker": "1", "text": "第二片"}])
    merged = merge_segments([c2, c1])
    check("分片时间偏移正确拼接", len(merged) == 6 and merged[-1]["start"] == 10000,
          str([s["start"] for s in merged]))
    check("词级时间戳已解析（供字幕切条）", bool(merged[0].get("words")) and len(merged[0]["words"]) == 1,
          str(merged[0].get("words")))
    check("未开启角色分离且仅一个说话人时不显示说话人",
          all(s["speaker"] == "" for s in merged))
    check("开启角色分离时保留说话人",
          all(s["speaker"] == "1" for s in merge_segments([c1], role_separation=True)))

    # 6) 字幕切条（按词级时间戳）
    long_words = []
    for i in range(24):
        long_words.append({"w": f"word{i} ", "s": 10000 + i * 400, "e": 10000 + i * 400 + 350})
    long_seg = {"index": 1, "start": 10000, "end": 19600, "speaker": "",
                "text": "".join(w["w"] for w in long_words).strip(), "words": long_words}
    long_cues = split_into_cues([long_seg], max_chars=32, max_seconds=8.0)
    check("长句按词级时间戳切成多条字幕", len(long_cues) >= 3, f"{len(long_cues)} 条")
    check("切条后每条不超字符/时长上限",
          all(len(c["text"]) <= 32 and c["end"] - c["start"] <= 8000 for c in long_cues),
          str([(len(c["text"]), c["end"] - c["start"]) for c in long_cues]))
    check("切条文本首尾相接无损",
          "".join(c["text"] + " " for c in long_cues).split() == long_seg["text"].split())
    check("切条时间单调不回退",
          all(long_cues[i]["end"] <= long_cues[i + 1]["start"] + 1 for i in range(len(long_cues) - 1)))
    short_cues = split_into_cues(merged)
    check("短句不被切条", len(short_cues) == len(merged))

    # 7) 输出渲染
    sample = merged
    srt = render_srt(short_cues)
    check("SRT 时间格式", "00:00:00,880 --> 00:00:01,680" in srt, srt[:120])
    sub = json.loads(render_subtitle_json(short_cues))
    check("字幕 JSON 结构与既有格式一致",
          set(sub["1"]) == {"start_time", "end_time", "original_subtitle", "translated_subtitle"}
          and sub["1"]["start_time"] == 880)
    check("TXT/MD/JSON 渲染非空",
          bool(render_txt(sample, {"source": "x", "duration_ms": 14000}))
          and bool(render_md(sample, {"source": "x", "duration_ms": 14000}))
          and bool(render_json(sample, {"source": "x"}, short_cues)))
    check("smart_join 中英文拼接",
          smart_join(["你好", "世界"]) == "你好世界" and smart_join(["hello", "world"]) == "hello world")

    # 7) 时间格式
    dt = now_datetime_str()
    check("dateTime 格式 yyyy-MM-dd'T'HH:mm:ss±HHmm",
          bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4}", dt)), dt)

    # 8) ffmpeg
    try:
        ffmpeg, ffprobe = require_ffmpeg()
        check("ffmpeg/ffprobe 可用", True)
        log(f"    ffmpeg = {ffmpeg}")
    except AsrError as exc:
        check("ffmpeg/ffprobe 可用", False, str(exc))

    # 9) 视频容器（临时生成一个带音轨的 mp4 做真实校验）
    tmpdir = Path(tempfile.mkdtemp(prefix="asr_vtest_"))
    try:
        ffmpeg, ffprobe_bin = require_ffmpeg()
        src_mp4 = tmpdir / "t.mp4"
        made = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "lavfi", "-i", "testsrc=size=160x120:rate=10:duration=2",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", str(src_mp4)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if made.returncode != 0 or not src_mp4.is_file():
            check("视频容器：生成测试 mp4", False, (made.stderr or "")[:200])
        else:
            vinfo = ffprobe_media(src_mp4)
            check("视频容器：识别出视频轨 + 音轨",
                  vinfo["has_video"] and vinfo["audio_stream_count"] == 1
                  and vinfo["video"].get("width") == 160,
                  json.dumps(vinfo)[:200])
            vchunks = prepare_chunks(src_mp4, tmpdir / "work", Config(sample_rate=16000))
            chunk_path = Path(vchunks[0].path) if vchunks else None
            check("视频容器：只提取音轨并转成 16k/单声道 wav（不整文件上传）",
                  len(vchunks) == 1
                  and chunk_path is not None
                  and chunk_path.suffix == ".wav"
                  and chunk_path.resolve() != src_mp4.resolve()
                  and chunk_path.exists() and chunk_path.stat().st_size > 1000,
                  f"{chunk_path}")

            srt = tmpdir / "t.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:01,500\n测试字幕\n", encoding="utf-8")
            muxed = mux_subtitles(src_mp4, srt, Config(out_dir=str(tmpdir)))
            probe_out = subprocess.run(
                [ffprobe_bin, "-v", "error", "-show_entries", "stream=codec_type,codec_name",
                 "-of", "csv=p=0", str(muxed or "")],
                capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            check("视频容器：字幕封装成功且含 subtitle 流",
                  bool(muxed) and muxed.is_file() and "subtitle" in probe_out, probe_out[:200])

            no_audio = tmpdir / "noaudio.mp4"
            subprocess.run(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                 "-i", "testsrc=size=160x120:rate=10:duration=1",
                 "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                 str(no_audio)], capture_output=True)
            try:
                prepare_chunks(no_audio, tmpdir / "w2", Config())
                check("无音轨视频给出明确报错", False, "未报错")
            except AsrError as exc:
                check("无音轨视频给出明确报错", "没有音轨" in str(exc), str(exc)[:120])
            check("目录输入能收集音视频文件",
                  len(expand_inputs([str(tmpdir)])) >= 2)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # 10) 可选联网通道检测（用假密钥，验证请求能否被服务端解析）
    if netcheck:
        try:
            client = XfyunAsrClient(Config(appid="00000000", api_key="0" * 32, api_secret="0" * 32))
            params = {
                "appId": "00000000", "accessKeyId": "0" * 32,
                "dateTime": now_datetime_str(), "signatureRandom": random_str(16),
                "fileSize": "1024", "fileName": "probe.wav",
                "language": "autodialect", "duration": "1000",
            }
            data = client._post_json(UPLOAD_PATH, params, b"\x00" * 16,
                                     "application/octet-stream", 30)
            check("联网检测（假密钥不应成功）", False, json.dumps(data, ensure_ascii=False)[:200])
        except AsrError as exc:
            message = str(exc)
            expect_codes = ("000002", "100009", "000001", "100003", "100007")
            ok = any(f"code={code}" in message for code in expect_codes)
            check("联网检测：请求已到达讯飞服务端并被正确解析"
                  "（返回预期的鉴权/参数错误即为通道正常）", ok, message[:300])
            log(f"    服务端返回：{message.splitlines()[0]}")

    print()
    if failures:
        log(f"自检失败 {len(failures)} 项：{', '.join(failures)}", "×")
        return 1
    log("全部自检通过", "√")
    return 0


# --------------------------------------------------------------------------- #
# 命令行
# --------------------------------------------------------------------------- #
def add_common_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("凭证")
    group.add_argument("--appid", default="", help="讯飞 AppID")
    group.add_argument("--api-key", default="", help="APIKey（即 accessKeyId）")
    group.add_argument("--api-secret", default="", help="APISecret（即 accessKeySecret）")
    group.add_argument("--env", default="", help="指定 .env 文件路径")

    group = parser.add_argument_group("识别参数（对应接口同名参数）")
    group.add_argument("--language", default="autodialect",
                       choices=["autodialect", "autominor"],
                       help="autodialect=中英+202种方言免切；autominor=37语种免切")
    group.add_argument("--pd", default="", choices=["", *PD_DOMAINS.keys()],
                       help="领域参数：" + "、".join(f"{k}={v}" for k, v in PD_DOMAINS.items()))
    group.add_argument("--role-type", type=int, default=None, choices=[0, 1, 3],
                       help="0 不分离 / 1 通用角色分离 / 3 声纹角色分离")
    group.add_argument("--role-num", type=int, default=None,
                       help="说话人数 0-10（需已开通角色分离）")
    group.add_argument("--feature-ids", default="", help="roleType=3 时的声纹 id，逗号分隔")
    group.add_argument("--smooth", choices=["true", "false"], default=None,
                       help="eng_smoothproc 顺滑，默认 true")
    group.add_argument("--colloq", choices=["true", "false"], default=None,
                       help="eng_colloqproc 口语规整，默认 false")
    group.add_argument("--vad-mode", type=int, default=None, choices=[1, 2],
                       help="eng_vad_mdn 1 远场 / 2 近场")
    group.add_argument("--rlang", type=int, default=None, choices=[0, 1],
                       help="eng_rlang 粤语 0 简体 / 1 繁体")
    group.add_argument("--analysis", type=int, default=None, choices=[0, 1],
                       help="1 开启语种识别（需多语种权限）")
    group.add_argument("--result-type", default="transfer",
                       help="getResult 的 resultType，默认 transfer")
    group.add_argument("--duration-check-disable", action="store_true",
                       help="不传 duration 做时长校验")

    group = parser.add_argument_group("音频处理")
    group.add_argument("--sample-rate", type=int, default=16000, choices=[8000, 16000],
                       help="转码采样率，默认 16000")
    group.add_argument("--channel", default="mix", choices=["mix", "left", "right"],
                       help="立体声取哪一路，默认 mix 混音")
    group.add_argument("--audio-track", type=int, default=0,
                       help="视频容器内有多条音轨时取第几条，从 0 开始，默认第 1 条")
    group.add_argument("--mux-subs", action="store_true",
                       help="视频输入：另外生成带字幕的视频（流拷贝，速度快、画质无损）")
    group.add_argument("--burn-subs", action="store_true",
                       help="视频输入：把字幕烧进画面（需重编码，4K 素材很慢）")
    group.add_argument("--srt-alongside", action="store_true",
                       help="视频输入：把 srt 复制到视频同目录同名，播放器（VLC/PotPlayer）自动加载")
    group.add_argument("--sub-lang", default="chi", help="字幕轨语言标记，默认 chi")
    group.add_argument("--chunk-seconds", type=int, default=None,
                       help="强制按时长切分（秒）；不指定时只要整段不超过 500MB/5h 就整段上传")
    group.add_argument("--no-normalize", action="store_true",
                       help="不做转码，原样上传（格式不合规时风险自负）")
    group.add_argument("--keep-chunks", action="store_true", help="保留切分出的临时音频")
    group.add_argument("--no-resume", action="store_true", help="忽略状态文件，全部重新上传")

    group = parser.add_argument_group("轮询 / 网络")
    group.add_argument("--poll-interval", type=float, default=10.0, help="轮询间隔秒，默认 10")
    group.add_argument("--poll-timeout", type=float, default=7200.0, help="单订单最长等待秒，默认 7200")
    group.add_argument("--upload-timeout", type=float, default=3600.0, help="上传超时秒")
    group.add_argument("--host", default=API_HOST, help=f"接口域名，默认 {API_HOST}")
    group.add_argument("--insecure", action="store_true", help="跳过 TLS 证书校验")

    group = parser.add_argument_group("输出")
    group.add_argument("--out", default="asr_out", help="输出目录，默认 ./asr_out")
    group.add_argument("--out-name", default="", help="输出文件名前缀，默认取音频文件名")
    group.add_argument("--format", default="txt,srt,json,subtitle",
                       help="输出格式，逗号分隔：txt,md,srt,json,subtitle")
    group.add_argument("--cue-chars", type=int, default=32,
                       help="字幕单条最大字符数，默认 32（用词级时间戳切条）")
    group.add_argument("--cue-seconds", type=float, default=8.0,
                       help="字幕单条最大时长秒，默认 8")
    group.add_argument("--keep-punct", action="store_true",
                       help="保留接口原始全角标点（默认英文行会转半角）")
    group.add_argument("--save-raw", action="store_true", help="额外保存接口原始 JSON")
    group.add_argument("--dry-run", action="store_true", help="只做音频准备，不发请求")


def config_from_args(args: argparse.Namespace) -> Config:
    cfg = Config(
        appid=args.appid, api_key=args.api_key, api_secret=args.api_secret,
        language=args.language, pd=args.pd,
        role_type=args.role_type, role_num=args.role_num, feature_ids=args.feature_ids,
        smooth=None if args.smooth is None else (args.smooth == "true"),
        colloq=None if args.colloq is None else (args.colloq == "true"),
        vad_mode=args.vad_mode, rlang=args.rlang, analysis=args.analysis,
        result_type=args.result_type,
        duration_check_disable=args.duration_check_disable,
        sample_rate=args.sample_rate, channel=args.channel,
        audio_track=args.audio_track,
        chunk_seconds=args.chunk_seconds, no_normalize=args.no_normalize,
        keep_chunks=args.keep_chunks,
        mux_subs=args.mux_subs, burn_subs=args.burn_subs,
        srt_alongside=args.srt_alongside, sub_language=args.sub_lang,
        poll_interval=args.poll_interval, poll_timeout=args.poll_timeout,
        upload_timeout=args.upload_timeout,
        host=args.host, insecure=args.insecure,
        out_dir=args.out, formats=tuple(f.strip() for f in args.format.split(",") if f.strip()),
        cue_chars=args.cue_chars, cue_seconds=args.cue_seconds,
        punct_auto=not args.keep_punct,
        out_name=args.out_name, save_raw=args.save_raw,
        resume=not args.no_resume, dry_run=args.dry_run,
    )
    resolve_credentials(cfg, args.env)
    allowed = {"txt", "md", "srt", "json", "subtitle"}
    bad = [f for f in cfg.formats if f not in allowed]
    if bad or not cfg.formats:
        raise AsrError(f"--format 取值非法：{','.join(bad) or '(空)'}；可选 {','.join(sorted(allowed))}")
    return cfg


def require_credentials(cfg: Config) -> None:
    missing = [name for name, value in
               (("AppID", cfg.appid), ("APIKey", cfg.api_key), ("APISecret", cfg.api_secret))
               if not value]
    if missing:
        raise AsrError(
            "缺少凭证：" + "、".join(missing) + "\n"
            "  三种方式任选其一：\n"
            "  1) 命令行：--appid xxx --api-key xxx --api-secret xxx\n"
            "  2) 环境变量：$env:XF_APPID / $env:XF_API_KEY / $env:XF_API_SECRET\n"
            "  3) 配置文件：在脚本目录或当前目录新建 .env，内容见 .env.example"
        )


def expand_inputs(items: Iterable[str]) -> List[Path]:
    """支持传入目录：自动收集目录下的音视频文件（含 mp4 等视频容器）"""
    files: List[Path] = []
    for item in items:
        path = Path(item)
        if path.is_dir():
            found = sorted((p for p in path.iterdir()
                            if p.is_file() and p.suffix.lower() in MEDIA_EXTS),
                           key=lambda p: p.name)
            if not found:
                raise AsrError(f"目录里没有可转写的音视频文件（支持 {len(MEDIA_EXTS)} 种扩展名）：{path}")
            log(f"目录 {path.name} 下发现 {len(found)} 个音视频文件", "·")
            files.extend(found)
        else:
            files.append(path)
    return files


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="xfyun_asr",
        description="讯飞「录音文件转写大模型」(Ifasr_llm) 语音转文字工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python xfyun_asr.py run 录音.wav\n"
            "  python xfyun_asr.py run 录音.wav --role-type 1 --role-num 2 --format txt,srt,subtitle\n"
            "  python xfyun_asr.py run 录音.wav --pd edu --smooth true --colloq true\n"
            "  python xfyun_asr.py split 录音.wav --dry-run\n"
            "  python xfyun_asr.py result --order-id DKHJQ... --signature-random AbCdEf...\n"
            "  python xfyun_asr.py selftest --netcheck\n"
        ),
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="完整流程：转码切分 → 上传 → 轮询 → 输出")
    p_run.add_argument("inputs", nargs="+", help="音频文件，支持多个")
    add_common_options(p_run)

    p_probe = sub.add_parser("probe", help="查看音频信息并判断是否需要转码切分")
    p_probe.add_argument("inputs", nargs="+")

    p_render = sub.add_parser("render", help="从状态文件重新生成输出（不再调用接口、不重复计费）")
    p_render.add_argument("inputs", nargs="+")
    add_common_options(p_render)

    p_refresh = sub.add_parser("refresh", help="用已保存的 orderId 重新拉取并重新解析，再生成输出（不计费）")
    p_refresh.add_argument("inputs", nargs="+")
    add_common_options(p_refresh)

    p_split = sub.add_parser("split", help="仅转码切分，生成符合接口要求的分片")
    p_split.add_argument("inputs", nargs="+")
    add_common_options(p_split)

    p_upload = sub.add_parser("upload", help="仅上传，输出 orderId 与 signatureRandom")
    p_upload.add_argument("input")
    add_common_options(p_upload)

    p_result = sub.add_parser("result", help="按 orderId 查询并输出结果")
    p_result.add_argument("--order-id", required=True)
    p_result.add_argument("--signature-random", required=True,
                          help="上传时使用的 signatureRandom（必填，需与上传一致）")
    p_result.add_argument("--source-name", default="", help="输出文件名前缀")
    add_common_options(p_result)

    p_url = sub.add_parser("url", help="外链音频转写（audioMode=urlLink）")
    p_url.add_argument("audio_url")
    add_common_options(p_url)

    p_self = sub.add_parser("selftest", help="离线自检（签名/解析/输出/ffmpeg）")
    p_self.add_argument("--netcheck", action="store_true",
                        help="额外做一次联网通道检测（用假密钥，不会产生费用）")

    p_auth = sub.add_parser("checkauth", help="验证凭证是否正确（不创建订单、不消耗额度）")
    add_common_options(p_auth)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "selftest":
        return run_selftest(netcheck=args.netcheck)

    if args.command == "probe":
        try:
            for item in args.inputs:
                path = Path(item)
                info = ffprobe_media(path)
                has_audio = info["audio_stream_count"] > 0
                ok = (has_audio and not info["has_video"]
                      and info["codec"] == "pcm_s16le" and info["sample_rate"] in (8000, 16000)
                      and info["channels"] == 1 and info["size"] <= MAX_UPLOAD_BYTES
                      and info["duration_ms"] <= MAX_AUDIO_MS)
                print(f"\n{path.name}")
                print(f"  类型    : {'视频' if info['has_video'] else '音频'}"
                      f"（{info['format'].split(',')[0] or '-'}）")
                print(f"  大小    : {human_size(info['size'])}（接口上限 500MB）")
                print(f"  时长    : {human_dur(info['duration_ms'])}（接口上限 5 小时）")
                if info["has_video"]:
                    video = info["video"]
                    print(f"  视频轨  : {video.get('codec')} "
                          f"{video.get('width')}x{video.get('height')}@{video.get('fps')}fps"
                          f"（{video.get('count')} 条，转写时忽略）")
                if has_audio:
                    bits = f" / {info['bits']}bit" if info["bits"] else ""
                    print(f"  音轨    : {info['codec']} / {info['sample_rate']}Hz / "
                          f"{info['channels']}ch{bits}"
                          f"（共 {info['audio_stream_count']} 条，默认取第 1 条）")
                else:
                    print("  音轨    : 无 —— 无法转写")
                if info["has_video"]:
                    print("  处理方式: 提取音轨 → 转 16k 单声道 → 上传（视频轨不参与，速度很快）")
                    print("  可直接传: 否（视频容器需先提取音轨）")
                else:
                    print(f"  可直接传: {'是' if ok else '否，需要转码/切分'}")
        except AsrError as exc:
            eprint(f"\n× {exc}")
            return 1
        return 0

    try:
        cfg = config_from_args(args)

        if args.command == "checkauth":
            require_credentials(cfg)
            return 0 if check_auth(cfg) else 1

        if args.command == "render":
            failures = 0
            for item in args.inputs:
                src = Path(item)
                try:
                    render_from_state(src, cfg)
                except AsrError as exc:
                    failures += 1
                    eprint(f"× {src.name}：{exc}")
            return 1 if failures else 0

        if args.command == "refresh":
            require_credentials(cfg)
            failures = 0
            for item in args.inputs:
                src = Path(item)
                try:
                    refresh_from_orders(src, cfg)
                except AsrError as exc:
                    failures += 1
                    eprint(f"× {src.name}：{exc}")
            return 1 if failures else 0

        if args.command == "split":
            for item in args.inputs:
                src = Path(item)
                workdir = Path(cfg.out_dir) / "_chunks" / (cfg.out_name or src.stem)
                chunks = prepare_chunks(src, workdir, cfg)
                print()
                for chunk in chunks:
                    print(f"  #{chunk.index + 1} {Path(chunk.path).name} "
                          f"[{human_dur(chunk.offset_ms)} ~ "
                          f"{human_dur(chunk.offset_ms + chunk.duration_ms)}] "
                          f"{human_size(chunk.size)}")
            return 0

        if args.command == "upload":
            require_credentials(cfg)
            src = Path(args.input)
            info = ffprobe_audio(src)
            client = XfyunAsrClient(cfg)
            data = client.upload_file(src, info["duration_ms"])
            print(json.dumps({
                "orderId": (data.get("content") or {}).get("orderId"),
                "signatureRandom": data["_signature_random"],
                "taskEstimateTime": (data.get("content") or {}).get("taskEstimateTime"),
            }, ensure_ascii=False, indent=2))
            log("请记下 signatureRandom，查询结果时必须使用同一个值", "!")
            return 0

        if args.command == "url":
            require_credentials(cfg)
            client = XfyunAsrClient(cfg)
            data = client.create_task_by_url(args.audio_url)
            order_id = (data.get("content") or {}).get("orderId")
            log(f"外链任务已创建 orderId={order_id}", "√")
            result = client.wait_result(order_id, data["_signature_random"])
            segments, meta = parse_order_result(result.get("content") or {})
            segments = merge_segments([Chunk(0, "", 0, 0, 0, segments=segments)],
                                      role_separation=bool(cfg.role_type))
            meta.update({"source": args.audio_url, "duration_ms": meta.get("original_duration_ms", 0),
                         "orders": [order_id]})
            for path in write_outputs(segments, meta, cfg, cfg.out_name or "url_task"):
                log(f"  → {path}")
            return 0

        if args.command == "result":
            require_credentials(cfg)
            client = XfyunAsrClient(cfg)
            data = client.wait_result(args.order_id, args.signature_random)
            segments, meta = parse_order_result(data.get("content") or {})
            segments = merge_segments([Chunk(0, "", 0, 0, 0, segments=segments)],
                                      role_separation=bool(cfg.role_type))
            meta.update({"source": args.source_name or args.order_id,
                         "duration_ms": meta.get("original_duration_ms", 0),
                         "orders": [args.order_id]})
            if cfg.save_raw:
                raw_dir = Path(cfg.out_dir) / "_raw"
                raw_dir.mkdir(parents=True, exist_ok=True)
                (raw_dir / f"{args.order_id}.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            written = write_outputs(segments, meta, cfg,
                                    cfg.out_name or args.source_name or args.order_id)
            log(f"完成：{len(segments)} 句", "√")
            for path in written:
                log(f"  → {path}")
            return 0

        # run
        inputs = expand_inputs(args.inputs)
        missing = [str(p) for p in inputs if not p.is_file()]
        if missing:
            raise AsrError("文件不存在：" + "、".join(missing))
        if cfg.out_name and len(inputs) > 1:
            raise AsrError("--out-name 只适用于单个输入文件（多个文件会互相覆盖输出）")
        if not cfg.dry_run:
            require_credentials(cfg)
        failures = 0
        for src in inputs:
            print()
            log(f"===== {src.name} =====", "▶")
            try:
                transcribe_file(src, cfg)
            except AsrError as exc:
                failures += 1
                eprint(f"\n× {src.name} 处理失败：{exc}")
                eprint("  提示：状态文件已保留，修复后重新执行同一条命令即可从断点续跑。")
        if len(inputs) > 1:
            print()
            log(f"全部结束：成功 {len(inputs) - failures} / 共 {len(inputs)}", "√" if not failures else "×")
        return 1 if failures else 0

    except AsrError as exc:
        eprint(f"\n× {exc}")
        return 1
    except KeyboardInterrupt:
        eprint("\n× 已中断（已上传的订单与结果保存在状态文件中，重跑可续）")
        return 130


if __name__ == "__main__":
    sys.exit(main())
