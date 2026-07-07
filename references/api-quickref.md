# Doubao Seedance 2.0 API Quick Reference

Base URL:

```text
https://ark.cn-beijing.volces.com/api/v3
```

Create task:

```http
POST /contents/generations/tasks
Authorization: Bearer <key>
Content-Type: application/json
```

Typical payload:

```json
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {"type": "text", "text": "video prompt"},
    {"type": "image_url", "image_url": {"url": "https://... or data:image/png;base64,..."}}
  ],
  "duration": 10,
  "resolution": "720p",
  "ratio": "16:9",
  "generate_audio": true,
  "watermark": false,
  "return_last_frame": true,
  "camera_fixed": false
}
```

Poll task:

```http
GET /contents/generations/tasks/{task_id}
Authorization: Bearer <key>
```

Expected success shape:

```json
{
  "id": "cgt-...",
  "model": "doubao-seedance-2-0-260128",
  "status": "succeeded",
  "content": {
    "video_url": "https://...",
    "last_frame_url": "https://..."
  },
  "usage": {
    "completion_tokens": 216900,
    "total_tokens": 216900
  },
  "resolution": "720p",
  "ratio": "16:9",
  "duration": 10,
  "framespersecond": 24
}
```

Continuous-video recipe:

1. Create segment 1 with `return_last_frame=true`.
2. Poll until `succeeded`.
3. Download `content.video_url`.
4. Use `content.last_frame_url` as an `image_url` input for segment 2.
5. Repeat for each segment.
6. Concatenate local MP4 segments with FFmpeg.

Token estimate:

```text
tokens ~= width * height * fps * seconds / 1024 * count
```

Common dimensions:

- `720p 16:9`: 1280 x 720, 24 fps, 10 s = 216,000 tokens before small service-side overhead.
- Observed API usage can be slightly higher, e.g. 216,900 tokens for 10 s, 720p, 16:9 with audio.
