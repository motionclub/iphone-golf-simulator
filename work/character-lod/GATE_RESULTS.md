# Character LOD — GATE_RESULTS (2026-10-17, character-lod chat)

Brief: per-view character cost in golf tee views ≤ 0.25 M triangles; no visible pop at the swap distances (film); LOD0 renders
identical; perf A/B at 1080p. Design and files: `README.md`. All runs: Editor play mode in `~/character-lod-UnityClone` (Unity/ as
of 10-17 evening + these scripts), 1920×1080 render target, muted, through `heavy.sh`. Proof: `proof/`.

| Gate | Result | Evidence |
|---|---|---|
| TEE_CHAR_TRIS ≤ 250 k, all 16 golf holes | **PASS** | 606–609 k → **183–186 k** on every hole, always LOD2 (`proof/gate_tee_r5.md`, `proof/r5/views.tsv`) |
| LOD0_IDENTICAL (close-ups) | **PASS** | 3 close-ups (front 1.25, face 2.73, side 0.96 of the view height): **0** differing pixels, CHARACTER_LOD on vs off, min of 3 off/on/off rounds, off-vs-off noise floor 0; `originals_only` = true (`proof/r6/report.json`, `proof/r6/identity_*.jpg`) |
| NO_POP_FILM | **PASS** | 15 s log dolly 1.6 → 60 m crossing all 8 swaps (0→1→2→3→4→3→2→1→0): hero-box image change at every swap frame / neighbours ≤ **1.01** (gate ≤ 1.5) (`proof/r6/film_dolly_lod.mp4`, `film_levels.tsv`, `tools/film_pop.py`) |
| NO_POP_AB (same frozen frame, both levels, at the band edge) | **PASS** | pixels changed > 32/255: 0→1 0.12 %, 1→2 0.24 %, 2→3 1.1 %, 3→4 0.7 % (4 px of a 43 px hero); tee LOD0 vs LOD2 0.31 % (`proof/r6/pop_*.jpg`, `proof_sheet.jpg`) |
| PERF_AB_1080P | **PASS on the Editor proxy / device NOT RUN** | sync 1080p render (median of 4 interleaved rounds): tee 13.13 → 11.74 ms, drive 13.35 → 12.80, green-back 7.86 → 7.53. FrameTimingManager GPU, tee: solo 24.18 → 24.02 ms (flat, Editor noise), 4-golfer party 13.05 → 11.29 ms (`proof/r5/report.json`). Device GPU capture not run. |
| TENNIS (info) | measured | gameplay camera, 2 heroes: characters 1,268,653 → **326,247** tris (−74 %), far opponent LOD3, near player LOD2 (`proof/r5t/tennis_report.json`). Tennis close-up identity is noise-bound in that scene (it keeps animating: off-vs-off 18,073 px ≥ on-vs-off 10,905 px), so identity is proven on the frozen golf frames. |
| EDITMODE TESTS | **PASS 4/4** (r7) | `CharacterLodTests`: bands, index-only invariants, compacted vertex data byte-identical (positions, normals, UVs, bone weights), shipped cache decodes |

## Numbers
- Golfer (male, visible renderers) per level: 198,356 / 95,813 / 57,483 / 22,987 / 19,156 triangles (female 176,835 → 17,095).
  Tennis male 228,158 → 22,294, female 174,021 → 16,762.
- Golf frame totals: characters were 0.61 M of the tee frame. The other ~1.6–2.0 M of the tee views is scenery (chat 10's
  make-room work). Character LOD alone does not bring tee views under the 1.0 M frame cap.
- Golf far views with a few-pixel golfer (green-back, reverse-mid, pan180, map): 407,912 → ~29 k character triangles.
- Runtime: LODs come from the baked cache (`install/HeroLodCache.bytes`, 31 meshes: golf + tennis, both sexes, 4.6 MB). Hero
  ready in 0.3 s on a cache hit. On a miss: ~5–13 s on a worker thread for a whole hero, which stays at LOD0 meanwhile.

## Method notes / pitfalls
- Profiler "Triangles Count" reads 0 or a doubled frame now and then. The probe takes the mode of 20 per-frame reads, and
  `gate_views.py` drops reads where switching the heroes off did not register. One outlier is left in r5 (hole 7 max 2.34 M);
  the gate uses the median of the ≥ 3 valid reads per hole.
- r5's front close-up showed 2,412 px: a blink (it runs on unscaled time, so a frozen clock does not stop it). r6 measures the
  off-vs-off noise floor. Never judge identity from a single pair.
- A fixed hysteresis margin (0.025) put the tee view (0.394–0.397) on LOD1 on 7 holes, and it swallowed the 0.04 band. Fix:
  the band edge moved to 0.46, and the hysteresis became relative (±7 %).
- Swapping `sharedMesh` (first design) let `HeroAccessories.ApplyCover` derive the body cover from a LOD copy (golf bag between
  shots). Proxies avoid that: originals are never modified.

## r7 (compact uint16 cache + tests)
- `install/HeroLodCache.bytes` recoded to uint16 index lists (`tools/recode_cache.py`, 9.2 → 4.6 MB, same version 4); the reader
  accepts both encodings. With it in the clone: golfer LODs from cache, hits 15 / misses 0, ready in 0.4 s (`proof/r7/report.json`).
- `CharacterLodTests` 4/4 PASS (`proof/r7tests/tests.xml`).

## Not done / open
- **Not installed into Unity/.** It self-attaches to every hero, so every chat's renders with a hero below 0.60 of the view
  height would change the moment it lands (garment and hand-clearance proofs are still running). `install/install.sh install`
  (rollback: `install.sh remove`) copies only new files: scripts, probe, test, cache and the clone's .meta files. Request for
  chat 6 in `work/delegation-2026-10-17/REQUESTS.md`.
- The cache is keyed by the final runtime meshes. Every garment / body / accessory install after today makes some entries
  stale. Those heroes then compute on a worker thread (correct, just ~5–13 s at LOD0 after each build). Re-bake after the
  integration: `tools/run_probe.sh <out>` with `CLOD_STEPS=bake` (golf) and `CLOD_METHOD=CharacterLodTennisProbe` (tennis),
  then copy the `.bytes` to `install/` and run `tools/recode_cache.py`.
- Plaza / hub heroes get HeroLod too (any MatchHeroLook) but were not measured. Lobby/locker is SceneKit: unaffected.
- Device GPU timing (Xcode frame capture on the TV view) not run. The Editor timers are noisy.
- Golf tee frames are still over 1.0 M because of scenery (chat 10). Characters now take ~0.19 M of it.
