---
name: doubao-seedance-video
description: Generate, poll, download, chain, review, edit, and prompt-optimize videos with Volcano Ark Doubao Seedance 2.0 / Seedance 2.0 Fast. Use when Codex needs to create Seedance text-to-video or image-to-video clips, bind multimodal assets, return last frames, make continuous short films from segments, estimate Seedance token usage, or troubleshoot Ark video generation API calls. For multi-character, story-driven, roleplay-adaptation, continuous videos, or character/world-setting docs, first create Seedream character references unless the user requests text-only generation. For multi-clip workflows, use disposable subagents for visual QA and final assembly, and use FFmpeg for real trimming, concatenation, transitions, audio muxing, and export. Generate or preserve audio by default unless the user asks for silent or visual-only output.
---

# Doubao Seedance Video

Use this skill for Doubao Seedance 2.0 video generation through Volcano Ark. When the user gives a rough idea, a prompt, or multimodal assets, optimize the prompt first using the official Seedance 2.0 prompt rules in `references/prompt-optimizer.md`.

For narrative videos with named recurring human characters, treat visual consistency planning as part of the video task. If the request includes multiple characters, a roleplay/story adaptation, a world or character setting document, continuous segments, or visually important outfits/props, create Seedream reference images before Seedance unless the user explicitly asks for pure text-to-video.

Treat audio as a required part of video delivery by default. For a single generated clip, use Seedance native audio by default. For multi-segment chains or concatenated videos, generate the video segments without native audio when practical, then create one coherent final audio track with `doubao-seed-audio` and mux it into the final video. Skip audio only when the user explicitly asks for no audio, a silent video, muted output, or visual-only output.

For long video, multi-role, or multi-reference-image workflows, keep the main thread's context lean. Do not call image-viewing tools on high-resolution generated/reference images in the main thread. For each visual QA pass, start a fresh disposable subagent, give it only the image path(s) and the checklist, let it inspect images in its own context, and have it return a short text-only verdict. Do not reuse visual-QA subagents across checks, because their own contexts can also bloat.

Use `digitalsamba/claude-code-video-toolkit@ffmpeg` as the post-production execution layer for trimming, concatenation, transitions, compression, audio extraction/muxing, and final MP4 export. It is installed locally as the `ffmpeg` skill at `the installed `ffmpeg` skill`; read that skill's `SKILL.md` when final editing, transcoding, or platform export details are needed. Seedance generates shots; disposable visual-review subagents decide what to keep; FFmpeg performs the actual cuts and encodes.

Use separate references for separate phases. During **segment generation QA**, read `references/visual-review-standards.md` before asking a disposable subagent to accept/reject a generated clip. During **final assembly/editing**, read `references/clip-assembly-workflow.md` before asking a disposable subagent to join clips, classify boundaries, choose straight cuts/action cuts/reaction cuts/J/L cuts/inserts/dissolves, or request regeneration. Do not load both in the same review pass. If final assembly finds that a source clip itself must be regenerated, stop assembly, start a new segment QA/regeneration pass, and load `references/visual-review-standards.md` only in that new pass.

Phase map:

- Prompt writing: read `references/prompt-optimizer.md`.
- Character/reference-image QA: use a disposable subagent with the image checklist in this file.
- Generated segment QA: read `references/visual-review-standards.md`; decide accept, trim handles, or regenerate.
- Final multi-clip assembly: read `references/clip-assembly-workflow.md`; produce beat map, boundary decisions, EDL, and FFmpeg output.
- FFmpeg details: read `the installed `ffmpeg` skill (`digitalsamba/claude-code-video-toolkit@ffmpeg`)` only when the edit needs more than simple hard cuts or export defaults.

## Tool

Run the bundled CLI:

```powershell
python scripts/seedance_video.py --help
```

Prefer the bundled Python runtime when available:

```powershell
python scripts/seedance_video.py --help
```

## Configuration

The CLI reads process environment variables first, then falls back to `~/.codex/seedance.env`.

Supported variables:

- `SEEDANCE_API_KEY`, fallback `ARK_API_KEY`
- `SEEDANCE_BASE_URL`, default `https://ark.cn-beijing.volces.com/api/v3`
- `SEEDANCE_MODEL`, default `doubao-seedance-2-0-260128`
- `SEEDANCE_CREATE_PATH`, default `/contents/generations/tasks`
- `SEEDANCE_STATUS_PATH_TEMPLATE`, default `/contents/generations/tasks/{task_id}`
- `SEEDANCE_LIST_PATH`, default `/contents/generations/tasks`
- `SEEDANCE_DURATION`, default `10`
- `SEEDANCE_RESOLUTION`, default `720p`
- `SEEDANCE_RATIO`, default `16:9`
- `SEEDANCE_GENERATE_AUDIO`, default `true`
- `SEEDANCE_WATERMARK`, default `false`
- `SEEDANCE_RETURN_LAST_FRAME`, default `false`
- `SEEDANCE_CAMERA_FIXED`, default `false`
- `SEEDANCE_POLL_INTERVAL`, default `5`
- `SEEDANCE_MAX_WAIT_MINUTES`, default `30`
- `SEEDANCE_SERVICE_TIER`, optional
- `SEEDANCE_CALLBACK_URL`, optional

Never print full API keys. When checking configuration, use `--show-config --dry-run`, which masks secrets.

## Common Commands

Text-to-video, poll, and download:

```powershell
python scripts/seedance_video.py generate --prompt "一艘银色飞船掠过木星云层，电影感，缓慢推镜" --duration 10 --resolution 720p --ratio 16:9 --output-dir ./outputs
```

Image-to-video from one first-frame image:

```powershell
python scripts/seedance_video.py generate --prompt "从图片1开始，镜头缓慢拉近，人物轻轻回头" --image /path/to/first.png --image-role first_frame
```

First and last frame generation:

```powershell
python scripts/seedance_video.py generate --prompt "从图片1平滑过渡到图片2，保持人物服装一致" --image /path/to/first.png --image /path/to/last.png --image-role first_frame --image-role last_frame
```

Multimodal reference with image, video, and audio:

```powershell
python scripts/seedance_video.py generate --prompt "参考视频1的运镜，参考音频1的背景音乐，生成图片1中的角色在科幻走廊中前进" --image /path/to/character.png --image-role reference_image --video /path/to/camera.mp4 --video-role reference_video --audio /path/to/music.mp3 --audio-role reference_audio
```

Video editing or extension:

```powershell
python scripts/seedance_video.py generate --prompt "严格编辑视频1，将墙面改为蓝色，天气和光线参考图片1，其余动作和运镜不变" --video /path/to/source.mp4 --video-role reference_video --image /path/to/snow.png --image-role reference_image
```

Create a Draft video where supported:

```powershell
python scripts/seedance_video.py generate --model doubao-seedance-1-5-pro-251215 --prompt "女孩抱着狐狸，镜头缓缓拉出" --image /path/to/first.png --draft --duration 6 --resolution 480p
```

Create a final video from a Draft task:

```powershell
python scripts/seedance_video.py generate --draft-task cgt-... --model doubao-seedance-1-5-pro-251215 --resolution 720p --return-last-frame
```

Create a continuous long video from segment prompts. This uses each segment's returned last frame as the next segment's first frame and optionally concatenates with FFmpeg:

```powershell
python scripts/seedance_video.py chain --prompts-json /path/to/segments.json --duration 10 --return-last-frame --concat --output-dir ./outputs
```

Check or fetch an existing task:

```powershell
python scripts/seedance_video.py status cgt-...
```

List or delete tasks:

```powershell
python scripts/seedance_video.py list --status succeeded --model doubao-seedance-2-0-260128
python scripts/seedance_video.py delete cgt-...
```

Estimate token usage without calling the API:

```powershell
python scripts/seedance_video.py estimate --duration 10 --resolution 720p --ratio 16:9 --count 15
```

Estimate cost and resource-package debit, and let the CLI pick a model by task goal:

```powershell
python scripts/seedance_video.py estimate --goal cheap --duration 5 --resolution 720p --ratio 16:9 --count 20
python scripts/seedance_video.py estimate --goal quality --duration 10 --resolution 1080p --ratio 16:9 --count 1
python scripts/seedance_video.py estimate --model fast --duration 5 --resolution 720p
```

The estimate output separates cash cost from package balance. `estimated_pay_as_you_go_cost_rmb` is the postpaid RMB estimate. `resource_package_tokens_estimated` is the expected resource-package token debit. Resource packages use the model's lower "with video input" package base price as 1:1, so higher-priced scenes such as text-to-video/no-video-input debit more package tokens than generated tokens.

## Cost Reporting

After every completed video generation task, report cost to the user. For a single `generate` task, report it immediately after that clip finishes. For a long-form or multi-segment task, report the aggregate cost after final editing/export is complete, and include per-segment detail when useful.

Use the actual API `usage.completion_tokens` or `usage.total_tokens` when present in the task response. If the API response does not include usage, use `seedance_video.py estimate` or the pricing tables in `references/official-capabilities.md` and clearly label the numbers as estimates. For video-input/reference-video tasks, include the input video duration in the estimate when known; if it is unknown, say the fallback estimate may be low.

Every final delivery message for a generated video must include:

- model used, resolution, duration, and whether video input was used;
- tokens used or estimated, including the token source (`api_usage` or `local_estimate`);
- pay-as-you-go RMB estimate: `estimated_pay_as_you_go_cost_rmb`;
- resource-package debit: `resource_package_tokens_estimated` and `resource_package_debit_ratio`;
- a note that final billing/remaining balance is authoritative in Volcano usage and resource-package management.

Dry-run a payload without spending tokens:

```powershell
python scripts/seedance_video.py generate --prompt "测试" --dry-run --show-config
```

## Prompt Optimization

Before calling the API, optimize rough prompts unless the user explicitly says to use the prompt verbatim.

For every video generation call, make prompt optimization auditable. Before `generate` or `chain`, either:

- read `references/prompt-optimizer.md`, rewrite the user/story prompt into a Seedance-ready prompt, and use that optimized prompt in the API call; or
- if the user explicitly requests verbatim generation, keep the original prompt and mark it as verbatim.

For single clips, include a short final note such as `提示词：已按 prompt-optimizer.md 优化` or `提示词：按用户要求原样使用`. For multi-segment or long-form videos, save the optimized segment prompts to an outputs/work JSON file and report that path with the final video. Do not silently generate from a rough prompt without either optimizing it or labeling the run as verbatim.

Read `references/prompt-optimizer.md` when:

- The user asks to optimize, rewrite, polish, or improve a Seedance prompt.
- The prompt uses images, videos, audio, asset IDs, first/last frames, editing, extension, or long-video segments.
- The user wants a continuous video, a short film, a multi-shot scene, or character/environment consistency.
- The input prompt is vague, only adjective-heavy, or missing subject/action/camera/stability constraints.

Use the official rules to produce a final prompt that can be passed directly to `seedance_video.py generate` or split into segment prompts for `seedance_video.py chain`.

## Workflow

1. Use `estimate` first when the user asks about cost, resource-package balance, or remaining quota. Report both pay-as-you-go RMB and resource-package token debit when the user has a package.
2. Select the model based on task goal:
   - highest final quality, complex shots, 1080p/4k: `doubao-seedance-2-0-260128`.
   - balanced speed/cost for drafts and ordinary 480p/720p clips: `doubao-seedance-2-0-fast-260128`.
   - lowest-cost tests and simple rough clips: `doubao-seedance-2-0-mini-260615`.
3. Decide whether text-only generation is sufficient:
   - Use pure text-to-video for simple, single-subject, one-off clips where exact identity is not important.
   - Create Seedream character references first when the video has 2+ named recurring characters, a roleplay/story adaptation, a character/world setting document, a continuous short-film structure, or outfit/prop identity that matters to the story.
4. If any generated/reference images need visual QA, isolate the check:
   - Do not inspect high-resolution images in the main thread for long, multi-role, or multi-image workflows.
   - Start a new disposable subagent for each QA pass. Give it only image paths and the checklist; require a concise text-only response with verdict, pass/fail points, and regeneration advice.
   - Discard the subagent after the check. Do not reuse the same subagent for later images or later stages.
5. Optimize the prompt using `references/prompt-optimizer.md` unless the user requests verbatim generation.
6. For multi-segment narrative videos, do not rely on blind `chain --concat` as the final creative workflow. Use a generate-review-revise-edit loop:
   - Generate one segment at a time, with `--return-last-frame` when continuity is needed.
   - After each segment finishes and downloads, create a dense visual-review pack with `scripts/video_review_tools.py pack` and assign a fresh disposable subagent to inspect the frames/contact sheets.
   - For this segment QA subagent, read and use only `references/visual-review-standards.md`. Boundary and joining decisions belong to the final assembly pass, not segment QA.
   - The subagent must return text only: pass/fail, visible defects, repeated action, identity/prop drift, weird jumps, narrative continuity, spatial continuity, pacing, recommended keep range, and whether the segment should be regenerated.
   - If the segment is not acceptable, rewrite that segment prompt using the subagent's concrete failure notes, then regenerate the segment before continuing. Prefer fixing the local segment prompt over accepting a bad segment and hoping final editing will hide it.
   - Keep the main thread lean: do not view dense extracted frames or contact sheets in the main thread.
7. Use `generate` for single clips, multimodal reference, editing, extension, Draft, or raw content JSON. Ask only for missing prompt or source assets.
8. Use `chain` only for quick drafts, simple continuity tests, or when the user explicitly prefers automatic chaining. For final story videos, generate segments under the visual-review loop above.
9. Before final delivery of any multi-segment video, run a final disposable-subagent visual editing pass:
   - Read `references/clip-assembly-workflow.md` and include its beat map, boundary classification, join-technique selection, montage rules, and EDL boundary schema in the subagent brief.
   - Prepare dense frames/contact sheets for all candidate clips with `scripts/video_review_tools.py pack`.
   - Ask the subagent to produce an edit decision list (EDL) JSON: each clip path, trim `start`, trim `end`, keep reason, repeated/defective material removed, boundary type, join technique, boundary risk, and regenerate recommendation.
   - The final-edit review must be story-aware, not only technical. Mark the cut as FAIL if it contains random-feeling quick cuts, unmotivated changes of subject, impossible spatial jumps, missing cause/effect between adjacent shots, emotional beats that vanish too quickly, or a montage that does not clearly read as intentional.
   - Apply the EDL with `scripts/video_review_tools.py apply-edl` or an equivalent FFmpeg command. For anything beyond simple hard cuts, read and use the installed `ffmpeg` skill from `the installed `ffmpeg` skill` (`digitalsamba/claude-code-video-toolkit@ffmpeg`) for trim, concat, crossfade, audio mux, compression, and export patterns.
   - If the assembly subagent flags a clip as requiring regeneration, treat that as a phase change: close the assembly pass, run a new segment QA pass using `references/visual-review-standards.md`, rewrite that clip prompt, regenerate the clip, and repeat final assembly instead of delivering a polished cut with a broken scene.
10. Use `status`, `list`, and `delete` for task management.
11. Include audio unless the user explicitly requests no audio:
   - For one generated segment, use Seedance native audio by default.
   - For multi-segment chains, concatenated videos, or continuous short films, disable native segment audio when practical, then use the `doubao-seed-audio` skill to create one coherent final track with ambience, Foley, music bed, voiceover, or dialogue, and mux it into the final video.
   - Use Seed Audio for single clips only when the user asks for precise dialogue, narration, timed audio, separate stems, or a post-production workflow.
12. Store user-facing videos under the active thread `outputs` directory when possible.
13. Report the local file path, audio/post-production path when separate, task ID, usage tokens, billing summary, visual-review verdict summary, EDL path when used, and remote URL expiry caveat. Do not expose signed URL secrets unless the user needs the direct link.

## Disposable Subagent Review

Use disposable subagents for video visual review whenever the task involves multiple generated clips, dense frame extraction, repeated visual QA, or final editing decisions. This prevents the main thread request body from ballooning with image data.

There are two review types:

- **Segment QA:** after generating one Seedance clip, read `references/visual-review-standards.md`. Evaluate whether the generated clip is usable or needs prompt revision/regeneration.
- **Final assembly:** after all candidate clips exist, read `references/clip-assembly-workflow.md`. Evaluate how clips should be joined, whether boundaries work, and what EDL/FFmpeg edit should be executed.

Do not merge the two reference files into every subagent prompt. Keep the subagent brief phase-specific. Final assembly may mention source-clip defects and ask for regeneration, but it must not read or re-run the segment QA standard inside the same pass.

Rules:

- Spawn a fresh subagent for each review batch. Do not reuse old visual-review subagents.
- Give it only the local video paths, extracted frame/contact-sheet directory, expected story beat, and a strict output schema.
- Tell it not to return images, screenshots, base64, or long frame-by-frame dumps.
- Require concise text plus machine-readable JSON paths when it writes EDL files.
- Require boundary decisions. The subagent must explain every join between adjacent clips: boundary type, selected join technique, reason, and whether the join is acceptable or needs insert/regeneration.
- Require narrative judgment, not just defect detection. The review must explicitly check whether each retained shot logically follows from the previous shot, whether the same subject/space/action is readable, and whether quick cuts are motivated as montage rather than accidental jumps.
- Close the subagent after receiving its final result.

Recommended segment-review prompt:

```text
你是一次性视频审片子代理。不要返回图片、base64、截图或长工具输出。
先按 doubao-seedance-video/references/visual-review-standards.md 的标准审片。
请检查这个 Seedance 片段的抽帧包：<manifest path>。
预期剧情：<segment beat>。
只返回：PASS/FAIL、可保留时间段 start/end、主要缺陷、叙事连续性、空间连续性、节奏是否像随机快切、是否需要重生、重生提示词修改建议。
如果写文件，请把 JSON 写到 outputs 或 work 并只返回路径。
```

Recommended final-assembly prompt:

```text
你是一次性视频审片/剪辑子代理。不要返回图片、base64、截图或长工具输出。
先按 doubao-seedance-video/references/clip-assembly-workflow.md 判断每两个片段之间应该如何拼接。
输入视频列表：<paths>。
请密集抽帧，判断重复、跳跃、坏帧、动作断裂、叙事连续性、空间连续性、情绪节奏、是否存在无逻辑快切。不要只做技术审片；如果 20 秒后类似“群众/旗帜/敬礼/大全景”之间没有明确因果或蒙太奇意图，应标为 FAIL 或建议重生/重剪。输出 EDL JSON，里面必须包含 clips 和 boundaries：每个 boundary 写明 boundary_type、join_technique、reason、risk、是否需要 insert 或 regenerate。然后用 FFmpeg 生成最终剪辑。
最终只返回：PASS/FAIL、输出视频路径、EDL 路径、每段裁点摘要、叙事问题摘要、哪些片段建议重生。
如果你认为某个源片段本身需要重生，只给出重生原因和 prompt_fix；不要在本次剪辑里强行遮掩它。
```

Helper script examples:

```powershell
python scripts/video_review_tools.py pack `
  --video /path/to/part01.mp4 `
  --video /path/to/part02.mp4 `
  --output-dir ./work/video_review `
  --fps 2 --thumb-width 320 --tile-cols 8

python scripts/video_review_tools.py apply-edl `
  --edl /path/to/visual_review_edl.json `
  --output /path/to/final_visual_cut.mp4
```
## Seedream Character References

When the user needs a consistent human character, face, outfit, prop, or role image for Seedance, create the still image first with the `doubao-seedream-image` skill. This is the default path for story videos with named roles, roleplay adaptations, character/world-setting documents, multi-shot continuity, or visually important costumes and props. Seedance 2.0 can use Seedream-generated human/face photos as reference images for video generation.

Do not treat reference-image generation as merely optional in these cases. If the user supplies no character images, generate clean front or three-quarter character portraits from the provided character descriptions, then use them as `reference_image` inputs. Generate only the minimum useful set: usually one reference per recurring primary character, plus an environment reference only when the setting is visually complex or repeated.

After generating Seedream references, verify them without polluting the main thread:

- For simple one-off clips with one small image, direct inspection is acceptable when necessary.
- For long video, continuous short film, multi-role, or multiple-reference workflows, do not use `view_image` or any image-viewing tool in the main thread on full-resolution images.
- Start a fresh disposable subagent for each image or small image batch that must be checked. Pass only the local path(s), intended role/scene description, and a short checklist.
- Require the subagent to return text only: `可用/需重做`, matching details, visible defects, missing props/outfits, text/watermark issues, and the exact prompt adjustment if regeneration is needed.
- Do not ask the subagent to return images, markdown image embeds, base64, screenshots, or full transcripts. Do not reuse the subagent after one QA pass.

Suggested visual-QA checklist:

```text
核查图片路径：
预期用途：
核查标准：身份/年龄/发型/服装/关键道具/场景元素/风格/无文字水印/无多余人物。
只返回短文本结论，不要返回图片、base64、截图或完整工具输出。
```

Recommended flow:

```powershell
python ~/.codex/skills/doubao-seedream-image/scripts/seedream_image.py character --name "角色名" --description "年龄、性别、发型、脸部特征、服装、气质" --ratio 3:4 --output-dir ./outputs
python scripts/seedance_video.py generate --prompt "参考图片1中的角色，在科幻走廊中缓慢前进，保持人物身份、脸部特征和服装一致" --image /path/to/seedream_character.png --image-role reference_image --duration 5 --resolution 720p --ratio 16:9
```

For best video consistency, ask Seedream for a clean front or three-quarter portrait, clear facial features, stable lighting, fixed outfit, no text, no watermark, and no extra people.

## Required Audio And Post-Production

Every delivered video should include audio unless the user explicitly asks for no audio, silent video, muted output, or visual-only output. Use Seedance native audio by default for a single generated clip. For multi-segment chains, concatenated videos, or continuous short films, use Seed Audio post-production by default so the final video has one coherent audio bed instead of mismatched per-segment audio. Use Seed Audio for single clips only when the user asks for precise dialogue, narration, timed ambience, separate stems, or stronger audio control.

```powershell
python scripts/seedance_video.py generate --prompt "北京胡同里，角色缓慢逛街，电影感跟拍" --no-generate-audio --duration 10 --resolution 720p --ratio 16:9 --output-dir ./outputs
python ~/.codex/skills/doubao-seed-audio/scripts/seed_audio.py generate --prompt "生成10秒北京胡同白天环境音：远处人声、自行车铃、脚步声、微风，无音乐无旁白" --format mp3 --output-dir ./outputs
python ~/.codex/skills/doubao-seed-audio/scripts/seed_audio.py mux --video /path/to/silent.mp4 --audio /path/to/audio.mp3 --output /path/to/with_audio.mp4
```

Use Seed Audio separately for dialogue, narration, ambience, Foley, or music-like sound beds. Generate separate tracks when timing matters, then mix with FFmpeg before final delivery. If the user provides no audio direction, infer a fitting sound plan from the scene and keep it conservative: natural ambience first, then subtle Foley or music only when it supports the story.

## Notes

- Seedance 2.0 single outputs are 4-15 seconds at 24 fps.
- Use `ratio=adaptive` when input images may not match the target aspect ratio.
- For continuous videos, the reliable pattern is previous `last_frame_url` as next segment first frame, then FFmpeg concat.
- Seedance first/last frame roles cannot be mixed with reference media roles in the same request; for long video continuation, use prior last frame as next first frame and enforce character identity in text.
- Read `references/api-quickref.md` if implementation details or payload fields are needed.
- Read `references/prompt-optimizer.md` for official prompt engineering rules, multimodal binding syntax, and stability constraints.
- Read `references/official-capabilities.md` for the compact official capability matrix, model-selection rules, pricing notes, parameters, and limits.
- For exact official examples, consult the linked Volcano Engine Seedance documentation in the repository README.
- Use `scripts/seedance_webhook_server.py` only when testing `callback_url`; it starts a local receiver, but public callbacks still require a publicly reachable URL or tunnel.


