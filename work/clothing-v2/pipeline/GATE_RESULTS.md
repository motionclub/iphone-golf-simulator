# Garment pipeline — GATE_RESULTS (chat 5, 2026-10-17) — status 23:00: FAIL on TEARS/LAYERS (improved), see the gate table

Brief: `work/delegation-2026-10-17/05_garments_survive_animation_pipeline.md` (+ "Added 10-17: match the reference images").
Method + commands: `work/clothing-v2/GARMENT_PIPELINE.md`. Nothing committed. Garments installed only into the clone `~/garments-UnityClone`; the pipeline's runtime/editor scripts are staged (inert until a `[gp]` garment is installed).

## Test suite (built, verified)
- Dump: `unity/GarmentPipelineDump.cs`, 4 heroes, every clip at 30 fps (tennis 43 / golf 26 clips incl. plaza + emote moves). Offline rebuild == Unity BakeMesh, max error 0.0008 mm (all parts, all heroes).
- Stress library: 153 poses per hero (`stress/<Hero>/poses.json`), worst frames per region + coverage, from 2,474 (tennis) / 1,776 (golf) frames.
- Detector: 24 orthographic GPU id views per pose; TEAR / LAYER / HOLES as defined in `gp/evaluate.py`; noise filter = 3×3 opening; pixel = 3.1 mm.

## BEFORE (today's installed garments, stress library, coverage v2 = rays + inside the outer wall)
| Hero | TEAR px (poses /153) | LAYER px (poses) | HOLES px (poses) |
|---|---|---|---|
| MatchHero_Male | 342,039 (103) | 52,961 (104) shorts through the polo hem | 246,986 (153) into the shoe throat |
| MatchHero_Female | 352,507 (152) shoulder blades / back through the tank | 13 (1) | 69,794 (147) |
| GolfKitHero_Male | 271,672 (124) | 20,400 (122) trousers through the polo | 336,965 (153) |
| GolfKitHero_Female | 225,768 (153) | 151 kit (+15,660 on the accessory glove, not a kit piece) | 463,401 (153) under the lifting polo hem |

## Method A/B (male tennis polo, the 40 worst BEFORE poses, same cover)
| Variant | TEAR px | LAYER px | verdict |
|---|---|---|---|
| BEFORE (today) | 323,028 | 18,928 | |
| E3 today's garments + new cover only | 337,134 | 18,953 | cover alone does not fix tears (it fixes HOLES: 564 px) |
| E1 today's weights + correctives | 252,482 | 19,217 | correctives help a little |
| E0 new weights (4 cm smoothing), no correctives | 126,911 | 51,627 | weights are the big lever |
| **E2 new weights + correctives** | **83,772** | 35,829 | best tears (−74 %), layers worse |
| E4 new weights 6 cm smoothing + correctives | 145,625 | 33,057 | too smooth: cloth leaves the body |
| E5 E2 + garment obstacles to 6 cm depth | 87,313 | 32,027 | ≈ E2 |
| E6 E2 + shorts bound to the polo (inner follows outer) | 107,859 | 38,147 | REJECTED: waistband crumples when the hem rises |
| E7 E2 + adaptive 10 cm transition smoothing | 262,144 | 42,480 | REJECTED: sleeve motion leaks into the chest |

Rules learned (all general, none per garment): shoes are rigid (footwear weights, no correctives: lifts round the sock shredded the collar);
corrective lifts are capped at 2.5 cm and each shape is ONE real pose field (per-vertex max over poses shredded the cloth); skin deep under a
garment needs no clearance (the cover hides it) and is only "seen" when it is outside its garment's silhouette (seen through a rip ≠ seen).

## Full-library runs (153 poses)
| Run | What | TEAR px (poses) | LAYER px (poses) | verdict |
|---|---|---|---|---|
| BEFORE | today's male tennis kit | 342,039 (103) | 52,961 (104) | |
| E8-uncapped (17:12) | new weights + hem riding + rigid shoes, but corrective fields from stale checkpoints (solved before the 2.5 cm cap, key did not change): lifts up to 60 mm | 284,398 (153) | 63,047 (86) | INVALID: shredded chest in Thrust/Pushups; arms/axilla/side seams −70–80 %, kneel/knee/seat worse (shoe heel + sole through the shoe, shorts through the polo hem) |

| E8 capped (17:23) | same, capped lifts (cover still from the stale run) | 224,534 (147) | 21,537 (55) | layers fixed; tears: 198k through the polo |
| F capped (17:28) | female rebuilt tennis top (sheet 09) | 374,340 (152) — BEFORE 352,507 | 7,946 (96) | WORSE: armhole bindings followed the upper arm (panel allowed groups = nearest skin, not covered skin) |
| K_MT (17:59) | male tennis full kit: polo + shorts refit, sheet-13 shoes, footwear cover, leg groups fixed | 198,228 (139) | 73,304 (54) | shoes fixed (14 px); polo still splits at its seams |

| K2_MT (18:23) | male tennis: + seam weld, leg groups fixed, coverage-limited panels | 186,095 (136) — **−46 %** | 63,171 (51) | polo chest in Thrust/Pushups + armpits overhead; shorts through the polo hem when kneeling (Defeat) |
| K2_GM (18:53) | golf male: polo + trousers refit, sheet-14 shoes | 68,252 — BEFORE 271,672, **−75 %** | 21,862 (123) — BEFORE 20,400 | |
| K2_FT (18:37) | female: rebuilt sheet-09 top + skirt refit, no limb-wrap rule | 468,857 (152) | 12,343 (79) | WORSE than BEFORE (352,507): arms under the straps |
| K2_FT_b (19:26) | same + limb-wrap rule (arms not followed by the sleeveless top) | 444,898 (152) | 12,720 (84) | still worse; elbow/overhead poses: arm skin under the strap edges pokes through. A/B with today's tank mesh through the pipeline (K2_FD) queued |

| K2_FT_c (20:02) | female tennis, limb-filtered metric + cover | 431,935 (152) | 12,720 (84) | the sheet-09 top still carries 8–9 % upper-arm weight (barycentric copy of torso faces near the armpit), so the filter keeps its arm cover; WORSE than today |
| K2_GF (19:58) | golf female: polo + skort refit | 877,924 (153) — BEFORE 225,768 | 19,367 (142) | WORSE: the new short sleeves follow the arm 94–100 % (today 50–76 %), raised arms stretch the side panels into webs; + 123k px on the accessory glove (not a kit piece) |

Status 20:10: the pipeline WINS on the male heroes (tennis −46 % tears, golf −75 %) and LOSES on both female heroes. Female garments stay on
today's weights (nothing female installed outside the clone). The male garments + shoes now continue in the male-garments chat
(local_982d9e7a…, shoe4.py, its own fit runs MG_* through this pipeline).

**Metric fix 19:40 (applies to every number from here on, BEFORE re-measured the same way in runs/before_v3):** a garment covers limb skin
only where it follows that limb (`evaluate.limb_filter`). The arm under a sleeveless armhole rim at rest is not covered by the top: when
the arm moves in front of the side panel it was counted as a TEAR (false positive, most of the female numbers above) and hidden by the cover.

Shoes in engine (proof/refmatch/11): rigid fit holds (shoe tears 14 px of 186k), but the look is not at sheet 13/14 yet; male shoe/garment DESIGN moved to the male-garments chat (shoe4.py) 10-17 19:15, this chat keeps the pipeline + fits.
PERF (clone, 1080p, 300 frames): driver 0.067 ms (male tennis, 32 shapes) / 0.081 ms (golf male) — **PASS ≤ 0.3 ms**; 1080p render with correctives live vs zero within noise (4.9 vs 5.9 ms, 5.6 vs 5.3 ms).

Root causes found 10-17 evening (all general, all fixed in code, K2_* runs pending):
- **Seams split**: vertices that coincide at rest (sewn panel edges / UV splits) got different weights; posed they separated up to 118 mm
  (Thrust), 64 mm (Serve). Today's installed polo already splits 73 mm in Thrust. Fix: coincident vertices (0.75 mm) share weights and
  corrective deltas exactly (`weights.weld_labels` / `group_mean`) -> seams stay within 1 mm in every pose.
- **Leg bones were in the arm groups**: `bone_group`'s hand rule matched every `Left*` / `Right*` bone, so legs/feet/toes counted as arms
  (panel restrictions + obstacle groups were wrong for every garment). Fixed (`LeftHand*` only).
- **Panels may only follow groups the garment covers** (bind-pose GPU coverage): a sleeveless armhole binding beside the arm no longer
  follows the arm.

Fixes from E8-uncapped (general): checkpointed fields are capped on load (the cap is the solver's last step, idempotent); the cover hides skin under
footwear deeper than 2.5 cm from uncovered skin (`cover.foot_deep`: a rigid shoe never shows the foot legitimately); the report now attributes
every through pixel to `victim<coverer`.

## Same metric for all (limb-filtered, 20:20) — BEFORE re-measured (runs/before_v3) vs the pipeline's K2 runs
| Hero | TEAR px BEFORE → K2 | LAYER px BEFORE → K2 | HOLES px BEFORE → K2 | verdict |
|---|---|---|---|---|
| MatchHero_Male | 341,530 → **186,095** (−46 %) | 52,961 → 63,171 (+19 %) | 246,986 → **32,957** (−87 %) | better; layers (shorts through the polo hem when kneeling) worse |
| GolfKitHero_Male | 271,621 → **68,252** (−75 %) | 20,400 → 21,862 (+7 %) | 336,965 → **77,140** (−77 %) | better |
| MatchHero_Female | 230,302 → 431,935 (+88 %) | 13 → 12,720 | 69,794 → **10,682** (−85 %) | WORSE tears (rebuilt sheet-09 top: arm skin under the straps) |
| GolfKitHero_Female | 206,050 → 877,924 (+326 %) | 15,811 → 19,367 | 463,401 → **63,589** (−86 %) | WORSE tears (short sleeves follow the arm fully -> side-panel webs) |
| MatchHero_Female **K3_FT** (21:40) | rebuilt sheet-09 top + **limb-root remap** (arm weight under the straps -> shoulder) + skirt refit | 183,080 (−20 %) | 14,132 | 9,392 | top fixed (368k -> 120k); refit skirt worse than today's (63k vs 5k) |
| MatchHero_Female **K3b_FT** (22:28) | K3_FT top + **today's skirt weights** (`keep=Kit_Bottom`) + pipeline correctives/cover | **126,415 (−45 %)** | 2,956 | **9,410 (−87 %)** | BEST female tennis |
| MatchHero_Female K2_FD (22:10) | TODAY's tank mesh through the pipeline | 472,687 | 10,934 | 9,831 | the rebuilt sheet-09 top is the better garment |
| GolfKitHero_Female K3_GF (22:50) | today's top/skort/belt weights kept + pipeline correctives/cover | 1,216,591 | 25,275 | 60,410 | WORSE: today's tube sleeves stay at the shoulder when the arm rises (today's cover hid that skin: BEFORE 463k HOLES); with sleeves following (K2_GF) the side panels web. Needs a GARMENT fix (sleeve ease / gusset), not weights |
HOLES (skin hidden by today's cover but seen) drop 77–87 % on every hero: the new cover is right everywhere; the tear gate is where females fail.

## Round 2 (10-18 00:00–) female tennis rips (Adnan on proof 13: fit OK, clean up the rips)
Rip classes found in the 1080p film + stress suite, and the general fix for each:
| Class | Where | Fix (general) |
|---|---|---|
| strap/armhole cloth shredding toward the arm | armholes, arms forward | limb-root remap only NEAR the limb's own skin (3→6 cm fade), keep real skin weights farther in |
| skin through the back at the shoulder blades | back, arms forward/back | same (full remap had moved the blade cloth to the clavicle) |
| frayed armhole binding | armhole edge | seam weld radius 0.75 → 2 mm (binding rings sit ~1.5 mm off the shell) |
| crushed / stretched rib hem band | hem, all poses | correctives: lift fades with depth instead of a hard 3 cm cutoff + 6 smoothing passes per pose (hem band stretch 103k → see K6) |
| arm passing in front of a sleeveless top counted as a tear | armholes | metric/cover: a garment covers limb skin only if it WRAPS that limb (`evaluate.limb_filter`) |
| compression folds of the back panel (Thrust) | back, arms forward | OPEN: own-skin deep clearing + 3.5 cm cap (K7) made it worse; reverted |

| Run | Change | TEAR | LAYER | HOLES |
|---|---|---|---|---|
| K3b_FT (10-17) | baseline of this round | 126,415 | 2,956 | 9,410 |
| K4_FT | no limb-root remap, 2 mm weld, wrap filter | 135,934 | 2,011 | 9,392 |
| K4r_FT | partial (near-limb) remap, 2 mm weld, wrap filter | 115,714 | 1,601 | 9,453 |
| **K6_FT** | K4r + corrective depth fade + lift smoothing | **91,830 (−27 %)** | **939** | 9,387 |
| K6 oracle | each stress pose gets its OWN solved field (no compression) | 75,601 | 412 | |
| K7_FT | K6 + own-skin deep clearing + 3.5 cm cap | 130,573 | 5,201 | 9,518 (reverted) |
| K6 + rest-poke cover | hide covered skin outside the outer wall at rest | 94,751 | 942 | 238,579 | REVERTED: hid visible shoulder skin beside the armholes (holes) |
| **K6_FT final (03:12)** | K6, cover without rest-poke, maps re-baked with the cover (AO smudge) | **91,830** | **939** | **9,827** | INSTALLED in the clone; 1080p rip film: no visible rips in Serve/Forehand/Backhand/Victory/Slump × front/side/back/¾; faint shoulder-blade dimples + slightly ragged armhole edge left |
**Female tennis rip gate:** visible rips in the 1080p captures: FIXED (back hole, crumpled hem, frayed armhole, armhole notch; proof/refmatch/14).
TEARS −27 % (126k -> 92k) vs the asked −50 %: NOT MET; the rest is back-panel compression folds in extreme emotes (Thrust).
Compression (16 shapes) costs ~17k px (oracle); 32/64 shapes or localized bases tested offline: 32 shapes 29 % short, 64 15 % (per-pose
fields are pose-specific). The remaining ~75k needs a different mechanism than lift-only correctives (compression folds).

## Round 2: male tennis polo for the male-garments chat (their shorts/socks/shoes, dump polo)
| Run | Change | TEAR | LAYER | HOLES | verdict |
|---|---|---|---|---|---|
| MG_MT (male chat, 10-17) | pipeline as of 10-17 | 214,205 | 36,861 | | |
| K5_MT | + hem-over-waistband push-in rule, GP_FOOT_ALL=1 | 215,557 | 485,176 | 747,985 | REJECTED: "inside the polo" is ill-defined at an open hem rim once the hem lifts; the shorts got shoved -> rule OFF by default |
| K5b_MT | rule off, height-map footwear rule | 349,126 | 58,255 | 83,514 | socks: skin through the left ankle (125k) |
| K5b_MT + GP_FOOT_ALL=1 | hide all foot skin in the shoe footprint | 349,328 | 58,294 | 631,794 (background 337,802 / lining 109,702 / outer 184,290) | REAL see-through: the low refpack upper does not enclose the cartoon forefoot |
| **K5c_MT** | socks re-fitted with 2 cm weight smoothing (now automatic for tight knits) | **224,702** | 59,647 | 54,224 (bg 13,948 / lining 9,929 / outer 30,347) | handed to the male-garments chat to install |
| K5d_MT | K5c + GP_FOOT_ALL=1 | 224,897 | 59,647 | 613,057 (bg 333,153) | not used |
New rules from this: tight knits (median outer gap < 5 mm) get 2 cm weight smoothing; HOLES are reported split into background / lining /
outer surface > 3 cm behind (the last one can be a solid low shoe upper).
Footwear cover rule (10-18): "inside a shoe" = the shoe has a surface directly above the skin (5 mm height map), replacing the 75 %-height
box (it hid visible ankle skin above low collars). Brand-new pieces (not in the dump) now join the worn set in coverage/cover/suite/offsets.
Offsets manifest fixed: hands/fingers never get a garment offset (0.6 m before), limbs a piece does not wrap are skipped, feet use the shoe test.

## Round 2: golf female sleeve
| Run | Change | TEAR | LAYER | HOLES | verdict |
|---|---|---|---|---|---|
| BEFORE (today) | | 206,050 | 15,811 | 463,401 | arm skin hidden under sleeves that stay down -> holes |
| K2_GF | sleeves follow the arm 94–100 % | 877,924 | 19,367 | 63,589 | webs at the side seams |
| G1_GF | extended shoulder via design data (armhole cut 2.5 cm out / 2.4 cm down, fuller sleeve) | 543,920 | 12,910 | 136,159 | tears+holes ≈ today; the cut reached under the armpit: the builder lofted 15 cm sliver edges = spikes |
| G2 builds | two more armhole cuts | – | – | – | builder (polo2 lofted sleeves) picks a wrong loop: edges up to 2.2 m. A real raglan needs builder CODE (polo2.py is shared with the male-garments chat) |
| G3_GF | today's top mesh, 8 cm sleeve->torso weight transition | 961,651 | 16,590 | 63,915 | worse: the wide transition drags the side panels with the arm |
**Golf female verdict: FAIL.** No weight rule beats today's install (206k); the extended shoulder by design data alone is the closest
(G1, tears+holes ≈ today) but the polo2 lofted-sleeve builder makes sliver spikes when its armhole cut moves. Next step needs builder CODE:
a raglan / dropped-shoulder sleeve generated as its own panel from the neckline to the underarm (polo2.py, shared with the male-garments
chat) - then the same pipeline fit. Today's golf-female garments stay installed unchanged.

## Round 3 (10-18 day): compression folds (female tennis, same pieces as K6)
| Run | Change | TEAR | LAYER | HOLES |
|---|---|---|---|---|
| K6_FT | baseline | 91,830 | 939 | 9,827 |
| K8_FT | + compression bulge k = 0.03 m (squeezed cloth pushed out along its normal by k x area loss) | 85,257 | 837 | 9,444 |
| K9_FT | own-skin deep clearing (6 cm) at the 2.5 cm cap | 117,657 | 5,259 | 9,454 (rejected again) |
| **K10_FT** | bulge k = 0.06 m | **62,685** (−50 % vs K3b, −73 % vs today's install 230,302) | 1,583 | 9,495 |
| K11_FT | bulge 0.03 + 32 shapes | 78,850 | 614 | 9,459 |
| **K12_FT** | bulge 0.06 + 32 shapes | **60,667** (−52 % vs K3b, −74 % vs install) | 1,583 | 9,444 (bg 7,428 / lining 1,694 / outer 322) | INSTALLED in the clone (batch_1018_1531), 1080p film: no puffiness (proof/18); driver 0.148 ms with 64 shapes (top 32 + skirt 32) |
| **male K7_MT** | K6_MT with the bulge only on outer garments (shorts refit) | polo 139,343, total 144,109 (K5c 224,702) | 8,530 (K5c 59,647) | 48,321 | handed to male-garments; polo target < 100k not met yet (K8_MT bulge 0.10 running) |
| male K6_MT | male polo, bulge 0.06 + 32 shapes, male-garments round-6 pieces | polo 139,414 (K5c 167,342) | 431,164 shorts<polo | 47,545 | the bulge also pushed the SHORTS through the polo hem -> bulge now only for garments with nothing over them; K7_MT rerun |

**Memory (10-18 16:00):** cover/suite in background Blender never release per-draw GPU work (~200 MB per cover frame: 21 GB per 100
frames, two parallel covers hit ~45 GB each and the out-of-memory pop-up). `render.footprint_gb()` (libproc phys_footprint, GPU included)
now ends a cover/suite chunk at GP_MEM_GB (default 4 GB); measured peak with a 3 GB cap: 2.76 GB.

## Round 3 (10-18 day): raglan sleeve in the polo2 builder (golf female)
- `polo2.py` design key `raglan: {under: [x, z], neck: [x, z], round}`: a straight diagonal seam (same plane front and back) from the underarm
  to just outside the collar replaces the ellipsoid armhole cut; the existing lofted sleeve grows from that long loop, so the sleeve panel
  owns the whole shoulder top. The seam must stop ~4 cm short of the neck opening (a cut reaching it merged armholes + neck into one loop).
- Builder sanity pass at the end of every polo2 build: outlier vertices (> 3 cm from their neighbours' mean) pulled back, faces with an
  edge > 20 cm deleted. The CURRENT golf_female build had 40–50 cm spike strips even without the raglan (the installed top predates them).
- Build `{"raglan":{"under":[0.135,1.225],"neck":[0.115,1.37]}}`: clean (max edge 54 mm), raglan seams front + back; some crumple at the
  underarm.
| Run | TEAR | LAYER | HOLES | verdict |
|---|---|---|---|---|
| R1_GF raglan | 585,522 | 13,031 | 55,244 | NO webs on the arm raise (proof/17); arm skin shows through the tight short sleeve |
| R2_GF raglan + sleeve ease (r .062/.056) + bulge .03 | 768,075 | 13,341 | 55,268 | worse |
| R3_GF raglan + sleeve ease, no bulge | 431,127 | 13,243 | 55,222 | better than R1/R2, still > today (206k) |
| R4_GF raglan, more ease (.070/.062) + lower underarm (gusset room) | 427,327 | 12,736 | 55,209 | best raglan; ease saturates (R3 431k) |
**Golf female verdict (10-18 evening): webs FIXED by the raglan (proof/17); TEARS still FAIL** (427k vs today's 206k). Counting all
see-through defects (tears + hidden-skin holes) R4 is 482k vs today's 669k (206k + 463k holes): −28 %. The remaining tears are arm skin
inside the short sleeve when the arm is raised; the compression bulge hurts sleeves (R2). Next idea, not done: sleeve weights that follow
the arm fully only past the deltoid, plus a corrective driven by arm elevation.

**Limb tube weight rule (10-18 20:00, `weights.py` GP_LIMB_TUBE).** Diagnosis on R4 worst poses: the short sleeve's underside copies the
torso skin it faces in the A-pose, so the raised arm passes through it and the sleeve splits into strips. Quick evals (`quick_eval`,
R4's cover, R4's 40 worst poses = 216,052 px):
| Run | Rule | TEAR (40 poses) | verdict |
|---|---|---|---|
| T1_GF | cloth within 13 cm of the upper-arm axis follows the arm (5.5k vertices per arm) | 313,279, holes 347k | REJECTED: the tube took the chest/back panels beside the armpit, torso cloth swung with the arms |
| T2_GF | tube = the arm's own skin radius (p95 per 10 % of its length) + 3.5 cm, and only cloth nearer the arm than the torso (1.2k vertices per arm) | 194,225 (−10 %), holes unchanged | kept (default on); not enough alone: ~385k projected on 153 poses vs the 206k gate |
| male T2_MT | same rule on the male polo (K8 base, 130,829 on its 40 worst) | 133,155 | neutral for the male (its sleeve panels already follow the arm) |

Worst poses of both heroes have 440–3,300 cloth vertices AT the 2.5 cm corrective lift cap (male Shock/Pushups, golf Shock/FistPump/HalfSwing):
the cap is the limiter there. Next: T3_MT (cap 4 cm alone, male) and T3_GF (tube + cap 4 cm, golf female).
| male T3_MT | lift cap 4 cm (tube off) | 131,235 (K8 130,829) | no gain |
| male T3_MT ORACLE | each pose's own solved field, no compression | 132,658 | **the correctives are not the limit** |

**Root cause found (20:45):** the solver skips covered skin > 3 cm from any uncovered skin ("deep", assumed hidden by the cover), but the
cover keeps skin DRAWN wherever some frame shows it legitimately: 3,673 of the male polo's 7,462 'deep' vertices are drawn in K8's cover,
and nothing ever clears them. New `GP_COVER_REF=<earlier run body.npz>` (`fit.deep_covered`): drawn skin is cleared like any other.
Quick evals (40 worst poses of the base run):
| Run | Change | TEAR (40 poses) | vs base |
|---|---|---|---|
| T3_GF | tube + lift cap 4 cm | 214,038 | cap rejected (tube alone 194,225) |
| **T4_GF** | tube + GP_COVER_REF (R4 cover: 1,455 of 2,469 deep vertices drawn) | **146,431** | −32 % vs R4 216,052 |
| **T4_MT** | GP_COVER_REF (K8 cover) | **68,299** | −48 % vs K8 130,829 |
Full 153-pose candidates (quick_eval N=153: new fit, the base run's cover = what installs with it): T5_GF (tube + cover ref + 32 shapes,
R4 cover) and T5_MT (cover ref + bulge .10 + 32 shapes on MG_MT = male-garments' round-8 shoes/socks + K8 shorts + its cover).

## STOPPED 2026-10-18 21:10 (Adnan: "stop the shirt tearing stuff for now")
T5_GF and T5_MT were cancelled mid-fit (all jobs, waiters and parent shells killed; heavy.sh shows no chat-5 job). Nothing new went to
integration or male-garments. **The final build ships today's golf female top (206,050 tears) and the K8 polo (male-garments' round-9
copy) + the female tennis K12_FT already handed off** (`handoff/README.md`). Later plan (Adnan, not now): adjust the emotes to fit the
clothes instead of the cloth chasing extreme emote poses.

### State to resume from
- **Root cause of the tears no corrective could fix:** the corrective solver treats covered skin > 3 cm from any uncovered skin as "deep"
  (hidden by the cover, no clearance), but the cover keeps skin DRAWN wherever some frame legitimately shows it. Male K8: 3,673 of 7,462
  'deep' vertices drawn; golf female R4: 1,455 of 2,469. Proof: male oracle (each pose's own field, no compression) 132,658 = compressed
  131,235, and a 4 cm lift cap changed nothing. Fix: `GP_COVER_REF=<earlier run>/<Hero>/body.npz` in `gp/fit.py deep_covered` (drawn skin
  is cleared like any other skin). It is opt-in; the cover of the run it points to must be the one installed with the result (or re-run the
  cover afterwards).
- Quick-eval numbers (40 worst poses of the base run): male T4_MT **68,299 vs K8 130,829 (−48 %)**, projected ~74k on 153 poses (< 100k
  target); golf female T4_GF **146,431 vs R4 216,052 (−32 %)**, projected ~289k (gate 206k: still FAIL, needs more).
- Limb tube rule (`GP_LIMB_TUBE`, default ON in `gp/weights.py`): golf −10 % (T2_GF), male neutral (T2_MT). First version (13 cm tube,
  T1_GF) rejected. Lift cap 4 cm rejected (T3_MT no gain, T3_GF worse).
- Checkpoints kept: `runs/T5_GF`, `runs/T5_MT` (per-pose corrective fields resume automatically).

### Exact commands (from work/clothing-v2/pipeline; each goes through heavy.sh; ~40–60 min each)
```
# male polo final candidate (male-garments' round-8 shoes/socks + K8 shorts, MG_MT cover)
GP_COVER_REF=$PWD/runs/MG_MT/MatchHero_Male/body.npz GP_BULGE=.10 GP_SHAPES=32 ./quick_eval MatchHero_Male T5_MT MG_MT 153 dump:Kit_Top@Kit_Top
# golf female (raglan R4 top, R4 cover)
GP_COVER_REF=$PWD/runs/R4_GF/GolfKitHero_Female/body.npz GP_SHAPES=32 ./quick_eval GolfKitHero_Female T5_GF R4_GF 153 npz:../out_gp/R4_GF/GolfKitHero_Female/unity/Kit_Top_final.npz@Kit_Top
# install a passing run into any project (integration):
handoff/install_garments.sh <project> MatchHero_Male:T5_MT            # male-garments installs the male into its own clone instead
handoff/install_garments.sh <project> GolfKitHero_Female:T5_GF:../out_gp/R4_GF
```
Then: the female tennis top would gain from the same cover ref (`GP_COVER_REF=runs/K12_FT/MatchHero_Female/body.npz`, base K12_FT).

## Gates
| Gate | Status | Evidence |
|---|---|---|
| TEARS | **FAIL** (no hero at 0). Best vs today's install, same metric: male tennis −46 %, male golf −75 %, female tennis −45 % (K3b); golf female worse (sleeve design) | tables above, runs/*/suite/<Hero>/REPORT.md + sheet_worst12.jpg |
| LAYERS | **FAIL**: male tennis 63k (today 53k: shorts through the polo hem when kneeling), golf male 21.9k (20.4k), female tennis 3.0k (13) | same |
| HOLES (cover) | improved 77–87 % on every hero | same |
| SHAPE (bind pose unchanged) | **PASS**: corrective weight at rest 0.0000–0.0002 on every fit, install max rest error 0.0000 mm | fit logs, logs/batch_*.log |
| COLOURS | **PASS** (female tennis kit; other heroes not run): 6 swatches (white, near-black, red, blue, green, yellow) through the game's SetKit, front + back, 1080p: binding, rib hem, pleats read in all | proof/15_colours_swatches_female_tennis.jpg, film/batch_1018_0312/swatch |
| PERF (≤ 0.3 ms/hero, 1080p) | **PASS** for the 3 installed heroes: male tennis 0.067 ms, golf male 0.081 ms, female tennis 0.056 ms (K6: 0.071 ms); 1080p render with correctives on vs zero within noise | perf/batch_1017_1855_perf.json, perf/batch_1017_2251_perf.json |
| NATIVE (SceneKit lobby) | **PASS for the garments (clone-only check, 06:57)**: `native.sh` runs hero-sync's own lobby export on ~/garments-UnityClone into a scratch CharacterAssets copy and renders the app's SceneKit lobby vs the Unity capture (same cameras): the rebuilt female top (K6) exports and renders with the game's shape. Notes: a real install must regenerate the garment `.ktx` maps (compress_maps.py; the scratch copy kept the old .ktx, faint chest smudge in the lobby); female face/skin parity (MAD 11–13) is the face shader not yet synced, not the kit. Nothing written to the repo | proof/16_native_lobby_vs_game_female_tennis.png, native/sheets/PARITY.md |
| NEW_GARMENT_30MIN | **PASS** | see row below |
| DOC | **PASS**: GARMENT_PIPELINE.md; the timed run used only its documented commands | work/clothing-v2/GARMENT_PIPELINE.md |
| OFFSETS manifest (chat 3) | written per install: out/<Hero>/garment_offsets.json -> Resources/<Sport>/KitsV2/<Sex>/KitV2_<Sport>_<Sex>_offsets.json (format in REQUESTS.md) | |
| REF_MATCH female tennis top | for Adnan's review: in-engine 1080p vs sheet 09 | proof/refmatch/13_female_tennis_top_ingame_vs_sheet09.jpg, proof/refmatch/09_* |
| REF_MATCH male shoes / male garments | moved to the male-garments chat 10-17 19:15 (shoe4.py); this chat's sheet-13/14 shoe3 attempt: proof/refmatch/11 (not a match) | |
| Repo install of the female top | BLOCKED: HeroShoulderDeformation rewrites/rejects `[gp]` tops (request in work/delegation-2026-10-17/REQUESTS.md; clone-only patch line 60) | |
| NEW_GARMENT_30MIN | PASS (compute 1,006 s ≈ 17 min, one command, design data only) | `garment_new MatchHero_Male polo2 tennis_male Kit_Top '{"sleeve":{"t":[0.05,0.20,0.30],"r":[0.086,0.072,0.060]}}' run=new_ls`: build+export+maps 14 s, fit 511 s, cover+suite 481 s (logs/new_ls.time). The 20:55 machine OOM interrupted the cover; it resumed from its checkpoint (`garment_fit … resume`). Result: 3/4-sleeve polo TEAR 145,019 / LAYER 27,467 (report runs/new_ls/suite/MatchHero_Male) |
