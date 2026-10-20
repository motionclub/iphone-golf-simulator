# Cloth overhaul audit — baseline 2026-10-05

Current runtime is the bald party-tennis match heroes, not golf. Source baseline and rollback hashes: baseline_files.json, protected_before.json. Fixed proof cameras: Unity/Assets/Editor/ClothProofRig.cs; real Tennis scene, real MatchHeroLook materials, Hero rim light, unchanged TennisURP. Stills: before/; motion input frames and audit are also there; compressed films: ArtDir/screenshots/cloth_overhaul/before/.

## Verified starting state

TennisCloth.shader: 166 lines, base seam map + weave normal/thread tile, wrap, grazing Fresnel sheen, rim/exposure/shoulder, shadows and SSAO; no garment N/M maps. Two authored texture samples in source (compiled Metal ALU/sample count still needs extraction; source sample count is not a compiled statistic).

MatchHeroLook creates runtime materials and binds all maps there. Seven role strings are present; SetKit uses the existing 35% trim derivation. Six separate skinned kit renderers are bound to 53 bones. Main skin, face and racket asset meshes are protected.

Installed kit FBX SHA/file dates and all replaced files are recorded in baseline_files.json; meshes and connected construction components are in kit_geometry_before.json. Each kit already contains real collar pieces, three buttons, hem/cuff ribbons, and shoe laces; weak normals and uniform material detail make them read as flat paint. P0 fixed close-ups expose these features.

10c: no work/tennis-clothes-volume output or installation evidence. Its volume/cut goals are absorbed here. The installed predecessor work/standard-tennis-kit-worn has measured loose shorts and an overlapping polo hem; retain that cut and improve construction.

16: installed indirectly. work/tennis-shoes-fit/GATE_RESULTS.md says the staged shoes were not exported by that pass itself. work/hero-dressed/README.md explicitly selects those output blends and skins them; the installed Male/Female Kit FBXs match the dressed-kit outputs. This is the installed fitted-shoe path, not the earlier placeholder-foot kit.

24: installed. work/locker-mirror/NOTE_locker_mirror.md, GATE_RESULTS.md and export logs exist. MatchHeroData/Surfaces carry UVs, per-surface runtime shader parameters, sampled normal/weave maps, and Ready/Serve bone tracks. CharacterModelPreview and the locker exporter have newer edits from other work; P5 will be last, with a fresh ownership/status check before editing.

## Geometry baseline

Male kit: top 22298, bottom 21032, socks 6270 each, shoes 17678 each = 91226 tris; full hero incl. face and racket 174032. Female: top 19408, bottom 25646, socks 5082 each, shoes 12910 each = 81038 tris; full hero 141840. The prior dressed-hero gate budget allows <=100k kit tris and <=80 MB resident mirror geometry/hero. No total match-hero ceiling was found in the active tennis/course budget documents yet; do not substitute the old 50k bald-base target for an approved dressed-match total. G10 remains unverified until this is resolved and device profiling is measured.

UV area/density per renderer and textures sampled: before/audit.json. Baseline px/cm (includes inner walls): male top 11.67, bottom 6.81, socks 5.30, shoes 10.74; female entries are in the same file. Existing sizes: top 2048², bottom/shoes 1024², socks 512², weave 256². Fixed-resolution tests retain these sizes; shared new fabric atlas 512².

## Skort streak investigation

The streak exists even in the earlier BEFORE without the detail map, so removing only map darkening cannot repair it. The female bottom contains a closed A-line main skirt plus a separate 1892-vertex wrap overlay and a narrow seam overlay; their hem surfaces meet at sub-millimetre separation. This is the candidate source of self-shadow/SSAO and depth competition. The new low mesh removes the redundant wrap/seam overlay, retains the closed skirt and undershort, adds shallow constructed pleats, and uses a fresh non-overlapping UV bake. The four rendered views must confirm this diagnosis before G6 passes.

## Restrictions and verification status

No gameplay, clip, pipeline, QualitySettings or post assets are edited by this job. The proof runner operates an APFS copy of Unity to avoid the active serve/lobby chats. Scene lighting is unchanged. Cloth-only shader/runtime/importer edits are in the shared source, but new meshes/maps will first be validated in the isolated copy. No commit. Adnan's eye is required by G12 and cannot be marked PASS automatically. Mac M5 editor timing is not an iPhone-class performance measurement.

## Final audit corrections

The valid baseline is now before_verified/ and the final candidate is after_final/. The original before/ foot views were replaced by the same fixed shoe-bound cameras in both variants. For shoe-side and underside inspection only, the occluding court floor is hidden identically; match frames and films retain the unmodified court.

P5 ran last after the lobby owner finished. The native SceneKit app builds, loads 25 ASTC KTX maps, and retains the existing rig/animation schema. All pre-P5 replacements were separately backed up after that owner’s completed changes.

The skort streak cause is confirmed by four views: redundant overlapping wrap/seam shells created depth/self-shadow competition. Removing those shells, rebuilding the UVs, and baking moderate pleats removes the streak.

Unity’s Metal CompileVariant succeeds with no diagnostics but exposes bytecode and binding layouts rather than a hardware ALU statistic. The exact Metal output was compiled to optimized Apple AIR and inventoried: court floating IR operations 87 -> 143, fused multiply-add intrinsics 31 -> 49; static texture sample calls 7 -> 6. Plain variants: 54 -> 96 floating IR operations, 19 -> 31 FMA, 2 -> 3 samples. These are separately labelled IR statistics, not hardware ALU counts. The required device comparison is now collected: mean full frame 33.345456→33.336250 ms (−0.009206), inside +0.5 ms. GPU mean rises 11.086737→13.881656 ms; this reduced headroom is disclosed. G10 remains FAIL only for the strict compiled Metal ALU report. Adnan directly approved the clothes on 2026-10-05, so G12 is PASS.
