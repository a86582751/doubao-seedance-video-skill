# Agentic Long-Video Studio for Codex + Doubao Seedance

Turn one plain-language idea into a finished AI short film, with Codex acting less like a thin API wrapper and more like a small production crew: storyboarder, prompt engineer, visual QA reviewer, pickup director, offline editor, and audio post supervisor.

This skill is built for the messy middle of long AI video creation: clips fail, continuity drifts, transitions need pickups, native per-clip audio resets, and the final edit changes the timing. The workflow handles those problems explicitly with disposable subagent review, regenerate-or-pickup loops, EDL-based final cutting, and storyboard-aware Seed Audio post-production.

It supports Volcano Ark Doubao Seedance 2.0, Seedance 2.0 Fast, and Seedance 2.0 Mini.

Keywords: agentic AI video studio, natural-language long video, Codex video agent, OpenAI Codex skill, Doubao Seedance 2.0, Volcano Ark, AI short film, story-to-video, text-to-video, image-to-video, subagent visual review, AI pickup shots, EDL editing, Seed Audio post-production, coherent soundtrack, dialogue, ambience, Foley, FFmpeg video editing, prompt optimization, resource package cost estimate.

## The Promise

Give Codex a natural-language request like:

```text
Turn this roleplay scene into a 60-90 second cinematic video.
Keep the characters consistent, split it into shots, generate each segment,
review the actual frames, regenerate or shoot pickups when the cut is weak,
lock the visual edit, rebuild the final audio plan from that edit,
create coherent ambience/dialogue/voiceover, export one MP4,
and tell me the final cost.
```

The skill is designed to let Codex handle the whole chain in one run:

- Read a story, script, roleplay log, or worldbuilding document.
- Break it into a shot list and continuity plan.
- Create Seedream character/reference images when recurring characters, outfits, props, or visual identity matter.
- Optimize each Seedance prompt with cinematic, motion, camera, and consistency rules.
- Generate Seedance clips from text, images, video references, audio references, first frames, or last frames.
- Inspect dense extracted frames in disposable visual-review subagents, instead of trusting the model response blindly.
- Reject, regenerate, or add pickup shots when clips have broken logic, bad continuity, strange jumps, weak motion, or missing connective tissue.
- Ask a separate assembly subagent to judge boundaries and produce a visual EDL for the final cut.
- Rebuild the final audio storyboard from the original script plus the locked EDL, so dialogue, narration, ambience, Foley, and music follow the actual edit.
- Preserve Seedance native audio for simple clips, or generate a coherent Seed Audio soundtrack for long-form edits.
- Report estimated RMB cost and resource-package token debit after the final export.

## What Makes It Different

- **Not just generation; actual post-production:** the skill treats planning, review, pickup generation, trimming, audio, muxing, and export as one production loop.
- **Subagent visual QA is part of the workflow:** disposable review agents inspect extracted frames/contact sheets and return concrete accept/regenerate/trim advice.
- **Regeneration and pickups are first-class:** weak shots are not politely tolerated. If a bridge, insert, reaction, reentry, or establishing shot would make the cut smoother, the workflow can generate it.
- **Final assembly uses an EDL:** a dedicated edit pass decides keep ranges and boundaries before FFmpeg creates the final cut.
- **Audio follows the locked cut:** long-video audio is generated after the visual edit is known, using a rebuilt final audio storyboard rather than raw EDL facts or isolated per-clip sound beds.
- **Dialogue-aware and ambience-aware:** Seed Audio prompts can be split by scene or stem when limits, timing, dialogue, music, or acoustic continuity require it.
- **Character continuity first:** for multi-role stories, roleplay adaptations, worldbuilding docs, or important costumes/props, Codex can create Seedream reference images before video generation.
- **Cost-aware:** every completed generation task reports both pay-as-you-go price and resource-package debit.

## Production Loop

```text
User story / assets
  -> storyboard + continuity plan
  -> optimized Seedance segment prompts
  -> generate candidate clips
  -> disposable subagent visual review
  -> accept, regenerate, or shoot pickups
  -> disposable subagent final assembly review
  -> visual EDL
  -> EDL edit-facts summary
  -> main agent rebuilds final_storyboard_for_audio.json
  -> Seed Audio post-production
  -> FFmpeg trim / concat / mix / mux
  -> final MP4 + cost report
```

The important boundary is deliberate: subagents judge visual evidence and editing facts; the main agent, which still has the original user intent and storyboard context, reconstructs the final narrative/audio plan.

## Subagent Review, Regeneration, And Pickups

Long AI video usually fails in small places: a hand jumps, a rocket loses scale, a character reappears in the wrong outfit, an action repeats, a crash has no setup, or two good clips simply do not cut together.

This skill makes those failures visible:

- `video_review_tools.py pack` extracts dense frames and contact sheets.
- A fresh disposable subagent reviews each generated segment against visual continuity, story logic, motion quality, identity consistency, pacing, and usable keep ranges.
- Failed or weak segments are regenerated with concrete failure notes folded back into the prompt.
- Optional pickups are encouraged when they materially improve the film, even if the current edit is technically passable.
- The final assembly subagent produces a standard EDL with source clip, source segment id, keep range, output timing, and boundary decision.

That means Codex can do the thing human editors do constantly: keep what works, cut what does not, and ask for one more shot when the scene needs it.

## Character Reference Workflow

For story-driven videos, character consistency is often the difference between "a few generated clips" and a believable short film.

When the request involves multiple characters, roleplay adaptation, recurring cast members, a world/character setting document, continuous segments, or visually important clothing/props, this skill is designed to call the companion [doubao-seedream-image](https://github.com/a86582751/doubao-seedream-image-skill) workflow first:

- Create clean character portraits, outfit sheets, prop references, or storyboard panels with Doubao Seedream 5.0 Lite.
- Review those images for identity, age, hairstyle, clothing, key props, style, and unwanted text/watermarks.
- Use the accepted images as Seedance `reference_image` inputs or as visual anchors for prompt writing.
- Keep the same visual references across related shots whenever the model/API combination allows it.

This gives Codex a practical route from a natural-language story or roleplay log to a more stable multi-shot video, instead of hoping every clip invents the same characters again.

## Audio Post-Production Workflow

The intended output is a finished video, not a silent visual draft and not a stack of unrelated per-clip sound beds.

For long videos, the default audio route is:

```text
initial storyboard
  + visual EDL edit facts
  -> final_storyboard_for_audio.json
  -> Seed Audio prompt(s)
  -> stems or section tracks
  -> FFmpeg mix and mux
```

Why this matters:

- A pure EDL only says what frames survived; it does not know which dialogue, narration, emotional beat, or sound cue was cut.
- The original storyboard knows the intended story, but not the final timing after review and trimming.
- The final audio storyboard reconciles both, so the soundtrack follows the movie that was actually edited.

Supported audio work includes:

- coherent ambience across cuts;
- Foley and impact design;
- voiceover and narration;
- dialogue and dubbing;
- reference-audio-guided voice style;
- subtitles/timestamps;
- music-like beds and tension layers;
- separate stems for dialogue, narration, ambience, Foley, music-like beds, and special effects.

Seed Audio prompt limits are handled as a production choice, not a blocker. If a unified prompt would exceed provider limits or become too dense, the skill can split audio by section or stem. Preferred split points are quiet transitions, ambience changes, non-dialogue bridges, establishing shots, or places with no prominent melody. It avoids splitting through dialogue, voiceover sentences, musical downbeats, impact transients, or sustained notes.

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

### API Key Sources

Volcano uses different API keys for different product families. Do not mix them:

- **Seedance 2.0 / Fast / Mini:** use the Volcano Ark key from https://ark.volcengine.com/region:cn-beijing/apiKey?apikey=%7B%7D
- **Seedream 5.0 Lite / image models:** use the same Volcano Ark key from https://ark.volcengine.com/region:cn-beijing/apiKey?apikey=%7B%7D
- **Seed Audio / OpenSpeech audio generation:** use the Speech console key from https://console.volcengine.com/speech/new/setting/apikeys?projectName=default

Recommended local files:

```text
~/.codex/seedance.env  # Ark key: SEEDANCE_API_KEY or ARK_API_KEY
~/.codex/speech.env    # Speech key: SEED_AUDIO_API_KEY or SPEECH_API_KEY
```

Environment variable split:

- Seedance CLI: `SEEDANCE_API_KEY`, fallback `ARK_API_KEY`.
- Seedream companion skill: `SEEDREAM_API_KEY`, `ARK_API_KEY`, or `SEEDANCE_API_KEY`.
- Seed Audio companion skill: `SEED_AUDIO_API_KEY`, fallback `SPEECH_API_KEY`; it does not use `SEEDANCE_API_KEY` as the audio key.

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

- [`doubao-seedream-image`](https://github.com/a86582751/doubao-seedream-image-skill) for character/reference images, role sheets, outfit/prop references, and storyboards.
- [`doubao-seed-audio`](https://github.com/a86582751/doubao-seed-audio-skill) for ambience, Foley, voiceover, dialogue, dubbing, subtitles/timestamps, and coherent final audio.
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
