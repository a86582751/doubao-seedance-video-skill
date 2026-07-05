# Clip Assembly Workflow

Use this when a disposable subagent must join Seedance clips into a coherent short film. This is a practical editing workflow, not a theory note.

## Goal

Build a readable sequence from generated clips. Do not merely remove bad frames. Every join between two clips needs an editing reason.

## Required Inputs

- Source video paths.
- Intended story beats for each source clip.
- Dense frame/contact-sheet manifest from `scripts/video_review_tools.py pack`.
- Optional: audio plan, dialogue/voiceover script, target duration, mood.

Do not load `references/visual-review-standards.md` during assembly. If this assembly pass concludes that a source clip itself is defective enough to require regeneration, output a regeneration request and start a separate segment QA/regeneration pass; that later phase will load `visual-review-standards.md`.

## Step 1: Make A Beat Map

Before deciding cut points, write one line per source clip:

```json
{
  "clip": "part03",
  "intended_beat": "Du Lingxuan tries to grab the broom; Su Anan enters",
  "actual_beats": [
    {"start": 0.0, "end": 1.2, "beat": "repeated sweeping setup"},
    {"start": 1.2, "end": 3.8, "beat": "girl in white approaches and reaches for broom"},
    {"start": 3.8, "end": 6.0, "beat": "Su Anan reaction hold"}
  ]
}
```

If actual beats do not match intended beats, mark the clip for regeneration unless a useful substitute beat exists.

## Step 2: Classify Each Boundary

For every boundary `A -> B`, choose one type:

- **Continuous action:** the same action continues across the cut.
- **Reaction cut:** A shows action, B shows reaction or consequence.
- **Scene progression:** B advances to the next story beat in the same location.
- **Montage compression:** B is a deliberately compressed image in a thematic sequence.
- **Scene change:** B moves to a new place/time and needs an establishing cue.
- **Broken boundary:** B does not logically follow A.

Broken boundaries cannot be fixed by a decorative crossfade. Recut with different handles, add an insert/establishing shot, or regenerate.

## Step 3: Pick A Join Technique

Use the simplest technique that preserves story readability.

### Straight Cut

Use when:

- A and B are spatially and emotionally clear.
- The cut advances the beat.
- There is no repeated action at the boundary.

Avoid when:

- The subject jumps position, scale, or direction without motivation.
- B is a random image with no cause/effect.

### Cut On Action

Use when:

- A contains a gesture, turn, sweep, reach, step, vehicle motion, or camera move.
- B can start during or immediately after that motion.

Workflow:

1. End A just after motion begins.
2. Start B after matching motion is already underway.
3. Remove static lead-in and static tail frames.

### Reaction Cut

Use when:

- A shows an action or reveal.
- B shows someone responding.

Workflow:

1. Hold A long enough for the action to be understood.
2. Cut to B before the action becomes repetitive.
3. Hold B long enough for the reaction to register.

### J-Cut / L-Cut Audio Bridge

Use when:

- The visual cut is slightly abrupt but the story relation is clear.
- Dialogue, crowd ambience, engine sound, broom sound, music, or narration can bridge the cut.

Workflow:

1. Keep the visual cut simple.
2. Let audio from B begin slightly before B appears (J-cut), or let audio from A continue briefly over B (L-cut).
3. Use this for emotional or spatial smoothing, not to hide a nonsensical visual jump.

### Insert Or Cutaway

Use when:

- A and B both matter but their direct join is rough.
- A prop, hand movement, sign, street detail, crowd reaction, or establishing shot can bridge them.

Workflow:

1. Insert a short 0.5-2.0s shot with clear story function.
2. Prefer inserts already present in generated clips.
3. If no insert exists, mark for regeneration and request a dedicated insert shot.

### Crossfade Or Dissolve

Use only when:

- Time passes, memory/soft emotion is intended, or the cut is a stylistic transition.

Avoid when:

- Two shots are already semantically redundant.
- The transition is trying to hide broken geography or random quick cuts.

## Step 4: Handle Montages

A montage must have a visible idea. Examples:

- Public trust building: civilians -> workers -> soldiers -> flag -> leader.
- City scale: street -> wall -> tower -> night skyline.
- Comedy escalation: prank -> reaction -> crowd laughter -> embarrassed hero.

Montage rules:

- Start with a clear anchor shot.
- Order shots by escalation or theme, not random variety.
- Keep each shot long enough to identify subject and meaning.
- Use audio, rhythm, or repeated visual motif to unify the sequence.
- If the viewer cannot name the montage idea, mark FAIL.

## Step 5: Decide Edit vs Regenerate

Use edit when:

- You can keep the intended beat with clear continuity.
- A better start/end point solves the issue.
- An insert already exists.

Use regenerate when:

- The required beat is missing.
- Boundary A -> B stays broken after trying handles.
- The last third becomes unrelated quick cuts.
- Needed insert/cutaway does not exist.
- A character, prop, place, or emotion is wrong in most usable frames.

When regeneration is recommended, stop treating the problem as an editing problem. Start a new segment QA/regeneration pass and use `references/visual-review-standards.md` there.

Regeneration prompt should be specific:

```text
Regenerate part05 as one coherent ending beat, not a montage of unrelated images. Keep Chen Junkai in the street, holding the broom and thermos. Show one clear progression: citizens react warmly -> he regains confidence -> camera pulls back to the lit city wall. Avoid salute shots, unrelated flag closeups, sudden new soldiers, or abrupt city-wide cutaways before the final pullback.
```

## Step 6: EDL Requirements

The EDL must include boundaries, not only clip ranges:

```json
{
  "verdict": "PASS_WITH_EDITS",
  "output": "C:/path/final.mp4",
  "clips": [
    {
      "path": "C:/path/part01.mp4",
      "start": 0.0,
      "end": 5.1,
      "beat": "establish street and official sweeping"
    }
  ],
  "boundaries": [
    {
      "from_clip": "part01",
      "to_clip": "part02",
      "boundary_type": "scene progression",
      "join_technique": "straight cut",
      "reason": "part02 starts on motorcycle/watermelon action after repeated close-up is removed",
      "risk": "low"
    }
  ],
  "regenerate": [
    {
      "clip": "part05",
      "reason": "ending montage has no clear cause/effect",
      "prompt_fix": "..."
    }
  ]
}
```

A final cut should not be delivered when any boundary is `Broken boundary` unless the output is explicitly labeled as a draft.

## Step 7: FFmpeg Execution

For hard cuts, `scripts/video_review_tools.py apply-edl` is enough when the EDL uses simple ranges.

For J/L cuts, crossfades, audio beds, compression, or platform export, read and apply the installed FFmpeg skill:

`C:\Users\isund\.agents\skills\ffmpeg\SKILL.md`

Use FFmpeg to execute the edit; do not ask Seedance to solve timeline assembly unless a clip needs regeneration.
