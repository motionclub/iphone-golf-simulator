# Chat 4 — Tennis animation integrity

You are one of 5 parallel chats in this repo; see `work/delegation-2026-10-17/README.md` for who owns what. Read `AGENTS.md` and `CLAUDE.md` first, then `work/frame-rate-60/README.md` and `work/anim-standard` (breakdown pages + `verdicts.json`), `work/tennis-gameplay-audit/README.md`, and the memory notes `anim-deformity-breakdown`, `tennis-gameplay-audit-2026-10-13`, `frame-rate-60`, `match-anims-2-build`, `serve-and-feet`, `serve-dip-jump`, `serve-toss-arm`, `tennis-hero-anim-root-causes`, `taunt-hold-gamespeed` and `tennis-knees-and-hands`.

## Goal
Adnan: "need to fix integrity of tennis animations, really bugged animations all around." Every tennis animation the player sees in a real match must play the way it was authored: both heroes, at 60 Hz, with correct contact, closed grips, planted feet and no pops between clips.

## Known problems (start list, not complete)
- Serve swing plays at swingPace 0.19–0.35: the swing near the toss apex fires while the ball is still ~1.4 m above the strings. The racket stops dead at contact (0 m/s) and follow-through is ≤ 4 m/s.
- The 10-16 60 Hz re-solve of the 14 strokes picked different racket-arm branches (the Forehand finish differs). Compare sheets are in `work/frame-rate-60/compare`.
- Racket-hand fingers open flat on the handle (side runs, finishes); fists with the thumb up; the free hand is a claw / splayed paddle / flat on the belly.
- Shoes dip up to ~17 mm on landings; planted feet slide; lock-release skate.
- Contact timing vs clip; slot contact/leftRelease times; ArmCorrected anims (`Resources/Tennis/Performance/*ArmCorrected.anim` via `TennisArmStrokeBuild`) are what really plays, not the FBX.
- Driver-level: clip selection, blend pops on transitions/resets, GameSpeed 1.2× timers, 120 Hz step traps in `HeroTennisDriver`.

## Real video references (Adnan, 10-17)
"It needs to use real video references of tennis being played from proper angles so it can actually look realistic, make sure its using youtube shorts clips for this."
- Use YouTube Shorts as the reference for every stroke, serve, split step, run/recovery, reach and reaction you touch. Real play over coaching talk-to-camera. Use full-body angles (side-on, behind the baseline, broadcast end view), at least two angles per stroke type where you can.
- List the chosen Shorts (id, what it shows, angle) in `work/tennis-anim-integrity/REFERENCES.md` and show Adnan before re-keying.
- Build per-clip reference contact sheets (frame-stepped, id + timestamps) next to our clip at matched phases and the same angle. Gate REF_MATCH per clip, naming the Shorts ids and timestamps.
- Cite by id and timestamp only, and watch in the Browser pane. Memory notes: `feedback-watch-only-listed-tennis-clips`, `reference-youtube-frame-stepping-browser-pane`, `match-anims-watch-state`.

## Do
1. **Watch first.** Film real matches in your clone, both heroes: serves, every stroke type, runs, reaches, idle, point-end taunts, at 60 fps from the gameplay camera plus a side camera. Build `work/tennis-anim-integrity/BUGS.md`: one line per bug with clip, frame/time, hero, capture and suspected cause (source clip vs import vs driver/blend). Show Adnan the list and the worst captures early.
2. **Fix at the right layer.** Source clip problems: re-key/re-solve in Blender headless and export at **60 Hz**. Import problems: metas, lastFrame, ArmCorrected rebuild. Runtime problems: driver timing, blends, transitions, retiming the serve swing to the ball. Re-run `TennisArmStrokeBuild` after any change to a source FBX or contact time.
3. **Strokes.** Choose the 60 Hz solution that matches the *approved* 30 Hz motion at shared frames (constrain the racket-arm branch). Don't accept a different motion just because it's 60 Hz.
4. **Grips and hands.** The racket hand stays wrapped on the handle in every frame (`HeroGripPolish`). The free hand gets natural relaxed/active poses, never a claw or paddle.
5. **Feet.** Planted feet stay planted; no sole dips.
6. Leave hand-through-body/cloth *clearance* to chat 3's solver. Don't hand-key around penetration unless the source pose itself is wrong.
7. Gameplay *rules* (aim from timing, serve power window) are out of scope. If an animation fix needs a rule change, write it up for Adnan instead.

## You own
Tennis source clips (male/female match strokes, serve, walk/run/side runs, reach, ReadyIdle, tennis intros/taunt timing), `Resources/Tennis/Performance`, tennis HeroMoves metas, `TennisArmStrokeBuild`, `HeroTennisDriver`, tennis animator/blend code, `HeroGripPolish`. Not `HeroPoseSafety` (chat 3), golf/plaza clips (chat 1), garments (chat 5). Shared emotes are 60 Hz already: leave them unless one is broken *in tennis only*.

## Gates (work/tennis-anim-integrity/GATE_RESULTS.md, binary, per clip × hero)
- RATE: every tennis clip is keyed at 60 Hz.
- APPROVED: hands/racket tip within 1.5 cm of the approved clip at shared frames, or Adnan approved the change.
- CONTACT: racket strings at ball within 3 cm at contact in a live match; racket speed at contact ≥ 70 % of the clip's peak, and the peak is within ±2 frames of contact.
- SERVE: in-game serve swing pace within 0.9–1.1 of authored across a ServeSweep run (`work/tennis-gameplay-audit`).
- GRIP: racket-hand finger curl stays over threshold in 100 % of frames; no thumb-up fist, claw or paddle free hand.
- FEET: planted-foot slide ≤ 1.5 cm, sole dip ≤ 5 mm.
- NO_POP: no joint angular velocity spike > 2× clip peak across any transition in a 5-minute filmed match.
- BUGS: every BUGS.md line is FIXED with proof, or OPEN with the reason.
- Visual: filmed rally + serve per hero, before vs after.

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only your reviewed files; no commits, resets or broad `git add`. Unity only in your own APFS clone (`cp -cR Unity /private/tmp/tennis-anim-UnityClone`), one Editor, `GOLF_MUTE=1`. Headless Blender, not the MCP. Disk ~38 GB: keep proof small and delete nothing that isn't yours. Install into `Unity/` only files you own; hero prefabs (slot contact times) go as a patch plus install script to chat 6. Push proof images to Adnan every ~15–20 min. Needs from other chats go in `work/delegation-2026-10-17/REQUESTS.md`.
