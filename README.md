# Natural-Language Long Video Creator for Codex + Doubao Seedance

Tell Codex a story in plain language. This skill turns that request into a full AI-video production loop: plan shots, optimize Doubao Seedance prompts, generate clips, review the actual frames, regenerate weak segments, create or preserve audio, assemble the final cut with FFmpeg, and report both pay-as-you-go and resource-package cost.

This is not just a Seedance API wrapper. It is a Codex workflow for one-request long-video creation with Volcano Ark Doubao Seedance 2.0, Seedance 2.0 Fast, and Seedance 2.0 Mini.

Keywords: natural-language long video, Codex video agent, OpenAI Codex skill, Doubao Seedance 2.0, Volcano Ark, AI short film, story-to-video, text-to-video, image-to-video, AI audio generation, voiceover, dialogue, ambience, Foley, FFmpeg video editing, visual review, prompt optimization, resource package cost estimate.

## The Promise

Give Codex a natural-language request like:

```text
Turn this roleplay scene into a 60-90 second cinematic video. Keep the characters consistent, split it into shots, generate each segment, review the result, regenerate broken clips, create coherent ambience/dialogue/voiceover if needed, edit everything into one MP4, and tell me the final cost.
```

The skill is designed to let Codex handle the whole chain in one run:

- Read a story, script, roleplay log, or worldbuilding document.
- Break it into a shot list and continuity plan.
- Create or use reference images when recurring characters matter.
- Optimize each Seedance prompt with cinematic, motion, camera, and consistency rules.
- Generate Seedance clips from text, images, video references, audio references, first frames, or last frames.
- Inspect dense extracted frames in disposable visual-review subagents.
- Reject or regenerate clips with broken logic, bad continuity, strange jumps, or unusable motion.
- Assemble the accepted clips with a story-aware edit decision list and FFmpeg.
- Preserve Seedance native audio for simple clips, or generate a coherent final soundtrack with Seed Audio for long-form edits.
- Report estimated RMB cost and resource-package token debit after the final export.

## What Makes It Different

- **Natural-language first:** the user asks for a finished video, not a pile of API calls.
- **Long-video oriented:** the workflow plans, generates, checks, and joins multiple short AI clips.
- **Visual QA built in:** generated segments are reviewed from extracted frames before they are trusted.
- **Audio-aware by default:** long videos can get a single coherent sound plan instead of mismatched per-clip audio.
- **Real editing, not prompt-only stitching:** FFmpeg performs trimming, concatenation, transitions, audio muxing, and export.
- **Cost-aware:** every completed generation task reports both pay-as-you-go price and resource-package debit.

## Audio Workflow

The intended output is a finished video, not a silent visual draft.

- **Single clip:** use Seedance native audio by default when it is good enough.
- **Multi-segment video:** usually disable per-segment native audio, then create one coherent final track with the companion `doubao-seed-audio` skill.
- **Supported sound design:** ambience, Foley, sound effects, voiceover, dialogue, dubbing, reference-audio-guided voice style, subtitles/timestamps, and music-like beds.
- **Final mix:** mux the generated audio into the edited video with FFmpeg, or mix separate stems first when timing matters.
- **User control:** skip audio only when the request explicitly says silent, muted, no audio, or visual-only.

For full audio generation, install the companion `doubao-seed-audio` skill. This Seedance skill knows when to call it during long-video production.

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
- `doubao-seed-audio` for ambience, Foley, voiceover, dialogue, dubbing, subtitles/timestamps, and coherent final audio.
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
