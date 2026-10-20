# AUDIT — venue presence (sky, volcano, resort note)

Written 2026-10-02, before any venue code was changed. Scope: `Skyscraper` (SKY OPEN), `Volcano` (MAGMA OPEN), a short resort note.
Shots cited are in `ArtDir/screenshots/venues/` unless a path is given.

## 0. How this audit was made, and why "before" is trustworthy

* Looked at every shot the brief names plus the drone frames, side and below views (all of `skyscraper_*`, `volcano_*`, `resort_1/2/6`).
* Read `TennisVenue.cs`, `TennisVenueBuilder.cs` (all of `Skyscraper` and `Volcano`), `TennisVenueFx.cs`, `TennisVenueCapture.cs`, the FX shaders, `TennisQuality`, the post profile, `TennisGame.Start` and the presentation cameras.
* Re-ran the existing capture path on the unchanged code into `work/venue-presence/proof/baseline/`. Mean absolute difference from the shipped frames is 0.18-0.84 / 255 (sky) and 1.47-1.64 / 255 (volcano), i.e. particles and drift only. **The shipped captures are what the code produces today**, so they are the "old shot" in the comparison sheets.
* Numbers below come from `work/venue-presence/tools/measure_shots.py` (pixel metrics) and from `HERO_VENUE_DUMP=1` on the capture tool (kit props, triangle counts). Both are read-only.
* The sky code in the working tree includes the neighbouring towers and horizon cloud banks that another session added and has not committed. They are part of "before"; a copy of the pre-change files is in `work/venue-presence/before_code/` (SHA-256 in `SHA256.txt`).

Camera facts that decide what is visible (they drive the plan):

* Gameplay camera sits at (0, 3.5, -15.6) looking at +z, pitched about -10.7 deg, fov 56. The deck's far edge is 37 m away and 3.5 m below the eye, so **everything steeper than 5.4 deg below the horizon is hidden by the deck**. A cloud layer at depth D below the deck can only be seen beyond (D+3.5)/tan(5.4 deg) = 10.6 x (D+3.5) m.
* Other cameras that show the venue: the drone flyover (`TennisVenue.Drone`), rival intro (looks toward +z from z~6), player intro (looks toward -z), replay cameras at deck height. So **both ends of the deck and the whole horizon matter, not just the +z view**.
* Only 1-2 pixel lights run on device (`TennisQuality`: PixelLights 2 High, 1 Standard/Low). **New real lights are not an option**; "lava light" has to be emission, glow cards and baked gradients. Bloom threshold is 1.05 with ACES, so HDR emission above ~1 blooms.

---

## 1. Skyscraper (SKY OPEN)

### What reads
* `skyscraper_2_postcard.png`: the teal deck on its pale stone coping is instantly legible; two framing towers plus a centre tower and the antenna mast give "rooftop among towers". The open edge with no rail reads as exposed. Keep this composition.
* `skyscraper_3_drone0.png`, `_drone2.png`: the green deck on a lone pencil shaft over the cloud is the hook. It is the one place height really reads, and only from above.

### What is flat (the brief's list, confirmed, with causes)
1. **Towers share one texture. Confirmed.** The whole venue uses three facade textures: `glass` (main shaft), `facade` (all 14 neighbours) and `win` (380 city boxes). Every visible neighbour is the same blue 4 x 4 grid, built from the same recipe: three stacked boxes at 1 / .78 / .49 of the width, plus optional needle (`City()`, `neighbours[]`). Only width and roof height differ, so the left and right framing towers in `skyscraper_2_postcard.png` are near twins. No tower has a different material, a round or slanted form, a crown or a bridge. The "window variation" is a hash on a texture that repeats every 4 columns, so it reads as a tile.
2. **Clouds are flat puffs. Confirmed.** `Puff`/`HorizonClouds`/`Wisps` are camera-facing alpha sprites with a lumpy cut-out outline, uniformly lit. In `skyscraper_2_postcard.png` (top) and `skyscraper_4_side.png` they read as stickers: identical outline, no lit side or shadow side, no parallax as the camera moves.
3. **The city is a distant noise plane. Confirmed, and the cause is geometric.** The "cloud sea" is four 9000 m alpha quads at -388...-348 m plus 150 puffs. By the 5.4 deg rule above they are only visible beyond 3.7-4.2 km, deep inside fog (starts 900 m), so from gameplay they collapse into a ~100 px beige band at the horizon (`skyscraper_1_gameplay.png`, rows ~345-447). From above (`skyscraper_3_drone0.png`, `_drone2.png`) the sheets are transparent, so tower shafts show through them with no depth and the sea looks like smeared peach. The 380 "city" boxes (7,230 tris) poke out as pale flat stumps with a dark-blue speckle texture (`skyscraper_6_edge.png`, left).
4. **The peach sky does not sell height. Confirmed.** `Skyscraper.Sky` is a three-stop gradient (peach horizon, lavender, blue) plus a soft glow: the default sunset. Nothing authored: no bands, no big shapes (`skyscraper_5_below.png`). Nothing in a gameplay frame says "high": no near cloud, no downward view, no landmark.
5. **The drop is a beige horizon, not a cloud sea. Confirmed** (items 3 and 4).

### Reused resort props
From the kit dump (all positions in deck coordinates; the deck is x +-12.6, z +-21.6; the court apron is x +-10, z +-19.5, so these stand on the stone margin):

| prop | count | where | triangles |
|---|---|---|---|
| garden lantern (TropicalV3_033) | 8 | x = +-10.8, z = -17, -8, 8, 18 | 49,720 |
| courtside bench, i.e. the sofas (TropicalV3_020) | 6 | x = +11.6 (z = -13, -5, 6, 15); x = -11.7 (z = -14, 18) | 32,724 |
| ceramic planter with plant (TropicalV3_017) | 4 | x = +11.0, z = -14.8, -6.8, 4.2, 13.2 | 25,784 |

These 18 props are **108,228 of the venue's 138,607 kit triangles (78%)**. `skyscraper_6_edge.png` shows a cushioned sofa with a shadow on a roof edge and `skyscraper_2_postcard.png` shows the lamps and plants in rows: this is the beach club terrace, not a rooftop. The umpire chair (5,815 tris), net (24,228), posts, lines and run-off apron are tennis kit, not resort dressing, and stay.

### What fights the ball
* Ball felt measures hue 67 deg, S .65, V .69-.92 in the three gameplay shots. Sky horizon band behind the court: **median ball-to-background contrast 1.47:1; 82.8% of the central band is under 1.5:1 and 91.2% under 2:1** (`skyscraper_1_gameplay.png`, same in the postcard). A lob that rises above the far baseline sits at the same brightness as the haze. For comparison the resort measures 1.35:1 and the volcano 7.05:1.
* Pale cloud sprites at the horizon add bright flat shapes in exactly the lob band.

### Cost (disclosed)
Venue-owned: **12,164 triangles** in 225 mesh renderers (+1,352 particle-cap tris). The real cost is overdraw: four screen-filling alpha sheets and ~196 alpha sprites. Kit 138,607 tris (108k of it resort props above).

---

## 2. Volcano (MAGMA OPEN)

### What reads
* `volcano_2_postcard.png`: obsidian slab with a glowing edge against fire is a strong silhouette. Lines and ball read cleanly on black: **median ball contrast 7.05:1; only 2.1% of the lob band is under 2:1; sulfur-yellow pixels (hue 38-62) 0.00%** (`volcano_1_gameplay.png`). The lava lake and lava streak language are bold. Keep the slab-on-lava idea and the contrast.

### What is flat or wrong (the brief's list, confirmed, with causes)
1. **Lava is wallpaper on the crater wall. Confirmed, and it is a UV bug.** `TerrainRing` maps `v = r / 90 m`, radial distance in plan. The wall climbs 16 m in 13 m of radius at its foot and 76 m over 180 m overall, so the texture is stretched vertically. Measured texture correlation length on the wall: **6 px vertical vs 2 px horizontal (3.0 : 1)** in `volcano_2_postcard.png` and `volcano_1_gameplay.png`; the resort's stone wall measures 0.5 : 1. The `rivers` texture adds 30 evenly spaced thin lines, and the sulfur blobs repeat. The result is the curtain/fur look. The 240 "boulders" are sphere primitives (768 tris each, one texture) stuck to the wall; they read as dark clumps.
2. **Nothing between the slab and the wall.** The lake is 246 m across; the nearest rock is more than 120 m from the deck. From gameplay the lake is never visible (it would need distance > 524 m), and the wall is only seen above about -9 m. No near layer, no mid layer, no parallax; the court floats in an empty room.
3. **The court is a flat black slab. Confirmed.** Deck (.075,.07,.078) and run-off (.04,.04,.048) are both near-black with no surface. Foreground deck measures mean RGB (.124,.116,.138), luminance std .045. The "Slab glow" point light sits at y = -9 and lights the underside; the "Lava up-light" is a directional light pointing up, which lights faces that look down. Nothing lights the top: warmth (R-B) is +0.003 25 px inside the seam against -0.036 mid-deck. Light stops at the 0.34 m seam. **The crater does not light the court. Confirmed.**
4. **The slab is a bare plank.** `Underside()` (rock keel) exists but is never called, so `volcano_5_below.png` shows a flat grey underside under a red sky.
5. **The sky is a red gradient. Confirmed.** Three-stop gradient, three ash sheets, 40 flat ash sprites (`volcano_5_below.png`, top strip of `volcano_1_gameplay.png`). The eruption plume vent is at (0, -44, 105), behind the near wall from the gameplay camera, and does not appear in `volcano_1_gameplay.png` or `volcano_2_postcard.png`.

### Reused resort props
Same 8 lanterns, 6 sofas, 4 plants at the same positions as the sky (108,228 tris). `volcano_6_edge.png` is the clearest leak: a cushioned sofa and a mid-century lantern with a white glass lamp sitting on molten edge lighting. Living plants on an obsidian slab. The four brazier bowls at the corners are volcano-specific and fine.

### What fights the ball
Currently nothing (numbers above). **The risk is the redesign**: new lava glow must not climb into the lob band behind the far baseline. Proof gate below keeps it measured.

### Cost (disclosed)
Dump corrected for static batching (the first dump counted every boulder's batch mesh, 22M, wrongly):

| group | triangles |
|---|---|
| Trees (420 EnvV4 toy trees, 623 renderers) | **1,327,160** |
| Boulders (240 x 768) | 184,320 |
| Volcano cone (288 x ~100 rings) | 49,536 |
| Grassland / rocky ground | 16,400 / 10,000 |
| everything else (lake, seams, braziers, sky dome...) | ~4,000 |
| **venue-owned total** | **~1.59 M** (+6,512 particle-cap tris, 9 active lights) |

**The trees (83% of the volcano) stand on grassland 780-1500 m away behind a 58 m rim. No shipped camera sees them**: gameplay, postcard, drone (it starts inside the crater looking down and stays below the rim line), intros and replays are all inside the bowl. They are cost with no pixels, and 9 active lights is far over the 1-2 pixel lights the device runs.

---

## 3. Resort note (TROPICAL OPEN) — not rebuilt

* **What reads**: a complete layered world (`resort_2_postcard.png`): palms near, stands and clubhouse mid, sea and rock far; painted cumulus sky; textured terrace. This is the quality bar the other two maps are measured against, and the home of the kit props.
* **What is flat**: the ocean-teal run-off apron is a large untextured plane (left and bottom of `resort_2_postcard.png`); the sea beyond the rail is a flat band; the sofas and lamps are right at home here.
* **Reused prop**: nothing, it is the source.
* **Fights the ball**: horizon band 1.35:1 (like the sky map); pre-existing, not touched.
* **Decision**: no resort change in this pass. The only candidate small fix would be value variation on the run-off apron, and it is not needed for any gate.

---

## 4. Summary: defect, evidence, where the plan answers it

| # | defect | evidence | plan |
|---|---|---|---|
| S1 | one facade look, twin towers | 1 material for 14 neighbours | PLAN S2 tower family |
| S2 | sprite clouds | stickers in postcard/side | PLAN S1 3D cloud sea + lumps |
| S3 | cloud sea unseen from play | 5.4 deg rule, sliver at horizon | PLAN S1 sea surface raised, lumps at deck level |
| S4 | sky = default sunset, ball camouflage | 1.47:1, 91% < 2:1 | PLAN S3 banded sky |
| S5 | beach-club props | 18 props, 108k tris | PLAN S4 hide and replace |
| V1 | wallpaper wall | 3.0 : 1 stretch, UV bug | PLAN V1 arc-length UV, terraces |
| V2 | empty near/mid layers | nearest rock > 120 m | PLAN V2 basalt islands |
| V3 | dead slab, no lava light on top | warmth +0.003 vs -0.036 | PLAN V3 glow rim, pylons |
| V4 | bare underside | `Underside()` unused | PLAN V3 keel |
| V5 | red-gradient sky, plume hidden | 3-stop gradient | PLAN V4 |
| V6 | resort props | same 18 props | PLAN V5 |
| V7 | 1.33M invisible tris, 9 lights | dump | PLAN V6 cut + budget |
