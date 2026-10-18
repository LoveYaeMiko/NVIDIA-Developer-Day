# 讯飞「录音文件转写大模型」语音转文字工具

按讯飞开放平台文档 [录音文件转写大模型 Ifasr_llm](https://www.xfyun.cn/doc/spark/asr_llm/Ifasr_llm.html) 实现的命令行工具：
把任意音频 / **视频（mp4、mov、mkv…）** 转成文字、字幕，并解决文档接口的三个硬限制（**16k/8k、16bit、单声道**；**≤500MB**；**≤5 小时**）。

```
语音转文字/
├─ xfyun_asr.py       主程序（纯标准库 + ffmpeg，无第三方 Python 依赖）
├─ .env.example       凭证配置模板
└─ README.md          本文件
```

> 视频怎么处理：接口只收音频，工具用 ffmpeg **只解音轨、跳过视频轨**（`-vn`），
> 4K 60fps 的 5.2GB 视频提取 1 分钟音轨只需 0.3 秒，转写代价与纯音频相同。
> 转完还能一键产出带字幕的视频（流拷贝，画质无损）或把 srt 放到视频旁让播放器自动加载。

---

## 1. 它做了什么

| 环节 | 说明 |
| --- | --- |
| 探测 | `ffprobe` 读取采样率/声道/位深/时长，判断能否直传；视频容器会额外报告分辨率/帧率/音轨条数 |
| 视频 | mp4/mov/mkv/avi/flv/webm/ts… 自动**提取音轨**（`-vn` 不解码视频轨，实测 4K 60fps 5.2GB 视频提取 1 分钟音轨仅 0.3 秒）；可另存带字幕的视频或旁挂 srt |
| 规整 | `ffmpeg` 转成 16kHz（或 8kHz）/ 16bit / 单声道 PCM WAV；立体声可选左/右声道或混音 |
| 切分 | 转码后若仍超 500MB 或 5 小时才切段（默认先尽量整段上传，订单更少、无切片边界影响）；`--chunk-seconds` 可强制切分 |
| 鉴权 | 严格按文档 3.1：参数字典序 → key/value 双端 URL 编码 → `&` 连接 → HMAC-SHA1 → Base64，放请求头 `signature` |
| 上传 | `POST /v2/upload`，`application/octet-stream`，请求体即音频二进制 → 拿 `orderId` |
| 查询 | `POST /v2/getResult`，请求体 `{}`，`signatureRandom` 沿用上传值、`dateTime` 重新生成，轮询到 `status=4` |
| 解析 | 解 `orderResult` → `lattice[].json_1best` → `st`（`bg`/`ed` 毫秒、`rl` 说话人、`rt[].ws[].cw[0].w`），跳过 `wp=g` 的空分段 |
| 合并 | 各分片时间轴按 `offset` 拼回整段录音的绝对时间 |
| 字幕粒度 | 接口的 VAD 句子常长达 10~20 秒，工具用返回的**词级时间戳**（`ws.wb/we`，1 帧 = 10ms）把长句切成 ≤32 字 / ≤8 秒的字幕条，切点自然、时间轴逐词对齐 |
| 断点续跑 | 订单号与分段结果写入 `<输出目录>/<文件名>.state.json`，中断后重跑不重复上传（不重复计费） |
| 输出 | `txt` / `srt` / `json` / `subtitle.json`（与项目内既有【原始字幕】格式一致）/ `md` |

## 2. 环境准备

需要 **Python 3.8+** 和 **ffmpeg**（含 ffprobe）。

```powershell
# ffmpeg 未安装时
winget install Gyan.FFmpeg
# 检查
ffmpeg -version
python --version
```

本机已具备：Python 3.12.3、ffmpeg 8.1.1。

## 3. 配置凭证

前往讯飞开放平台控制台取 **AppID / APIKey / APISecret**（`APIKey` 即接口参数 `accessKeyId`，`APISecret` 即 `accessKeySecret`）。

三种方式任选其一，优先级从高到低：

```powershell
# ① 命令行
python xfyun_asr.py run 录音.wav --appid 你的AppID --api-key 你的APIKey --api-secret 你的APISecret

# ② 环境变量（当前 PowerShell 会话有效）
$env:XF_APPID      = "你的AppID"
$env:XF_API_KEY    = "你的APIKey"
$env:XF_API_SECRET = "你的APISecret"

# ③ 配置文件（推荐，一次写好长期有效）
Copy-Item .env.example .env
notepad .env
```

`.env` 内容：

```ini
XF_APPID=你的AppID
XF_API_KEY=你的APIKey
XF_API_SECRET=你的APISecret
```

> 也兼容 `APPID` / `APIKEY` / `APISECRET` 与 `IFLYTEK_*` 命名。`.env` 会被自动搜索：`--env 指定路径` → 当前目录 → 脚本目录。

## 4. 常用命令

```powershell
# 第一步：先验证凭证（不创建订单、不消耗额度，服务端返回"订单号不存在"即说明签名已通过）
python xfyun_asr.py checkauth

# 完整流程（最常用）
python xfyun_asr.py run '录音机-20261016-0945.wav' --out '转写结果'

# 一次跑多个
python xfyun_asr.py run 录音机-*.wav --out 转写结果

# 课堂/会议录音：开角色分离 + 教育领域 + 口语规整
python xfyun_asr.py run 录音.wav --role-type 1 --role-num 2 --pd edu --colloq true

# 只输出字幕（项目内【原始字幕】格式）
python xfyun_asr.py run 录音.wav --format subtitle,srt --out-name '【原始字幕】录音机-20261015-0935-B 接口-英语'

# ===== 视频转文字 =====
# 最基本：MP4/MOV/MKV 直接丢进来，自动提音轨转写
python xfyun_asr.py run 'VID_20261016_105447.mp4' --out '转写结果'

# 字幕放到视频旁边（播放器 VLC/PotPlayer 会自动加载，零额外磁盘）
python xfyun_asr.py run 讲座.mp4 --srt-alongside

# 另存一份带字幕的视频（流拷贝，画质无损、速度快；4K 素材会多占一份体积）
python xfyun_asr.py run 讲座.mp4 --mux-subs

# 把字幕烧进画面（改写像素，需重编码，4K 素材很慢，谨慎使用）
python xfyun_asr.py run 讲座.mp4 --burn-subs

# 视频有多条音轨（如双语言）时指定第几条（从 0 开始）
python xfyun_asr.py run 双语.mp4 --audio-track 1

# 批量：直接传目录，自动收集里面所有音视频
python xfyun_asr.py run '.' --out '转写结果'

# 先干跑：只转码切分、不发请求、不产生费用
python xfyun_asr.py run 录音.wav --dry-run

# 看音频是否合规
python xfyun_asr.py probe 录音.wav

# 只切分不改动其它
python xfyun_asr.py split 录音.wav --chunk-seconds 1200 --keep-chunks

# 只上传拿订单号（异步场景）
python xfyun_asr.py upload 录音.wav
# 之后凭订单号查询（signatureRandom 必须是上传时那一个）
python xfyun_asr.py result --order-id DKHJQ2025... --signature-random Ab3dEf9hIjKlMn0p

# 音频已在公网可访问：免上传，直接给链接
python xfyun_asr.py url https://example.com/talk.mp3

# 换字幕粒度/标点风格后重新出文件：只读状态文件，不联网、不计费
python xfyun_asr.py render 录音.wav --cue-chars 20 --cue-seconds 5

# 用已保存的 orderId 重新拉取结果并重新解析（查询免费，不产生新订单）
python xfyun_asr.py refresh 录音.wav

# 离线自检（签名交叉校验 / 官方样例解析 / 输出渲染 / ffmpeg）
python xfyun_asr.py selftest
# 额外做一次联网通道检测（用假密钥，不会产生费用）
python xfyun_asr.py selftest --netcheck
```

## 5. 主要参数

| 参数 | 说明 |
| --- | --- |
| `--language autodialect\|autominor` | 中英+202 种方言免切（默认）／37 语种免切 |
| `--pd <领域>` | `court` 法律、`finance` 金融、`medical` 医疗、`tech` 科技、`sport` 体育、`edu` 教育、`isp` 运营商、`gov` 政府、`game` 游戏、`ecom` 电商、`mil` 军事、`com` 企业、`life` 生活、`ent` 娱乐、`culture` 人文历史、`car` 汽车 |
| `--role-type 0\|1\|3` | 角色分离：不分离／通用／声纹（3 需配 `--feature-ids`） |
| `--role-num 0-10` | 说话人数，需已开通角色分离 |
| `--smooth true\|false` | `eng_smoothproc` 顺滑，默认 true |
| `--colloq true\|false` | `eng_colloqproc` 口语规整（顺滑升级版），默认 false |
| `--vad-mode 1\|2` | 远场／近场 |
| `--rlang 0\|1` | 粤语字型：0 简体 / 1 繁体 |
| `--analysis 1` | 语种识别（需多语种权限），查询时 `--result-type transfer,analysis` |
| `--sample-rate 16000\|8000` | 转码采样率，默认 16000 |
| `--channel mix\|left\|right` | 立体声处理：混音（默认）／只取左／只取右 |
| `--audio-track N` | 视频容器内有多条音轨时取第几条，从 0 开始（默认第 1 条） |
| `--srt-alongside` | 视频：把 srt 复制到视频同目录同名，播放器自动加载（推荐） |
| `--mux-subs` | 视频：另存带字幕的视频（`-c:v copy` 流拷贝，画质无损、很快） |
| `--burn-subs` | 视频：字幕烧进画面（重编码，4K 素材很慢） |
| `--sub-lang` | 字幕轨语言标记，默认 `chi` |
| `--chunk-seconds N` | 强制按时长切分（秒）。不指定时：整段转码后仍 ≤480MB 且 ≤5 小时就**整段上传**，否则自动切成不超过上限的分片 |
| `--format ...` | `txt,md,srt,json,subtitle`，默认 `txt,srt,json,subtitle` |
| `--cue-chars N` / `--cue-seconds N` | 字幕单条最大字符数（默认 32）／最大时长（默认 8 秒），仅作用于 `srt`/`subtitle` |
| `--keep-punct` | 保留接口原始全角标点（默认英文行自动转半角并补空格） |
| `--out DIR` / `--out-name PREFIX` | 输出目录（默认 `./asr_out`）／输出文件名前缀（默认取音频文件名） |
| `--save-raw` | 另存接口原始 JSON（排查问题用） |
| `--no-resume` | 忽略状态文件全部重传 |
| `--no-normalize` | 不做转码，原样上传（格式不合规时有风险） |
| `--poll-interval` / `--poll-timeout` | 轮询间隔（默认 10s）／单订单最长等待（默认 7200s） |
| `--insecure` | 跳过 TLS 证书校验 |

## 6. 输出文件

以 `录音机-20261016-0945.wav` 为例，输出到 `--out` 目录：

| 文件 | 内容 |
| --- | --- |
| `录音机-20261016-0945.txt` | 纯文本，按说话人/停顿自动分段，便于阅读与喂给翻译 |
| `录音机-20261016-0945.srt` | 标准字幕，逐句时间轴（毫秒精度） |
| `录音机-20261016-0945.json` | 结构化结果：`text` + `segments[{index,start,end,speaker,text}]`（VAD 句级）+ `cues[...]`（字幕条级）+ 分片订单 |
| `录音机-20261016-0945.subtitle.json` | 项目内既有字幕格式：`{"1":{"start_time","end_time","original_subtitle","translated_subtitle"}}` |
| `录音机-20261016-0945.state.json` | 断点续跑状态（订单号、分片、分段结果），删除即从头开始 |

## 7. 关键实现说明

**签名（文档 3.1）**

```python
base_string = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}"
                       for k, v in sorted((k, v) for k, v in params.items()
                                          if k != "signature" and v not in (None, "")))
signature = base64.b64encode(hmac.new(secret.encode(), base_string.encode(), "sha1").digest())
```

- 空值、空串、`None` 不参与签名；参数名按 ASCII 字典序（等价 Java `TreeMap`）
- 签名用**未编码原始值**计算，最终 URL 再做同样的编码（`:`→`%3A`、`+`→`%2B`）
- 签名放**请求头** `signature`（文档 4.1.3 / 4.2.3），不是 query 参数
- 查询接口：`signatureRandom` 必须与上传时一致，`dateTime` 必须重新生成

**结果解析**：`orderResult` 是**字符串套 JSON**，`lattice[].json_1best` 里再套一层 JSON 字符串；句级时间取 `st.bg`/`st.ed`（毫秒），词级 `ws.wb`/`ws.we` 是相对 `st.bg` 的帧数（1 帧 = 10ms）。`wp`：`n` 正常词、`s` 顺滑、`p` 标点、`g` 分段（空串，不入文本）。开启顺滑后还会返回 `lattice2`（未顺滑原文），工具默认取 `lattice`。

**状态码**：`orderInfo.status`：`0` 已创建、`3` 处理中、`4` 完成、`-1` 失败；失败看 `failType`（`0` 正常、`4` 时长超限、`5` duration 与实际不符、`6` 静音文件…），工具已内置中文映射。

## 8. 常见报错

| 错误码 | 含义 | 处理 |
| --- | --- | --- |
| `000002` | accessKeyId 不存在 | 检查 APIKey 是否复制错、是否与 AppID 同属一个应用 |
| `100009` | 签名校验不通过 | 检查 APISecret；确认系统时间准确（`100008` 为时间超限）；不要改动签名串 |
| `100003` / `000001` | 参数错误 | 常见于 `fileName` 缺后缀、`duration` 与真实时长不符 |
| `100012` | 请求超过频率限制 | 工具已内置自动退避重试（最多 6 次），并给轮询加抖动；多任务并行时建议间隔启动 |
| `100030` | 未知的文件格式 | 用 `--no-normalize` 关掉转码后传了非常规格式，改回默认转码 |
| `failType=5` | duration 与实际音频时长不符 | 默认已按真实时长计算；如自建音频需保证时长精确 |
| `failType=6` | 静音文件 | 该分片无有效语音 |
| `failType=4` | 时长超限 | 单片超过 5 小时，减小 `--chunk-seconds` |

## 9. 费用与限制提醒

- 接口按**音频时长**计费；切分不会改变总时长，但**重复上传会重复计费**，所以中断后请重跑同一条命令（默认续跑）。
- 单文件：≤5 小时、≤500MB。本仓库 4 个录音合计约 5.1 小时，源文件虽是 48kHz/立体声/24bit 的 0.9~1.9GB，
  转成 16kHz/单声道/16bit 后分别约 **99MB / 124MB / 220MB / 118MB**（实测 2 小时那段耗时 23 秒），
  每段录音只需 **1 个转写订单**即可整段提交。
- 订单结果有**过期时间**（`orderInfo.expireTime`），转写完成后请及时取回并落盘（本工具完成即写文件）。
- 切片缓存在 `<输出目录>/_chunks/`，同一条命令重跑会自动复用（省掉重复转码），成功后才自动清理；`--keep-chunks` 可保留。

## 10. 已验证项

`python xfyun_asr.py selftest` 覆盖 16 项，全部通过：

- baseString 排序 + key/value 双端 URL 编码，与文档 3.1 一致；HMAC-SHA1 签名结果与 .NET `HMACSHA1` 独立实现逐字节一致
- 空值 / `null` / `signature` 字段不参与签名；签名与参数插入顺序无关
- 文档 4.2.6 官方样例（`lattice[].json_1best` 双层 JSON）解析出 5 句，文本、起止毫秒、`rl` 说话人全部正确，`wp=g` 空分段不入文本
- 分片时间偏移合并、SRT/字幕 JSON/TXT/MD 渲染、`dateTime` 格式、ffmpeg 可用性
- `--netcheck`：用假密钥向讯飞发起真实请求，返回 `000002 accessKeyId不存在` 即证明域名/路径/参数编码/请求头/请求体通道全部正常
- 流式上传通道已用本地 sink 校验：5MB 二进制原样送达，`Content-Length`、`Content-Type: application/octet-stream`、`signature` 头均正确
- 端到端协议模拟已跑通：本地 mock 服务端按文档用收到的参数重算签名并与 `signature` 头比对一致，`run` 完成
  「转码 → 单切片 → 上传 → 轮询（处理中→完成）→ 5 种格式落盘 → 清理切片 → 状态置 done」全流程
- **视频链路**：临时生成带音轨的 mp4 校验「识别视频轨+音轨 → 只提取音轨成 16k/单声道 wav（绝不整文件上传）→
  字幕封装后含 `subtitle` 流 → 无音轨视频明确报错 → 目录批量收集」；真实 4K 60fps 5.2GB MP4 提取 1 分钟音轨仅 0.3 秒
- **真实录音全流程跑通**：4 段共 5.1 小时、源文件 48kHz/立体声/24bit(0.9~1.9GB) 的录音全部转写成功，
  共 5403 条字幕 / 1683 个 VAD 句，时间轴零倒错、零空条、全部 ≤32 字且 ≤8 秒，正文字数覆盖率 100%
  （`subtitle.json` 与 `txt` 的差值恰好等于 `txt` 头部信息长度）

## 11. 本仓库已有的转写结果

**录音（音频）** —— 均输出到 `转写结果\<文件名>.{txt,md,srt,json,subtitle.json}`：

| 录音 | 时长 | VAD 句 | 字幕条 | 正文字数 |
| --- | --- | --- | --- | --- |
| 录音机-20261016-0945.wav | 53:56 | 297 | 1086 | 21,485 |
| 录音机-20261016-1103.wav | 1:07:28 | 378 | 1490 | 30,083 |
| 录音机-20261016-1331.wav | 2:00:00 | 670 | 1879 | 36,525 |
| 录音机-20261016-1531.wav | 1:04:21 | 338 | 948 | 17,829 |

**视频（4K 60fps H.264 + AAC 48k 立体声）** —— 输出同上，并且 srt 已旁挂到视频同目录
（`VID_xxxx.srt`，用 VLC/PotPlayer 打开视频会自动挂上字幕）：

| 视频 | 时长 | 源大小 | VAD 句 | 字幕条 | 正文字数 |
| --- | --- | --- | --- | --- | --- |
| VID_20261016_105447.mp4 | 15:00 | 5.1GB | 81 | 521 | 13,365 |
| VID_20261016_110133.mp4 | 5:28 | 1.8GB | 31 | 198 | 5,257 |
| VID_20261016_110211.mp4 | 0:08 | 43MB | 1 | 4 | 112 |
| VID_20261016_110316.mp4 | 1:01 | 355MB | 5 | 42 | 1,111 |

`VID_20261016_110211.字幕.mp4` 是「带字幕的视频」示范产物（流拷贝，41.3MB，画质无损，
含 `h264 + aac + mov_text(chi)` 三条流）。其余视频如需同样产物，执行下面任一命令即可，
**不会重新计费**（订单已完成，工具会自动跳过上传与轮询）：

```powershell
python xfyun_asr.py run 'VID_20261016_105447.mp4' --mux-subs --out '转写结果'
# 或烧进画面（要重编码 4K，较慢）
python xfyun_asr.py run 'VID_20261016_105447.mp4' --burn-subs --out '转写结果'
```

内容是 NVIDIA 中国开发者日的演讲（含中英混说），`autodialect` 自动中英+方言免切识别。
已知识别短板：CUDA 常被识别成 whoda/couldda、DGX Spark 识别成 adgx part 等专有名词；
若需提升可加 `--pd tech`（科技领域）重跑——注意重跑会再次计入时长。修复这类术语的通用做法是在下游做术语替换表。

