# Male garments to the male reference pack — GATE_RESULTS (2026-10-17; 10-18 rounds 6 and 9)

Brief: rebuild the MALE hero's clothes + shoes (tennis + golf) to `ArtDir/style/alive/male-reference-pack-2026-10-17` in Unity and the native
lobby, without changing body, face, rig or animations. Sheet colours are examples; every garment colour stays a player pick.
Nothing committed. Hand-over notes for other chats: side-session-notes `male_garments_refpack.md`. Tools: `tools/` (README at the end).

## Summary
**10-18 round 9 (current): 11 of 13 gates PASS, 2 FAIL — shoe silhouette (gate 3: lateral 13.3 / 13.4 %, other views 15–29 %) and
stress-suite tears (gate 9: tennis 164,623 px, polo 139,343 of it; golf 59,641).** Round 9 = round-8 shoes (0.365 / 0.375 m long, enclose the
foot with 10 mm room, skinned with the foot's own weights, GP_SHOE_SKINW=1) + chat 5's K7_MT polo / shorts fit (compression-bulge correctives).

Round 6 (10-18 morning): 11 of 13 gates PASS, 2 FAIL — shoe silhouette (gate 3) and stress-suite tears (gate 9, mostly the tennis polo).
Golf master view (gate 8) now PASS: the tall golf tongue is gone and the golf hero wears short socks under the trouser hem.
The shoes now ENCLOSE the cartoon foot (see '10-18 round 6' below): no bare toes, no see-through, which costs silhouette match per view.

10-17 summary (kept for history): **10 of 13 gates PASS, 3 FAIL (shoe silhouette, golf master view = the golf shoe, stress-suite tears = the tennis polo; see table).** Slim golf trousers added 10-17 late (see 'Golf trousers slim'). The shoes now carry the sheets' construction (the old shoes had none of it).
The polo and shorts details match sheets 09/11, the golf polo matches sheet 10, and colour picks work in light, dark and saturated.
Open: the shoe proportions can't fully match the sheets on this hero's cartoon foot and ankle. The tennis polo still tears in arms-up poses:
it is the 10-13 polo mesh, the same open item as chat 5's pipeline gate. The golf trousers are now slim and straight like sheet 11 (gate 6). Lobby parity: see LOBBY (golf male lobby NOT re-synced for the slim trousers yet).

## What was built
| Piece | How | Mesh tris | Construction (vs sheet) |
|---|---|---|---|
| Tennis shoes L/R | NEW `clothing-v2/py/shoe4.py` `male_tennis`: profiles + panel polygons TRACED off sheet 13 (sheet units s,h) + `maps.details_shoe4` | 24,336 each (was 27,2xx) | navy heel counter + saddle V, toe cap, perforation field, eyestay + vamp seams with stitching, padded navy collar + lining, pull loop, white midsole with sculpt lines, grey herringbone outsole, 7 eyelets, criss-cross laces + bow, padded tongue |
| Golf shoes L/R | `shoe4.py` `male_golf` (sheet 14) | ~24,7k each | navy saddle + heel counter + padded collar, stitched cap toe, navy low sole (trim colour) with 6 star spikes + traction lugs, cream laces, tongue |
| Tennis socks | sock2 + `tools/trim_sock.py`: the sock ends 1.5 cm under the shoe rim | 5,596 / 5,518 | crew height, rib cuff (unchanged) |
| Tennis shorts | 10-13 shorts minus drawcord / eyelets / aglets | 35,546 | plain waistband (sheet 11), side vents, turned hem |
| Tennis polo | same mesh; new maps | 37,876 | ONE navy tip on the collar edge, plain rib cuffs (sheet 09), 2-button placket, hem out + vents |
| Golf polo | `polo2 golf_male` rebuilt | 38,524 | collar stand + underside in the trim colour (sheet 10), 3 buttons, rib cuffs, hem lowered behind the belt |
| Golf belt | `belt2` rebuilt with a ray-miss fix | 6,208 | today's installed belt had a strap strip spiralling ~10 cm off the back (visible flap in game) |
| Golf trousers | `pants2 golf_male_trousers` + `tools/trousers_slim_v3.json` (PANTS_DESIGN leg rings); hem detection fixed in pants2 | 15,192 | belt + 5 loops, pressed crease, slant + back welt pockets, slim straight leg (~9 mm over the calf), hem 11.8 cm with a light break on the shoe |

Today's game bugs found and fixed along the way: the golf polo hem stopped 1.3 cm above the belt (a band of skin at the waist); the belt flap.

## Gates
| # | Gate | Result | Numbers / evidence |
|---|---|---|---|
| 1 | SHOE_TENNIS_CONSTRUCTION: every element of sheet 13 present, six views incl. sole | **PASS** | proof/unity/tennis_shoes_unity_vs13.jpg (Unity), proof/shoes/shoes_r4_vs_13_14.jpg (six views incl. sole, game maps) |
| 2 | SHOE_GOLF_CONSTRUCTION: every element of sheet 14 present, six views incl. sole | **PASS** | proof/unity/golf_shoes_unity_vs14.jpg, proof/shoes/shoes_r4_vs_13_14.jpg |
| 3 | SHOE_SILHOUETTE: silhouette difference (1 - IoU after scale/offset fit) <= 5 % per view (10-18 coordinator gate; was lateral IoU >= 0.75) | **FAIL** | **10-18 round 8/9 (current)**, lateral / medial / front / back / top / sole: tennis **13.3 / 15.1 / 21.6 / 29.3 / 21.7 / 17.4 %**, golf **13.4 / 18.9 / 17.7 / 23.0 / 19.8 / 19.9 %** (proof/shoes/silhouette_r8.jpg, Unity proof/shoes/unity_shoes_r8.jpg): shoes ~10 % longer than the foot needs to restore the sheets' side / top aspect (length test proof/shoes/length_test_tennis.jpg: 0.385 m reaches lateral 10.3 % but the feet read big vs the body; shoe / body height already 0.21 vs the sheet's 0.17). Round 6, lateral / medial / front / back / top / sole: tennis **18.5 / 20.2 / 24.8 / 32.5 / 27.1 / 22.8 %** (10-17: 18.7 / 20.6 / 18.7 / 21.3 / 24.2 / 20.3), golf **20.0 / 25.7 / 17.6 / 30.8 / 28.1 / 26.1 %** (10-17: 30.1 / 29.5 / 14.5 / 26.5 / 20.4 / 20.1). proof/shoes/silhouette_r6.jpg; best sheet-traced builds before the enclose step reached lateral 12.3 % (tennis) / 13.6 % (golf), proof/shoes/silhouette_pass_r3.jpg, but showed bare toes or see-through in game. ≤ 5 % is not reachable on this body: the foot is 0.30 m long, ~0.13 m tall at the instep and widest well above the sole (the sheet shoe's width/length is 0.37, the foot needs ≥ 0.48), and the 13 cm ankle sets the collar. 10-17: tennis 0.739, golf 0.587 (proof/shoes/lateral_iou_t_g.png). Cause: the hero's foot is 0.30 m long and 0.12 m tall at the instep, so the lace line must rise ~2–4 cm over it, and the 13 cm ankle needs a wider collar; golf collar also raised to meet the 11.8 cm trouser hem (golf kit has no socks) |
| 4 | DETAIL_TENNIS_POLO (sheet 09: collar tip, 2-button placket, cuffs, hem out) | **PASS** | proof/details/tennis_polo_vs09.jpg |
| 5 | DETAIL_GOLF_POLO (sheet 10: stand + underside, 3 buttons, cuffs, hem tucked) | **PASS** | proof/details/golf_polo_vs10.jpg, proof/unity/golf_unity_vs_03.jpg (belt over the hem) |
| 6 | DETAIL_BOTTOMS (sheet 11): shorts waistband / vents / hem; trousers belt + loops, crease, slim leg, hem break | **PASS** | shorts: proof/details/shorts_trousers_vs11.jpg. Trousers (rebuilt slim): belt loops, crease, back welts, hem break kept (proof/trousers/details_vs11_blender.jpg). Unity leg width / hip width at 37-61 % height 0.56/0.54/0.50/0.48 → **0.54/0.49/0.45/0.43** (sheet 11: 0.46/0.42/0.40/~0.37); side depth now ~constant below the knee like the sheet. Rest left = the fit floor (6.5 mm gap + 2.8 mm cloth) over the cartoon calf, which is wider vs the hip than the sheet's. proof/trousers/golf_unity_before_after_vs03.jpg (Unity, before/after), proof/trousers/trousers_before_after_vs11_blender.jpg |
| 7 | MASTER_TENNIS: Unity front/side/back/side vs sheet 01 | **PASS** | 10-18: proof/unity/tennis_unity_vs_01_r6.jpg; 10-17: proof/unity/tennis_unity_vs_01.jpg (+ 3/4 views in turn/refpack2) |
| 8 | MASTER_GOLF: Unity vs sheet 03 | **PASS** (10-18) | proof/unity/golf_unity_vs_03_r6.jpg: the root cause (tall golf shoe: instep-raised throat + tongue standing 4 cm over the sheet line) is fixed; trouser hem breaks over the shoe like the sheet, short golf socks (trouser colour) under the hem. The shoe stays chunkier than the sheet's (gate 3). Before: proof/unity/golf_feet_before_after_r3.jpg |
| 9 | MOTION: 0 skin / garment pixels through cloth in the 153-pose stress suite (serve, overhead, swing, run, emotes) | **FAIL** | **10-18 round 9 (current)**: tennis tears **164,623 px** = polo 139,343 (chat 5 K7_MT: compression-bulge correctives, 32 shapes), socks 14,713 + 8,540, shorts 2,027; layers **8,433** (shorts<polo, was 57,931); holes 22,140; shoes 0. Golf (round 8): tears **59,641** = trousers 35,015, polo 22,684, belt 932, shoes 35; layers 10,680; holes 79,621. Worst poses: ../clothing-v2/pipeline/runs/MG_MT/suite/MatchHero_Male/sheet_worst12.jpg. **10-18 round 6** (pipeline of 10-18 ~06:00; numbers are not comparable 1:1 with 10-17, chat 5 changed the suite + correctives): tennis tears **219,600 px** = polo 167,342 (chat 5's current fit K5c_MT: chest in Thrust / Push-ups + shoulder blades; 10-17 polo 183,048), left sock 31,938 (front of the ankle when the foot points), shorts 14,513, shoes 2,880 + 2,854; layers 57,931 (shorts<polo); holes 46,136. Golf tears **63,802 px** = trousers 35,020, polo 22,698, shoes 2,373 + 1,478; layers 14,783; holes 110,955. 10-17: tennis: tears 342,039 → 214,205 px (183,048 = the polo; Serve 11.1k, Overhead 2.5k, RunForward 135); golf: 271,672 → **60,606 px** with the slim trousers (body<Kit_Bottom 49,861 → **36,006**; Drive 4.3k, IronSwing 5.7k, Chip 1.8k; layers 13,509 → 13,606, Kit_Bottom<Kit_Belt 10,214 → 10,532). proof/trousers/stress_worst12_slim.jpg. Shoes/socks/belt: small (sock/shoe layer clashes 1.9k + 3.2k px tennis). Unity film: proof/motion/*.jpg |
| 10 | COLOURS: light / dark / saturated picks render correctly through the game's SetKit + trim rules | **PASS** | proof/unity/colour_swatches_unity.jpg |
| 11 | PERF: garment driver <= 0.3 ms per hero; 1080p frame with both heroes under 16.7 ms | **PASS (Editor estimate)** | 10-18 round 9: driver 0.14 ms tennis (95 corrective shapes) / 0.23 ms golf, 1080p 4.2–6.2 ms per hero, measured while 2 other Unity jobs ran (perf/mg_1018_*_perf.json). 10-18 round 6: driver 0.098 ms (tennis) / 0.114 ms (golf), 1080p 1.9–3.2 ms per hero (perf/mg_1018_0646_perf.json, last install of the same pieces). 10-17: driver 0.13 ms (tennis) / 0.10 ms (golf); 1920x1080 render 4.0–6.9 ms tennis, 4.3–4.7 ms golf per hero (Editor batch, `GarmentPipelinePerf`); device run NOT done |
| 12 | LOBBY_PARITY (SceneKit renders match Unity, same cameras) | **PASS** | Rounds 8/9 (longer shoes, K7 polo) NOT re-synced by me: the integration chat's second pass runs sync_heroes.sh after the r9 prefab patch. 10-18 round 6 (private re-sync from the clone, lobby/sheets/): tennis male 24 shots luminance ratio 0.960–0.989, mean abs diff 4.9–9.2/255; golf male 4 shots 0.923–0.960 / 6.5–8.9 (lobby/sheets/golf_male.png, tennis_male.png); 10-17 sheets in lobby/sheets_1017. 10-17: LOBBY.md: tennis male luminance ratio 0.960–0.982, mean abs diff 4.7–8.2/255 over 20 shots; golf male 0.920–0.963 / 6.4–9.1 (lobby/sheets/*_male.png). Installed into a private copy of CharacterAssets only; the real install is the integration chat's sync run |
| 13 | IDENTITY + STAGING: body / face / rig / clips untouched; own files only, staged by explicit path, no commits | **PASS** | 10-18 round 9: 46 owned files re-staged (87 owned paths in total, patches/installed_files.txt); shoe4.py re-staged; round-9 prefab update `patches/male_prefabs_r9_p0.patch` APPLIED 10-18 18:22 at Adnan's OK (unstaged; backup patches/backup_prefabs_1018_1822; prefabs == clone; bone check 0 BAD). 10-18: 56 more owned files staged (87 paths in total, patches/installed_files.txt; new: golf Kit_Sock_L/R + maps/hide/correctives), shoe4.py + sock2.py re-staged (my hunks only). The male prefab patch of 10-17 was APPLIED to the working tree at Adnan's OK (unstaged, backup + revert in patches/INSTALL.md); the round-6 prefab update `patches/male_prefabs_r6_p0.patch` was APPLIED 10-18 11:09 at Adnan's OK (unstaged; backup patches/backup_prefabs_1018_1109; bone check 0 BAD). 10-17 staged: 65 garment files under `Unity/.../KitsV2/{MatchHero_Male,GolfKitHero_Male}` and `Resources/{Tennis,Golf}/KitsV2/Male` (patches/installed_files.txt), my builder hunks (shoe4.py new; belt2, pants2, polo2_export, sock2; my hunks of maps.py + polo2.py only), this folder's docs/tools/proof. No body, face, rig, clip or prefab file staged; shared prefabs + MatchHeroLook go as patches (patches/INSTALL.md). No commits |

## Notes
- The shoes on the hero (`proof/unity/shoes_unity_vs_13_14.jpg`) and with the colour picks (`proof/unity/colour_swatches_unity.jpg`) are the best
  view of where this stands. Per clip and per garment numbers: `tools/suite_by_clip.py ../clothing-v2/pipeline/runs/MG_MT/suite/MatchHero_Male`.
- `HOLES` in the pipeline report (tennis 358k, golf 1.08M px) count hidden skin "seen" where the shoe's own lining or the trouser's inside wall is
  drawn (foot hidden inside the shoe on purpose, `GP_FOOT_ALL=1`); no see-through was found in the Unity low / feet views.
- The film tool plays raw clips without the game's grip driver, so the racket floats in `proof/motion/*.jpg`; unrelated to the garments.
- Builders depend on chat 5's unstaged edits in `shoe2.py`, `polo2.py` (POLO_DESIGN), `export2.py` and the untracked `pipeline/` (gp/*): stage
  those with chat 5's work.

## 10-18 round 6 (what changed and why)
- **Silhouette pass (round 3):** shoe4 outline tables re-traced from sheets 13/14 (`SILHOUETTE` dict: collar, top line, sole, tongue, bow,
  heel lean; `instep=False` keeps the sheet's low throat). Lateral reached 12.3 % / 13.6 %, but on this foot it only works if the foot is hidden.
- **Why it could not stay:** the cartoon forefoot is taller and wider than a sheet-proportioned upper. Without hiding: bare toes drawn over the
  upper (turn/r3c_refpack). Hiding all foot skin (GP_FOOT_ALL=1): chat 5's split of the HOLES metric showed real see-through (K5d_MT: background
  333,153 + lining 107,637 px) at low / side views. So the shoe has to contain the foot.
- **enclose (shoe4):** upper top >= foot top + 10 mm from just behind the throat to the toe tip; each section widened (superellipse test, as for
  the sock) until every foot point at that station is inside + 10 mm (the rigid shoe and the blended foot skin drift a few mm off the bind pose).
  Unity: no skin through the shoes in rest / ready (proof/shoes/unity_shoes_r6.jpg); left: a speck of ankle skin at the tongue / collar
  junction in the front view (few px at game distance).
- **Golf socks:** crew socks (top .288) poked through the slim trousers (205k layer px) -> new `sock2` design `male_golf` (top .170, just over
  the hem), role Kit_Shorts so it follows the trouser colour. New prefab pieces on PlayerMaleGolfKit (prefab patch).
- **Tennis polo:** garment-pipeline (chat 5) refit it with its current rules (limb-root remap, 2 mm seam weld, capped correctives; hem-over-
  waistband rule tried and switched off, it shoved the shorts): polo tears 183k -> 167k px; the arms-up / chest tears remain (gate 9).
- Pipeline bugs found on the way and fixed by chat 5: a NEW piece (not in the dump) crashed the coverage step (cov_cli); the 3 cm hole clause.
- Runs: pipeline runs/MG_MT, runs/MG_GM (no GP_FOOT_ALL); scripts tools/round3.sh … round6.sh, golf_socks_r3b/r3c.sh.

## 10-18 rounds 7–9
- Round 7: shoes lengthened (tennis Ls .365, golf .375) + room 7 mm + GP_SHOE_SKINW=1 (chat 5: footwear skinned with the foot's own weights)
  -> silhouette better, but medial forefoot skin spots came back. Round 8: room back to 10 mm, length + skin weights kept -> clean (one 1-2 px
  golf speck), shoe tears ~0. Round 9: chat 5's K7_MT polo + shorts fit copied into MG_MT (resume, cover + suite re-run), tennis re-installed.
- tools: round7.sh, round8.sh, tennis_polo.sh <chat-5 run> <tag>; render_npz.py has a phys-footprint memory cap (GP_MEM_GB, resume=1).

## What would close the FAILs
- Shoe silhouette: only a smaller / lower body foot (identity-locked, Adnan's call) lets a sheet-proportioned shoe contain it. Golf socks: done.
- Trousers: done (gate 6 PASS).
- Tears: the tennis polo chest / shoulder-blade tears (167k px) need a polo pass in garment-pipeline (chat 5); the left-sock ankle front (32k)
  may need a sock with more ankle room or chat 5's 2 cm tight-knit smoothing on the next fit.

## Tools (work/male-garments-refpack/tools)
`run_shoe4.sh` build+export+maps (private CV2_OUT, refuses otherwise) · `render_npz.py` Blender proofs from the exported data · `compose_*.py`
sheet comparisons · `onbody.sh` garments on the dumped body · `trim_sock.py` · `fit_gm.sh` / `round2.sh` pipeline fits · `install_batch.sh` +
`unity_chain*.sh` Unity in the clone · `lobby_sync.sh` private lobby parity · `install_to_repo.sh` owned files into Unity/ + staging.

## Golf trousers slim (10-17, follow-up chat)
- **Why the slim build crashed:** `pants2.leg_axis_fn` oriented every leg face against ONE fixed axis (leg ring 1, x .127), but the trouser leg
  drifts out to x .16-.19 at the hem; with slimmer rings the inner-front faces near the hem fell on the wrong side and were flipped, the hem's
  boundary edges disagreed in direction and the directed loop walk shattered one hem into 4-vertex pieces (14 loops). Fix: per-height leg axis
  (interpolated ring centres) + a clear error if the shell ever has != 3 boundary loops. The three existing designs flip exactly the same faces as
  before (checked), so their output is unchanged.
- **Design** (`tools/trousers_slim_v3.json`, via PANTS_DESIGN): rings defined as straight outer / inner / front / back lines (sheet 11 legs are
  columns) at body + ~9-12 mm; centres follow the body (calf sits behind the shin, so the old rings were pushed into a bulge at the back).
  Build/export/maps: `tools/run_trousers.sh <json>` (private CV2_OUT only). Proof: `tools/trousers_proof.sh`, `tools/trouser_profile.py`.
- **Fit:** `tools/fit_gm_trousers.sh` (MG_GM, resume, only Kit_Bottom refitted) with **GP_MAX_LIFT=.035** for the trousers. Why: the hip just
  under the belt needs > 2.5 cm of corrective lift in hip-flexed swings in every version (old included: the shapes sit at the 25 mm cap), and
  the 16 k-means corrective shapes are chosen over the whole garment, so ANY leg change re-clusters the swing poses and moves ~2-3k px of
  hip tear in or out (v3 at the default cap 52,201, v4 53,466, unchanged trousers through the same npz path 50,250). With the cap at 3.5 cm the
  hip is covered: 36,006 px, no visible bulge in the worst poses (proof/trousers/stress_worst12_slim.jpg; cause: proof/trousers/hip_tear_cause_old_v3_v3chip.jpg, tools/tear_shots.py).
- **Installed:** clone `~/male-garments-UnityClone` (install_batch, turnaround `turn/slim`), repo: 9 owned golf files re-staged
  (patches/installed_files.txt), `patches/male_prefabs.patch` regenerated (golf prefab: Kit_Bottom renderer now 9 bones; tennis part identical;
  `git apply --check -p0` passes). Perf: driver 0.085 ms, 1080p 5.0 ms (perf/mg_1017_2329_perf.json).
- **Rollback:** previous MG_GM trouser fit + report in build/MG_GM_before_slim/, previous patch build/male_prefabs_before_slim.patch.
- **Not done:** lobby (SceneKit) re-export of the golf male for the slim trousers: run `tools/lobby_sync.sh` / `sync_heroes.sh` after the prefab patch.

