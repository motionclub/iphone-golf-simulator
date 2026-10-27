# HeroLod: dark streaks / black faces on LOD copies — 2026-10-26

Bowling (10-26 fix pass) saw dark swirl streaks on arms, legs and neck, plus fully black faces, whenever HeroLod drew its LOD copy of a
hero body. The A/B with `CHARACTER_LOD=0` was clean, so bowling heroes were given `HeroLodExempt`. The fault was not bowling-specific:
the tennis heroes show it too (below).

## Root cause
**The LOD meshes were fine. The fault was how HeroLod hid its proxy renderer.** `HeroLod.Show` hid a proxy with
`proxy.enabled = false` and `Proxy` switched it back on with `enabled = true`. In Unity 6000.3 the **body** proxy
SkinnedMeshRenderer, once switched off and on again (GameObject still active), draws with broken per-vertex shading data. The
geometry stays in place, but the skin shading goes wrong: speckles at LOD1, vertical stripes / a black face at LOD2. It stays broken
until the GameObject is deactivated and reactivated. The first time a proxy turns on it is clean. The kit / garment / cap proxies were
never affected. The body mesh is the only one with Color + UV0..4 (UV1 float3 bind pose, UV3 kit contact, UV4 skin unwrap) and no
tangents.

In the game, every LOD0 ↔ LOD>0 band crossing (and CHARACTER_LOD_FORCE stills taken after an "off" frame) re-enables the proxy, so a hero
that has once come close and gone back out draws a broken skin from then on. Bowling's walk-ups cross the 0.60 / 0.46 bands constantly.

Evidence (`proof/`, probe `unity/Assets/Editor/HeroLodCoverProbe.cs`, clone `~/unity-clones/herolod-fix` = bowling-ship + this HeroLod):
- `before/report.txt`: every LOD1/LOD2 body copy matches its source exactly. posMiss 0; normal, colour, uv0–uv4 mismatch 0; bind poses
  and blendshape counts equal; same bones and materials. Flipped triangles and border length (holes) are unchanged (e.g. BowlingF body
  border 7.263 → 7.253 m), so the simplifier opened no holes. (The `weights:N` column is an artifact of matching by position; the
  printed weights are identical.)
- `ab3_sheet.jpg`: the stored LOD2 mesh, a fresh Compact of it, and variants (null blendshape normals/tangents, no blendshapes) are all
  clean while the proxy stays on.
- `seq1_sheet.jpg` (old code): the first L2 is clean. off→L2, L1→L2, L0→L2 and L2→L1 all go black or speckled and stay that way.
  `seq_nulltan_sheet.jpg`: the blendshape-tangent fix does not help. Deactivating and reactivating the hero clears it.
- `seq_recreate_sheet.jpg` (new proxy on every re-show) and `seq_force_sheet.jpg` (proxy hidden with forceRenderingOff, never disabled):
  both clean through every transition.

Ruled out: holes from the simplifier on the cover's boundary edges, a stale HeroLodCache entry (the bodies are cache misses computed
from the live cover mesh: 8 hits / 16 misses), a missing property block or HeroFaceSkin head uniforms (same shared materials; the
block is copied), and bind-pose or bone mismatch.

## Fix (`Unity/Assets/Scripts/CharacterLod/HeroLod.cs`, staged)
- A proxy is never disabled. `Show` hides it with `forceRenderingOff = true`. `Proxy` mirrors the original's drawn state with
  `forceRenderingOff = !drawn` instead of `enabled`. A hidden proxy is not visible, so it does not skin (updateWhenOffscreen stays false).
- `OriginalsOnly` treats a proxy with forceRenderingOff as resting.
- Second bug found while reading the code: `HeroLodLibrary.Release` was called for parts that never requested LODs (OnDestroy, and a
  part whose mesh its owner replaced before the build). With shared garment meshes, that took another hero's user count, destroyed LOD
  meshes it was still drawing, and the part vanished. Parts now carry `requested` and release only then.
- No change to the simplifier, the cache format or `Version`: the shipped HeroLodCache.bytes stays valid.

## Gates
| Gate | Result |
|---|---|
| G1 LOD1/LOD2 close-ups match CHARACTER_LOD=0, 4 heroes (bowling M/F, tennis M/F) × face/body/side: dark-pixel excess ≤ 0.5 % (`tools/gate.py`) | before **25.04 % FAIL** → after **0.01 % PASS** |
| G2 no black after any toggle (off→L2, L1↔L2, L0→L2, 60 frames at L1, hero deactivate/reactivate), at timeScale 0 and 1 | `after_seq_sheet.jpg` — 96/96 frames clean, **PASS** |
| G3 no holes: border length / flipped triangles of the LOD bodies vs source | unchanged (before report) — **PASS** |
| G4 CharacterLod EditMode tests | 4/4 **PASS** (`proof/tests/results.xml`) |
| G5 compiles in the bowling-ship clone (Unity 6000.3.24f1) | **PASS** |

Proof sheets: `proof/before_sheet.jpg` vs `proof/after_sheet.jpg` (columns: CHARACTER_LOD=0 / FORCE=1 / FORCE=2 per view; the forced
levels are the same `HeroLod.ForceLevel` the env var sets). Note: in `before/` the probe's two tennis heroes were spawned on top of each
other (fixed in the probe for later runs), so those rows show two overlapping heads. The black skin is still plain to see.

## Bowling's HeroLodExempt
**It can be removed** once this HeroLod.cs is in the bowling branch. The probe spawns the real bowling-kit heroes
(`PlayerMale/FemaleBowlingKit`, Tiki venue) with the exempt component removed, and they pass G1/G2. To remove it, drop the
`AddComponent<HeroLodExempt>()` line in `BowlingHero.Spawn` and then the `HeroLodExempt` class + boot check in that branch's HeroLod.cs
(both bowling-worktree edits, not made here). Then re-film one venue with BowlingFilm to confirm in the game's own shots: not run here.
(LOD1 keeps 50 % and LOD2 30 % of a hero's triangles. The bowlers' screen heights in the game cameras were not measured here.)

## Re-run
`tools/run_probe.sh <out>` (env: `HLF_SEQ=1` toggle sequence, `HLF_AB=1` Compact variants + mesh dumps, `HLF_STILLS=0`,
`HLF_LEVELS=1,2`, `HLF_SRC=<dir>` to test another HeroLod copy), then `tools/sheet.py`, `tools/seq_sheet.py`, `tools/gate.py`.
