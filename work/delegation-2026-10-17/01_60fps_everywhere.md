# Chat 1 — Every animation at 60 fps

You are one of 5 parallel chats in this repo; see `work/delegation-2026-10-17/README.md` for who owns what. Read `AGENTS.md`, `CLAUDE.md` and `work/frame-rate-60/README.md` first, then the memory notes `frame-rate-60`, `locker-mirror`, `golf-swing-fix`, `golf-emotes-stale-clips`, `emote-standard-kit` and `intro-flyover-skip-votes`.

## Goal
Adnan: "getting all animations to be at 60 fps." The game must actually look 60 fps everywhere it is shown: Unity tennis, golf, plaza/hub, intros and the native SceneKit lobby/locker, on the phone and over AirPlay.

## Already done (10-16, uncommitted, see work/frame-rate-60)
- `LuminousCoastFrameBudget` no longer drops to 30 fps. The iOS thermal cap is now Serious 60 / Critical 30.
- Re-baked at 60 Hz: the 14 tennis match strokes (ReadyIdle excluded), Serve, Walk/Run and the 7 standard emotes plus Free Walk/Run. Spike/Scuba/Thrust/Intros were already partly 60 Hz.
- **Do not touch tennis match/serve/locomotion clips.** Chat 4 owns them and keeps them at 60 Hz.

## Do
1. **Inventory first.** List every AnimationClip and every baked track the game plays: golfer_m/f clips, the golf swing splice, golf emotes, plaza/hub clips, intro/flyover clips, accessory/prop anims, camera anims, ReadyIdle, emote-fluid clips and the SceneKit lobby bone tracks. Include UI/tween animation that drives visible motion. For each, record its key rate, length, source file, whether it is shared between sports, and who builds it. Write `work/frame-rate-60b/INVENTORY.csv`.
2. **Re-bake every clip below 60 Hz** from its source (Blender headless), except tennis clips. At shared frames the new clip must match the approved one; where a 60 Hz re-solve changes the motion, show a compare sheet the way 10-16 did. Remember the pitfalls: `.fbx.meta` `lastFrame` is in frames; wire/import scripts (EmoteStandardWire, ServeAndFeetWire, MatchHeroImport and the golf equivalents) copy 30 Hz sources back if re-run, so fix the source, not just the output; prefab contact/release times must follow the clip.
3. **Golf emotes.** They are stale Oct 4 clips borrowed from another branch (memory `golf-emotes-stale-clips`). Replace them with the current rev at 60 Hz.
4. **Runtime pacing.** Every scene must request and hold 60: `Application.targetFrameRate`, vSync count, iOS `preferredFramesPerSecond`, the SceneKit lobby `preferredFramesPerSecond`, AirPlay external display and anything that drops to 30. Check visible motion that steps at the physics rate (ball/racket Rigidbody interpolation, fixed timestep vs render), cameras updated in the wrong loop (jitter), and Animator update mode / culling that freezes clips.
5. **Lobby.** If the SceneKit exporter bakes bone tracks below 60 Hz, change the exporter's rate. Do **not** run the full lobby re-export (`work/hero-sync/sync_heroes.sh`); chat 6 does that once at the end. Prove the exporter on one clip.

## You own
Golf/plaza/hub/intro/lobby clip files and their import metas; the golf/plaza import/wire scripts; frame-rate/frame-budget/thermal code; the SceneKit exporter frame rate. Everything else belongs to someone else: tennis source clips (chat 4), `HeroPoseSafety` (chat 3), garments (chat 5), skies (chat 2).

## Gates (GATE_RESULTS.md in work/frame-rate-60b/, binary)
- INVENTORY: 100 % of played clips/tracks listed; each one is ≥ 60 Hz key density or has a written reason (e.g. a static hold).
- MATCH: re-baked clips at shared frames are within 5 mm (hands/feet/racket/club tip) of the approved clip, or there is a compare sheet Adnan has seen.
- RUNTIME: an Editor profiler capture shows ≥ 58 fps median and no 30 fps lock in the tennis match, golf hole, plaza and intro scenes. Device/AirPlay capture is PASS or NOT RUN, with the reason.
- NO_STEP: a 60 fps screen recording of the ball, racket, club and camera shows no 30 Hz stepping (frame-diff check).
- REGRESSION: existing EditMode/PlayMode tests pass, or failures are listed as same as before.

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only your reviewed files; no commits, resets or broad `git add`. Unity only in your own APFS clone (`cp -cR Unity /private/tmp/fps60b-UnityClone`), one Editor, `GOLF_MUTE=1`. Headless Blender, not the MCP. Disk ~38 GB: keep proof small and delete nothing that isn't yours. Install into `Unity/` only files you own; shared prefabs/scenes go as a patch plus install script to chat 6. Push proof images to Adnan every ~15–20 min. Needs from other chats go in `work/delegation-2026-10-17/REQUESTS.md`.
