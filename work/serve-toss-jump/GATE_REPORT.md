# Prompt 26 — FAIL, not installed

Project: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`. Prompt read in full: `ArtDir/hero/base_lock/parallel_prompts/26_SERVE_TOSS_THEN_JUMP.txt`.

Two candidates were rebuilt, exported, independently re-imported, collision checked and tested in the APFS clone `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump/UnityClone`. The original male/female installed Serve FBXs and their metas still equal the four rollback backups byte for byte. No commit. No INSTALLED_SHA256SUMS.txt was written because installation did not occur.

The gate verdict includes the requested runtime proof. Missing runtime fields count as FAIL; edit-mode Unity import data does not replace a live film trace. M/F means male/female. Air uses positive emitted lowest-foot clearance with no added air allowance; the existing runtime foot logger rounds to 0.1 mm. Both the zero-mm result and the over-3-mm count are provided. Wrist hand-pop rows outside the stated trophy-to-contact interval retain the 150 mm limit. Collision counts increasing on an already-listed obstacle also fail.

- **TOSS_FEET_DOWN: FAIL** — FBX toe maxima M/F 1.785/1.423 mm; Unity male lowest-right-foot maximum 63.8 mm > 10 mm; runtime heel/pelvis fields 0/0.
- **NO_AIR_BEFORE_DRIVE: FAIL** — FBX early-air frames 0/0; Unity M/F 11/39 positive-clearance frames before 1.55 s (air threshold 0 mm; over 3 mm: 1/0).
- **RELEASE_ON_PATH: FAIL** — FBX anchor maxima M/F 0.0012/0.0041 mm; Unity-import maxima 0.0047/0.0051 mm; live-palm trace fields 0.
- **LOAD_AT_TROPHY: FAIL** — FBX knee maxima M/F 76.39/76.33 deg at 1.2667 s; lowest pelvis 1.2667 s both; runtime knee/pelvis fields 0/0.
- **TAKEOFF: FAIL** — FBX 1.6000 s both; first positive Unity foot clearances M/F 0.2479/0.1517 s, outside 1.57–1.63 s.
- **AIR_AT_CONTACT: FAIL** — FBX front/back clearances M 203.2/418.4 mm, F 203.3/418.3 mm; hips +150.0 mm both; runtime pelvis fields 0.
- **APEX_AFTER_CONTACT: FAIL** — FBX apex 1.7667 s and airtime 0.4333 s both; Unity first positive-clearance segment after 1.55 s, airtime M/F 0.384/0.017 s; runtime pelvis fields 0.
- **FRONT_FOOT_LANDS_FIRST: FAIL** — FBX left lead 5 frames both, knees 58.89/59.21 deg, dip 40.0 mm both; runtime knee/pelvis fields 0/0; Serve exits 1.9783 s before authored touch 2.0333 s, captured Serve landing rows 0/0.
- **CONTACT_POSE_KEPT: FAIL** — Strings shifts at 1.3x M/F 13.15/33.43 mm (limit 30 mm); FBX elbows 173.71/173.69 deg; live interpolated elbows 170.09/170.03 deg.
- **NO_FOOT_SLIDE: FAIL** — FBX planted motion M/F 0.379/1.596 mm; landing spot maxima 0.333/0.534 mm; runtime planted-foot position fields 0.
- **WRIST_SMOOTH: FAIL** — FBX hand steps outside trophy→contact M/F 170.17/168.25 mm > 150 mm; twist steps 12.92/18.52 deg; runtime rotation fields 0.
- **CLEARANCE: FAIL** — M/F increased collision frame/obstacle pairs 2/5, extra intersecting vertices +35/+315; entirely new pairs 0/2; racket 1.3x, original penetrate_dj.py threshold 3 mm.
- **GAME_TIMES_UNCHANGED: PASS** — Clip lengths 2.5000 s / 76 frames both; stance/release/trophy/contact 0.20/0.70/1.3333334/1.70 unchanged; prefab/meta byte changes 0; films in Rally 2/2; contact-window logs 30/30 within ±0.16 s, largest clip delta 13.7 ms.

## Proof completeness — FAIL

Unity front films: **0/2**. `ServeTossFilm.Run` has fixed game/back/side captures and no front capture; no C# was edited. Side, back, game and half-speed side films exist for both heroes. Full game films from the existing `MatchHeroFilm.Run` supplement the supplied recorder, which stops saving Serve pictures before the ball bounces. Adnan eye acceptance: **0 reviews, FAIL**. Six representative movies decoded successfully at three times each; side/back pair films are 3.0 s, half-speed films 6.0 s, and full game films 10.70/10.667 s. These films are failed candidates, not an installed build.

Runtime measured fields missing from the supplied film/proof tools: palm, heel, toe, knee, pelvis, wrist rotation and planted-foot position: **0 each**. The imported Unity probe has all 52 mapped skeleton bones (Root is omitted by that probe), 76 samples, maximum disagreement with the re-imported FBX below 0.009 mm. Root translation is 0.000 mm; maximum FBX bone-length variation M/F is 0.00049/0.00123 mm (numerical evaluation).

Timeline audits also fail: maximum toss-knee flexion M/F is 38.28/38.90 degrees against the requested 25-degree maximum; stance bone positions over 0.00–0.20 s differ from actual READY by as much as 366.05/345.18 mm; front-knee flexion at contact is 78.12/73.71 degrees. See `data/timeline_audit.json` for exact values. Authoring rekeys and quaternion smoothing did not solve all constraints.

## Deliverables

- `proof/serve_keys.jpg`: both heroes, side view, every requested event including exact 0.45 s mid-toss. Authored Blender poses are explicitly labelled; landing/end are not passed off as Unity captures.
- `proof/serve_reference_comparison.jpg`: release, trophy, contact and landing next to watched reference frames. Reference time uncertainty is recorded in `WATCH_SERVE.md`.
- `film/serve_toss_jump_<sex>.mp4`: supplied recorder's game view.
- `film/serve_toss_jump_<sex>_views.mp4`: supplied recorder's back | side view.
- `film/serve_toss_jump_<sex>_side.mp4`, `_back.mp4`, `_side_half_speed.mp4`: individual supplied views.
- `film/serve_toss_jump_<sex>_game_full.mp4`: complete game-camera serve, ball landing and rally.
- `data/`: independent FBX traces, original/candidate collision lists, Unity import and runtime audits, final binary results.
- `logs/`: rebuild, export, re-import, collision and clone-only Unity logs.

## Files changed by this task

All working changes are under `work/serve-toss-jump/`: copied/rekeyed serve authoring and proof scripts; new generated NPZs and copied/baked blend files; two candidate FBXs under `export/fbx/`; these same two FBXs staged in `UnityClone/Assets/Characters/MatchHeroes/<Sex>/`; reference captures, films, sheets, logs, audits and rollback backups. No original Unity FBX, .meta, prefab, .cs, shader, kit or other animation was edited by this task. A deliverable copy also lives in the invoking chat's `outputs/serve-toss-jump/`.

Four unrelated original Unity files changed during the source-wide hash audit: `Assets/Editor/MatchHeroLockerExport.cs`, `Assets/Editor/HeroDetailTextures.cs`, `Assets/Scripts/Tennis/MatchHeroLook.cs`, `Assets/Resources/Tennis/Shaders/TennisCloth.shader`. This task did not edit or revert them. The frozen clone keeps the source it was cloned from; production Serve FBX/meta hashes remain unchanged.

## Rollback

Original backup path: `work/serve-toss-jump/rollback/` under the project above. It contains the two installed FBXs, both metas and `SHA256SUMS.txt`. Rollback is unnecessary because this candidate was not installed. `rollback/README.md` in the deliverable explains restoration of only these four files.

