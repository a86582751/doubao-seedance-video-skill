# Doubao Seedance Video Skill for Codex

A Codex skill for creating, reviewing, editing, and cost-estimating videos with Volcano Ark Doubao Seedance 2.0, Seedance 2.0 Fast, and Seedance 2.0 Mini.

Keywords: Codex skill, OpenAI Codex, Doubao Seedance 2.0, Volcano Ark, video generation, AI video, text-to-video, image-to-video, FFmpeg video editing, visual review, prompt optimization, resource package cost estimate.

## What It Does

- Generate Seedance 2.0 videos from text, images, video references, audio references, first frames, and last frames.
- Chain multi-segment videos using returned last frames.
- Optimize rough prompts using Seedance-style cinematic prompt rules.
- Review generated clips with dense frame extraction and disposable visual-review subagents.
- Assemble final cuts with story-aware edit decision lists and FFmpeg.
- Estimate both pay-as-you-go RMB cost and resource-package token debit.
- Report billing summaries after single clips or final long-form exports.

## Repository Layout

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
    seedance_video.py
    seedance_webhook_server.py
    video_review_tools.py
```

## Install In Codex

Clone this repository, then copy or install the skill folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R doubao-seedance-video ~/.codex/skills/
```

Or install from GitHub with Codex's skill installer if your environment supports GitHub skill paths:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo <owner>/<repo> \
  --path doubao-seedance-video
```

Restart Codex after installing a new skill.

## Configuration

The CLI reads process environment variables first, then falls back to:

```text
~/.codex/seedance.env
```

Create that file from the example:

```bash
cp .env.example ~/.codex/seedance.env
```

Required:

```text
SEEDANCE_API_KEY=your_volcano_ark_api_key
```

Optional:

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

Never commit your real `.env` file or API key.

## Quick Start

Estimate cost:

```bash
python doubao-seedance-video/scripts/seedance_video.py estimate \
  --model fast --duration 5 --resolution 720p --ratio 16:9
```

Generate one video:

```bash
python doubao-seedance-video/scripts/seedance_video.py generate \
  --prompt "A cinematic street scene at dusk, slow tracking shot, natural light" \
  --duration 5 --resolution 720p --ratio 16:9 \
  --output-dir outputs
```

Create dense visual-review frames:

```bash
python doubao-seedance-video/scripts/video_review_tools.py pack \
  --video outputs/example.mp4 \
  --output-dir work/video_review \
  --fps 2 --thumb-width 320 --tile-cols 8
```

Apply an edit decision list:

```bash
python doubao-seedance-video/scripts/video_review_tools.py apply-edl \
  --edl work/final_edl.json \
  --output outputs/final_cut.mp4
```

## Cost Reporting

The estimate logic covers:

- Doubao Seedance 2.0: 480p, 720p, 1080p, 4K, with and without video input.
- Doubao Seedance 2.0 Fast: 480p, 720p, with and without video input.
- Doubao Seedance 2.0 Mini: 480p, 720p, with and without video input.

It separates:

- `estimated_pay_as_you_go_cost_rmb`
- `resource_package_debit_ratio`
- `resource_package_tokens_estimated`

When API `usage.completion_tokens` or `usage.total_tokens` is available, the CLI uses it. Otherwise it falls back to local estimates.

## Recommended Companion Skills

This skill can work alone for Seedance API calls. For full production workflows, install:

- `doubao-seedream-image` for character/reference images.
- `doubao-seed-audio` for coherent final audio.
- `digitalsamba/claude-code-video-toolkit@ffmpeg` for advanced FFmpeg editing patterns.

The `video_review_tools.py` script still uses your system `ffmpeg` and `ffprobe`, so make sure both are on `PATH`.

## Official Documentation

For current official model capabilities, API fields, and pricing, consult Volcano Engine documentation:

- Video generation API: https://www.volcengine.com/docs/82379/1520758
- Seedance 2.0 tutorial: https://www.volcengine.com/docs/82379/2291680
- Seedance 2.0 prompt guide: https://www.volcengine.com/docs/82379/2222480
- Model billing information: https://www.volcengine.com/docs/82379/1544106

The bundled reference files are practical summaries and workflows, not a substitute for current official docs.

## Privacy And Safety

This public package does not include API keys, private proxy settings, generated videos, local output folders, or machine-specific configuration. Review prompts and media paths before sharing logs or result JSON, because generated task responses can include signed URLs.

## License

MIT. See [LICENSE](LICENSE).
