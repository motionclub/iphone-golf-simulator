# Majestic landmark kit (PLAN 4.1 "L")

Blender-built, Unity-ready FBX landmarks, hole set pieces and shore kit for the golf courses of `work/majestic-all-maps/PLAN.md`, matched to the hole targets in `work/majestic-all-maps/refs/holes/` (crops in `targets/`, positions from `design/HOLE_BRIEFS.md`). **Not installed into Unity**: the golf track places them.

Gates: [GATE_RESULTS.md](GATE_RESULTS.md) — **GATE: LANDMARK_KIT PASS** (34 assets: SHAPE_MATCH, TRIS, LOD, PIVOT_SCALE, CLEAN, TILE, MATERIALS). Overview: `sheets/_overview.jpg`; one 1920x1080 sheet per asset in `sheets/<Name>.jpg` (target crop | matching-angle render | facts + gates, then a 4-view turntable, LOD1 and LOD2).

## Rebuild (headless, through the heavy-job gate)

```bash
cd work/majestic-landmarks
bash ../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python scripts/build.py -- [Name ...]
python3 scripts/gates.py && python3 scripts/readme.py   # GATE_RESULTS.md, README table, overview
```

The whole kit builds, renders, exports and re-imports in about 2 minutes (one Blender process, ~3 s per asset). `scripts/crop_targets.py` re-cuts the target crops listed in `scripts/targets.json`; `scripts/sheets.py` and `scripts/review.py` make the sheets.

| file | does |
|---|---|
| `scripts/kit.py` | builder library: closed-shell primitives (box, lathe, sweep, prism, heightfield slab, noise blob), bevels, per-face or per-vertex colour, glow, LOD quality, finishing (triangulate, weighted normals on hard parts) |
| `scripts/assets_landmarks.py` | Lighthouse, StepTemple, TwinFallsIsle, CalderaVolcano, CalderaWall_A/B |
| `scripts/assets_setpieces.py` | the hole set pieces |
| `scripts/assets_shore.py` | shore kit |
| `scripts/build.py` | per asset: LOD0 + LOD1 build, impostor atlas, renders, FBX export, re-import, metrics (`proof/metrics/<Name>.json`) |
| `scripts/gates.py` | binary gates -> `GATE_RESULTS.md`, `proof/gates.json` |

## Conventions (read before placing)

- **Units / axes:** metres, FBX scale 1 (`apply_scale_options=FBX_SCALE_ALL`, `-Z forward, Y up`, `bake_space_transform`), so every object imports with identity rotation and scale. Blender +Z up -> Unity +Y. Each asset's **front faces Blender -Y**, which lands on Unity +Z (the racket mapping Unity (x, y, z) = Blender (-x, z, -y)); turn the root to face the tee.
- **Hierarchy:** root empty `<Name>` at the pivot -> `<Name>_LOD0`, `<Name>_LOD1`, `<Name>_LOD2` (impostor) and separate parts `<Name>_<Part>_LOD0/1`. Unity's `_LODn` suffix import builds the LODGroup. FX listed as *shared* (`Lighthouse_Beam`, `CalderaVolcano_Plume`, chimney `Smoke`) have no suffix and stay visible at every distance.
- **One material per asset** (`<Name>_Mat`), made for chat 9's `GolfArcade/MajesticDressing` shader: vertex colour = albedo (sRGB in the FBX), UV0 = (sway, phase) = 0, UV1 = 0, **UV2.x = glow** (lava, lit windows, lantern glass, crater). FX cards use `<Name>_FX` (needs a transparent, double-sided, UV0.y-scrolling shader: falls, lava fall, plume, smoke, beam, foam; alpha is in vertex colour A). The impostor uses `<Name>_Impostor` (alpha-clip, double-sided) with `fbx/<Name>_Impostor.png` (front + side views in one atlas).
- **LODs:** LOD1 is rebuilt from the same recipe at lower segment counts with chamfers instead of round bevels and small details dropped (25–60 % of LOD0). LOD2 is a cross of two cards (4 tris). Flat shore pieces have no LOD2 by design.
- **Pivots:** base centre on the ground (z 0) unless the table says *waterline* (z 0 = sea level, land +Y, sea -Y), *anchor* (rope bridge) or *centre*. Animated parts sit at their own pivot: `Windmill_Sails` at the hub (spin about local Y = Unity Z), `Waterwheel_Wheel` at the hub (local X), `Lighthouse_Beam` at the lantern (local Z = Unity Y).
- **Tiling:** ShoreBand / BlackSandShore / CliffSkirt / FoamStrip repeat every 20 m along X; ShoreBand_Arc: 10 tiles of 36 deg close a ring of radius 31.8 m (centre at local (0, 31.8, 0)); CalderaWall_A/B: 24 segments of 15 deg close a ring of radius 200 m (centre at local (0, -200, 0)); TILE gate = cut-end vertices identical (0 mm).

## Assets

| asset | course | holes | LOD0 / LOD1 / LOD2 tris | materials | size x·y·z (m) | pivot | intended position (brief) |
|---|---|---|---|---|---|---|---|
| **Lighthouse** | A | 7, 8, 9, 12, 15 | 3,742 (incl. 12 shared FX) / 1,414 / 4 | FX, Impostor, Mat | 18.8·15.6·20.3 | base | Cliffside course landmark on a headland, seen from every tee (h07 FWD beyond-right of the green; h08 far R; h12 on the island green; h15 R across the bay). Brief chat 9 rule: one landmark visible from every tee.; separate: Beam (lantern centre, spin about local Z (Unity Y)) |
| **TwinFallsIsle** | B | 13, 14, 17, 18, 19, 20 | 9,288 / 2,840 / 4 | FX, Impostor, Mat | 99.6·102.5·71.4 | base | Wild Isles course landmark: high central isle with a ruined stepped temple on top and twin waterfalls; on h19 FWD behind the green, in the distance from 13/14/17/18/20 (brief: a misty glow marks it). LOD2 impostor for the far views. |
| **CalderaVolcano** | C | 10, 16, 21, 22, 23 | 2,780 (incl. 16 shared FX) / 1,500 / 4 | FX, Impostor, Mat | 288.0·288.0·144.9 | base | Magma Open course landmark: the great caldera volcano with a glowing crater and a slow plume, visible from every hole; h16 sits right under it (looms large), h10/h21-23 see it beyond the green / caldera wall.; separate: Plume (crater centre; scroll/billow UV0.y, sway) |
| **Balustrade** | A | 8, 15 | 1,484 / 572 / 4 | Impostor, Mat | 3.1·0.7·1.5 | base | h15 BACK: tee platform with a stone balustrade and planters (both sides of the tee); also h08 tee terrace. Tiles every 3 m along X; the post sits at the -X end, so close a run with one extra post (scale X of this segment to 0.15 for a lone post). |
| **Planter** | A | 8, 15 | 2,428 / 650 / 4 | Impostor, Mat | 1.6·1.6·1.7 | base | h15 BACK: planters on the tee balustrade posts / at its ends (h15 tee: flower urns left and right). |
| **StoneGazebo** | A | 8, 15 | 4,702 / 1,898 / 4 | Impostor, Mat | 7.0·7.0·7.8 | base | h08 BACK: the tee terrace with a stone gazebo (end of the knife-edge path); h15 FWD: the little temple-gazebo on the three-tier island green. |
| **AlpineChalet** | B | 17 | 3,124 (incl. 8 shared FX) / 1,036 / 4 | FX, Impostor, Mat | 14.8·11.3·8.0 | base | h17 FWD: green beyond the frozen lake, an alpine chalet with smoke (left of the green, below the fjord walls).; separate: Smoke (chimney top; scroll UV0.y) |
| **CanalBridge** | B | 20 | 1,192 / 476 / 4 | Impostor, Mat | 12.5·3.4·5.6 | waterline | h20 set piece: canals with small brick bridges (R of the line beyond the canal lock; tee BACK by the farmhouse). |
| **Farmhouse** | B | 20 | 2,456 / 684 / 4 | Impostor, Mat | 8.2·8.9·8.5 | base | h20 BACK: red-brick farmhouse and a canal lock by the tee (left of the tee view). |
| **IceFishingHut** | B | 17 | 1,100 / 444 / 4 | Impostor, Mat | 3.6·3.9·3.8 | base | h17 off-line: snowdrifts, laden pines, an ice-fishing hut on the frozen lake (R of the line in the flyover). |
| **LookoutTower** | B | 13 | 2,226 / 1,186 / 4 | Impostor, Mat | 4.5·4.5·11.2 | base | h13 FWD: the summit green on the pine hill, a red-roofed lookout tower at the top (behind/above the green). |
| **MesaArch** | B | 18 | 2,336 / 816 / 4 | Impostor, Mat | 22.7·6.8·11.4 | base | h18 FWD: far red mesa with the green on top, a desert rock arch (on the mesa beyond/right of the green). |
| **RopeBridge** | B | 14, 18 | 3,968 / 1,004 / 4 | Impostor, Mat | 16.2·1.7·2.4 | anchor | h14 set piece: rope bridge over the root window; h18 set piece: rope bridge across the chasm. 16 m span along X; scale X for other spans (planks stretch). Pivot = mid-span at the anchor (post-foot) height; the deck sags below it. |
| **StepTemple** | B | 19 | 5,200 / 1,340 / 4 | Impostor, Mat | 23.1·24.3·15.8 | base | h19 FWD: the green sits under the stone temple, the twin falls behind (brief). Also the shrine of the TwinFallsIsle landmark. |
| **StiltHut** | B | 19 | 1,616 / 778 / 4 | Impostor, Mat | 7.8·10.2·9.2 | waterline | h19 R: jungle lagoon, stilt huts (L and R of the tee view over the water). Pivot at the waterline; stilts go 1.5 m below. |
| **StoneGate** | B | 19 | 3,056 / 1,008 / 4 | Impostor, Mat | 6.8·1.9·6.3 | base | h19 BACK: the jungle tee, palms, a carved stone gate (frames the tee; pillars seen at the edges of the tee view). |
| **WaterTower** | B | 18 | 2,096 / 1,200 / 4 | Impostor, Mat | 4.0·4.0·9.5 | base | h18 BACK: the tee mesa with a desert-ranch fence and a water tower (tee side, left). |
| **Waterwheel** | B | 13 | 1,496 / 660 / 4 | Impostor, Mat | 5.2·5.2·4.8 | base | h13 set piece: a waterwheel on a stream beside the winding road (L of the corridor in the flyover).; separate: Wheel (hub; spin about local X (Unity -X)) |
| **Windmill** | B | 20 | 2,348 / 618 / 4 | Impostor, Mat | 18.2·10.1·23.4 | base | h20 FWD: big Dutch windmill turning beside the green; a second, smaller copy (scale 0.6) on the far side of the tulip fields.; separate: Sails (hub; spin about local Y (Unity Z, the sails face -Y in Blender)) |
| **WitchCottage** | B | 14 | 2,382 (incl. 8 shared FX) / 860 / 4 | FX, Impostor, Mat | 12.3·10.8·14.5 | base | h14 FWD: the green sunk in the crater ringed by gnarled trees, a crooked witch's cottage with a glowing window and a cauldron chimney.; separate: Smoke (cauldron top; scroll UV0.y) |
| **BasaltSpire** | C | 22, 23 | 1,018 / 418 / 4 | Impostor, Mat | 10.5·10.5·19.1 | base | h22 FWD: the plateau green at the end of the winding black causeway, a basalt spire (beyond the green); h23 L lagoon islet spire. |
| **CalderaWall_A** | C | 21, 22, 23 | 1,794 / 638 / 4 | FX, Impostor, Mat | 59.0·29.0·48.3 | base | Caldera wall ring around the 21-23 lava lake: hides the lava-disc rim seam from green-back, off-line and flyover views (PLAN 4.2). 24 segments of 15 deg at radius 200 m close the ring; ring centre = local (0, -200, 0) Blender (Unity (0, 0, 200) before placement). Mix A (lava fall) and B (plain).; separate: LavaFall (UV0.y scroll) |
| **CalderaWall_B** | C | 21, 22, 23 | 1,786 / 630 / 4 | Impostor, Mat | 59.0·29.0·50.5 | base | Caldera wall ring around the 21-23 lava lake: hides the lava-disc rim seam from green-back, off-line and flyover views (PLAN 4.2). 24 segments of 15 deg at radius 200 m close the ring; ring centre = local (0, -200, 0) Blender (Unity (0, 0, 200) before placement). Mix A (lava fall) and B (plain). |
| **ObsidianArch** | C | 22 | 1,104 / 368 / 4 | Impostor, Mat | 16.2·5.5·8.6 | base | h22 BACK: the causeway's start with an obsidian archway (the tee view sees it on the left; frames green-back views). |
| **RangerHut** | C | 16 | 918 / 330 / 4 | Impostor, Mat | 7.5·6.4·5.2 | base | h16 BACK: tee ledge with a ranger hut and a lava-glass sign (left of the tee). |
| **StoneLantern** | C | 10, 16 | 794 / 410 / 4 | Impostor, Mat | 1.0·1.0·2.2 | base | h10 BACK: lanterns on the basalt tee shelf (pairs either side of the torii); reusable along the h16 rim path. |
| **ToriiGate** | C | 10 | 868 / 428 / 4 | Impostor, Mat | 7.6·1.2·6.2 | base | h10 BACK: the tee on a basalt shelf with a stone torii-style gate and lanterns (frames the tee; seen in green-back views). |
| **CliffSkirt** | A | 7, 8, 12, 15 | 4,542 / 1,404 / — | Mat | 20.0·9.0·8.0 | waterline | Z3 cliff edges with surf (h07 R cliff drop, h08 sea-stack bases, h12 tee cliff, h15 island rim): turf lip 5.5 m above the sea. Pair with FoamStrip at the foot. |
| **FoamRing** | A | 8, 9, 12, 15, 19 | 192 / 96 / — | FX | 68.7·68.7·0.0 | centre | Foam ring round island rims and sea stacks (h12 island, h08 stacks, h15). Pivot = ring centre at sea level; centre line radius 33.2 m (1.4 m outside the ShoreBand_Arc shoreline), 2.2 m wide, at z +0.03; scale XY for other islands. |
| **FoamStrip** | A | 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 20 | 96 / 48 / — | FX | 20.3·4.1·0.0 | waterline | Foam line for ShoreBand / CliffSkirt tiles: follows the ShoreBand waterline wiggle 1.2 m seaward, tiles every 20 m. |
| **RockShelf** | A | 8, 9, 12 | 3,354 / 1,050 / — | Mat | 12.0·8.0·2.0 | waterline | h08 off-line: rock shelves with tide pools at the sea-stack bases (both sides of the path); also h09/h12 shores. |
| **ShoreBand** | A | 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 20 | 2,466 / 820 / — | Mat | 20.0·12.0·2.6 | waterline | Z3 island rim on every sea hole with a sand edge (Cliffside lagoon/beaches h09/h12/h15, Wild Isles 13-20). Lays along the island edge, land +Y; tiles every 20 m. Pair with FoamStrip (same wiggle) and the shallows gradient of MajesticShore. |
| **ShoreBand_Arc** | A | 8, 9, 12, 15, 19 | 2,466 / 820 / — | Mat | 23.4·13.3·2.6 | waterline | Island rims of round islands (h12 island green, h15 three-tier island, h19 lagoon islets): 10 tiles of 36 deg close a ring of radius 31.8 m (centre = local (0, 31.8, 0)); scale XY uniformly for other islands. |
| **BlackSandShore** | C | 10, 16 | 2,466 / 820 / — | Mat | 20.0·12.0·2.6 | waterline | h10 off-line: black sand beach with glowing tide line; h16 lava-river banks to the sea. Same layout/tiling as ShoreBand. |

## Honest notes and open items

- SHAPE_MATCH is my read of each sheet against its feature checklist; Adnan's eye is final. Weakest matches: **TwinFallsIsle** (rounder, more regular outline than the craggy target), **MesaArch** (target is more massive), **WitchCottage** (target is more crooked), **StoneGate** (the h19 tee target shows a single tall totem pillar edge-on; the brief asks for a gate, so this is a two-pillar gate). **ToriiGate** and **Waterwheel** have no target view (brief only).
- Previews are Blender EEVEE with a flat course light; the in-game look depends on `MajesticDressing` + the course grade. Waterfalls, lava fall, plume and foam are plain cards until the Unity FX shader scrolls them.
- The expected-size ranges were written before building; after the first build I widened six of them where my guess had left out a part: Windmill sails (z to 26 m), WitchCottage chimney (16 m), IceFishingHut stovepipe (4 m), MesaArch/ObsidianArch boulder feet (x), CalderaWall skirt 3 m under the lava (pivot at lava level, z to 52 m), FoamRing/FoamStrip/ShoreBand_Arc/CliffSkirt bounds. The ranges in the recipes are the current ones.
- Scale: landmarks are built at plausible real sizes (lighthouse 20 m, volcano 288 m wide x 145 m, isle ~100 m x 71 m, caldera ring radius 200 m). The golf track should scale them uniformly to its course layout; the far ones (volcano, isle, walls) were sized for ~300–800 m viewing distance.
- Not done here (golf track): placement per `MajesticHoleKit`, LODGroup screen sizes, colliders, FX shaders, Unity import check.
