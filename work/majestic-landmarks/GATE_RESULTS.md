# GATE_RESULTS: Majestic landmark kit (L)

**GATE: LANDMARK_KIT PASS** (34 assets; gates measured on the re-imported FBX by `scripts/build.py`, judged by `scripts/gates.py`)

SHAPE_MATCH is an author read of each side-by-side sheet (`sheets/<Name>.jpg`: target crop | matching-angle render | turntable, LOD1, LOD2). Adnan's eye is final; each line says what still differs.

| asset | course | SHAPE_MATCH | TRIS | LOD | PIVOT_SCALE | CLEAN | TILE | MATERIALS |
|---|---|---|---|---|---|---|---|---|
| Lighthouse | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| TwinFallsIsle | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| CalderaVolcano | C | PASS | PASS | PASS | PASS | PASS | - | PASS |
| Balustrade | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| Planter | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| StoneGazebo | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| AlpineChalet | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| CanalBridge | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| Farmhouse | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| IceFishingHut | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| LookoutTower | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| MesaArch | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| RopeBridge | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| StepTemple | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| StiltHut | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| StoneGate | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| WaterTower | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| Waterwheel | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| Windmill | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| WitchCottage | B | PASS | PASS | PASS | PASS | PASS | - | PASS |
| BasaltSpire | C | PASS | PASS | PASS | PASS | PASS | - | PASS |
| CalderaWall_A | C | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| CalderaWall_B | C | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| ObsidianArch | C | PASS | PASS | PASS | PASS | PASS | - | PASS |
| RangerHut | C | PASS | PASS | PASS | PASS | PASS | - | PASS |
| StoneLantern | C | PASS | PASS | PASS | PASS | PASS | - | PASS |
| ToriiGate | C | PASS | PASS | PASS | PASS | PASS | - | PASS |
| CliffSkirt | A | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| FoamRing | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| FoamStrip | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| RockShelf | A | PASS | PASS | PASS | PASS | PASS | - | PASS |
| ShoreBand | A | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| ShoreBand_Arc | A | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| BlackSandShore | C | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

## Detail

### Lighthouse
- `GATE: SHAPE_MATCH PASS` vs targets/Lighthouse.jpg: all 7 features; target tower a touch more slender, gallery house white
- `GATE: TRIS PASS` LOD0 3,742 (incl. 12 shared FX) <= 15,000; LOD1 1,414; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 38% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 20.32 m in [16, 24]
- `GATE: CLEAN PASS` 4 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (Lighthouse_FX, Lighthouse_Impostor, Lighthouse_Mat)

### TwinFallsIsle
- `GATE: SHAPE_MATCH PASS` vs targets/TwinFallsIsle.jpg: jungle isle + summit temple + two-stage twin falls; outline rounder and more regular than the craggy target, falls are flat white cards until the Unity scrolling water shader is on them
- `GATE: TRIS PASS` LOD0 9,288 (incl. 0 shared FX) <= 15,000; LOD1 2,840; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 31% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; x 99.61 m in [80, 115], z 71.45 m in [65, 80]
- `GATE: CLEAN PASS` 7 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (TwinFallsIsle_FX, TwinFallsIsle_Impostor, TwinFallsIsle_Mat)

### CalderaVolcano
- `GATE: SHAPE_MATCH PASS` vs targets/CalderaVolcano.jpg: ridged cone, glowing crater, three lava rivers, plume card; target flank has more gullies
- `GATE: TRIS PASS` LOD0 2,780 (incl. 16 shared FX) <= 15,000; LOD1 1,500; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 54% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; x 288.00 m in [250, 330], z 144.95 m in [130, 160]
- `GATE: CLEAN PASS` 4 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (CalderaVolcano_FX, CalderaVolcano_Impostor, CalderaVolcano_Mat)

### Balustrade
- `GATE: SHAPE_MATCH PASS` vs targets/Balustrade.jpg: plinth, rail, turned balusters, capped post
- `GATE: TRIS PASS` LOD0 1,484 (incl. 0 shared FX) <= 3,000; LOD1 572; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 39% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; x 3.06 m in [2.9, 3.6]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (Balustrade_Impostor, Balustrade_Mat)

### Planter
- `GATE: SHAPE_MATCH PASS` vs targets/Balustrade.jpg: plinth, cream urn, mixed flower clump
- `GATE: TRIS PASS` LOD0 2,428 (incl. 0 shared FX) <= 3,000; LOD1 650; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 27% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 1.67 m in [1.4, 2.2]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (Planter_Impostor, Planter_Mat)

### StoneGazebo
- `GATE: SHAPE_MATCH PASS` vs targets/StoneGazebo.jpg: round steps, 8 columns, entablature, ribbed terracotta dome, finial
- `GATE: TRIS PASS` LOD0 4,702 (incl. 0 shared FX) <= 6,000; LOD1 1,898; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 40% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 7.78 m in [5, 8]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (StoneGazebo_Impostor, StoneGazebo_Mat)

### AlpineChalet
- `GATE: SHAPE_MATCH PASS` vs targets/AlpineChalet.jpg: log walls, thick snow roof, glowing windows, balcony, chimney + smoke, drifts
- `GATE: TRIS PASS` LOD0 3,124 (incl. 8 shared FX) <= 8,000; LOD1 1,036; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 33% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 7.98 m in [7, 11]
- `GATE: CLEAN PASS` 4 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (AlpineChalet_FX, AlpineChalet_Impostor, AlpineChalet_Mat)

### CanalBridge
- `GATE: SHAPE_MATCH PASS` vs targets/CanalBridge.jpg: brick humpback arch with voussoir ring, parapets, coping, white rail
- `GATE: TRIS PASS` LOD0 1,192 (incl. 0 shared FX) <= 4,000; LOD1 476; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 40% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -1.00..+4.63); x 12.49 m in [11, 13]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (CanalBridge_Impostor, CanalBridge_Mat)

### Farmhouse
- `GATE: SHAPE_MATCH PASS` vs targets/Farmhouse.jpg: red brick, steep red roof, white barge boards, white-framed windows, green door, flower boxes
- `GATE: TRIS PASS` LOD0 2,456 (incl. 0 shared FX) <= 6,000; LOD1 684; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 28% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 8.50 m in [7, 10]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (Farmhouse_Impostor, Farmhouse_Mat)

### IceFishingHut
- `GATE: SHAPE_MATCH PASS` vs targets/IceFishingHut.jpg: plank hut on skids, snow roof, stovepipe, glowing window, fishing hole
- `GATE: TRIS PASS` LOD0 1,100 (incl. 0 shared FX) <= 3,000; LOD1 444; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 40% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.01 in [-0.06, 0.06]; z 3.83 m in [2.4, 4.0]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (IceFishingHut_Impostor, IceFishingHut_Mat)

### LookoutTower
- `GATE: SHAPE_MATCH PASS` vs targets/LookoutTower.jpg: legs, braces, railed platform, red pyramid roof, flag; target roof is a deeper hip with log balcony rails
- `GATE: TRIS PASS` LOD0 2,226 (incl. 0 shared FX) <= 6,000; LOD1 1,186; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 53% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.00 in [-0.06, 0.06]; z 11.20 m in [9, 12]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (LookoutTower_Impostor, LookoutTower_Mat)

### MesaArch
- `GATE: SHAPE_MATCH PASS` vs targets/MesaArch.jpg: red sandstone arch with strata and flaring legs; target arch is more massive and blocky
- `GATE: TRIS PASS` LOD0 2,336 (incl. 0 shared FX) <= 6,000; LOD1 816; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 35% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.05 in [-0.2, 0.06]; x 22.68 m in [14, 24], z 11.45 m in [9, 13]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (MesaArch_Impostor, MesaArch_Mat)

### RopeBridge
- `GATE: SHAPE_MATCH PASS` vs targets/RopeBridge.jpg: posts, sagging plank deck, two hand-lines, hangers
- `GATE: TRIS PASS` LOD0 3,968 (incl. 0 shared FX) <= 5,000; LOD1 1,004; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 25% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; posts rise above, deck sags below the anchor (z -1.09..+1.35); x 16.24 m in [15, 17]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (RopeBridge_Impostor, RopeBridge_Mat)

### StepTemple
- `GATE: SHAPE_MATCH PASS` vs targets/StepTemple.jpg: tiers, centre stair, shrine; target stone is darker and mossier (in-game AO/shader will darken)
- `GATE: TRIS PASS` LOD0 5,200 (incl. 0 shared FX) <= 8,000; LOD1 1,340; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 26% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; x 23.14 m in [14, 26], z 15.85 m in [10, 18]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (StepTemple_Impostor, StepTemple_Mat)

### StiltHut
- `GATE: SHAPE_MATCH PASS` vs targets/StiltHut.jpg: layered conical thatch, hut on railed deck, braced stilts, ladder, pier
- `GATE: TRIS PASS` LOD0 1,616 (incl. 0 shared FX) <= 6,000; LOD1 778; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 48% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -1.50..+7.70); z 9.20 m in [7, 10]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (StiltHut_Impostor, StiltHut_Mat)

### StoneGate
- `GATE: SHAPE_MATCH PASS` vs targets/StoneGate.jpg: two carved pillars with tiki faces + lintel + vines (brief: carved stone gate); the tee target only shows one tall totem pillar edge-on, with more stacked faces
- `GATE: TRIS PASS` LOD0 3,056 (incl. 0 shared FX) <= 6,000; LOD1 1,008; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 33% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 6.32 m in [4.5, 6.5]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (StoneGate_Impostor, StoneGate_Mat)

### WaterTower
- `GATE: SHAPE_MATCH PASS` vs targets/WaterTower.jpg: barrel tank with hoops, conical roof, trestle, ladder
- `GATE: TRIS PASS` LOD0 2,096 (incl. 0 shared FX) <= 5,000; LOD1 1,200; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 57% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.00 in [-0.06, 0.06]; z 9.45 m in [8, 11]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (WaterTower_Impostor, WaterTower_Mat)

### Waterwheel
- `GATE: SHAPE_MATCH PASS` brief-only: brief-only (no ref view shows it): mill house, separate wheel, chute
- `GATE: TRIS PASS` LOD0 1,496 (incl. 0 shared FX) <= 5,000; LOD1 660; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 44% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.15 in [-0.3, 0.06]; z 4.82 m in [4, 6]
- `GATE: CLEAN PASS` 5 meshes (4 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (Waterwheel_Impostor, Waterwheel_Mat)

### Windmill
- `GATE: SHAPE_MATCH PASS` vs targets/Windmill.jpg: brick base, red octagon body, white trims, gallery, dark cap, 4 lattice sails (separate part)
- `GATE: TRIS PASS` LOD0 2,348 (incl. 0 shared FX) <= 8,000; LOD1 618; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 26% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 23.41 m in [15, 26]
- `GATE: CLEAN PASS` 5 meshes (4 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (Windmill_Impostor, Windmill_Mat)

### WitchCottage
- `GATE: SHAPE_MATCH PASS` vs targets/WitchCottage.jpg: crooked stone + timber body, tall leaning purple roof, cauldron chimney with glow, smoke; target is more crooked
- `GATE: TRIS PASS` LOD0 2,382 (incl. 8 shared FX) <= 8,000; LOD1 860; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 36% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 14.52 m in [9, 16]
- `GATE: CLEAN PASS` 4 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (WitchCottage_FX, WitchCottage_Impostor, WitchCottage_Mat)

### BasaltSpire
- `GATE: SHAPE_MATCH PASS` vs targets/BasaltSpire.jpg: ridged bullet spire with glowing trough seams + hex column ring
- `GATE: TRIS PASS` LOD0 1,018 (incl. 0 shared FX) <= 5,000; LOD1 418; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 41% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 19.10 m in [16, 22]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (BasaltSpire_Impostor, BasaltSpire_Mat)

### CalderaWall_A
- `GATE: SHAPE_MATCH PASS` vs targets/CalderaWall.jpg: dark fluted caldera cliff, glowing lava line, lava-fall channel + card; target walls are more stepped
- `GATE: TRIS PASS` LOD0 1,794 (incl. 0 shared FX) <= 8,000; LOD1 638; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 36% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -3.00 in [-3.1, -2.9]; z 48.29 m in [36, 52]
- `GATE: CLEAN PASS` 5 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: TILE PASS` CalderaWall_A_LOD0: ends 38/38 verts, worst 0.0 mm; CalderaWall_A_LOD1: ends 22/22 verts, worst 0.0 mm
- `GATE: MATERIALS PASS` 1 body material (CalderaWall_A_FX, CalderaWall_A_Impostor, CalderaWall_A_Mat)

### CalderaWall_B
- `GATE: SHAPE_MATCH PASS` vs targets/CalderaWall.jpg: plain segment of the same ring
- `GATE: TRIS PASS` LOD0 1,786 (incl. 0 shared FX) <= 8,000; LOD1 630; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 35% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -3.00 in [-3.1, -2.9]; z 50.48 m in [36, 52]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: TILE PASS` CalderaWall_B_LOD0: ends 38/38 verts, worst 0.0 mm; CalderaWall_B_LOD1: ends 22/22 verts, worst 0.0 mm
- `GATE: MATERIALS PASS` 1 body material (CalderaWall_B_Impostor, CalderaWall_B_Mat)

### ObsidianArch
- `GATE: SHAPE_MATCH PASS` vs targets/ObsidianArch.jpg: chunky black arch, ember crack lines, boulder feet, glowing base seam
- `GATE: TRIS PASS` LOD0 1,104 (incl. 0 shared FX) <= 6,000; LOD1 368; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 33% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.13 in [-0.2, 0.06]; x 16.15 m in [10, 17], z 8.62 m in [6, 9]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (ObsidianArch_Impostor, ObsidianArch_Mat)

### RangerHut
- `GATE: SHAPE_MATCH PASS` vs targets/RangerHut.jpg: plank hut, layered thatch, porch posts, glowing window, lava-glass sign; target thatch is shaggier palm-leaf
- `GATE: TRIS PASS` LOD0 918 (incl. 0 shared FX) <= 6,000; LOD1 330; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 36% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z -0.00 in [-0.06, 0.06]; z 5.20 m in [3.8, 5.5]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (RangerHut_Impostor, RangerHut_Mat)

### StoneLantern
- `GATE: SHAPE_MATCH PASS` vs targets/StoneLantern.jpg: hex base, post, glowing light box, wide roof, finial
- `GATE: TRIS PASS` LOD0 794 (incl. 0 shared FX) <= 2,000; LOD1 410; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 52% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 2.17 m in [1.6, 2.4]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (StoneLantern_Impostor, StoneLantern_Mat)

### ToriiGate
- `GATE: SHAPE_MATCH PASS` brief-only: brief-only (no ref view shows the h10 tee gate): basalt torii, curved kasagi, nuki, ember plaque
- `GATE: TRIS PASS` LOD0 868 (incl. 0 shared FX) <= 4,000; LOD1 428; LOD2 4
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 49% of LOD0 (band 25%-60%); LOD2 impostor cross-card present
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; min z +0.00 in [-0.06, 0.06]; z 6.17 m in [5.5, 7.5]
- `GATE: CLEAN PASS` 3 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (ToriiGate_Impostor, ToriiGate_Mat)

### CliffSkirt
- `GATE: SHAPE_MATCH PASS` vs targets/RockShelf.jpg: grass cap, cream limestone face, dark wet foot, boulders
- `GATE: TRIS PASS` LOD0 4,542 (incl. 0 shared FX) <= 5,000; LOD1 1,404; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 31% of LOD0 (band 25%-60%); no LOD2 by design: flat ground strip: LOD1 to the end of its cull range, then the island bevel + shore shader
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -2.40..+5.65); z 8.05 m in [6, 8.5]
- `GATE: CLEAN PASS` 2 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: TILE PASS` CliffSkirt_LOD0: ends 70/70 verts, worst 0.0 mm; CliffSkirt_LOD1: ends 40/40 verts, worst 0.0 mm
- `GATE: MATERIALS PASS` 1 body material (CliffSkirt_Mat)

### FoamRing
- `GATE: SHAPE_MATCH PASS` vs targets/FoamRing.jpg: annulus foam card (look comes from the shore shader texture)
- `GATE: TRIS PASS` LOD0 192 (incl. 0 shared FX) <= 1,000; LOD1 96; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 50% of LOD0 (band 25%-60%); no LOD2 by design: flat FX card on the water; UV0.y runs along it for scrolling foam
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; centre pivot; x 68.66 m in [66, 70]
- `GATE: CLEAN PASS` 2 meshes (0 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 0 body material (FoamRing_FX)

### FoamStrip
- `GATE: SHAPE_MATCH PASS` vs targets/ShoreBand.jpg: foam card following the ShoreBand waterline
- `GATE: TRIS PASS` LOD0 96 (incl. 0 shared FX) <= 1,000; LOD1 48; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 50% of LOD0 (band 25%-60%); no LOD2 by design: flat FX card on the water; UV0.y runs along it for scrolling foam
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z +0.03..+0.03); x 20.31 m in [19.9, 20.5]
- `GATE: CLEAN PASS` 2 meshes (0 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 0 body material (FoamStrip_FX)

### RockShelf
- `GATE: SHAPE_MATCH PASS` vs targets/RockShelf.jpg: low limestone shelf with three tide pools, moss and anemone dots
- `GATE: TRIS PASS` LOD0 3,354 (incl. 0 shared FX) <= 5,000; LOD1 1,050; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 31% of LOD0 (band 25%-60%); no LOD2 by design: flat ground strip: LOD1 to the end of its cull range, then the island bevel + shore shader
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -1.60..+0.43); x 12.00 m in [11.5, 12.5]
- `GATE: CLEAN PASS` 2 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: MATERIALS PASS` 1 body material (RockShelf_Mat)

### ShoreBand
- `GATE: SHAPE_MATCH PASS` vs targets/ShoreBand.jpg: grass lip -> sand -> wet sand -> shallows, wavy, tiles
- `GATE: TRIS PASS` LOD0 2,466 (incl. 0 shared FX) <= 4,000; LOD1 820; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 33% of LOD0 (band 25%-60%); no LOD2 by design: flat ground strip: LOD1 to the end of its cull range, then the island bevel + shore shader
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -1.80..+0.77); x 20.00 m in [19.9, 20.1]
- `GATE: CLEAN PASS` 2 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: TILE PASS` ShoreBand_LOD0: ends 42/42 verts, worst 0.0 mm; ShoreBand_LOD1: ends 24/24 verts, worst 0.0 mm
- `GATE: MATERIALS PASS` 1 body material (ShoreBand_Mat)

### ShoreBand_Arc
- `GATE: SHAPE_MATCH PASS` vs targets/FoamRing.jpg: same profile on a 10-tile ring
- `GATE: TRIS PASS` LOD0 2,466 (incl. 0 shared FX) <= 4,000; LOD1 820; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 33% of LOD0 (band 25%-60%); no LOD2 by design: flat ground strip: LOD1 to the end of its cull range, then the island bevel + shore shader
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -1.80..+0.77); z 2.57 m in [2.4, 2.7]
- `GATE: CLEAN PASS` 2 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: TILE PASS` ShoreBand_Arc_LOD0: ends 42/42 verts, worst 0.0 mm; ShoreBand_Arc_LOD1: ends 24/24 verts, worst 0.0 mm
- `GATE: MATERIALS PASS` 1 body material (ShoreBand_Arc_Mat)

### BlackSandShore
- `GATE: SHAPE_MATCH PASS` vs targets/BlackSandShore.jpg: black sand with glowing tide line
- `GATE: TRIS PASS` LOD0 2,466 (incl. 0 shared FX) <= 4,000; LOD1 820; LOD2 0
- `GATE: LOD PASS` LOD0+LOD1 present, LOD1 = 33% of LOD0 (band 25%-60%); no LOD2 by design: flat ground strip: LOD1 to the end of its cull range, then the island bevel + shore shader
- `GATE: PIVOT_SCALE PASS` root at origin, scale 1: True; all objects scale 1 / no rotation: True; static meshes at origin: True; pivot inside footprint: True; spans sea level (z -1.80..+0.77); x 20.00 m in [19.9, 20.1]
- `GATE: CLEAN PASS` 2 meshes (2 closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, loose, wire, degenerate): all 0
- `GATE: TILE PASS` BlackSandShore_LOD0: ends 42/42 verts, worst 0.0 mm; BlackSandShore_LOD1: ends 24/24 verts, worst 0.0 mm
- `GATE: MATERIALS PASS` 1 body material (BlackSandShore_Mat)
