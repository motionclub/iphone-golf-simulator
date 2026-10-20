# POSTCARD_LOOK — visual checklist (for the vision reviewers)

The brief's gate lines that need EYES. Quotes are verbatim from `ArtDir/environments/14_POSTCARD_LOOK.txt`. The mesh / material /
UV preconditions are machine-gated by `blender/scripts/postcard_look_verify.py` (see `GATES.md`, cross-referenced as [gate]); a
Blender PASS never replaces a line here. "A Blender render is not a pass."

## The shots

"Proof. In-game screenshots, not Blender viewport grabs. Save them under ArtDir/screenshots/golf_postcards/look/."
"One tee view and one green view per hole, at the phone camera." "One close shot of Needle's arch, one of Split's scrub ridge,
one of Crater's lava meeting the basalt." Phone camera = `CameraRig.FrameAddress`, 900x1600, Play mode, Canvas off
(as `PostcardCameraStills.cs`). File names are the integrator's; suggested:

| id | shot | file (suggested) | look target |
|---|---|---|---|
| S1 | Needle tee view (ball on the tee, looking down the hole) | `hole08_tee.png` | refs/needle.jpg |
| S2 | Needle green view (approach / putt camera at the green) | `hole08_green.png` | refs/needle.jpg |
| S3 | Needle arch close shot | `hole08_arch.png` | refs/needle.jpg (arch, centre) |
| S4 | Split tee view | `hole09_tee.png` | refs/split.jpg |
| S5 | Split green view | `hole09_green.png` | refs/split.jpg |
| S6 | Split scrub ridge close shot | `hole09_ridge.png` | refs/split.jpg (left ridge) |
| S7 | Crater tee view | `hole10_tee.png` | refs/crater.jpg |
| S8 | Crater green view | `hole10_green.png` | refs/crater.jpg |
| S9 | Crater lava meeting the basalt close shot | `hole10_lava.png` | refs/crater.jpg + ArtDir/screenshots/venues/volcano_2_postcard.png |

The brief's GATE line counts six ("The six proof shots exist" = S1, S2, S4, S5, S7, S8); the three close shots are required by the
Proof section and by LOOK_CONTRACT §6 (nine files).

## How to review

* For every shot, answer EVERY item that lists that shot: `V<n> PASS|FAIL - <what you see, where in the frame>`.
* Not visible / cannot tell = FAIL for the item that needs it (say what blocks the view). No "mostly", no "better than before".
* Compare against the look target still and the before sheets (`ArtDir/screenshots/golf_postcards/sheet_hole08/09/10.jpg`:
  flat green bands, grey icosahedra, solid blue / orange planes). Quality bar: `ArtDir/screenshots/venues/resort_2_postcard.png`,
  `volcano_2_postcard.png`.
* The stills win on silhouette, colour blocks and landmarks, NOT on photo detail ("They do not win on photo detail.").

## Every shot (S1-S9)

**V1. "FAIL a shot that still shows a flat green ribbon, a faceted gray blob, a solid blue plane, or a solid orange plane."**
(also GATE: "none of them is a flat-color ribbon on a solid plane")
- PASS: grass shows texture at 2-20 yd (mottle, mow stripes, tufts); every rock shows chipped planes with lit and shaded relief and
  a stone albedo; water has a shallow-to-deep gradient and moving highlights; lava shows crust and glow.
- FAIL (any one): a band of one green with no visible texture; a grey low-poly rock with flat-shaded triangles (icosahedron look);
  a single-colour blue sea; a single-colour orange (or salmon) lava field. [NO_LEGACY_MATERIALS, ROCK_NOT_ICOSAHEDRON, UV_DENSITY]

**V2. "In the Game view, fairway, green, rough, cliff, and rock show an albedo and a normal. HoleView no longer forces _BaseColor only."**
- PASS: each of fairway, green, rough, cliff, rock that is in frame shows an image texture (variation that tiles, not noise from
  lighting alone) AND surface relief that changes with the light direction (normal map), at a sensible scale (grass blades / stone
  joints, not a giant blurred texture, not a tiny repeating grid).
- FAIL: any of them flat-coloured; texture visibly stretched or smeared (cliff walls with vertical streaks = planar UVs);
  an obvious repeating grid across the fairway. [LK_TEXTURED, LOOK_FILES, UV_DENSITY]

**V3. "Style. Switch Sports / Wii clarity, soft and readable on a phone. Not photoreal, not grim, not Roblox flat color."**
- PASS: clear colour blocks (emerald play surfaces vs darker rough vs rock vs water/lava), soft saturated palette, readable
  silhouettes at phone size; "A vine-covered stone arch, not a scanned ruin. Textured grass, not a photograph of grass."
- FAIL: photographic noise; dark muddy / grim grade; untextured toy-block surfaces.

**V4. "Painted sky, warm key, cool fill, rim, softer fog than the current 250–700 gray wash." / "The existing TennisPost stack, or the same settings, on the golf camera."**
- PASS: a painted sky panorama with clouds (Needle/Split bright blue + warm cumulus; Crater smoky orange-to-aubergine dusk); warm
  sunlight with cool shadow fill; gentle bloom on bright highlights and a light vignette; the horizon is not a grey wall.
- FAIL: flat gradient or grey-blue empty sky; grey fog wash eating the distance; harsh single-light look; no bloom/vignette at all.

**V5. "Smoothness stays low (about 0.1 to 0.15), except wet rock near water."**
- PASS: grass, sand, dry rock are matte (no plastic sheen); only rock at the waterline may glisten.
- FAIL: shiny / plastic grass or sand; mirror-like highlights on dry rock.

## Tee and green views (S1, S2, S4, S5, S7, S8)

**V6. "Fairway and green are textured and a little varied." / "Mow stripes, if you keep them, are in the fairway albedo."**
- PASS: fairway stripes run along the line of play (lengthwise, following the bends) and are soft; the green is finer and brighter
  than the fairway; both show gentle variation.
- FAIL: stripes as hard flat bands across the hole (the old MAT_FAIRWAY_STRIPE look); green and fairway the same flat tone.
  [GROUND_MATERIALS, UV_DENSITY]

**V7. "The green does not hover."** (KEEP section) and "One play height."
- PASS: green, fringe and fairway meet flush at one height; no visible step, gap or floating edge.
- FAIL: a visible lip, gap or shadow line under the green edge. [PLAY_SURFACE_GRID, PLAY_SURFACE_TOPS]

**V8. "Do not spawn them on the green in a way that hides the pin."** (S2, S5, S8)
- PASS: the flag and cup area are unobstructed; plants sit on the rough / pad edges.
- FAIL: a shrub, flower or tuft in front of or around the pin, or on the putting surface. [PROPS_OFF_PLAY]

**V9. "Ocean uses GolfArcade/TennisWater. No MAT_FOAM strip remains."** (S1, S2, S4, S5)
- PASS: turquoise near the islands to deep blue further out, swell normals, fresnel to the sky at grazing angles, sun sparkle;
  whitewater is broken, noisy foam hugging the island bases (GolfSurf), fading out to sea.
- FAIL: solid blue plane; a continuous white ribbon / strip of foam; foam floating away from the cliffs. [OCEAN_WATER, SURF_SHORE, NO_MAT_FOAM]

## Needle (hole 8) — S1, S2, S3

**V10. "Left pad: a pale stone path, shrubs, and purple flowers."** (S1)
- PASS: a pale flagstone path with grass in the joints reads as a path on the tee pad; rounded shrubs and clusters of PURPLE
  flowers along the pad edges.
- FAIL: no path; path reads as a grey strip or a decal floating above the grass; no purple. [NEEDLE_PATH, NEEDLE_FLOWERS_SHRUBS_TUFTS]

**V11. "A vine-covered stone arch on its own rock, beside the bunker, visual only. Masonry blocks and hanging vines. FAIL if it is still ROCK_LARGE icosahedra."** (S3; also visible in S1/S2)
- PASS: individual cut stone blocks with dark mortar gaps, round voussoir ring with a keystone, green vines hanging from the
  ring and piers; it stands on its own rock beside the green-pad bunker, silhouette like refs/needle.jpg.
- FAIL: lumpy grey icosahedra; one smooth stone shape with no block joints; no vines; floating above its rock. [NEEDLE_ARCH]

**V12. "A waterfall off the lower right pad, visual only. A sheet mesh plus whitewater at the bottom. It does not collide, it does not move, and it is not a platform."** (S1 or S2, whichever frames the green pad)
- PASS: reads as falling water: a white, streaked sheet leaving the pad edge, curving out and falling to the sea, with a patch
  of whitewater foam where it lands.
- FAIL: not visible in any shot; a solid white slab; a sheet hanging in the air away from the cliff; no foam at the foot.
  (No motion is required: "No animated lava, no flowing shaders".) [NEEDLE_WATERFALL]

**V13. "Dark stratified cliff texture on the terrain walls, hanging vines, a few sea stacks in the water. Whitewater comes from TennisWater, not a MAT_FOAM band."** (S1, S2)
- PASS: pad walls are dark layered rock (horizontal strata) with relief, vines hang over the lips; several tall textured sea
  stacks stand in the water between and behind the pads.
- FAIL: grey flat walls; no stacks, or stacks that are grey faceted blobs. [GROUND_MATERIALS, NEEDLE_CLIFF_SKIN, NEEDLE_WALL_VINES, NEEDLE_SEA_STACKS]

**V14. "Grass: short tuft meshes on the rough edges and around the pads, plus the shrubs and flowers."** (S1, S2)
- PASS: small 3D grass tufts break the edge between fairway and rough and along the pad lips (meshes, not flat cards).
- FAIL: bare edges; flat billboard cards; tufts on the fairway line. [NEEDLE_FLOWERS_SHRUBS_TUFTS, PROP_FACE_BUDGET]

## Split (hole 9) — S4, S5, S6

**V15. "Left ridge: olive dry scrub, rocks, and the ruined arch. FAIL if that ridge is still the same flat green as the fairway."** (S6; also S4)
- PASS: the ridge reads olive / khaki / dry-brown, clearly a different hue from the emerald ribbon, with scrub plants and rocks
  scattered on it (refs/split.jpg left island).
- FAIL: the ridge is the fairway green, or a flat single colour. [SPLIT_SCRUB_RIDGE, SPLIT_RIDGE_SCATTER]

**V16. "The ruin reads as broken stone masonry, visual only. Not a pile of 12-vertex rocks."** (S6, or whichever shot frames the north ridge)
- PASS: coursed cut blocks in broken walls of uneven height (a doorway / fallen arch), stone texture.
- FAIL: a pile of faceted rocks; a smooth wall. [SPLIT_RUIN]

**V17. "Right ribbon: manicured emerald fairway, sand bunkers reading as sand (albedo, not a flat disc), clifftop green."** (S4, S5)
- PASS: emerald striped fairway; bunkers show warm sand with soft ripples and a grass lip; the green sits on the clifftop.
- FAIL: bunkers as flat beige discs; fairway dull or flat. [GROUND_MATERIALS, LOOK_FILES]

**V18. "Shore is jagged rock with a normal map and TennisWater foam. FAIL if the shore is a smooth extruded wall in flat MAT_CLIFF gray."** (S4, S5, S6)
- PASS: rocky, broken cliff faces with relief along the channel and outer shore; foam at their feet.
- FAIL: a smooth straight grey wall. [SPLIT_SHORE_SKIN, SURF_SHORE]

**V19. "No second green."** (S5)
- PASS: exactly one green in view (refs/split.jpg's green).
- FAIL: any second green-looking disc or putting surface. [ONE_GREEN]

## Crater (hole 10) — S7, S8, S9

**V20. "Walls are columnar basalt with a normal and a crack mask."** (S7, S9)
- PASS: near-black hexagonal basalt columns, chipped edges, glowing orange cracks (refs/crater.jpg); reads as columns at phone size.
- FAIL: grey faceted blobs (the old icosahedron wall); a smooth dark wall with no columns. [CRATER_COLUMNS, ROCK_MATERIALS]

**V21. "Lava has a dark crust texture and emission, so it lights the nearby rock. Static."** (S9; also S8)
- PASS: dark crust plates with bright orange/yellow fissures; the basalt near the lava is visibly lit orange from below; bloom on
  the hottest cracks.
- FAIL: a solid orange (or salmon) plane; lava that does not light the rock; animated flow. [CRATER_LAVA, CRATER_LAVA_LIGHTS, NO_ANIMATION]

**V22. "Square tee pad, textured."** (S7)
- PASS: a square grass tee mat with texture, framed by dark stone (refs/crater.jpg lower left).
- FAIL: flat-colour tee. [CRATER_TEE_PAD]

**V23. "Plants along the grass shelf."** (S7, S8)
- PASS: agave / tufts / shrubs along the rim shelf edges.
- FAIL: a bare shelf. [CRATER_SHELF_PLANTS]

**V24. "Pillar sides drop into the lava and read as rock, not as a green disc floating on orange. Top stays at fairway height."** (S8, S9)
- PASS: from the green's grass rim, basalt sides drop all the way into the lava (refs/crater.jpg right); the green top is level
  with the fairway.
- FAIL: a green disc with a thin edge hovering over orange; no visible rock under the green. [CRATER_PILLAR, PLAY_SURFACE_GRID]

**V25. "A background cone and a little smoke card behind the bowl, visual only, non-colliding. No new hole."** (S7 or S8)
- PASS: a volcano cone silhouette rises above the far wall with a soft smoke plume (no hard card edges).
- FAIL: no cone; the cone hidden behind the walls; smoke reads as a flat rectangle. [CRATER_CONE_SMOKE]

## Summary lines (the GATE POSTCARD_LOOK rows that need these)

| GATE line (verbatim) | items |
|---|---|
| "In the Game view, fairway, green, rough, cliff, and rock show an albedo and a normal. HoleView no longer forces _BaseColor only." | V1, V2, V6 |
| "Ocean uses GolfArcade/TennisWater. No MAT_FOAM strip remains." | V9, V13, V18 |
| "No rock on holes 8–10 is a 12-vertex icosahedron. Crater walls read as columns. Crater lava is emissive and static." | V1, V13, V20, V21 |
| "Needle has a stone path, flowers, a masonry arch with vines, and a non-colliding waterfall. Split's left ridge is olive scrub, not fairway green, and the ruin reads as stone. Crater has plants and a background cone." | V10, V11, V12, V15, V16, V23, V25 |
| "The six proof shots exist, and none of them is a flat-color ribbon on a solid plane." | V1 on S1, S2, S4, S5, S7, S8 (+ S3, S6, S9) |
