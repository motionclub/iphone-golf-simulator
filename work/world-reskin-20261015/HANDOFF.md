> Latest: golf has been rebuilt in the user-selected fantasy direction. Start with `revision2/GATE_RESULTS.md` and `revision2/PLAN.md`. `revision2/proof/comparisons` is the current golf review set; the installed review app predates this revision.

# Luminous Coast — completed two-map pilot

Read `GATE_RESULTS.md` for evidence and limits. Resort tennis and authored golf hole 12 (Cliffside’s displayed hole 04) are now enabled by default. Set `LUMINOUS_COAST=0` only to capture the original baseline.

The user accepts 30 fps when needed and explicitly said to skip phone testing. Do not ask for another device unlock. No physical-device frame rate is verified. The pilot governor preserves art quality while moving from 120 → 60 → 30 under sustained late frames, then permits existing quality reductions if 30 remains late. Native load target choices take precedence over restoration when a pilot is destroyed.

- `proof/comparisons/` contains finished before/after boards made from actual Unity screenshots. `source/make_comparisons.py` labels/scales screenshots only; no paintover.
- `proof/regression-30fps.xml` records 63 passing tests. `proof/default-on/` captures the pilots with no opt-in environment variable and the golf12 → golf7 transition.
- `SOURCE_MANIFEST.json` hashes current owned source and shipped pilot assets.
- `source/build_pines.py` / `assets/CoastalPines.blend` own the opaque tree kit: four instanced variants, near 14,250 triangles each, far 6,762. Existing submission currently uses near meshes at all distances. No new colliders.
- Rejected ridge assets are under `assets/rejected`, outside Resources. Candidate captures are intermediate work, not final evidence.
- `device/root` is an isolated native clone with bundle `com.aloniewski.GolfArcade.CoastReview`. The signed art review app was built and installed, but it predates the final fallback. Do not describe the installed app as containing the fallback.
- Device scripts are retained for optional future profiling. The analyzer still evaluates a strict 60 fps target and is not the current acceptance gate. No new device run is requested.
- No commits or production deployment. Extensive unrelated work exists in this checkout; never stage/reset it.

Known limits: the horizon is a detailed panorama without translation parallax; no console AAA parity claim. Existing weather logic remains. Runtime 30/60 pacing and thermal behavior are unmeasured.
