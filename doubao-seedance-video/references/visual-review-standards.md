# Visual Review Standards For Generated AI Video Segments

Use these standards when reviewing newly generated Seedance clips or source clips before they enter the editing timeline. This file is intentionally practical: treat it as a pass/fail checklist for disposable segment-QA subagents.

Do not use this file as the default workflow for final multi-clip assembly. For joining clips, classifying boundaries, writing an EDL, or deciding cut techniques, use `references/clip-assembly-workflow.md` instead.

## Source Principles

- Continuity editing must keep the viewer grounded in time, space, and action, with props, costumes, eyelines, direction, and movement making sense across cuts. Adobe notes continuity editing blends shots into a seamless narrative and grounds viewers in time and space: https://www.adobe.com/creativecloud/video/hub/ideas/what-is-continuity-editing-in-film.html
- Cuts affect narrative flow, pacing, tone, and audience focus. Adobe's cuts guide stresses choosing cuts for the story, timing cuts to rhythm, cutting on motion, using J/L cuts for smoother transitions, and avoiding excessive jump cuts unless stylistic: https://www.adobe.com/creativecloud/video/post-production/cuts-in-film.html
- Continuity editing is storytelling-oriented: temporal continuity controls order, duration, and frequency; spatial continuity uses establishing shots and spatial rules so camera changes do not break viewer immersion: https://edumovie-tfai.org.tw/article/content/377
- Short film edits must be ruthless: every second should push the story, and character positions/directions should make sense across cuts: https://www.indieshortsmag.com/tutorials/post-production/2026/01/ultimate-guide-to-short-film-post-production/
- Pacing changes must have intent. Random pace changes read as amateur; pace should support the emotional destination of the scene: https://www.insidetheedit.com/blog/pacing-in-video-editing

## Internal Cut Review

Seedance may create internal cuts inside one generated clip. For those internal cuts, answer:

1. **Story cause/effect:** Does shot B follow logically from shot A, or does it feel like a random inserted image?
2. **Temporal continuity:** Is time passing, compressing, repeating, or jumping? Is that clear to the viewer?
3. **Spatial continuity:** Do subject position, screen direction, eyeline, and geography still make sense?
4. **Action continuity:** Does motion continue, complete, or intentionally jump? Prefer cutting on motion when possible.
5. **Subject continuity:** Is the main subject still identifiable? Did identity, costume, prop, or role drift?
6. **Emotional continuity:** Does the cut preserve the intended feeling, or does it interrupt the moment before it lands?
7. **Pacing intent:** Is the shot length justified by information, emotion, rhythm, or montage logic?
8. **Audio bridge:** Would a J-cut/L-cut, ambience bed, Foley, or music bridge make the visual transition less abrupt?

## Segment-Level Review

A generated segment passes only when the retained shots form one readable unit:

- Basic common sense and physical plausibility pass first. Do not judge beauty, mood, or style before checking whether bodies, objects, gravity, mechanics, and space can exist.
- The viewer can state what happened, where, and why.
- Shot order has a clear progression: setup -> action/reaction -> consequence, or a deliberately structured montage.
- Fast cutting is motivated by tension, comedy, celebration, chaos, or compression. If it is merely a cluster of unrelated images, mark FAIL.
- Establishing shots and close-ups are balanced. Do not jump from crowd to flag to salute to wide city view unless the montage idea is clear.
- Repeated beats are removed unless repetition is a deliberate joke, emphasis, ritual, or rhythm.
- Emotional beats are held long enough to register. Do not cut away from a face, gesture, or reveal before the viewer understands it.

## Common Sense And Physics Gate

Run this gate before aesthetic review. Treat obvious common-sense or physics violations as hard story failures, not minor visual defects. A beautiful clip still fails when the viewer immediately thinks "that cannot happen."

Check:

- **Human locomotion:** people should not walk or run backward while the shot implies normal forward travel. Feet, knees, hips, torso, head direction, center of gravity, arm swing, and travel direction should agree unless the action is clearly deliberate.
- **Ground contact and gravity:** characters should not slide without footfalls, float without cause, pass through floors, or ignore slopes, stairs, impacts, weight, or inertia.
- **Mechanical clearance:** doors, ground hatches, elevators, platforms, vehicles, gates, and machinery must not open through people or objects. If the ground opens or a large door rises, the danger zone below/in front of it should be empty or visibly cleared first.
- **Spatial occupancy:** crowds should avoid openings, moving machinery, collapsing ground, fire, flood, or other hazards unless the story explicitly shows panic or harm. People cannot occupy the same space as doors, walls, vehicles, or each other.
- **Cause/effect order:** alarms, tremors, reactions, or visible triggers should precede major mechanical or disaster actions when the beat depends on them. People should move toward an entrance only after the entrance is visible or announced.
- **Force and material behavior:** hair, clothing, smoke, snow, dust, debris, water, fire, and fabric should follow the same wind and gravity direction. Heavy metal structures need weight, delay, vibration, or hydraulic motion; they should not move like paper.
- **Prop and body continuity:** a phone, bag, weapon, coat, handhold, scarf, or other key prop should not swap hands, vanish, duplicate, or change size during a continuous action.

Prefer **edit** only when the physically wrong moment can be removed while preserving the beat. Prefer **regenerate** when the required action itself depends on the violation, such as a character walking backward into a shelter, a hatch opening under a crowd that is still standing on it, or a machine clipping through the main subject.

## Hard FAIL Conditions

Mark the clip/cut as FAIL and recommend regeneration or stronger re-editing if any apply:

- The clip violates basic common sense or physics in a way that a normal viewer will notice: backward locomotion, impossible sliding/floating, body/object clipping, machinery moving through people, or a hazard opening while people occupy the danger zone.
- Adjacent shots have no visible narrative, spatial, emotional, or montage relationship.
- A rapid montage changes subject every shot without a stated idea or escalating rhythm.
- The scene suddenly changes location or scale without an establishing cue or motivated transition.
- A character teleports, changes costume/identity, changes handedness, or switches screen direction without explanation.
- The important action happens offscreen or is skipped so the next shot is incomprehensible.
- A shot is technically valid but narratively useless: pretty image, no story function.
- The edit hides a bad generated segment by cutting so aggressively that the story becomes unreadable.

## Regenerate vs Edit

Prefer **edit** when:

- The clip contains a good story beat but has redundant head/tail frames.
- A short frozen/static or repeated portion can be removed without losing meaning.
- A rough cut can be fixed with handles, straight cuts, J/L cuts, or a short transition.

Prefer **regenerate** when:

- The required action or reaction never appears.
- The only usable frames do not connect logically to neighboring clips.
- The clip contains persistent identity/prop/location drift.
- The final 20-30 percent of a clip turns into an unrelated montage or no-logic quick cut.
- Fixing the clip would require removing so much material that the story beat disappears.

## Disposable Subagent Output Schema

Return text only and write JSON when requested. Do not return images, screenshots, base64, or long frame listings.

```json
{
  "verdict": "PASS | FAIL | PASS_WITH_EDITS",
  "story_readability": "clear | partial | unclear",
  "continuity_score": 1,
  "pacing_score": 1,
  "emotion_score": 1,
  "technical_score": 1,
  "hard_fail_reasons": [],
  "clips": [
    {
      "path": "C:/path/clip.mp4",
      "keep_ranges": [{"start": 0.0, "end": 4.2, "reason": "keeps action and reaction"}],
      "remove_ranges": [{"start": 4.2, "end": 6.0, "reason": "unmotivated flag/crowd quick cuts"}],
      "regenerate": false,
      "regenerate_prompt_fix": ""
    }
  ],
  "sequence_notes": "One-paragraph review of story continuity, spatial continuity, and pacing intent."
}
```

Scoring: `1=bad`, `2=weak`, `3=usable`, `4=good`, `5=strong`. A generated segment should not be accepted when story readability is `unclear`, continuity score is below `3`, or any hard fail reason is present.
