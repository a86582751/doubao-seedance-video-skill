# 面向 Codex + 豆包 Seedance 的 Agentic 长视频工作室

[English README](README.md)

这个项目希望把一句自然语言想法变成一支完整 AI 短片。Codex 在这里不是一个薄薄的 API 调用壳，而更像一个小型制作组：分镜师、提示词工程师、视觉审片员、补拍导演、离线剪辑师和音频后期主管。

它面向的是 AI 长视频制作里最麻烦的中段：片段会失败，连续性会漂，转场需要补拍，单段原生音频会在拼接时反复重置，最终剪辑又会改变原始节奏。本技能把这些问题显式放进流程里：一次性子代理审片、重拍/补拍循环、基于 EDL 的最终剪辑，以及跟随锁定剪辑的 Seed Audio 后期。

支持火山方舟豆包 Seedance 2.0、Seedance 2.0 Fast 和 Seedance 2.0 Mini。

关键词：agentic AI video studio、自然语言长视频、Codex video agent、OpenAI Codex skill、豆包 Seedance 2.0、火山方舟、AI 短片、story-to-video、text-to-video、image-to-video、子代理视觉审片、AI 补拍、EDL 剪辑、Seed Audio 后期、统一音轨、对白、环境声、拟音、FFmpeg 剪辑、提示词优化、资源包成本估算。

## 长期愿景

我们的目标是：一键生成《星际穿越2》，且无需任何人工干预和专业影视制作、剪辑知识（虽然目前看上去还很遥远）。

落到工程上，这意味着把 Codex 从“调用一次视频 API”推进成一个自动化制作系统：理解故事、规划镜头、生成片段、审查画面、要求补拍、完成剪辑、设计最终音频、检查预算安全，并尽可能少地依赖人工干预，最终导出一支能看的影片。

## 它承诺做什么

你可以给 Codex 一个类似这样的自然语言请求：

```text
把这个角色扮演场景改成一支 60-90 秒的电影感视频。
保持角色一致，拆成镜头，逐段生成，
审查真实抽帧，如果剪辑不顺就重拍或补拍，
锁定视觉剪辑，根据最终剪辑重建音频方案，
生成统一的环境声/对白/旁白，导出一个 MP4，
并告诉我最终成本。
```

这个技能设计为让 Codex 在一次流程里处理整条链路：

- 读取故事、剧本、角色扮演记录或世界观文档。
- 拆成镜头表和连续性计划。
- 在角色、服装、道具或视觉身份重要时，先创建 Seedream 角色/参考图。
- 按电影感、运动、运镜和一致性规则优化每段 Seedance 提示词。
- 从文本、图片、视频参考、音频参考、首帧或尾帧生成 Seedance 视频。
- 把密集抽帧交给一次性视觉审片子代理，而不是盲信模型返回。
- 当片段逻辑断裂、连续性差、跳切奇怪、运动弱或缺少衔接时，拒绝、重拍或补拍。
- 让单独的剪辑审查子代理判断片段边界，并产出最终剪辑用的视觉 EDL。
- 根据原始脚本和锁定 EDL 重建最终音频分镜，让对白、旁白、环境声、拟音和音乐跟随真实剪辑。
- 简单片段保留 Seedance 原生音频；长视频默认生成统一的 Seed Audio 后期音轨。
- 报告人民币成本估算和资源包 token 扣减，并在已复核分镜锁定、即将正式生成前执行一次 Seedance Fast 资源包余额预检。

## 它与普通视频 API 调用的区别

- **不是只生成，而是做后期：** 分镜、审片、补拍、裁剪、音频、混流和导出是一个完整生产循环。
- **子代理视觉 QA 是流程的一部分：** 一次性审片代理检查抽帧和联系表，返回明确的接受、裁剪、重拍建议。
- **常识和物理检查是硬门槛：** 画面再漂亮，只要人物无意倒着走、身体或道具穿模、人群站在地面裂口/大门/升降平台运动路径里，或风向/重力/材质运动明显冲突，都应判为失败或要求裁剪。
- **重拍和补拍是一等公民：** 弱镜头不会被礼貌放过。如果桥接、插入、反应、回场或大全景能让剪辑更顺，就生成它。
- **最终组接使用 EDL：** 专门的剪辑审查阶段决定保留范围和边界，再由 FFmpeg 生成最终剪辑。
- **音频跟随锁定剪辑：** 长视频音频在视觉剪辑确定后生成，避免用原始分镜或每段孤立音床硬拼。
- **对白和环境声可控：** Seed Audio 提示词可以按场景或 stem 拆分，应对长度、节奏、对白、音乐和空间声学连续性。
- **角色一致性优先：** 多角色、角色扮演改编、世界观文档或重要服装/道具场景，会优先创建 Seedream 参考图。
- **有成本与余额门禁：** 估算同时报告现金价格和资源包扣减；Seedance 2.0 Fast 长视频在正式生成前调用 `volcengine-resource-query` 做一次最终资源包余额检查，不足则暂停。

## Codex 子代理权限说明

这个工作流会刻意使用一次性子代理来做片段审片和最终剪辑复核。但在部分 Codex/OpenAI 环境里，`spawn_agent` 或子代理工具可能受到更高优先级的权限规则约束：主代理不能仅凭技能说明启动子代理，必须由用户明确授权。

因此，仅仅安装技能不一定足以授权子代理审片。想使用完整工作流，请在请求里加入类似：

```text
使用 doubao-seedance-video 工作流，包括一次性子代理视觉 QA 和最终剪辑复核。
```

或：

```text
我明确授权你为该技能所需的视频审片、剪辑复核和 QA 启动子代理。
```

如果用户没有授权，而当前客户端又强制要求显式授权，主代理不应把子代理流程偷偷替换成主线程审片。它应说明权限限制并请求授权，或明确标注当前只是降级审查流程。

## 生产循环

```text
用户故事 / 素材
  -> 分镜 + 连续性计划
  -> 优化后的 Seedance 分段提示词
  -> 生成候选片段
  -> 一次性子代理视觉审片
  -> 接受、重拍或补拍
  -> 一次性子代理最终剪辑复核
  -> 视觉 EDL
  -> EDL 剪辑事实摘要
  -> 主代理重建 final_storyboard_for_audio.json
  -> Seed Audio 后期
  -> FFmpeg 裁剪 / 拼接 / 混音 / 混流
  -> 最终 MP4 + 成本和余额报告
```

这里有一个重要边界：子代理负责判断视觉证据和剪辑事实；主代理仍保留原始用户意图和分镜上下文，用它来重建最终叙事和音频方案。

## 子代理审片、重拍与补拍

AI 长视频常常败在小地方：手跳了，火箭比例变了，角色穿错衣服，动作重复，事故没有铺垫，或者两个好片段根本剪不到一起。

这个技能把这些失败暴露出来：

- `video_review_tools.py pack` 抽取密集帧和联系表。
- 全新的一次性子代理根据常识、基础物理、视觉连续性、故事逻辑、动作质量、身份一致性、节奏和可保留范围审查每个生成片段。
- 明显物理不可能是硬失败，除非能干净裁掉：人物无意倒着走/跑、没有脚步却滑行、无故漂浮、身体/道具穿模、机械穿过人群，或地面裂开/大门/升降平台运动前危险区域仍有人。
- 失败或偏弱的片段会把具体问题折回提示词里重拍。
- 当补拍能明显改善影片，即使当前剪辑勉强可用，也鼓励补拍。
- 最终剪辑子代理产出标准 EDL，包含源片段、源分镜 id、保留区间、输出时间线和边界判断。

也就是说，Codex 会做一件人类剪辑师经常做的事：保留有效的，剪掉无效的，必要时要求再拍一个镜头。

## 角色参考图流程

对于叙事视频，角色一致性往往决定成片是否像短片，而不是一堆生成片段。

当请求涉及多角色、角色扮演改编、反复出现的人物、世界/角色设定文档、连续短片结构，或重要服装/道具时，本技能设计为先调用伴随的 [`doubao-seedream-image`](https://github.com/a86582751/doubao-seedream-image-skill) 工作流：

- 创建干净的角色肖像、服装表、道具参考或分镜图。
- 审查身份、年龄、发型、服装、关键道具、风格和不需要的文字/水印。
- 将通过审查的图片作为 Seedance `reference_image` 输入或提示词视觉锚点。
- 在相关镜头中尽量复用同一组视觉参考。

这比让每个片段重新发明角色要稳定得多。

## 音频后期流程

目标输出是一支完成视频，而不是无声视觉草稿，也不是一堆彼此割裂的单段音床。

长视频默认音频路线：

```text
初始分镜
  + 视觉 EDL 剪辑事实
  -> final_storyboard_for_audio.json
  -> Seed Audio prompt(s)
  -> 分 stem 或分段音轨
  -> FFmpeg 混音和混流
```

为什么这样做：

- 纯 EDL 只知道哪些画面留下来了，不知道哪些对白、旁白、情绪或声音提示被删掉。
- 原始分镜知道故事意图，但不知道审片和裁剪后的最终节奏。
- 最终音频分镜把两者对齐，所以声音跟随真正剪出来的影片。

支持的音频工作包括：

- 跨剪辑的统一环境声；
- 拟音和冲击音设计；
- 旁白和解说；
- 对白和配音；
- 参考音频引导的声音风格；
- 字幕和时间戳；
- 类音乐氛围床和紧张层；
- 对白、旁白、环境声、拟音、音乐床和特效的分 stem。

最终 Seed Audio 提示词不会直接使用 JSON 摘要，而是先按伴随的 `doubao-seed-audio` 技能里的 Audio Director Prompting 指南重写成音频导演提示词。

如果完整音频提示词超过服务商限制或信息过密，技能可以按段落或 stem 拆分。优先选择安静转场、环境变化、无对白桥段、建立镜头或没有明显旋律的位置切分，避免切在对白、旁白句子、音乐重拍、冲击瞬间或持续音中间。

完整音频生成需要安装 `doubao-seed-audio` 技能。

## 仓库结构

```text
doubao-seedance-video/
  SKILL.md
  agents/openai.yaml
  references/
    api-quickref.md
    clip-assembly-workflow.md
    official-capabilities.md
    prompt-optimizer.md
    visual-review-standards.md
  scripts/
    check_dependencies.py
    seedance_video.py
    seedance_webhook_server.py
    video_review_tools.py
```

## 在 Codex 中安装

克隆本仓库，然后把技能目录复制或安装到 Codex 技能目录：

```bash
mkdir -p ~/.codex/skills
cp -R doubao-seedance-video ~/.codex/skills/
```

如果环境支持 GitHub 技能路径，也可以使用 Codex 的 skill installer：

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo <owner>/<repo> \
  --path doubao-seedance-video
```

安装新技能后重启 Codex。

完整长视频生产流程还需要安装下面列出的必需伴随技能，然后运行依赖检查：

```bash
python doubao-seedance-video/scripts/check_dependencies.py
```

本仓库目前不需要 `requirements.txt` 来安装 Python 包：脚本只使用 Python 标准库。真正重要的依赖是 Codex 技能和本地 `ffmpeg`/`ffprobe`，因此由依赖检查脚本直接报告。

## 配置

CLI 会先读进程环境变量，再回退到：

```text
~/.codex/seedance.env
```

可以从示例文件创建：

```bash
cp .env.example ~/.codex/seedance.env
```

必需：

```text
SEEDANCE_API_KEY=your_volcano_ark_api_key
```

### API Key 来源

火山不同产品线使用不同 API Key，不要混用：

- **Seedance 2.0 / Fast / Mini：** 使用火山方舟 key：https://ark.volcengine.com/region:cn-beijing/apiKey?apikey=%7B%7D
- **Seedream 5.0 Lite / 图像模型：** 使用同一个火山方舟 key：https://ark.volcengine.com/region:cn-beijing/apiKey?apikey=%7B%7D
- **Seed Audio / OpenSpeech 音频生成：** 使用语音控制台 key：https://console.volcengine.com/speech/new/setting/apikeys?projectName=default
- **资源包余额查询：** 使用火山引擎 IAM 用户 AK/SK：https://console.volcengine.com/iam/identitymanage/user

推荐本地文件：

```text
~/.codex/seedance.env  # 方舟 key: SEEDANCE_API_KEY 或 ARK_API_KEY
~/.codex/speech.env    # 语音 key: SEED_AUDIO_API_KEY 或 SPEECH_API_KEY
~/.codex/volcengine-billing.env  # 资源包查询 AK/SK
```

环境变量划分：

- Seedance CLI：`SEEDANCE_API_KEY`，回退 `ARK_API_KEY`。
- Seedream 伴随技能：`SEEDREAM_API_KEY`、`ARK_API_KEY` 或 `SEEDANCE_API_KEY`。
- Seed Audio 伴随技能：`SEED_AUDIO_API_KEY`，回退 `SPEECH_API_KEY`；它不使用 `SEEDANCE_API_KEY` 作为音频 key。
- 资源包查询伴随技能：`VOLC_ACCESS_KEY_ID` 和 `VOLC_SECRET_ACCESS_KEY`，回退文件 `~/.codex/volcengine-billing.env`。

可选：

```text
SEEDANCE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
SEEDANCE_MODEL=doubao-seedance-2-0-260128
SEEDANCE_DURATION=10
SEEDANCE_RESOLUTION=720p
SEEDANCE_RATIO=16:9
SEEDANCE_GENERATE_AUDIO=true
SEEDANCE_WATERMARK=false
SEEDANCE_RETURN_LAST_FRAME=false
```

不要提交真实 `.env` 文件或 API Key。

## 快速开始

估算成本：

```bash
python doubao-seedance-video/scripts/seedance_video.py estimate \
  --model fast --duration 5 --resolution 720p --ratio 16:9
```

生成一个视频：

```bash
python doubao-seedance-video/scripts/seedance_video.py generate \
  --prompt "A cinematic street scene at dusk, slow tracking shot, natural light" \
  --duration 5 --resolution 720p --ratio 16:9 \
  --output-dir outputs
```

创建密集审片抽帧：

```bash
python doubao-seedance-video/scripts/video_review_tools.py pack \
  --video outputs/example.mp4 \
  --output-dir work/video_review \
  --fps 2 --thumb-width 320 --tile-cols 8
```

应用 EDL：

```bash
python doubao-seedance-video/scripts/video_review_tools.py apply-edl \
  --edl work/final_edl.json \
  --output outputs/final_cut.mp4
```

## 成本报告

估算逻辑覆盖：

- 豆包 Seedance 2.0：480p、720p、1080p、4K，带或不带视频输入。
- 豆包 Seedance 2.0 Fast：480p、720p，带或不带视频输入。
- 豆包 Seedance 2.0 Mini：480p、720p，带或不带视频输入。

输出会区分：

- `estimated_pay_as_you_go_cost_rmb`
- `resource_package_debit_ratio`
- `resource_package_tokens_estimated`

当 API 返回 `usage.completion_tokens` 或 `usage.total_tokens` 时，CLI 使用真实返回值。否则回退到本地估算。

对于 Seedance 2.0 Fast 长视频计划，不要在粗略估算或分镜迭代中查询账单。只在最终镜头计划已经写完、复核、修改并锁定，且已经明确段数、每段秒数、模型、分辨率和预计重拍/补拍余量之后，正式生成第一个付费任务之前，联网执行一次资源包预检：

```bash
python ~/.codex/skills/volcengine-resource-query/scripts/volc_resource_query.py \
  seedance-fast-quota --required-tokens <resource_package_tokens_estimated>
```

如果检查返回 `ok: false`，在第一个付费生成任务前暂停，报告所需 token、剩余 token 和缺口，并要求用户充值或缩减计划。若缺少凭据，也应暂停付费生成，直到用户配置完成或明确接受余额未知/按量计费风险。

## 必需伴随技能

本技能可以单独完成简单 Seedance API 调用。但要使用 README 描述的完整长视频生产流程，请安装：

- [`doubao-seedream-image`](https://github.com/a86582751/doubao-seedream-image-skill)：角色/参考图、角色表、服装/道具参考和分镜图。
- [`doubao-seed-audio`](https://github.com/a86582751/doubao-seed-audio-skill)：环境声、拟音、旁白、对白、配音、字幕/时间戳和统一最终音频。
- [`volcengine-resource-query`](https://github.com/a86582751/volcengine-resource-query-skill)：正式长视频生成前检查火山 Seedance Fast 资源包余额。
- `digitalsamba/claude-code-video-toolkit@ffmpeg`：高级 FFmpeg 剪辑模式。

`video_review_tools.py` 仍依赖系统 `ffmpeg` 和 `ffprobe`，请确保它们在 `PATH` 上。

## 官方文档

当前模型能力、API 字段和价格请以火山引擎官方文档为准：

- 视频生成 API：https://www.volcengine.com/docs/82379/1520758
- Seedance 2.0 教程：https://www.volcengine.com/docs/82379/2291680
- Seedance 2.0 提示词指南：https://www.volcengine.com/docs/82379/2222480
- 模型计费信息：https://www.volcengine.com/docs/82379/1544106

仓库里的参考文件是实用摘要和工作流说明，不替代当前官方文档。

## 隐私与安全

这个公开包不包含 API Key、私有代理设置、生成视频、本地输出目录或机器特定配置。分享日志或结果 JSON 前请检查提示词和媒体路径，因为生成任务响应可能包含带签名的 URL。

## License

MIT. See [LICENSE](LICENSE).
