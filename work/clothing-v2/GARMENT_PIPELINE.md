# GARMENT_PIPELINE — fit any garment or skin to every animation (2026-10-17)

One general system replaces the per-garment binders (`bind_polo_harmonic.py`, `bind_tank_follow.py`, the golf `HeroGarmentHemWeights` …).
Everything lives in `work/clothing-v2/pipeline/`. Numbers and gates: `pipeline/GATE_RESULTS.md`. Proof images: `pipeline/proof/`.

## 0. The three commands
```
cd work/clothing-v2/pipeline
./garment_new  <Hero> <builder> <design> <Kit_Tag> ['<json design overrides>'] run=<name>   # NEW garment: build -> export -> maps -> garment_fit
./garment_fit  <Hero> <source> [<source> ...] run=<name>                                       # fit + cover + stress suite + report
./garment_install <Hero> <run> [new_src=<out_gp dir>]                                           # into the Unity CLONE, then perf
./garment_install_batch <Hero>:<run>[:<out_gp dir>] ... [film=<clips>] [look=target]              # several heroes, ONE Editor session (+ 1080p film)
./quick_eval <Hero> <run> <base_run> <N> <source> [...]                                         # iterate fast: fit, reuse base_run's cover, suite on base_run's N worst poses only
handoff/install_garments.sh <unity project> <Hero>:<run>[:<out_gp dir>] ...                      # integration: install a finished run into ANY project (README in handoff/)
```
- Iterate on one hero with `quick_eval` (40 worst poses ≈ ¼ of the suite, the cover is reused from the base run, so a weight or
  corrective change shows up in minutes, not hours); run the full 153-pose `garment_fit` only for the final candidate.
- `<Hero>`: `MatchHero_Male | MatchHero_Female | GolfKitHero_Male | GolfKitHero_Female`
- `<source>`: `dump:Kit_Top` (re-fit what the hero wears today), `npz:<builder export>_final.npz@Kit_Tag`, `obj:file.obj@Kit_Tag` (body mesh
  space: metres, Z up, hero faces −Y). Several sources are fitted inner layer first (socks, bottoms, tops, shoes, belts).
- Builders with JSON design overrides (data, no code): `polo2` (`POLO_DESIGN`), `shoe3` (`SHOE_DESIGN`), the female reference tops via
  `py/tank_ref.py` (`TANK_DESIGN`, jobs `tennis_top` / `golf_top`).
- Report: `runs/<run>/suite/<Hero>/REPORT.md` + `sheet_worst12.jpg` (1080×1350 tiles, red = through cloth); the report attributes every
  through pixel to `victim<coverer` (which garment it tears through).
- `garment_fit` options: `keep=<Tag,...>` keeps those dump pieces' current skin weights (only seams, correctives, cover are fitted; e.g. the
  female skirt, whose existing weights beat the transfer: female tennis K3b), `resume`, `smooth=<cm>`.
- `garment_install_batch`: `GP_OUT_DIR=<dir>` (separate install source per chat), `GP_CLONE=<clone>`, `GP_SHOE_TRIM=<hex>` + `GP_FOCUS=feet`
  for shoe films. `gp/cover.py`: `GP_FOOT_ALL=1` hides all foot-weighted skin inside a shoe's footprint (opt-in).

### Switches (env, all default to the rules in section 1)
| Env | Default | What |
|---|---|---|
| `GP_LIMB_ROOT` | 1 | non-wrapping garments move a limb's weight to its torso root, only within 3→6 cm of that limb's own skin (`GP_ROOT_NEAR/FAR`) |
| `GP_WELD_TOL` | 0.002 | sewn-seam weld radius (m) |
| `GP_LIMB_TUBE` | 1 | a garment that wraps a limb: every cloth vertex inside a 13 cm tube round that limb's root bone axis (from 10 % to 130 % of the bone length, faded in over 20 %) takes the weights of that limb's skin, not the torso's — a short sleeve's underside no longer stays behind with the chest when the arm rises (golf female sleeve strips) |
| `GP_SHAPES` | 16 | corrective blend shapes per garment (32 for the knit tops; driver 0.148 ms with 64 shapes on the female tennis kit) |
| `GP_BULGE` | 0 | compression bulge (m): where a pose squeezes cloth area (`1 − area/rest`, up to 0.6) the corrective pushes it OUT by `k × compression` — fixes skin through folded cloth (elbow, armpit, waist bends). Only for garments with nothing over them (a bulging waistband goes through the polo hem). Female tennis 0.06, male polo 0.06–0.10 |
| `GP_SHOE_SKINW` | 0 | footwear takes skin-transferred weights instead of the rigid foot rule |
| `GP_MEM_GB` | 4 | background Blender leaks ~200 MB of GPU memory per rendered frame (visible in phys_footprint, NOT in RSS): cover and suite chunks exit at this footprint and the next process resumes from the checkpoint |
| `GP_COVER_REF=<run>/<Hero>/body.npz` | – | the correctives also clear 'deep' covered skin that this earlier cover still DRAWS (some frame shows it legitimately). The fix for tears no corrective could reach: male −48 %, golf female −32 % on the worst 40 poses (10-18). Pair it with that cover at install |
| `GP_SUITE_SUBSET=<json>` | – | suite only these pose keys (used by `quick_eval`) |
| `GP_HEM_LAYER`, `GP_OWN_DEEP`, `GP_REST_POKE` | 0 | REJECTED experiments, off: push-in under an outer hem (layer fights 485k), clearing own deep skin, hiding rest-pose pokes (holes 239k) |
| `GP_MAX_LIFT`, `GP_LIFT_SMOOTH` | 0.025, 6 | corrective lift cap (m) and smoothing passes per pose; the lift fades out between ½ and 1× the depth limit |
| `GP_FOOT_ALL` | 0 | hide every foot-weighted skin triangle inside a shoe's footprint |
| `GP_ORACLE=<Tag>=<ckpt dir>` | – | suite only: that garment gets each pose's own solved field (the ceiling for correctives) |
| film: `GP_FOCUS=torso|feet`, `GP_VIEWS=0,90,180,45`, `GP_SWATCHES=hex,...`, `GP_FILM_BEFORE=1`, `GP_SHOE_TRIM=hex` | – | 1080p proof films: framing, fixed views relative to the hero's facing, colour swatches (COLOURS gate), film-install-film in one session |

## 1. What each stage does
| Stage | Code | What |
|---|---|---|
| dump | `unity/GarmentPipelineDump.cs` (Unity clone, batch, muted) | every hero exactly as the game builds it: FULL body (cover source), worn garments, every clip (tennis/golf + plaza/emote moves) at 30 fps as bone matrices + blend weights; runtime pose fixes run per frame like LateUpdate. Offline rebuild == Unity < 0.001 mm (`gp/validate.py`). Re-dump when the body, rig or clips change. |
| stress library | `gp/stress.py` | ~150 poses per hero: worst frames per region (axilla, side seam, shoulder blade, waist, seat, kneel, lunge, overhead, arms crossed …) + farthest-point coverage. `stress/<Hero>/poses.json` says why each pose is there. |
| weights | `gp/weights.py` | from the FULL body: each panel (UV island / piece) only takes skin of the body groups it lies over (≥ 20 % of its nearest-skin mass) AND that the garment really covers in the bind pose (GPU coverage, ≥ 3 % share); a limb group (arm / leg) only when the garment WRAPS it (covered skin within 4 cm of the cloth spans ≥ 8 of 12 sectors round the bone axis: a sleeve, a trouser leg — not the arm beside a sleeveless armhole or a hand against a skirt). Lining copies its own shell; loose cloth filled harmonically; pieces with no matched skin (buttons) take the nearest skin; field diffused over the sewn graph (4 cm; 2 cm for tight knits whose median outer gap to the skin is < 5 mm, e.g. socks). **Sewn seams**: vertices that coincide at rest (≤ 0.75 mm) share their weights and corrective deltas exactly (otherwise seams open when posed: up to 118 mm). **Hem riding**: an outer garment's cloth within 1.5–4.5 cm over another worn garment takes that garment's weights (polo hem on the shorts waistband). **Limb root**: weight a non-wrapping garment would copy from a limb's bones (arm skin under a sleeveless strap) moves to the limb's torso root (Shoulder / Hips) — the general form of HeroShoulderDeformation's arm→chest rewrite. **Footwear** (≥ 60 % of the piece on foot skin): rigid foot + toe flex + collar on the shin, no riding, no correctives. |
| coverage | `gp/evaluate.py coverage()` (GPU, 96 directions) | which garment covers which skin / garment in the bind pose; skin INSIDE a garment's outer wall counts as covered (a foot down a shoe collar). |
| correctives | `gp/correctives.py`, run by `gp/fit.py` | per stress pose the smallest smooth outward lift that keeps the cloth outside the skin it must clear and outside the garments under it. Skin deep under the garment (> 3 cm from any uncovered skin) is hidden by the cover and needs no clearance; penetrations deeper than 3 cm are limbs through the body (hand-clearance solver). Compressed to ≤ 16 (`GP_SHAPES`) blend shapes `GP_PoseNN`, RBF over 33 pose features, bind pose = neutral anchor (exactly 0 at rest). Runtime: `Unity/Assets/Scripts/Tennis/GarmentPoseCorrectives.cs` (same features as `gp/features.py`). |
| cover | `gp/cover.py` | covered skin is hidden unless some frame of some clip shows it legitimately (not through cloth); one-ring safety band. Skin inside a shoe (its box below 60 % of its height) counts as covered by it, and footwear-covered skin > 2.5 cm from uncovered skin is always hidden. Checkpoints are keyed on the posed garments (weights + corrective shapes), not geometry alone. |
| stress suite | `gp/suite.py` | coverage is limb-filtered first (`evaluate.limb_filter`: a garment covers limb skin only where it follows that limb, so an arm passing in front of a sleeveless top is not a tear). 24 orthographic GPU id views per pose: TEARS (covered skin seen with its garment < 2.5 cm behind it), LAYERS (a garment through an outer garment), HOLES (hidden skin seen through). 3×3 speck filter. |
| offsets | `gp/offsets.py` | per bone, skin-to-outer-cloth distance (rest + stress p95/max) → `KitV2_<Sport>_<Sex>_offsets.json` for the hand/arm clearance solver (format in `work/delegation-2026-10-17/REQUESTS.md`). |
| install | `gp/export.py`, `cover.export_cover`, `Unity/Assets/Editor/GarmentPipelineInstall.cs` | patches the worn mesh asset in place (weights, bind poses, GP_Pose shapes; UVs/normals untouched; mesh name gets ` [gp]` so old per-garment runtime binders skip it), renderer bones, Resources correctives / hide lists / offsets. Brand-new meshes go through `ClothingV2Install` first (`new_src=`). |
| perf | `unity/GarmentPipelinePerf.cs` | driver ms per hero + 1920×1080 render ms with correctives live vs zero. |

## 2. Read the report
- `GATE TEARS: PASS` = 0 skin pixels through cloth in every stress pose. FAIL lists the poses; the sheet shows them (red).
- `HOLES` must be 0: hidden skin seen through an opening (cover too greedy, or a hem that lifts). The report splits them into background /
  lining (real see-through) / an outer surface > 3 cm behind the hidden skin (can be a solid low shoe upper).
- Typical fixes, no code: more ease in the builder design, `smooth=3` (smoother weights), move an opening / hem in the design JSON.

## 3. Operational notes (2026-10-17)
- The machine restarted several times today and `/private/tmp` is wiped on restart: the Unity clone lives at `~/garments-UnityClone`
  (`cp -cR Unity ~/garments-UnityClone`; same APFS volume). One Editor, `GOLF_MUTE=1` + Editor master mute in every tool.
- Long stages are resumable: corrective fields are checkpointed per pose (`runs/<run>/<Hero>/ckpt_*`), suites per pose (`rows_*.jsonl`);
  `./queue.sh jobs.txt` runs a job list and skips finished lines — after a restart just run it again.
- Builders write into `out_gp/` (`CV2_OUT`), never into `out/` (today's staged garments).
- **Sharing the machine** (`work/delegation-2026-10-17/README.md`): every Blender / Unity launch in these scripts (`garment_fit`, `garment_new`,
  `garment_install`, `fit.py`'s coverage subprocess, `shoes/run_shoe3.sh`, `tank/ref_try.sh`) goes through
  `work/delegation-2026-10-17/heavy.sh` (10-18: 2 Unity + 2 Blender, 3 heavy jobs total, a second job of a kind needs ≥ 30 % free and low swap; override the path with `GP_HEAVY`).
  The stall watchdog ignores time spent waiting for a slot. Run one pipeline command at a time per chat, book it on `SCHEDULE.md`,
  and put several heroes/garments in one queue instead of parallel commands. No warm Blender server (`scratch2/server.py`) left running.
- `garment_fit … resume` keeps the pieces already fitted in that run (after a restart); cover and suite resume from their checkpoints.

- Never edit a zsh script (`garment_fit`, `queue.sh` …) while it runs: zsh reads scripts incrementally and the running copy breaks.

## 4. A new skin (body) instead of a garment
Re-dump (`GarmentPipelineDump`), `python3 gp/stress.py <Hero>`, then `./garment_fit <Hero> dump:Kit_Top dump:Kit_Bottom …` for every worn piece.
