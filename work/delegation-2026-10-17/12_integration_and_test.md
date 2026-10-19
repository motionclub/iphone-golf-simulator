# Chat 12 — Integration + test (replaces 06)

Adnan (10-18): "once we are finished with maps and weather we will integrate, then test." Maps and weather reported done on 10-18 ~15:45.

## Read first
- `AGENTS.md`, `CLAUDE.md`, `work/delegation-2026-10-17/README.md` (all sections: machine-sharing rules, heavy.sh limits [2 Unity + 2 Blender, 3 total], decisions log) and `REQUESTS.md` (every install/patch request from other chats, including the HeroShoulderDeformation blocker for the female top).
- The memory notes for each piece below.

## What to integrate (each has its own GATE_RESULTS + install/rollback)
| Piece | Where | Install |
|---|---|---|
| 60 fps (golf/shared emotes, 1080p step-down) | work/frame-rate-60b | staged |
| Rendered skies/backgrounds | work/rendered-backgrounds | staged (+ DreamEnvironment AfterApply hook) |
| Tennis animation integrity | work/tennis-anim-integrity | staged |
| Hand clearance (bake-first tracks) | work/hand-clearance | staged; BODY/CLOTH/NO_POP still FAIL (round 3) |
| Garments: female tennis top etc. | work/clothing-v2/pipeline | clone-installed only; HeroShoulderDeformation fix in REQUESTS.md |
| Male garments + shoes | memory male-garments-refpack | prefab patch applied (unstaged, backups) |
| Female face/shader | work/female-face-shader | installed + staged |
| Male face/shader | work/male-face-body | installed + staged |
| Male caps re-hug | work/accessories | staged |
| Character LOD | work/character-lod | install.sh (not installed); cache goes stale after garment installs, so re-run after garments |
| Majestic layer (6 places) | work/majestic-maps-research/build | installed (untracked) |
| Majestic all maps (16 holes) | work/majestic-all-maps | tools/install_majestic.sh {dry-run, install, rollback} |
| Landmark kit | work/majestic-landmarks | consumed by majestic-all-maps |
| Weather | work/majestic-weather | dormant files installed; `python3 -I work/majestic-weather/tools/patch_shared.py apply Unity` |

The garments, male-garments and hand-clearance chats may still be producing a newer round. Integrate their latest staged state now, and list anything that lands later as a second pass.

## Steps
1. Inventory every changed or pending file. Flag overlaps (hero prefabs, DreamEnvironment, shared shaders, Resources manifests) and check the patches apply cleanly against today's tree (`--check` / dry-run).
2. Make one integration clone in `~/integration-UnityClone` (reuse majestic-all-maps' 17 GB clone at ~/majestic-all-maps-UnityClone only if that's cleaner, then delete it after). Install in a safe order: clips → garments (+ HeroShoulderDeformation fix) → face/shader/caps → hand clearance → character LOD (rebuild its cache after garments) → majestic layer → majestic all maps → weather patch.
3. Re-sync the lobby: `work/hero-sync/sync_heroes.sh` + `work/clothing-v2/lobby/compress_maps.py`, with lobby = game sheets.
4. Test the combined project:
   - EditMode + PlayMode tests: compare against the baseline and report anything that fails differently than before.
   - Each chat's key check re-run on the combined build: the clearance sweep, the garment stress suite, the majestic budget + weather gates, and 60 fps at 1920×1080 per scene.
   - A filmed smoke playthrough: a tennis rally + serve, a golf hole in rain, a plaza walk, the locker/lobby.
5. Write `work/integration-1018/GATE_RESULTS.md` (per piece: integrated / regressed / blocked) and send Adnan the sheets and films.
6. Install into the real `Unity/` only with a single rollback script, after the combined tests pass or with the failures listed. Stage only; never commit. Ask Adnan before committing or opening a PR.

## Rules
Machine: heavy.sh for every Unity/Blender run, booked on SCHEDULE.md, clones in ~/, Unity muted (GOLF_MUTE=1 + Editor mute). Branch 10/13 holds a big staged index: preserve unrelated work. VFX + sound research is on hold (Adnan); don't integrate it. Pine walls on holes 7/15 stay.
