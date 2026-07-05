# Seedance Official Capabilities Summary

This file summarizes public Volcano Engine Seedance 2.0 capabilities, pricing examples, and practical API behavior. For exact wording and current official examples, consult the Volcano Engine documentation linked from the repository README.

## Main Models

- `doubao-seedance-2-0-260128`: Seedance 2.0. Choose this for highest quality, final shots, complex cinematic scenes, better character/environment consistency, or 1080p/4k output. Supports 480p, 720p, 1080p, and 4k 10-bit where available.
- `doubao-seedance-2-0-fast-260128`: Seedance 2.0 Fast. Choose this when speed and cost matter and the task does not require maximum quality. Good for draft iterations, storyboarding, and ordinary 480p/720p clips.
- `doubao-seedance-2-0-mini-260615`: Seedance 2.0 Mini. Choose this for lowest-cost tests, rough blocking, high-volume simple shots, and first-pass prompt validation. Supports 480p and 720p where API access is available.
- `doubao-seedance-1-5-pro-251215`: supports Draft mode and offline inference in docs examples.

## Model Selection Rules

- Highest-quality final output: use `doubao-seedance-2-0-260128`.
- Balanced speed/cost: use `doubao-seedance-2-0-fast-260128` for 480p/720p unless the user asks for final quality.
- Lowest cost: use `doubao-seedance-2-0-mini-260615` for 480p/720p rough work.
- If the user asks for 1080p or 4k, prefer `doubao-seedance-2-0-260128`; Fast/Mini public pricing and capability snippets in this package only cover 480p/720p.
- For a production workflow, generate cheap/fast drafts first, then regenerate selected final clips with Seedance 2.0.

## Pricing And Token Estimation

The official calculator formula is:

```text
estimated tokens = (input video duration + output duration) * output width * output height * output fps / 1024 * clip count
```

If there is no video input/reference, input video duration is `0`. The API response field `usage.completion_tokens` is authoritative after generation.

Pricing examples captured from Volcano Engine public/console pricing references:

- Seedance 2.0 without video input:
  - 480p 16:9 5s: 50,220 tokens, 46 RMB / million tokens, about 2.31 RMB per clip.
  - 720p 16:9 5s: 108,000 tokens, 46 RMB / million tokens, about 4.97 RMB per clip.
  - 1080p 16:9 5s: 243,000 tokens, 51 RMB / million tokens, about 12.39 RMB per clip.
  - 4k 16:9 5s: 972,000 tokens, 26 RMB / million tokens, about 25.27 RMB per clip.
- Seedance 2.0 with video input:
  - 480p 16:9, input 10s + output 10s: 200,880 tokens, 28 RMB / million tokens, about 5.62 RMB per clip.
  - 720p 16:9, input 10s + output 10s: 432,000 tokens, 28 RMB / million tokens, about 12.10 RMB per clip.
  - 1080p 16:9, input 10s + output 10s: 972,000 tokens, 31 RMB / million tokens, about 30.13 RMB per clip.
  - 4k 16:9, input 10s + output 10s: 3,888,000 tokens, 16 RMB / million tokens, about 62.21 RMB per clip.
- Seedance 2.0 Fast without video input:
  - 480p 16:9 5s: 50,220 tokens, 37 RMB / million tokens, about 1.86 RMB per clip.
  - 720p 16:9 5s: 108,000 tokens, 37 RMB / million tokens, about 4.00 RMB per clip.
- Seedance 2.0 Fast with video input:
  - 480p 16:9, input 10s + output 10s: 200,880 tokens, 22 RMB / million tokens, about 4.42 RMB per clip.
  - 720p 16:9, input 10s + output 10s: 432,000 tokens, 22 RMB / million tokens, about 9.50 RMB per clip.
- Seedance 2.0 Mini without video input:
  - 480p 16:9 5s: 50,220 tokens, 23 RMB / million tokens, about 1.16 RMB per clip.
  - 720p 16:9 5s: 108,000 tokens, 23 RMB / million tokens, about 2.48 RMB per clip.
- Seedance 2.0 Mini with video input:
  - 480p 16:9, input 10s + output 10s: 200,880 tokens, 14 RMB / million tokens, about 2.81 RMB per clip.
  - 720p 16:9, input 10s + output 10s: 432,000 tokens, 14 RMB / million tokens, about 6.05 RMB per clip.

Resource package debit rules summarized from Volcano Engine resource-package documentation:

- Resource packages are prepaid and only offset online inference token consumption for the matching model family: Seedance 2.0 package for Seedance 2.0, Fast package for Fast, Mini package for Mini.
- The package token balance uses the lower "with video input" scenario as the 1:1 base. Package base prices are 28 / 22 / 14 RMB per million package tokens for Seedance 2.0 / Fast / Mini.
- When a call uses a higher-priced scenario, actual generated tokens are multiplied by `official scenario price / package base price` to determine package-token debit.
- Example ratios:
  - Seedance 2.0 480p/720p: with video input 1.0, no video input 46/28 = 1.6429.
  - Seedance 2.0 1080p: with video input 31/28 = 1.1071, no video input 51/28 = 1.8214.
  - Seedance 2.0 4K: with video input 16/28 = 0.5714, no video input 26/28 = 0.9286.
  - Fast 480p/720p: with video input 1.0, no video input 37/22 = 1.6818.
  - Mini 480p/720p: with video input 1.0, no video input 23/14 = 1.6429.

Use `seedance_video.py estimate` before generation when cost matters.

## Core API

- Create: `POST /contents/generations/tasks`
- Query: `GET /contents/generations/tasks/{id}`
- Delete/cancel: `DELETE /contents/generations/tasks/{id}`
- List: `GET /contents/generations/tasks`
- Webhook: set `callback_url` on create; callback body matches query response shape.

## Supported Task Types

- Text-to-video.
- Image-to-video with first frame.
- Image-to-video with first and last frames using `role: first_frame` / `role: last_frame`.
- Multimodal reference using images, videos, and audio.
- Video editing: add, delete, replace, repaint/repair, or modify elements.
- Video extension: extend video forward/backward, or track completion with up to three video segments.
- Continuous long video: generate with `return_last_frame=true`, feed prior `last_frame_url` as next segment first frame, then concatenate.
- Draft mode where supported: create with `draft=true`, inspect, then create final video with `content: [{"type":"draft_task","draft_task":{"id":"..."}}]`.
- Web search tool where supported: `tools: [{"type":"web_search"}]`; actual search count appears under `usage.tool_usage.web_search`.

## Content Items

Text:

```json
{"type": "text", "text": "prompt"}
```

Image:

```json
{"type": "image_url", "image_url": {"url": "https://... or asset://... or data:image/..."}, "role": "reference_image"}
```

Video:

```json
{"type": "video_url", "video_url": {"url": "https://... or asset://... or data:video/..."}, "role": "reference_video"}
```

Audio:

```json
{"type": "audio_url", "audio_url": {"url": "https://... or asset://... or data:audio/..."}, "role": "reference_audio"}
```

Draft task:

```json
{"type": "draft_task", "draft_task": {"id": "cgt-..."}}
```

Asset IDs must be passed as `asset://<asset ID>` in the `<modality>_url.url` field, but prompts should still refer to assets as `图片1`, `视频1`, or `音频1`.

## Common Create Parameters

- `model`
- `content`
- `duration`: integer seconds. Seedance 2.0 range: 4-15 seconds.
- `frames`: optional frame count where supported; official docs note `frames` has higher priority than `duration`.
- `resolution`: `480p`, `720p`, `1080p`, `4k` where supported.
- `ratio`: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `adaptive`.
- `generate_audio`: boolean.
- `watermark`: boolean.
- `return_last_frame`: boolean.
- `camera_fixed`: boolean.
- `seed`: integer.
- `draft`: boolean where supported.
- `service_tier`: `default` or `flex` where supported.
- `execution_expires_after`: seconds.
- `callback_url`: public webhook URL.
- `tools`: e.g. `[{"type":"web_search"}]`.

## Input Limits

Images:

- URL, Base64 data URI, or asset ID.
- Formats include jpeg, png, webp, bmp, tiff, gif; newer models also support heic/heif.
- Size under 30 MB per image; request body under 64 MB.
- First-frame image-to-video: 1 image.
- First-last-frame: 2 images.
- Seedance 2.0 multimodal reference: 1-9 images.

Videos:

- URL or asset ID.
- MP4/MOV; H.264/H.265 video and AAC/MP3 audio.
- 480p, 720p, 1080p.
- Each video 2-15 seconds; up to 3 reference videos; total video reference duration up to 15 seconds.

Audio:

- URL, Base64 data URI, or asset ID.
- WAV/MP3.
- Each audio 2-15 seconds; up to 3 reference audios; total audio reference duration up to 15 seconds.
- Single audio under 15 MB; request body under 64 MB.

Unsupported multimodal combinations include text+audio only and pure audio.

## Practical Notes

- Use `ratio=adaptive` to reduce frame jump when image aspect ratio differs from output ratio.
- For strict first/last frame alignment, prefer roles `first_frame` and `last_frame` over only describing first/last frames in text.
- The Ark API rejects mixing `first_frame`/`last_frame` image roles with `reference_image`, `reference_video`, or `reference_audio` in the same request. For chained long videos, feed the previous segment's `last_frame_url` as the next segment's `first_frame`, then preserve identity with explicit text constraints.
- Seedance 2.0 does not directly accept real-person face reference images/videos unless they are trusted platform outputs, preset virtual portraits, or authorized human assets as described in official docs.
- Task records are retained for 7 days; generated content URLs may expire quickly. Download or transfer results promptly.


