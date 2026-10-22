# Chat 6 — Integration (run only after chats 1–5 are done)

Read `AGENTS.md`, `CLAUDE.md`, `work/delegation-2026-10-17/README.md` and `REQUESTS.md`, then each chat's `GATE_RESULTS.md`:
- `work/frame-rate-60b/` (60 fps)
- `work/rendered-backgrounds/` (skies)
- `work/hand-clearance/` (hand/arm solver)
- `work/tennis-anim-integrity/` (tennis clips)
- `work/clothing-v2/pipeline/` (garments + fit pipeline)

## Goal
Get all five results into the real project together and prove they work together in the actual game.

## Do
1. List every file each chat changed in `Unity/` and in native Swift, plus every pending patch/install script. Flag overlaps (hero prefabs, scenes, ProjectSettings, manifests).
2. Install in this order, checking after each step: chat 4 tennis clips → chat 1 other clips + frame rate → chat 5 garments → chat 3 clearance (its proxy reads the final garments) → chat 2 skies. Resolve prefab conflicts by hand: contact times from 4, garment parts from 5.
3. Re-bake chat 3's corrected tracks, then run the full lobby re-export once (`work/hero-sync/sync_heroes.sh`) and `work/clothing-v2/lobby/compress_maps.py`.
4. Re-run on the combined project: chat 3's full clearance sweep, chat 5's stress suite, chat 4's match film plus ServeSweep, chat 1's runtime fps capture, and the `work/anim-standard` breakdown on a sample of clips.
5. Run EditMode/PlayMode tests and report anything that fails differently from before.
6. Phone build (memory `phone-build-recipe`) and an AirPlay check if a device is available; otherwise NOT RUN.

## Gates
All five chats' gates still PASS on the combined project (list any that regress); tests same or better; lobby = game sheets match (memory `hero-sync-lobby-parity`).

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only reviewed files; no commits unless Adnan says so. Unity in one APFS clone first, then the real `Unity/` only for the final install with a rollback script. `GOLF_MUTE=1`.
