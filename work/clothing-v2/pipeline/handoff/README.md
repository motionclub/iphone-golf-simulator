# Garment pipeline → integration hand-off (chat 5)

## Ready now: female tennis (MatchHero_Female), run K12_FT
Stress suite, 153 poses (full suite, `runs/K12_FT/suite/MatchHero_Female/REPORT.md`):

| | today's install | K12_FT |
|---|---|---|
| TEARS (skin through cloth) | 230,302 | **60,667 (−74 %)** |
| LAYERS | — | 1,583 |
| HOLES | — | 9,444 (background 7,428) |

Installed and filmed in chat 5's clone (`~/garments-UnityClone`, batch_1018_1531): 1080p film without puffiness
(proof/18), COLOURS swatches PASS, driver cost 0.148 ms (64 blend shapes: top 32 + skirt 32).
New pieces: `Kit_Top [gp]` (sheet-09 rebuilt tank, 22,516 verts) from `work/clothing-v2/out_gp/MatchHero_Female`,
and the existing skirt and shoes with pipeline weights, correctives and cover.

### Install into your project (one Unity batch per step, through heavy.sh, muted)
1. Files from the repo (staged by chat 5) must be in the project:
   - `Assets/Editor/GarmentPipelineInstall.cs` and `Assets/Editor/ClothingV2Install.cs`
   - `Assets/Scripts/Tennis/GarmentPoseCorrectives.cs`
   - `KitV2PoseCorrectives.cs` (chat 5's hunks)
   - `HeroGarmentHemWeights.cs` (the `[gp]` skip)
2. Apply `HeroShoulderDeformation_gp_skip.patch`. Without it the `[gp]` top throws "Tank shoulder corrective topology mismatch":
   ```
   cd <project> && patch -p1 < <repo>/work/clothing-v2/pipeline/handoff/HeroShoulderDeformation_gp_skip.patch
   ```
   This is one line in a file chat 5 does not own; the request is in `work/delegation-2026-10-17/REQUESTS.md`.
3. Run the install:
   ```
   work/clothing-v2/pipeline/handoff/install_garments.sh <project> MatchHero_Female:K12_FT:../out_gp
   ```
   It exports the run (weights, GP_Pose correctives, cover hide lists, offsets), installs the new mesh (ClothingV2Install) and installs the pipeline data (GarmentPipelineInstall). It prints the install report.
4. Lobby:
   - regenerate the garment `.ktx` maps (`work/clothing-v2/lobby/compress_maps.py`);
   - run `work/hero-sync/sync_heroes.sh`.

Rollback: re-run `ClothingV2Install` with today's `work/clothing-v2/out`, or revert the prefab and meshes from git.

## Stopped 2026-10-18 21:10 (Adnan: "stop the shirt tearing stuff for now")
- The final build ships:
  - the male polo as male-garments' round-9 copy of K8;
  - today's golf female top;
  - the female tennis K12_FT above.
- Resume state and exact commands are in `../GATE_RESULTS.md`, section "STOPPED".
