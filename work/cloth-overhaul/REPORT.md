# Cloth quality overhaul — prompt 29

Project: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`. Implemented in the shared project; stage only, no commit. Eleven gates pass, including Adnan’s direct clothing approval. G10 remains FAIL for the strict compiled Metal ALU report; physical frame timing is now recorded. The Goal tool retains its prior blocked status while resumed work proceeds.

- **G1 CONSTRUCTION_READS — PASS**: 25 labelled crops: [CONSTRUCTION_SHEET.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/CONSTRUCTION_SHEET.png); thick rolled collars, real buttons/cord/pockets/vents, turned hems and dashed stitching, pleats, rib cuffs, flat laces, panels, foam and rubber tread.
- **G2 FOLDS — PASS**: male_armpit 17.321%; female_armpit 13.818%; male_waist 13.632%; female_waist 12.795%; male_crotch 8.030%; maximum lit fold reduction 23.850% <30%. [fold_measurement.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/fold_measurement.json)
- **G3 WHITE_STAYS_WHITE — PASS**: male_shirt L* 90.856; male_bottom L* 90.081; male_trim L* 19.804; female_shirt L* 90.214; female_bottom L* 90.307; female_trim L* 18.284. [white_measurement.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/white_measurement.json)
- **G4 FABRIC_VARIES — PASS**: [FABRIC_SHEET.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/FABRIC_SHEET.png); pique .10/.55, rib .13/.38, mesh .16/.24, rubber .04/0 (smoothness/sheen). Six IDs, derivative-filtered atlas and neutral N/M.
- **G5 NO_SHIMMER — PASS**: male 0.003347759 -> 0.003308970; female 0.005852958 -> 0.003841651 linear luma RMS; 180 frames at 1170×2532/60 Hz, shirt interior eroded 3 px. No visible moiré in inspected strips. [shimmer_measurement.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/shimmer_measurement.json)
- **G6 SKORT_ARTIFACT_GONE — PASS**: [SKORT_FOUR_VIEWS.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SKORT_FOUR_VIEWS.png); streak absent front/side/back/opposite. Cause: overlapping wrap and seam shells produced depth/self-shadow competition. Remove redundant shells, keep main skirt/undershort, rebuild UVs and bake pleats.
- **G7 RECOLOUR — PASS**: [RECOLOUR_GRID.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/RECOLOUR_GRID.png); eight catalog colours + white/black, 60 rendered picks, 100 main/trim material checks; maximum RGB error 1.16e-07. Existing 35% trim derivation retained.
- **G8 SPEC_REUSE — PASS**: [GARMENT_SPEC.md](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/kit/GARMENT_SPEC.md); spec-only blue polo duplicate, same executable/maps/geometry, DUMMY_POLO.json main_hex=3FA9F5. [SPEC_REUSE_male.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SPEC_REUSE_male.png) [SPEC_REUSE_female.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SPEC_REUSE_female.png); hashes [spec_reuse_proof.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/locker/spec_reuse_proof.json)
- **G9 RIG_SAFE — PASS**: 80 protected hashes unchanged; non-kit prefab nodes/meshes, avatar and clips exact, 53 bones and ≤4 weights. Racket socket delta 0 mm at Ready and Serve contact; maximum measured other socket delta 0.000008900 mm. [RIG_WORST_FRAMES.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/RIG_WORST_FRAMES.png) [prefab_identity_results.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/prefab_identity_results.json) [rig_socket_results.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/rig_socket_results.json)
- **G10 BUDGET — FAIL**: Geometry, ASTC memory, ≤6 static samples and iOS/native builds pass. Physical two-hero frame mean 33.345456 → 33.336250 ms (−0.009206 ms), within +0.5 ms. GPU mean 11.086737 → 13.881656 ms (+2.794919), median +1.280896; unchanged capped frame time does not imply unchanged GPU cost. Strict compiled Metal ALU statistics remain outstanding; the isolated iPhone capture helper is built but iOS locked the phone again. A local trace of the four Unity-generated Metal variants was captured/profiled on Apple M5 (plain registers 100→112, court 140→130; zero spilled bytes), but Xcode UI timed out before exact ALU counts were extracted. Neither register counts nor vector AIR estimates are substituted for the strict ALU statistic. [device_timing_comparison.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/device_timing_comparison.json) [air_instruction_inventory.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/compile_final/air_instruction_inventory.json) [ios_after_exact_final.log](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/logs/ios_after_exact_final.log)
- **G11 LOCKER_PARITY — PASS**: [LOCKER_PARITY_male.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/LOCKER_PARITY_male.png) [LOCKER_PARITY_female.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/LOCKER_PARITY_female.png); default trim, folds, differentiated weave, panel stitches, foam/rubber read in both renderers. Different court/locker illumination is retained; no pixel-identical lighting claim. P5 ran last after lobby owner finished; native iOS build succeeds.
- **G12 EYE — PASS**: Adnan approved the delivered clothes directly on 2026-10-05: “clothes look good”; requested the same detail standard for golf selections. Approved art is unchanged; shared contract/template and golf handoff added. [eye_approval.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/eye_approval.json) [COPY_TO_GOLF.md](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/kit/COPY_TO_GOLF.md)

## Budgets and validation

| Hero | Kit before | Kit after | Delta | Total before | Total after | Inferred dressed cap |
|---|---:|---:|---:|---:|---:|---:|
| male | 91,226 | 93,839 | +2,613 | 174,032 | 176,645 | 182,806 |
| female | 81,038 | 76,962 | -4,076 | 141,840 | 137,764 | 160,802 |

The existing dressed gate allows kit additions ≤100k triangles with the protected base unchanged (`work/hero-dressed/GATE_DEFS_preregistered.md:143`). The cap above is the unchanged body/face/racket plus that allowance; it is an inference, not a newly invented absolute match ceiling. This change also meets the stricter current-kit ≤100k and ≤6k increase tests. No separate total match ceiling was found in the active tennis/course documents.

| Map | Size | ASTC | Full-mip MB |
|---|---:|---|---:|
| Cloth_FabricAtlas.png | 512² | ASTC_4x4 | 0.349552 |
| Kit_Female_Bottom_M.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Female_Bottom_N.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Female_ShoeL_M.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Female_ShoeL_N.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Female_ShoeR_M.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Female_ShoeR_N.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Female_SockL_M.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Female_SockL_N.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Female_SockR_M.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Female_SockR_N.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Female_Top_M.png | 2048² | ASTC_8x8 | 1.398144 |
| Kit_Female_Top_N.png | 2048² | ASTC_8x8 | 1.398144 |
| Kit_Male_Bottom_M.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Male_Bottom_N.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Male_ShoeL_M.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Male_ShoeL_N.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Male_ShoeR_M.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Male_ShoeR_N.png | 1024² | ASTC_8x8 | 0.349568 |
| Kit_Male_SockL_M.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Male_SockL_N.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Male_SockR_M.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Male_SockR_N.png | 512² | ASTC_8x8 | 0.087424 |
| Kit_Male_Top_M.png | 2048² | ASTC_8x8 | 1.398144 |
| Kit_Male_Top_N.png | 2048² | ASTC_8x8 | 1.398144 |

Before cloth maps: one ASTC6 seam map per piece + ASTC4 256² weave, 4,780,848 full-mip bytes/hero. After: 5,680,352 bytes/hero, below 6,000,000. Shared 512² ASTC4 atlas and still-loaded 256² legacy weave count once per hero; they total 436,960 bytes. The SceneKit loader uses native ASTC KTX textures with mipmaps and preserved mask alpha, not decoded RGBA PNGs.

Metal court variant: 7 → 6 static sample calls; plain variant 2 → 3. Floating AIR instructions 87 → 143 (court), 54 → 96 (plain); FMA intrinsics 31 → 49 and 19 → 31. Vector IR operations, dots and intrinsics are reported separately, without calling them hardware ALU counts. Unity CompileVariant reports success and zero shader diagnostics; SRP Batcher code 0; zero new keywords. [air_instruction_inventory.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/compile_final/air_instruction_inventory.json)

The [Unity CompileVariant API](https://docs.unity.com/en-us/engine/6000.0/script-reference/unityeditor/shaderdata/pass/compilevariant) returns compiled variant bytecode and layouts. Apple’s [pipeline statistics](https://developer.apple.com/documentation/xcode/analyzing-draw-command-and-compute-dispatch-performance-with-pipeline-statistics) are a separate on-device GPU analysis. The strict requested ALU report remains open.

Locker MatchHero bundle: 69,691,514 bytes = 69.692 MB, below existing 70 MB. Unpacked new candidate was 76.778 MB. Cloth-only position/normal mantissa rounding saves 7,086,484 bytes; maximum pose position deviation 0.064023 mm, max normal-vector error 0.00020552. All non-cloth bytes and rig files are exact; the production Unity exporter matches the independent packing prototype. [packing_export_verification.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/locker/packing_export_verification.json)

Male mirror geometry: base 5.640 MB + all 12 morphs 31.188 MB + rig 10.041 MB = 46.870 MB <80. This counts exported geometry buffers, not process RSS or SceneKit’s internal allocations.
Female mirror geometry: base 4.509 MB + all 12 morphs 25.577 MB + rig 8.990 MB = 39.076 MB <80. This counts exported geometry buffers, not process RSS or SceneKit’s internal allocations.

Physical baseline: iPhone 17 Pro Max (`iPhone18,2`), Apple A19 Pro, iOS 26.6.1; two real match heroes, unchanged TennisURP/quality and 30 Hz cap. Initialize, warm 8+3 s, collect 720 frames and discard first 180; 540 valid timing rows.

- Before cpuMs: mean 33.345456 ms, median 33.335729, p95 33.394514.
- Before gpuMs: mean 11.086737 ms, median 7.564313, p95 21.541313.
- Before cpuMainThreadMs: mean 4.370983 ms, median 5.089542, p95 6.121660.
- Before cpuRenderThreadMs: mean 4.817123 ms, median 5.141500, p95 6.811088.
- Before presentWaitMs: mean 28.957119 ms, median 28.231022, p95 31.878207.

Final 29.2.0 after profile is recorded on the same unlocked device: 540 valid rows, two heroes, all GPU values nonzero. Mean CPU frame delta −0.009206 ms and median +0.001209 ms; p95 −0.010165 ms. GPU mean +2.794919 ms and median +1.280896 ms, with p95 −0.094377 ms. The capped frame budget passes; GPU headroom is reduced and is reported separately. Compare full means/medians/p95 in device_timing_comparison.json. Saved baseline: [device_profile_before.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/device_profile_before.json). Profile script: [ClothDeviceProfile.cs](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/scripts/ClothDeviceProfile.cs). This timing comes from the real iPhone, not a Mac editor or build duration.

Build evidence:

- Unity iOS export: [ios_after_exact_final.log](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/logs/ios_after_exact_final.log) and [build_summary.txt](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/ios_after/build_summary.txt) — succeeded, 0 errors.
- Signed device native build: [xcode_after_exact_final.log](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/logs/xcode_after_exact_final.log) — BUILD SUCCEEDED.
- Native SceneKit app including 25 KTX resources: [locker_ios_build_packed.log](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/logs/locker_ios_build_packed.log) — BUILD SUCCEEDED.
- [video_verification.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/video_verification.json) — all 28 MP4s have video tracks, correct dimensions/durations and three decoded samples.

## Implementation and inherited work

23’s prior weave/sheens were installed; this pass extends them. 10c had no installation/output evidence and its volume/construction goals were absorbed. 16 is installed indirectly through the dressed-kit build selecting its fitted shoes. 24 is installed and its rig schema, skin, face, racket and playback remain. See [AUDIT.md](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/AUDIT.md) for source hashes and predecessor evidence.

Low geometry adds clean recessed pockets with existing four-bone interpolated weights, cord/tips and a real side vent; collar stand/roll and turned edges use the existing shells. Female redundant wraps are removed; 12 shallow knife pleats and hem steps break the silhouette. Bake-only subdivided high surfaces author moderate folds, seams, rib cuffs, stitched hems, mesh/panel construction and herringbone tread. New garment N/M UVs remain neutral and recolourable. Default stays white/black without marks.

Runtime binds every map by sex/piece, merges mask-driven trim while retaining all seven role strings and the existing 35% rule. Shader uses Charlie/Ashikhmin-style sheen, knit-only fuzz, wrap diffuse, AO/specular occlusion, cavity, separate rubber/foam and derivative fade. No QualitySettings, pipeline, post, body/face assets, sockets, clips or prohibited gameplay code changed.

P5 ran last after the lobby owner completed. Data/Surfaces/exporter and both project resource lists were backed up from that completed state. SceneKit receives native ASTC maps, tint masks, six fabrics, wrap/sheen/AO and derivative weave fade. Existing files from other chats are preserved; no messages were sent to them.

## Proof paths

Fixed rig: [ClothProofRig.cs](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Editor/ClothProofRig.cs). Before input frames [before_verified](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/before_verified); final input frames [after_final](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/after_final). The shimmer-only captures start from fresh initialization in both variants, avoiding motion/lighting state left by the longer full proof run. Protocols [SHIMMER_MEASUREMENT_PROTOCOL.md](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/SHIMMER_MEASUREMENT_PROTOCOL.md) and [FOLD_MEASUREMENT_PROTOCOL.md](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/FOLD_MEASUREMENT_PROTOCOL.md). Sole/shoe inspection hides only the occluding floor equally in both variants; match views/films use the unmodified court.

- [CONSTRUCTION_SHEET.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/CONSTRUCTION_SHEET.png)
- [FABRIC_SHEET.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/FABRIC_SHEET.png)
- [LOCKER_PARITY_female.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/LOCKER_PARITY_female.png)
- [LOCKER_PARITY_male.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/LOCKER_PARITY_male.png)
- [RECOLOUR_GRID.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/RECOLOUR_GRID.png)
- [RIG_WORST_FRAMES.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/RIG_WORST_FRAMES.png)
- [SHEET_female_bottom_back.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_bottom_back.png)
- [SHEET_female_bottom_front.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_bottom_front.png)
- [SHEET_female_bottom_other.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_bottom_other.png)
- [SHEET_female_bottom_side.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_bottom_side.png)
- [SHEET_female_collar.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_collar.png)
- [SHEET_female_drawcord.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_drawcord.png)
- [SHEET_female_full_back.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_full_back.png)
- [SHEET_female_full_front.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_full_front.png)
- [SHEET_female_full_threequarter.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_full_threequarter.png)
- [SHEET_female_match_behind.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_match_behind.png)
- [SHEET_female_match_phone.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_match_phone.png)
- [SHEET_female_opponent.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_opponent.png)
- [SHEET_female_pocket_detail.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_pocket_detail.png)
- [SHEET_female_shoe.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_shoe.png)
- [SHEET_female_shoe_side.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_shoe_side.png)
- [SHEET_female_sleeve.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_sleeve.png)
- [SHEET_female_sock.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_sock.png)
- [SHEET_female_sole.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_sole.png)
- [SHEET_female_vent_detail.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_vent_detail.png)
- [SHEET_female_waist.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_female_waist.png)
- [SHEET_male_bottom_back.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_bottom_back.png)
- [SHEET_male_bottom_front.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_bottom_front.png)
- [SHEET_male_bottom_other.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_bottom_other.png)
- [SHEET_male_bottom_side.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_bottom_side.png)
- [SHEET_male_collar.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_collar.png)
- [SHEET_male_drawcord.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_drawcord.png)
- [SHEET_male_full_back.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_full_back.png)
- [SHEET_male_full_front.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_full_front.png)
- [SHEET_male_full_threequarter.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_full_threequarter.png)
- [SHEET_male_match_behind.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_match_behind.png)
- [SHEET_male_match_phone.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_match_phone.png)
- [SHEET_male_opponent.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_opponent.png)
- [SHEET_male_pocket_detail.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_pocket_detail.png)
- [SHEET_male_shoe.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_shoe.png)
- [SHEET_male_shoe_side.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_shoe_side.png)
- [SHEET_male_sleeve.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_sleeve.png)
- [SHEET_male_sock.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_sock.png)
- [SHEET_male_sole.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_sole.png)
- [SHEET_male_vent_detail.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_vent_detail.png)
- [SHEET_male_waist.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHEET_male_waist.png)
- [SHIMMER_female_after.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHIMMER_female_after.png)
- [SHIMMER_female_before.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHIMMER_female_before.png)
- [SHIMMER_male_after.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHIMMER_male_after.png)
- [SHIMMER_male_before.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SHIMMER_male_before.png)
- [SKORT_FOUR_VIEWS.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SKORT_FOUR_VIEWS.png)
- [SPEC_REUSE_female.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SPEC_REUSE_female.png)
- [SPEC_REUSE_male.png](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/SPEC_REUSE_male.png)

Motion clips: ReadyIdle, Forehand, Serve trophy, Run, Pushups and 360° turntable are 2 s/60 Hz at 960²; shimmer is 3 s/60 Hz at 1170×2532.

- [female_forehand.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_forehand.mp4)
- [female_pushups.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_pushups.mp4)
- [female_ready.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_ready.mp4)
- [female_run.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_run.mp4)
- [female_shimmer.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_shimmer.mp4)
- [female_trophy.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_trophy.mp4)
- [female_turntable.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/female_turntable.mp4)
- [male_forehand.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_forehand.mp4)
- [male_pushups.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_pushups.mp4)
- [male_ready.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_ready.mp4)
- [male_run.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_run.mp4)
- [male_shimmer.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_shimmer.mp4)
- [male_trophy.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_trophy.mp4)
- [male_turntable.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/after/male_turntable.mp4)
- [female_forehand.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_forehand.mp4)
- [female_pushups.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_pushups.mp4)
- [female_ready.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_ready.mp4)
- [female_run.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_run.mp4)
- [female_shimmer.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_shimmer.mp4)
- [female_trophy.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_trophy.mp4)
- [female_turntable.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/female_turntable.mp4)
- [male_forehand.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_forehand.mp4)
- [male_pushups.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_pushups.mp4)
- [male_ready.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_ready.mp4)
- [male_run.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_run.mp4)
- [male_shimmer.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_shimmer.mp4)
- [male_trophy.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_trophy.mp4)
- [male_turntable.mp4](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/screenshots/cloth_overhaul/before/male_turntable.mp4)

## Changed files, rollback and staging

Every production replacement has a baseline rollback; new files are marked NEW. [changed_files.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/changed_files.json) lists current hashes and exact rollback paths. First snapshot [baseline_files.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/baseline_files.json); installed kit [installed_files.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/installed_files.json); fresh P5 baseline [p5_preinstall.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/p5_preinstall.json); locker install [installed_files.json](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/locker/installed_files.json).

Restore only a listed owned file from its recorded rollback after checking subsequent edits; do not bulk-reset the repository. `rollback/p5_after_lobby/` preserves the completed lobby changes, and `rollback/p5_unpacked/` retains the unpacked cloth export. `protected_final.json` records all 80 protected source hashes matching the baseline.

Staged paths: [staged_paths.txt](/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/cloth-overhaul/staged_paths.txt). Only cloth-owned source, maps, geometry, spec/reference notes, reproducibility scripts, proof films/sheets, metrics, logs and rollback copies are included. Raw frames, isolated projects, DerivedData, caches, downloaded toolchain and discarded iterations are excluded. Both pbxproj index updates contain only our 25 KTX resource additions while preserving the existing index. No commit.

## Optional refinements and remaining technical work

I would still refine the pocket lip silhouette and the collar tip joins if Adnan wants a softer cut, and tune any pose-specific crease he flags in the films. The baked stitch size is deliberately readable in close-up; match-distance detail fades. Adnan has approved the delivered look. These are optional refinements. Strict ALU evidence remains required; no waiver is inferred.
