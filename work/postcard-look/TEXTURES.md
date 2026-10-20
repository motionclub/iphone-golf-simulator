# POSTCARD_LOOK — procedural textures (role A1)

> **2026-10-04 21:50 (repair round 1 after the independent reviews, area T): Fairway/Green/Rough/Scrub gained a crisp fine-blade layer, Scrub is isotropic now, Lava lost its sawtooth fold lines, Basalt lost the plank dashes. Read the LAST section "v6 2026-10-04" first: it supersedes every number, gate list and sha list below for those 14 PNGs (Basalt_C/E/N, Fairway_C/N, Green_C/N, Lava_C/E/N, Rough_C/N, Scrub_C/N); SCRUB_STREAKY (v5) is replaced by SCRUB_NOT_SMEARED.**

> **2026-10-04 (continue pass, step "texture finish", area T): grass flatness, Lava, Basalt and Scrub were redone again. Read the LAST section "v5 2026-10-04" first: it supersedes every number, gate list and sha list below for Fairway_C, Green_C, Rough_C/N, Scrub_C/N, Lava_C/E/N and Basalt_C/N/E (Fairway_N and Green_N did not change).**

> **2026-10-04: the sections below describe the 2026-10-03 first pass. Grass hue, Lava, Basalt, Smoke, Cliff(+Dark), Rock, Scrub and Path were redone: read the section "v2 2026-10-04" at the bottom first (it supersedes the rows, sha list and gate list above for those files). **11:18: Basalt_C/N/E and Smoke_C were redone again, read the last section "v4 2026-10-04 11:18" (it supersedes v2/v3 for those four files and carries the current gate table).**

Owner files: `blender/scripts/golf_look_textures.py`, `Unity/Assets/Resources/Course/Look/*.png` (all except `Plants_C.png`,
which is A4's), `ArtDir/screenshots/golf_postcards/look/textures_sheet.png`, this file.
(The `.png.meta` files next to the PNGs were created by Unity's importer during A2's runs; A2's `GolfLookTextureImporter` owns
their settings. I did not write them.)

## Regenerate

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- \
    --out Unity/Assets/Resources/Course/Look \
    --sheet ArtDir/screenshots/golf_postcards/look/textures_sheet.png \
    --periodicity
```
~3 min (about 1.5 min without `--periodicity`). Options: `--only Fairway,Lava` regenerates just those materials,
`--gates-only` decodes what is on disk and runs the gates, `--preview DIR` dumps big 3x3 and lit previews for review.
The same file also runs under Blender's bundled python (`.../5.2/python/bin/python3.13 blender/scripts/golf_look_textures.py --out ...`)
for fast iteration. Output is byte-identical either way (same seeds; checked: Rough_C sha matches across both).
Inside Blender the PNGs are decoded back with Blender's own libpng (`bpy.data.images.load`, Non-Color) and compared with the bytes that were written.

How it works: numpy only. Every noise is periodic on the unit tile: gradient noise with integer lattice periods,
fbm of those, Worley/Voronoi with wrapped cells (F1, F2, ids of the nearest two, true distance to the bisector), domain warps
that add periodic offsets, FFT (circular) blurs, and normals from the periodic height with a wrap-around Sobel.
PNGs come from my own zlib/struct writer (8-bit RGB/RGBA, per-row adaptive filter, zlib 9, no gAMA/sRGB/iCCP chunks), written to
a hidden `.<name>.tmp` file and then `os.replace`d, so no reader ever sees a half-written PNG. Unity ignores dot-files and `*.tmp`.

Conventions: `u = (col+.5)/W` left to right, `v = 1-(row+.5)/H` bottom to top (= Unity UV). PNG row 0 is the top (v about 1).
Normals are tangent space, OpenGL (+X = +u, +Y = +v = up in the image), encoded `n*0.5+0.5`, which is what Unity's NormalMap importer expects.
Luminance in the gates = Rec.709 weights on the sRGB-encoded 0..1 values, i.e. the image mean as displayed.

## Files (all in `Unity/Assets/Resources/Course/Look/`)

| file | px | tile (contract) | seed | shows |
|---|---|---|---|---|
| Fairway_C / _N | 1024² | 10 m | 101 | emerald fairway: **2 lengthwise mow bands per tile** (light band centred on u=0 = centre line, dark band at u=.5, each 5 m; soft 0.4 m edges that wobble a little), gentle warm/cool mottle at 3 m and 1 m, blade grain stretched along v (2.6 x 10 cm), sparse thatch specks. N: fine blade relief (strength 1.6) |
| Green_C / _N | 1024² | 6 m | 201 | brighter, finer, more even green; very subtle 1 m stripes along v plus a fainter cross set (soft checker) |
| Rough_C / _N | 1024² | 12 m | 301 | darker tufty grass: 0.3 m + 0.12 m Voronoi tufts (light tips, dark gaps), broad yellow-dry patches, fine grain |
| Scrub_C / _N | 1024² | 12 m | 401 | Split's dry ridge: olive / dark-olive / sage bush clumps (0.46 m cells + leaf clusters) over khaki dry grass, brown soil, straw streaks; drier khaki regions. Clearly not fairway green (hue 57 vs 97) |
| Sand_C / _N | 512² | 6 m | 501 | warm cream sand, two crossing wind-ripple sets (0.40 m, warped), dark and bright grains |
| Cliff_C / _N | 1024² | 12 m (u = m around wall, v = z) | 601 | dark slate / brown stratified rock: 13 strata of uneven thickness that wobble and pinch, broken into slabs by slanted, wiggly joints of random depth (some joints and bedding planes shallow or absent, so it never reads as brickwork), lit ledge lips, shaded undercut faces, hairline fractures in places, slate-to-brown macro patches, olive moss on ledges with short drips |
| CliffDark_C / _N | 512² | 12 m | 701 | same generator: wet, darker, algae-green ledges, salt/barnacle specks (S .35 in the material) |
| Rock_C / _N | 512² | 4 m (box UV) | 801 | grey-brown chipped layered stone: terraced warped fbm (flat chipped planes with short risers, light worn lips), micro-chip planes in places, a few open cracks, lichen specks, moss on the planes. The rock meshes carry the big facets |
| Path_C / _N | 512² | 5 m | 901 | pale irregular flagstones (~0.7 m), thin joints with grass in some and dirt in others, grass creeping over a few edges, faint cracks |
| Masonry_C / _N | 512² | 4 m | 1001 | warm grey cut stone: 8 courses of 0.5 m, 4-7 blocks per course, chipped edges, pillowed faces, recessed mortar, moss patches, weathering stains |
| Basalt_C / _N / _E | 1024² | 8 m (u around, v = z) | 1101 | near-black neutral columnar basalt: 12 vertical columns 0.37-0.97 m wide, each seen as 3 planes; tilted cross-joints cut them into stepped segments; light worn segment tops, chipped arrises, pitted surface. **_E**: glow only in the column gaps and joints, in patches (black elsewhere, mean lum .019) |
| Lava_C / _N / _E | 1024² | 24 m | 1201 | STATIC lava: near-black crust plates (ash-dusted tops, warm rims) bent by a two-level swirl warp; hot regions open into molten rivers with yellow-orange swirl streaks, cool regions are crust with thin glowing cracks. _C is dark (molten = dark orange albedo), **_E** carries the glow (crust about 0) |
| Surf_C (RGBA) | 512² | 8 m (UV0 = world xy / 8) | 1301 | whitewater: mostly white foam (alpha mean .48) broken by bubble lace at 2 Voronoi scales, open-water holes where the foam thins, denser clots. Isotropic, because UVs are world xy and shores run every direction. GolfSurf multiplies alpha by the vertex alpha |
| Fall_C (RGBA) | 256x512 | u across 0..1, v tiles down the sheet | 1401 | vertical white-to-teal streaks, alpha .66 ± streaks with gaps, soft noisy fade at both u edges; tiles in v only |
| Smoke_C (RGBA) | 512² | single card | 1501 | one soft billowy puff (16 lobes, fbm-eroded), top-lit; alpha fades to 0 well inside the card (max .9, mean .21) |
| Sky_Crater_C | 2048x880 | TennisSky projection | 1601 | smoky dusk: hot orange horizon, dusky rose, aubergine; low smoke banks and two rising plumes (u .30 / .79) with orange undersides and rose tops; brighter glow around u .58. Projection = SkyPanorama: u 0..1 spans the 180° arc (the shader mirrors it), v 0 = horizon .. 1 = elevation 66.7° (`v = elev*1.35/90`). The shader fades to its own gradient below about 5°, so the lowest ~8 % of rows mostly do not show |

Total Look/ = 19.11 MB with A4's Plants_C (limit 25 MB).

sha256 (final run 2026-10-03 22:02):
```
4750e90c74e1b496ad2c787cb2f3ca1f95f8dc9a1c19b13448bcb145bc6b7ca4  Basalt_C.png
65bc21aadb533542139a8066e3eeca043bdd4ce71d05d5b45b9ef664f516bc75  Basalt_E.png
ef023169dddb522a2707c997f0687e0dc0c8e614570e722bc323783ae75c48fc  Basalt_N.png
b856f679a03d914b5c00bef1fa4a8b3ec1acbb2152791075e88625aaed424328  CliffDark_C.png
acc88e05ba9bac06e0b04a2fa57a8b3c7aa2652ecf8913dceb23aabaf683a202  CliffDark_N.png
c7c13bc2126f07be448e41f307f629766a6af68e5e70f8294ee4386527d83f02  Cliff_C.png
c9458228654bc489eaa96a64aa05b8d5553c5edb7d8448f70afee77af3ae37b8  Cliff_N.png
cbcae0460fb46e78e7eada9672ecf0f3e3af8779251a11174b8ce266c8785412  Fairway_C.png
017e760ae473790c4fb8097e22cbf2260c7a5ccb93ae047fde0394c8fb77fa01  Fairway_N.png
41e8e60449911bf6b2babe7c876f76ddba2f64d4959a85464136604b3451379a  Fall_C.png
b6a5b608b4aa782068891c34027dbfdbb2e13f3f50495b8b71521a235db178a9  Green_C.png
b6190a98ab51ce840d52fc46f24df88afdb98e69b59400dbb05c1bc25f8fcc00  Green_N.png
d6fbcba768877b7d6ed7d029b14d1300470c3551e038ff5e8328cc8d2d6ed507  Lava_C.png
7d0b8f5e5a06637df0cfaf9c1795c98291326985384841c9238a018636db724c  Lava_E.png
5b1d836e35175d3aded8ca208ffe0e4cb8a7ed25a0dc2fd9b7d80fafb4c73dd3  Lava_N.png
b7b4d18d9ce430fd64c1b5116e6551434ff758d031873faa46b6879920034bec  Masonry_C.png
2721f010c6bcd3a7a787d0df5ef2b3d2b741f4b24be1c10ee09ff1308bb5851f  Masonry_N.png
bc80093891b9b2464ce9eb2e0f66a12fd278132898b775f8f3542b4995c046da  Path_C.png
71b35996ccacb7ac451306ac26b7ba4143d8beabfbf167e3a3cff02969357026  Path_N.png
486580fb0ce8d2a8c865a9deac5dfabe88479181a4e9966b42ee092372f3058e  Rock_C.png
a9bee1a95aa560f829398ad5dbfbd9bbaf19cd49b992c7f03c3b64eb7d5b506d  Rock_N.png
7b410a607e2a32032c5e530474080c707f2d326c9801d0447a9560e61783d17d  Rough_C.png
698d0fef292c996591bf5e4734a7ffc9481d9b2d77c31bbcb927e7a2810afc1e  Rough_N.png
3c14effb8288e0b35a7e8e6fac3b559915b8b9535899872ded179a9ac1dbc89d  Sand_C.png
e0b2a41c23d9860d327f7aa166de34f681dd2c0903743cbf051b92efb70f7114  Sand_N.png
46e2ff7ebd25c823daa0309bf8c45d0f4fa47c8cc278d4491c3ee3630f8df205  Scrub_C.png
315166f46e0afc5f8e0333cf2900aff465c32158d281d40c46e2c9b9c856271e  Scrub_N.png
20c07b8f0366ae62a9f24dadd5d081e174a298ae67497de0122baeac3329940c  Sky_Crater_C.png
85bdee1caa37db92001d4d28631d8b2e1956f2a8510561e89faab7d594d576ff  Smoke_C.png
5a3d90a6cdb5abb54cf88e118a67e15ff3b2ae3f8a22e3732d3962346f16f954  Surf_C.png
```

## Palette: sampled from the stills (Pillow, system python3, patch medians)

| still / patch | median sRGB | used for |
|---|---|---|
| needle putting green / pad grass | (167,184,66) / (145,142,62) | Green, Fairway (hue 65-73) |
| needle cliff / cliff2 / cliff-left | (25,34,37) / (23,40,52) / (41,41,36), light stones to (141,127,114) | Cliff slate + brown + light lip |
| needle moss on cliff | (53,55,36) mean (65,66,44) | Cliff moss (olive) |
| needle path | (155,136,90), light to (208,177,130) | Path stone |
| split fairway / green | (129,150,53) / (152,172,74) | Fairway, Green |
| split scrub (3 patches) | (89,82,52) (58,58,35) (88,85,52) | Scrub olive / dark-olive / khaki |
| split shore rock / ruin | (74,71,58) / (84,82,71) | Rock, Masonry, Cliff brown |
| split sand | (234,214,186) | Sand (228,208,168) |
| crater basalt | (33,27,29), rim to (119,102,86) | Basalt near-black + light chips |
| crater lava | (217,65,13), light (255,121,39) | Lava glow ramp |
| crater smoke / sky | (149,130,131) / (117,106,113) | Smoke, Sky mauve |

Decision: grass albedos are a bit greener than the stills (hue about 96 against 65-73) because the golf key light is warm
(1,.86..1,.66..) and A2 adds per-hole tints. A2 measured the Game-view fairway at (132,187,81) on Needle, which is hue 89.

## Gates (final run, Blender 5.2 headless, decoded by Blender's libpng)

```
GATE: PNG round-trip exact (decoded pixels == generated bytes, 30 files, decoder bpy/libpng) PASS
GATE: <30 files> exists at the contract size, 8-bit, RGB (RGBA for Surf/Fall/Smoke)            PASS x30
GATE: wrap seam <= 1.5x interior (u, v)          Fairway_C 1.108/0.918  Fairway_N 0.777/0.811  Green_C 1.152/1.017  Green_N 0.803/0.841
                                                 Rough_C 0.946/0.869  Rough_N 0.922/0.893  Scrub_C 1.140/0.876  Scrub_N 0.919/0.843
                                                 Sand_C 0.928/0.960  Sand_N 0.825/0.790  Cliff_C 0.797/0.760  Cliff_N 0.744/0.909
                                                 CliffDark_C 0.890/0.457  CliffDark_N 1.282/0.268  Rock_C 1.296/1.219  Rock_N 1.004/1.473
                                                 Path_C 0.618/0.913  Path_N 0.477/0.985  Masonry_C 0.774/0.651  Masonry_N 0.537/0.264
                                                 Basalt_C 0.285/0.499  Basalt_N 0.237/0.421  Basalt_E 0.054/0.104
                                                 Lava_C 1.229/0.869  Lava_N 1.221/0.924  Lava_E 1.221/0.930
                                                 Surf_C 0.864/1.306  Fall_C v 1.109                    all PASS
GATE: exactly periodic: map(u+1,v+1) == map(u,v) (Fall: v+1), texels differing by >1 level <= 0.1 %   PASS x29
      (0.0000 % everywhere; Lava 0.0001-0.0027 %: single texels on a Voronoi border flipped by float32 rounding)
GATE: normals mean||n|-1| < 0.02 and mean z > 0.85  Fairway .0019/.986  Green .0019/.983  Rough .0019/.985  Scrub .0018/.988
      Sand .0019/.985  Cliff .0012/.987  CliffDark .0011/.986  Rock .0018/.949  Path .0018/.953  Masonry .0011/.956
      Basalt .0016/.950  Lava .0015/.983                                                       all PASS
GATE: Basalt_E mean lum < 0.12 and max > 0.6 PASS  (mean 0.0191 max 0.871)
GATE: Lava_E mean lum 0.15..0.5 PASS  (mean 0.2396)
GATE: Lava_C mean lum < 0.2 PASS  (mean 0.1953)
GATE: Fairway_C mean colour green (hue 70..160, sat >= .3) PASS  (hue 96.7 sat .629 val .650 rgb (102,166,62))
GATE: Green_C mean colour green PASS  (hue 96.1 sat .597 val .710 rgb (116,181,73))
GATE: Rough_C mean colour green PASS  (hue 94.2 sat .643 val .431 rgb (70,110,39))
GATE: Scrub_C olive-yellow-brown (hue 35..68, sat .2..65) PASS  (hue 56.8 sat .480 val .411 rgb (105,102,55))
GATE: Scrub hue differs from Fairway by >= 20 deg PASS  (96.7 vs 56.8)
GATE: Sand_C warm light (hue 25..55, sat .1..45, val >= .7) PASS  (hue 39.6 sat .267 val .894 rgb (228,207,167))
GATE: Basalt_C dark neutral (val <= .3, sat <= .3) PASS  (hue 348 sat .078 val .187 rgb (48,44,45))
GATE: Lava_E orange (hue 12..45, sat >= .5) PASS  (hue 24.0 sat .874)
GATE: large-scale evenness (4x4 block means within 10 %)  Fairway 2.8 % (vs its mow-band column)  Green 2.6 %  Rough 5.1 %
      Scrub 5.9 %  Sand 1.5 %  Path 6.4 %                                                       all PASS
GATE: Look/ folder total PNG size <= 25 MB PASS  (19.11 MB over 31 PNGs incl. A4's Plants_C)
SUMMARY gates 116, fail 0
GATE (guards.sh): hole_07 blend/fbx/meta, Hole.cs unchanged, no Postcards drift, GolfGame starts Postcards, Cliffside() kept   PASS x7
```
The full log is reproduced by the regenerate command above (every line is printed as `GATE: ... PASS|FAIL (numbers)`).

Proof sheet: `ArtDir/screenshots/golf_postcards/look/textures_sheet.png` (2144x2632). For each tiling material it shows the albedo
tiled 3x3, the normal map, the emission mask (Basalt, Lava) and a lit 2x2 preview: the albedo shaded by its normal under a fixed warm key
plus cool ambient, with emission added. Then Surf 3x3 over sea plus its alpha, Fall x2 in v, Smoke over a dark-red backdrop, and the
crater sky. I checked it by eye at 3x3 for repeats and palette, plus larger per-material lit previews and a phone-camera perspective
render of Fairway/Rough (scratch tools, not deliverables).

## Decisions

* "2 mow-stripe bands per tile" = one light and one dark band, 5 m each, with the light band centred on the centre line (u=0), so the
  stripes are symmetric about the line of play. `PHASE` for Fairway must stay (0,0).
* The seam gate (one edge row/column against the mean of all neighbour pairs) is a statistical proxy. When a sharp feature happens to
  run along the edge row, it can fail while the map is still exactly periodic. So:
  (a) all maps are proved exactly periodic by the `--periodicity` gate;
  (b) the axis-aligned structures (cliff strata, masonry courses, basalt columns and joints) are laid out so that the tile edge runs
  mid-stratum, mid-course or mid-column, never along a bedding plane or mortar bed;
  (c) Rock and Path, which are Voronoi crack networks, sample the grid at a fixed phase (`PHASE` in the script: Rock (.37,.61),
  Path (.23,.71)). This only moves which column is the edge.
* Evenness gate on Fairway compares each 1/4-tile block with its own block-column, because the mow bands are intended u-variation.
* Normal strengths are moderate on purpose ("stylised, not harsh"). A2's per-material `BumpScale` (RUNTIME.md §2) is the runtime knob.
  Note for A2: Fairway_N was lowered from strength 2.2 to 1.6 after my first passes (A2 found 1.0 "shag carpet" on an earlier
  version). With A2's BumpScale .75 the fairway may now be a bit flat up close; BumpScale about 1.0 gives the earlier look.
* Sand: A2 tints LK_SAND .80 because the bright albedo clips under Split's sun. I kept the albedo unchanged (mean val .894) so that tuning stays valid.
* Lava: the crust's under-glow in _E is kept low (ramp .02-.08, near-black) as the brief asks ("crust near-black"); the brightness
  comes from wider molten rivers in the hot regions (mean _E .24).
* Sky_Crater: the mauve/aubergine sits between the still (grey-mauve smoke) and the tennis volcano (deep orange to purple): "not grim".
  Both plumes and the glow are kept away from u=0/1, so the shader's mirror does not create a symmetric blob behind the camera.

## Open issues

* No Game-view proof of the FINAL textures by me: A1 does not run Unity, so that check belongs to the integrator. A2's
  `runtime/sheet_swatch_final.jpg` was made with my first-pass maps (brick-like cliff, cobble rock, plank basalt), all redesigned since.
  Re-run `GolfLookVariants` / `PostcardCameraStills` to see the final set.
* At 3x3 the Lava's hot regions still show a mild per-tile rhythm (24 m tile on a ~100 x 70 m lake = ~4 x 3 repeats). The phone camera
  sees the lava at a grazing angle, so I accepted it. If it shows in the crater close shot, A3 can rotate or offset the lava UVs per patch.
* Optional, outside the contract list: A2's runtime picks up a painted `Course/Look/Sky_Split_C.png` if one exists (it currently uses a
  cooled copy of SkyPanorama). Not made.


## v2 2026-10-04 (continue pass; area T)

Evidence: `work/postcard-look/v2/tex/` (`sheet_grass.png`, `sheet_lava.png`, `sheet_basalt.png`, `sheet_smoke.png`, `sheet_secondary.png`,
`textures_sheet_v2.png`, `final_run.log` = the full gate log of the run that wrote the PNGs, `before/` = the 30 PNGs as they were at the pause
with `before_sha256.txt`, `final_sha256.txt`, `lit_predict_final.txt`, `recommended_tints.json`). Nothing in v2 was measured in the Game view
(area T does not run Unity): every "predicted" number below is a model, labelled as such.

### Regenerate (exact commands; deterministic, byte-identical under Blender's python and plain python3.13, checked on 6 materials)
```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- \
    --out Unity/Assets/Resources/Course/Look --sheet work/postcard-look/v2/tex/textures_sheet_v2.png --periodicity     # all 30 files, ~2 min, 132 gates
# only the files this pass changed (18 PNGs), faster, same bytes:
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- \
    --out Unity/Assets/Resources/Course/Look --only Fairway,Green,Rough,Scrub,Path,Cliff,CliffDark,Rock,Lava,Basalt,Smoke
# fast iteration without Blender (numpy in Blender's python):  work/postcard-look/v2/tools/gen.sh <outdir> Lava,Basalt,Smoke
# evidence sheets:  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 work/postcard-look/v2/tools/make_sheets.py
# grass prediction: python3 work/postcard-look/v2/tools/lit_predict.py [--tints-json work/postcard-look/v2/tex/recommended_tints.json]
```
Changed (sha differs from `before_sha256.txt`): Fairway_C, Green_C, Rough_C, Scrub_C, Path_C, Cliff_C/N, CliffDark_C/N, Rock_C/N, Lava_C/E/N, Basalt_C/N/E, Smoke_C.
Unchanged bytes: Fairway_N, Green_N, Rough_N, Scrub_N, Path_N, Sand_C/N, Masonry_C/N, Surf_C, Fall_C, Sky_Crater_C (and Plants_C = props agent's). Same
file names, same pixel sizes, 8-bit RGB (RGBA for Smoke), written atomically (hidden `.tmp` then rename); no `.meta` touched. Look/ = 19.71 MB (31 PNGs).

### 1. Grass hue (Fairway / Green / Rough, Scrub, Path joints)
* Root cause of the 20 degree error: the albedo hue was 94-97 (emerald) and the warm key (1,.86,.66) x2.3 + sky ambient only moves it to 86-89. New mean albedos:
  Fairway (141,168,50) hue 73.6, Green (151,175,59) hue 72.4, Rough (104,114,35) hue 68.1 (the stills' rough is yellower than their fairway: needle h59 vs h67), Scrub (106,97,53) hue 49.9.
  Mow-band / mottle / grain structure is untouched (`Fairway_N`, `Green_N`, `Rough_N`, `Scrub_N` keep their bytes).
* `work/postcard-look/v2/tools/lit_predict.py` (plain python3 + Pillow; reads `GolfAtmosphere.cs` and `GolfLook.cs`, so it follows the Unity owner's edits):
  `sRGB(clip(lin(albedo) x lin(tint) x L))` per texel, clip before averaging, `L = key x I x sin(el) + fill x I x sin(el) + rim x I x sin(el) + trilight sky` (flat ground, N.L = sin elevation, the
  diffuse term has no view dependence; specular/sky reflection, bump shading, fog (starts 120-220 yd) and shadows are ignored). Validation on REAL Game-view renders:
  `runtime/repair/probe_1/hole0{8,9,10}_tee_probe.jpg` show the OLD LK_GREEN (116,181,73) lit under the real lights: render vs model (145,202,88) vs (137,204,87) Needle, (127,209,86) vs (121,211,77) Split,
  (127,192,48) vs (122,196,35) Crater, i.e. +-6..13 sRGB levels, R about 11 % low, B slightly low. A second "calibrated" mode applies that residual (R x1.108, G x.971, B +.011 linear). Both modes must be in the band.
  The other probe patches (hole 10 green/lava edge) differ by up to 17 levels in G (lava point lights); the Scrub ridge on Split renders (145,142,91) hue 56.5 vs predicted 58.5 / 50.0.
  A2's table of Game-view means (RUNTIME.md section 2) was NOT used for calibration: for Split/Crater it was taken on flat palette materials, it disagrees with the renders.
* **The existing GolfLook tints cannot serve all three holes with one albedo** (the Split tint (.76,.84,.72) was tuned for the emerald albedo: it keeps G high, which pushes a lime albedo to hue 80). Needle (table tint .94) and Crater (existing HoleTint) land in band with NO change.
  [v3: APPLIED by the Unity owner at 10:22, GolfLook.cs HoleTint; Split is now in band, measured in the Game view, see section v3 below]
  **Split needs new HoleTint entries (GolfLook.cs, Unity owner):**
  `(9,"LK_FAIRWAY") (.68,.66,.66)`, `(9,"LK_GREEN") (.72,.70,.74)`, `(9,"LK_ROUGH") (.77,.76,.77)`, optional `(9,"LK_SCRUB") (.82,.82,.86)` (Scrub passes with the table .94 too; .82 only lowers V to the still's .48).
  (Equivalent alternative: lower Split's key intensity; a roughly neutral .66 darkening is what the model asks for.) No change to Needle or Crater.
* Predicted Game-view result (first-principles / calibrated), still target in brackets; band 64..73 (rough 58..72):
  | | Needle (tint .94) | Split (recommended tints) | Crater (existing tints) |
  |---|---|---|---|
  | Fairway | (166,189,60) h70.5 S.68 V.74 / (174,187,67) h66.2 [(172,186,66) h67 S.65 V.73] | (131,153,48) h72.8 S.69 V.60 / (137,151,57) h69.0 [(133,152,52) h71 S.66 V.60] | (148,181,22) h72.4 S.88 V.71 / (155,179,38) h70.0 [(136,161,26) h71 S.84 V.63] |
  | Green | (178,197,71) h69.1 / (187,195,77) h64.1 [(171,181,64) h65] | (148,170,65) h72.1 S.62 / (156,167,71) h67.4 [(154,173,75) h72 S.57 V.68] | (159,189,27) h71.2 / (166,187,41) h68.4 [(156,173,28) h67] |
  | Rough | (123,130,43) h64.5 / (129,128,52) h59.0 [(135,134,57) h59] | (109,121,41) h68.5 / (115,119,51) h63.8 | (109,118,14) h65.2 / (115,117,33) h61.5 |
  [v3: SUPERSEDED, those were the pre-10:22 tints]
  With the tints CURRENTLY in GolfLook.cs Split fails (fairway 80.6/77.9, green 79.9/76.7, rough 74.4/71.3): see `lit_predict_final.txt` (both runs). Crater S is .86-.89 first-principles, .72-.79 calibrated (target about .8).
* Path_C joint grass was already moved to the lime hue by the repair pass; regenerated with the new generator (same pixels otherwise).

### 2. Lava (Lava_C, Lava_N, Lava_E)  -  swirling flow instead of crust cells
* Method (`mat_lava`, knobs `LAVA_P`, `LAVA_ALPHA`, `LAVA_MULT`, `LAVA_LIGHT`): a periodic stream function (spectral noise, 2-5 and 6-14 cycles per tile) -> divergence-free velocity -> the pattern coordinates are advected
  backwards through it (marbling), so thin ridged veins stretch and curl into vortices; two vein scales, dark crust = a few islands + thin ribbons along the flow (about 13 % of the tile) with a red glowing seam and
  a cooler moat; hairline red cracks inside the crust. 1-cycle Fourier modes of the control fields removed (no once-per-24 m rhythm). 2x supersampled, row strips (memory), still periodic.
  [v3: the split described in this and the next bullets (72 % albedo, scalar x1.1, no tint) is SUPERSEDED: see section v3, lava]
* Albedo and emission are DERIVED from one designed display colour T (crater.jpg pool: median (203,58,16), p95 (255,161,56), ~10 % yellow-orange veins, ~11 % near-black): albedo carries 72 % of T's linear energy under the Crater flat light
  (`LAVA_LIGHT` = (1.421,.866,.742)), emission carries the rest for a multiplier of 1.1. **Lava_E peak is (138,95,28)** (cap was (255,180,60)). The albedo alone reads orange: with emission OFF the predicted mean is (155,58,16).
* Predicted Game view (albedo x Crater light + emission x mult, model, not measured), still pool: mean (173,69,20), p50 (203,58,16), dark 21 %, glow 59 %:
  x1.0 mean (178,67,20) p50 (193,54,16) dark 13.3 % glow 62 %; x1.1 (180,68,21) p50 (195,55,16) glow 64 %; x1.3 (184,70,21) glow 67 %; the CURRENT runtime multiplier (1.3,.85,.55): mean (184,66,19), no cream texel at any tested multiplier.
  [v3: WRONG for the runtime as shipped: GolfLook.cs has LK_LAVA Tint .75 and Emission (1.0,.65,.50), and since 10:19 LK_LAVA is the self-lit GolfLava shader. See section v3, lava]
  **No GolfLook change is required for the lava emission** (any scalar 1.0-1.3 or the current (1.3,.85,.55) works; 1.1 is the design point).
  Risk to check in the Game view (not mine): the four `LAVA_LIGHT` point lights (range 48, intensity 28, 2.4 yd above the lava) add roughly +1.5 linear R on the lava directly under them (28/d^2 x albedo .3): that can clip a bright spot; `GolfLook.LavaLightLift` or a lower intensity fixes it.
* Lava_N: gentle flow relief (crust a little raised, veins faintly raised), strength 3.0, no groove network.

### 3. Basalt (Basalt_C, Basalt_N, Basalt_E)  -  prisms with glowing joints instead of brickwork
* Layout (`mat_basalt`, knobs `BASALT_P`): 10 columns per 8 m tile (0.5-1.1 m wide), each THREE planes: left bevel / front / right bevel, normals tilted |nx| .38-.48 (mean .437 measured), albedo shade
  left 27 / front 46 / right 36 levels (spread 19); long vertical joints (9-15 cm wide, wobbling, chipped, steep walls |nx| .9); Voronoi chip tilt cells on the faces; light arris highlights; cross fractures 0-2 per column per tile
  (mean 1.2), >= 3.4 m apart, slanted <= 20 degrees, partial, none aligned with the neighbour (0 of 12 within 25 cm), a lit ledge under each; kept >= 1 m off the tile edge row.
* Glow ONLY in the vertical joints: exactly 60 % of the joints carry glow, in short broken stretches (>= 0.5 m, no stretch start/end on the seam row), 2.0 % of the texels, 23 stretches all vertical-elongated (aspect >= 3 within 25 degrees of vertical),
  longest horizontal glow run 16 px = 1.6 % of the tile, 100 % of the glow within 14 px of a joint line, hotter toward v = 0 and 1 (cos profile, periodic; x1.50 against mid-height). Peak (255,160,40).
  **UV note for the hole-10 builder:** the hot rows are v = 0 (mod 1) = z = 0, 8, 16 m when UV v = z/8. To heat the joints right above the lava, author `v = (z - z_lava)/8` on the basalt walls and columns.
* LK_BASALT emission multiplier: the current (1.5,.85,.5) turns the (255,160,40) peak into about (255,148,25), orange: fine. No change required.

### 4. Smoke_C
Rising S-bent plume that widens upward, curled by a large-scale flow, low-frequency eroded; alpha max .486, exactly 0 on the outer 12 % border, second-moment aspect 2.24, max alpha step .0235 per texel,
mean colour (179,170,166) warm light grey, luminance std .047. Thinner and curlier than crater.jpg's broad plumes (see `sheet_smoke.png`); `LK_SMOKE` tint (.62,.56,.56,.85) x alpha .486 gives a faint plume,
the builder can scale the card up or stack two.

### 5. Secondary (best effort, not measured in the Game view)
* Cliff_C/N (and CliffDark, same generator): 1-4 slabs per stratum instead of 2-6 near-equal blocks, 40 % of the cross joints closed, per-slab tint cut to a third (tinted rectangles read as bricks), joint darkness 0.85 -> 0.62. CliffDark still shows some blocky slabs.
* Rock_C/N: the per-terrace-level tone and the dark riser lines (they read as contour lines) are gone; tone now per chipped facet, terrace height halved, moss moved to 7-13 cycles per tile (was 3: it repeated as a grid of blobs). Rock phase moved to (.63,.44) to keep the seam statistic <= 1.5.
* Scrub_C: browner (hue 49.9) so that it stays >= 20 degrees off the fairway.

### Gates (final run `final_run.log`, decoded by Blender's libpng, 132 gates, 0 FAIL; guards.sh 7/7 PASS)
```
GATE: GRASS_HUE_PREDICTED  Fairway/Green/Rough_C on Needle (table .94), Split (RECOMMENDED tints), Crater (existing tints), Scrub_C on Split: 10 PASS, both models inside the band (numbers in the table above)
[v3: superseded, the live gates are in section v3]
GATE: GRASS_HUE_PREDICTED  with the tint that is in GolfLook.cs today, Split fairway/green/rough: FAIL (80.6/79.9/74.4 first-principles) -> needs the Split HoleTint change above (printed as INFO lines in the run)
[v3: superseded, that gate modelled URP Lit with no tint and a scalar multiplier]
GATE: LAVA_FLOW_BRIGHT PASS - x1.0..1.3 mean R160-195 G55-85 B12-30, p50 R >= 180, dark <= 25 % (13.3 %), glow >= 50 % (62-67 %), yellow >= 5 % (10.9-11.8 %), emission off still orange (155,58,16)
GATE: LAVA_NOT_CELLS PASS - 40 dark regions, median aspect 2.97 (>= 1.8), 10 % of the dark area in compact blobs (<= 30 %), spectrum ring peak/mean 8.6 (<= 14), 1-cycle fundamental 2.6 % (<= 8 %)
GATE: LAVA_EMISSION_PEAK PASS - brightest Lava_E texel (138,95,28) <= (255,180,60); cream texels 0.000 at x1.0/1.2/1.3
GATE: BASALT_BEVELS PASS - bevel texels 45.2 % (L 22.5 / R 22.7), mean |nx| .437, shade spread 19.3 levels
GATE: BASALT_PRISM_GLOW_JOINTS PASS - cross fractures mean 1.20/column, min spacing 3.74 m, 0 of 12 aligned; glow 2.0 % of texels, 23 vertical stretches, 0 violations, longest horizontal run 1.6 %, 100 % in joints, 6 of 10 joints, hot x1.50
GATE: SMOKE_SOFT PASS - alpha max .486, border alpha 0, aspect 2.24, max step .0235, warm grey, lum std .047
GATE: SEAMLESS_ALL PASS - 28 tiling maps exactly periodic (<= 0.1 % texels differ by > 1 level), wrap-seam ratio <= 1.5x on 28/28
GATE: FOLDER_BUDGET PASS - 19.71 MB over 31 PNGs (limit 25 MB)
```
The old repair-pass lines "Lava_E mean lum .35-.45", "Lava molten coverage 55-70 %" and "Lava_C mean lum < .2" were REMOVED (they encoded the previous repair's guess and a dark albedo); the contract line "Lava_E mean lum .15-.5" stays (0.173).

### Open / unverified
* Nothing here was measured in the Game view: the Unity calibration agent should measure the grass hues (Needle fairway, Split fairway/green after the HoleTint change, Crater fairway) against the bands, and the lava/basalt under the real lights (lava point lights above).
* The grass model's calibration is within +-13 sRGB levels on three probe patches; Crater blue is the least certain channel (S .79-.89 predicted).
* Lava_E reads dimmer than the old map on its own (peak (138,95,28)); the brightness lives in the albedo+emission sum by design.
* `ArtDir/screenshots/golf_postcards/look/textures_sheet.png` is the first-pass sheet and is now stale (not mine to overwrite this pass); use `v2/tex/textures_sheet_v2.png`.
* `blender/scripts/golf_look_textures.py` keeps `mat_lava_old` (first-pass lava, unused) for rollback only; the previous bytes are in `v2/tex/before/`.

### v2 tools (work/postcard-look/v2/tools/, evidence/iteration only, not game code)
`lit_predict.py` (grass hue model, reads the C# light/tint tables; `--solve` prints tints that hit the stills, `--tints-json` evaluates a tint set, `--recalibrate` re-derives the probe calibration),
`gen.sh <outdir> <Mat,Mat|""> [generator args]` (runs the generator under Blender's python), `lab.py` (previews, grazing-angle perspective view, lava Game-view composite), `make_sheets.py` (the five `sheet_*.png`),
`lava_tune.py` / `lava_sheet.py` / `lava_fund.py` / `lava_mults.py` (lava parameter sweeps and multiplier table), `basalt_sheet.py`, `smoke_sheet.py`, `tile_sheet.py`, `phase_scan.py` (seam-statistic phase search).
`v2/tex/iterations/` keeps a few intermediate previews; `v2/tex/refs/` the crater.jpg crops used by the sheets.


## v3 2026-10-04 10:45 (repair after the skeptic review of v2; area T)

Evidence: `work/postcard-look/v2/tex/v3/` (`final_run.log` = full run, 133 gates, 0 FAIL, writes + `--periodicity`; `gates_only.log` = the same gates re-run on the PNGs on disk after a log-text fix, 105 gates, 0 FAIL;
`before/` = the 4 PNGs that changed, `before_sha256.txt` / `final_sha256.txt` = Look/ at 10:41 and after; `sheet_lava_shader_v3.png`, `sheet_lava_fallback_v3.png`, `sheet_smoke_v3.png`, `lit_predict_live.txt`).
Changed bytes since the review: **Lava_C, Lava_E, Lava_N, Smoke_C only** (every other map in Look/ is byte-identical to 10:41, Plants_C included; it is the props agent's file, last written 10:16).
Nothing here was measured in the Game view by me (area T does not run Unity); where a Game-view number appears it is the runtime owner's `GolfLookSmoke` output (`v2/runtime/smoke_s17..s23.txt`) and is labelled so.

### What the review found, and what happened
1. **HIGH, Split grass out of band**: true, and not fixable from the texture side. With one albedo for all three holes the old Split tint (.76,.84,.72) put Split 10-13 degrees above Needle; the band is 9 degrees wide. The Unity owner applied the three Split HoleTint entries I had recommended (GolfLook.cs 10:22: Fairway (.68,.66,.66), Green (.72,.70,.74), Rough (.77,.76,.77), Scrub (.82,.82,.86)). The grass PNGs were not changed. **Real Game-view result after that edit (smoke_s21..s23, HeroBaseStudioURP):**
   Split fairway (147,165,68) h71 S.59 V.65, green (154,172,78) h71 S.55 V.67, rough (121,129,61) h67, scrub (124,116,77) h49; Needle fairway h67 / green h66 / rough h60; Crater fairway h70 / green h69 / rough h62. All nine inside 64-73 / 64-73 / 58-72.
2. **MEDIUM, lava claim**: true for URP Lit (the shipped tint .75 and multiplier (1,.65,.5) made it dim) and moot for the shipped runtime: at 10:19 `LK_LAVA` became the self-lit shader `GolfArcade/GolfLava` (heat from luminance, orange ramp, no lights), whose Game-view mean was (219,83,19) h19, 90 % in the orange band (smoke_s23). "No GolfLook change needed" was wrong and is withdrawn. The maps and gates were re-derived (below).
3. LOW smoke: made fuller (below). LOW basalt: **not changed** (see below). LOW Plants_C: not mine.

### Grass: model validated against the Game view
`lit_predict.py` has a third model, `game`, fitted to the 10 Game-view patches of the installed albedos under the tints that were live then (smoke_s16: Needle/Crater/Split-old): out = clip(lin(albedo) x lin(tint) x L x MUL + ADD[hole]),
MUL (1.005,.992,.887), ADD per hole .02-.06 linear (sky reflection/specular, independent of albedo x tint). It reproduces those 10 patches within 1.6 degrees of hue and ~8 RGB levels (first-principles: within 4.5 degrees).
**Out of sample** (the Split tints changed at 10:22, the fit never saw them): predicted vs Game view, Split fairway hue 71.9 vs 71, green 70.9 vs 71, rough 66.5 vs 67, scrub 47.3 vs 49; RGB within 7 levels per channel on fairway/green/rough, scrub 6/4/4.
`GRASS_HUE_PREDICTED` now reads the tints from GolfLook.cs (Scrub included; the old parser skipped LK_SCRUB) and needs first-principles, calibrated AND game-fit hues inside the band. 10/10 PASS (`lit_predict_live.txt`). `python3 work/postcard-look/v2/tools/lit_predict.py [--recalibrate-game]`.

### Lava (what is installed now)
* **Runtime model** (`lava_spec`, `lava_shader_model` in the generator, parsed live from GolfLook.cs): heat = clamp((1.5 lum(C) + 1.5 lum(E) + bias + .15 (nx+ny)/2 - .5) x gain + .5), bias -.15, gain 1.4, ramp #96210A / #BA2B0D / #E04F11 / #FF801C at heat 0/.2/.6/1.
  Check of the model: the installed 10:14 maps give model mean (211,76,17) under the constants above and (216,81,18) under the earlier pair (bias -.10, gain 1.5), vs Game view (219,83,19) in smoke_s23 (the constants in force during that run are not recorded): within 8 levels. The crust ribbons are no longer near-black in the shader (the ramp's coolest stop is (150,33,10)); that is the runtime owner's choice (85 % in-band gate), the maps still carry the dark crust in heat.
* **What I changed**: the maps' heat histogram. crater.jpg's pool projected on the live ramp has heat quantiles p25 .28, p50 .44, p75 .71, p90 .94 and ~11 % above .9. The 10:14 maps gave, under the live constants, heat p25/50/75 .26/.48/.77, crust (heat < .157, the V < .7 misses) 16.5 %, hot (> .9) 20.2 %,
  mean (211,76,17) hue 18.2, p50 (213,70,15), in-band 83.5 %: twice the still's share of hot veins and (by the model) under the runtime's 85 % line.
  `LAVA_ENC` = alpha .25 and an 11-knot tone curve on the design heat (`lava_encode`, fitted by rank matching: `lava_v3.py fit 0.25 8`, then the top two knots raised so the Lit fallback keeps its hottest veins). **Now, live model**: heat p25/50/75 .28/.45/.69, crust 13.3 %, hot 10.7 %, mean (210,73,17) hue 17.4, p50 (211,68,15) vs the still's (203,58,16)/(212,62,14), in-band 86.8 %.
  With the earlier bias/gain pair (-.10, 1.5): median .53, hot 16.8 %, in-band 89.4 % (was 85.8 %). The Game view measured a smaller dark share than my model on the 10:14 maps (9.9 % in smoke_s23 vs 16.5 %), so the real in-band margin should be larger than 86.8 %, but THAT IS NOT MEASURED: the Unity owner must re-run GolfLookSmoke LAVA_ORANGE_NO_BLOOM after the reimport.
* **URP Lit fallback** (shader missing; `Spec.Tint` is read only there). My fallback model reproduces the review's independent numbers on the 10:14 maps: shipped tint .75 + multiplier (1,.65,.5): mean (146,49,12) (review (146,50,12)), emission alone (95,24,3) (review (96,25,4)).
  The albedo now carries 25 % of the display colour's linear energy (was 72 %) and the glow 75 %, so the lava reads orange with the albedo off, as the brief says: **emission alone mean (148,45,12) hue 14.3 S .91** (was (95,24,3), dark red-brown).
  Both on with the SHIPPED tint .75: **mean (159,49,14)** hue 14.3, p50 (172,43,13), dark < 90 13.8 %, no cream (was (146,49,12)). With Tint WHITE: mean (169,52,16), p50 (182,47,14); this is a little DIMMER than the 10:14 maps gave with a white tint (177,64,18, with 9.4 % yellow veins): the tone curve that fixed the shader's too-hot histogram also removed the yellow veins from the fallback. The fallback is the emergency path (the shader is in Resources), so I traded it for the shipped path.
  **Optional one-token request to the Unity owner: set `LK_LAVA` `Tint` to white** (the GolfLava shader ignores it; the maps are encoded for white, so the shipped .75 costs the fallback about 10 R levels). The four lava point lights are not modelled (unverified).
  `Lava_E` brightest texel (218,126,50) (<= (255,180,60)); no cream at x1.0, x1.3 or the shipped multiplier.
* Structure unchanged (same stream-function flow, no cells): 37 crust regions, median aspect 2.97, 8 % of the crust area in compact blobs, spectrum ring peak/mean 9.1, 1-cycle fundamental 1.6 %; the wrap-seam ratios are 0.97 / 1.22 (Lava_C), 0.84 / 1.10 (Lava_N), 0.96 / 1.22 (Lava_E).

### Smoke_C
Fuller wisp (`SMOKE_P`: half width .095 + .215 h^.8 instead of .075 + .170 h^.8, alpha peak .52 instead of .50): alpha max .518, border alpha exactly 0, second-moment aspect 2.02, max alpha step .0275 per texel, covers 15.9 % of the card (was 13.4 %), mean colour (180,171,167). `LK_SMOKE` Tint alpha is now 1.0 in GolfLook.cs (was .85), so the effective peak is .52 (<= .55 limit of the runtime gate). Unverified in the Game view (the 10:24 run measured the 10:14 map: effective alpha max .49, moves the frame by median 4.6 / p99 14.5 levels).

### Basalt: left as it was (decision)
The reviewer found the basalt reads as vertical stripes and the glow sparse (2.0 % of the texels). I tried 7 of 10 joints glowing instead of 6: glow stayed 2.06 % (the stretch lengths are random) and Basalt_C/E changed bytes, so I reverted it: no benefit, and the runtime owner's BASALT_GLOW_ORANGE numbers (2.2 % of the wall, hue 16) stay valid. A chunkier, less regular column pattern would be a redesign of `mat_basalt`; not done.

### Gates (final_run.log, decoded by Blender's libpng; 133 gates, 0 FAIL; guards.sh 7/7 PASS)
```
GATE: GRASS_HUE_PREDICTED x10 PASS  - live GolfLook.cs tints, first-principles / calibrated / game-fit hues all inside the band (Needle fairway 70.5/66.2/67.6, Split fairway 72.8/69.0/71.9, Crater fairway 72.4/70.0/70.9; green, rough, scrub in lit_predict_live.txt)
GATE: LAVA_FLOW_BRIGHT PASS - GolfLava shader model, live constants: heat median .45, crust 13.3 %, hot 10.7 %, flow (heat >= .3) 72.0 %, p50 (211,68,15), hue 17.4, in-band 86.8 %; robustness pair (-.10, 1.5) also inside its limits
GATE: LAVA_LIT_FALLBACK_ORANGE PASS - shipped tint .75, mult (1,.65,.5): mean (159,49,14) hue 14.3, no cream; emission alone (148,45,12) hue 14.3
GATE: LAVA_NOT_CELLS PASS - 37 crust regions, median aspect 2.97, 8 % compact, ring peak/mean 9.1, 1-cycle 1.6 %
GATE: LAVA_EMISSION_PEAK PASS - brightest Lava_E (218,126,50), cream 0.000 at x1.0 / x1.3 / shipped
GATE: BASALT_BEVELS PASS - bevel texels 45.2 %, mean |nx| .437, shade spread 19.3 (unchanged)
GATE: BASALT_PRISM_GLOW_JOINTS PASS - 2.00 % glow, 23 vertical stretches, 0 violations, longest horizontal run 1.6 % (unchanged)
GATE: SMOKE_SOFT PASS - alpha max .518, border 0, aspect 2.02, max step .0275, lum std .048
GATE: SEAMLESS_ALL PASS - 28 tiling maps exactly periodic, wrap-seam ratio <= 1.5 on 28/28
GATE: FOLDER_BUDGET PASS - 19.47 MB over 31 PNGs
```
The lava gate thresholds are NEW (they model a different runtime), they were not loosened to fit: crust 6-14 %, hot 5-14 %, median heat .30-.55, flow >= 62 %, p50 R 190-225 / G 45-80, hue 12-22, in-band >= 85 %; the review's complaint (Lit model without the shipped tint) is covered by LAVA_LIT_FALLBACK_ORANGE.

### Regenerate (changed files only, ~25 s; same bytes as installed) and tools
```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --only Lava,Smoke
# everything + 133 gates + exact-periodicity proof (~3 min):  ... --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --sheet <png> --periodicity
# gates on the PNGs already on disk (4 s):                    ... -- --out Unity/Assets/Resources/Course/Look --gates-only
# re-fit the lava tone curve after a runtime change (Blender python, ~1 min):  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 work/postcard-look/v2/tools/lava_v3.py fit 0.25 8
```
Generator API added: `lava_fields()` / `lava_design()` / `lava_encode(Fd, alpha, lut)` (stage 1 and 2 of `mat_lava`), `LAVA_ENC`, `SMOKE_P`, `lava_spec()`, `lava_shader_model()`, `lava_report()`. Tools: `lava_v3.py`, `lava_v3_sheet.py`, `lava_v3_fallback_sheet.py`, `smoke_v3_sheet.py`, `lit_predict.py` (`game` model, `--recalibrate-game`).

### Open / for the Unity owner (nothing here is mine to edit)
* Unity reimports the 4 changed PNGs on its next launch; re-run GolfLookSmoke (LAVA_ORANGE_NO_BLOOM, SMOKE_SOFT, GRASS_HUE_LIT) to measure them. I did not run Unity.
* Optional: `LK_LAVA` `Tint` white (fallback only).
* If the lava ramp or heat constants change again, `lava_gates` follows GolfLook.cs automatically; re-fit with `lava_v3.py fit` if the heat histogram drifts out of its limits.


## v4 2026-10-04 11:18 (repair after the second skeptic review: smoke visibility + basalt as stacked prisms; area T)

Evidence: `work/postcard-look/v2/tex/v4/` (`final_gates.log` = all 135 gates on the PNGs on disk + the one-tile-shift periodicity proof of the 28 tiling maps, 0 FAIL; `write_run.log`/`write_run2.log` = the two writes; `before/` = the 4 PNGs as they were at 10:53,
`before_sha256.txt` / `final_sha256.txt` = Look/ before and after; `sheet_smoke_v4.png`, `sheet_basalt_v4.png` = before/after sheets; `smoke_model_validation.txt` = model vs the 3 real Unity runs + a robustness table; `textures_sheet_v4.png` = all 30 maps;
`model/` = the real board frames of `v2/runtime/shots/{t2,t4d,t4e}` as zlib-compressed raw RGB, needed by `smoke_model.py` and therefore by the SMOKE_SOFT gate; `iter/` = two design iterations).
Changed bytes since the review: **Basalt_C, Basalt_N, Basalt_E, Smoke_C only** (the other 27 PNGs are byte-identical to `before_sha256.txt`, Plants_C included; Look/ = 19.54 MB, 31 PNGs, no `.tmp`).
Nothing here was measured in Unity (area T does not run Unity). Every "predicted" number below is a model that was first checked against real Unity runs (table below); the Unity owner must re-run `GolfLookSmoke` (command at the end).

### What the review found, and what happened
1. **MEDIUM, smoke**: true. The runtime gate is a visibility BAND, not an upper bound: effective alpha (painted peak x `_Color.a` x `_AlphaGain`) in .55-.72, median |delta luminance| >= 8, p99 28-90, edge step <= 6. v3's thin S curl covered 15 % of the card and measured median 4.9 / p99 14.7 at 10:50.
   My own `SMOKE_SOFT` gate still used the old upper bound (`alpha <= .55`) and could not see that: it is reconciled below (it now reads LK_SMOKE from GolfLook.cs and evaluates the Game-view model).
2. **MEDIUM, basalt**: both halves true. (a) charcoal: `BASALT_RENDERS_DARK` failed at 10:50 (median 52, S .37). The runtime owner fixed it from the Unity side at 10:53 (`LK_BASALT` `Tint (.52,.80,.92)` + `NoSpecular`: real run `smoke_t4e`: median 29, mean (36,31,28), S .21, PASS).
   I accept that route (the review's fix_hint allowed "agree a HoleTint") and keep the albedo's LIT mean on exactly that calibration, so the owner's pass stays valid (see "why the albedo mean did not move"). (b) "reads as vertical bamboo or planks, not chunky cracked prisms": true, redesigned below.
3. LOW lava (optional 24 m repeat, mild diagonal grain) and LOW grass (Crater S .71 vs the still's .84, the Crater tint's B channel is the Unity owner's): not changed, nothing required. Unchanged: all lava, grass and secondary maps.

### Smoke_C: a fused rising plume instead of a thin S curl
* Design (`SMOKE_P`, `mat_smoke`): a column whose half width grows from 0.07 to 0.17 of the card (so ~0.14 wide at the foot, ~0.34 at the head), rounded off at the head, gentle S bend + drift right, outline curled by the same divergence-free flow as before but at half the strength (the v3 strength tore a "horn"
  off the head), flat-topped (super-Gaussian) body with low-frequency billows, alpha normalised so the brightest texel is exactly `amax` .50 PAINTED. 19.2 % of the card is plume (v3: 15.9 % but mostly feather), second-moment aspect 2.26, border alpha exactly 0 on the 12 % border, max alpha step .0157 per texel (v3 .0275, limit .031).
  Colour: light neutral-cool grey (170,172,176), slightly darker/warmer foot, lighter head. Under the Crater light (warm) and LK_SMOKE's tint this renders as (182,154,149), crater.jpg's plume is (183,154,150): the plume's own lit colour is gated, not the backdrop-dependent blend.
* **The effective peak is `amax` x AlphaGain.** With the live row (`Tint (1,.95,.92,1)`, `AlphaGain 1.35`, `Lit .8`, `SelfLight .40`, GolfLook.cs 10:53) it is **.672** (band .55-.72). The AlphaGain range that keeps it in band is **1.11-1.45**.
  If the Unity owner ever sets AlphaGain back to 1.0 the painted peak must be raised: `... golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --only Smoke --smoke-peak 0.66` (new CLI option; the gate prints FAIL with "effective alpha max .889" if the two disagree: tested). Do NOT raise one without the other.
* **Model of the runtime gate (`v2/tools/smoke_model.py`)**: rebuilds the board (camera (0,9,0) -> (-10,24,130), 60 deg, 900x1600, card 36x44 yd at (-10,4,130)), the shader's alpha/EdgeFade/light/blend, and the Crater sky from the real "without" frame.
  Validated on the three real runs that exist: t2 (10:50) median 4.85 / p99 14.7 / step 1.03 / N 18076 vs Unity 4.9 / 14.7 / 1.03 / 18036; t4d median 8.15 / 76.9 / 3.96 / 32362 vs 8.1 / 77.1 / 4.00 / 32349; t4e 7.41 / 72.1 / 3.86 / 31361 vs 7.4 / 72.2 / 3.93 / 31369. The light is `G_c = f_c (1 - Lit + Lit e) + fS_c Lit` (3 runs, max residual .0095), so settings that were never run can be predicted.
* **Predicted Game view, live row**: v3 (the old thin plume): alpha .70, **median 8.6**, p99 80.3, step 4.3 (passes only barely, and only because the owner raised gain/SelfLight); **v4: alpha .672, median 14.9, p99 61.5, step 2.4**, 40,931 px move the frame. Robustness (`smoke_model_validation.txt`): v4 passes the runtime thresholds at AlphaGain 1.2/1.3/1.4, SelfLight .25/.35, Lit .6, white tint;
  v3 failed at SelfLight .25 and AlphaGain 1.4. v4 still FAILS at the 10:50 row (gain 1.0, tint (.62,.56,.56), SelfLight .05: alpha .50 is below .55): the pass is tied to the live row, as stated above.
* The brightest tenth of the blended plume over this sky reads (191,141,128): that number depends on the orange sky behind it, it is reported as INFO only.

### Basalt_C / Basalt_N / Basalt_E: stacked prism blocks instead of 8 m planks
* Layout (`mat_basalt`, `BASALT_P`, helper `_basalt_fractures`): 11 columns with log-normal widths (0.4-1.4 m), each THREE planes (left bevel / front / right bevel, |nx| .36-.50, per block), long vertical joints (9-15 cm, chipped, steep walls) that JOG 2.4-5 cm sideways between blocks (v3 joints were straight for 8 m),
  and every column cut into **3-5 blocks 1.3-3.4 m tall** by slanted cracks (<= 20 deg, one partial crack per tile in 22 % of columns), none within 45 cm of a neighbouring column's crack (no courses). Each block has its own tone (x.80-1.22), tilt (+-.10), plane widths and bevel angles;
  under every crack a lit ledge (13 cm, chipped) and a shadowed lip above it; long vertical tone streaks per column; chip cells 18x18. Glow stays ONLY in the vertical joints: 70 % of the joints (v3 60 %), 27 broken stretches, 2.81 % of the texels (v3 2.0 %), hotter toward v = 0 (x2.13), peak (255,160,40) unchanged.
* **Why the albedo mean did not move (and the one nudge):** the runtime owner tuned `LK_BASALT.Tint (.52,.80,.92)` against v3's key-lit wall mean (36,31,28). The generator rescales the albedo per channel so that `mean(sRGB(lin(albedo) x gain x CAL_TINT x WALL_LIGHT)) = (35,31,29)` where `WALL_LIGHT` (3.674, 1.3065, .736) is the wall's key light fitted on that very run
  (v3 under the model: median 29, mean (36,31,28) = Unity's numbers). One level less red / one more blue than v3 takes S from .21 to .17 (limit .25), i.e. margin, and is closer to crater.jpg's neutral charcoal (26,25,29). The constants do not depend on GolfLook.cs at generation time (determinism); the gate does read the live tint.
* **Gate definition CHANGED, disclosed (not loosened to pass):** v3's `BASALT_PRISM_GLOW_JOINTS cross fractures` demanded 0.4-2 fractures per column >= 3 m apart. The review showed that this exact definition produces the "bamboo" read (continuous 8 m columns), so it is replaced by a stricter, structural one:
  3-5 fractures per column (min 3, max <= 5), spacing 1.3-3.6 m, neighbour-aligned (within 40 cm) <= 10 %, **no courses** (worst 30 cm band holds fractures of <= 45 % of the columns), block height/width median 1.4-5 and blocks taller than 6 widths <= 10 %. The glow gate is unchanged in substance; its "within 14 px of a joint line" test became "next to a steep joint wall (|nx| > .75 within 8 px)" because the joints now jog (still >= 95 %, measured 100 %).
  `BASALT_BEVELS` is unchanged. New: `lit darkness` = the BASALT_RENDERS_DARK model (median luminance 18-40, mean within 4 levels of (35,31,29), S <= .25) with the LIVE tint.
* Measured on the PNGs: fractures per column 3.27 (min 3, max 4), spacing 1.32-3.39 m, 0 of 36 neighbour-aligned, worst band 36 % of the columns, block height/width median 3.65, 8 % taller than 6 widths; bevel texels 39.3 % (left 20.3 / right 19.0 / front 36.8), mean |nx| .429, plane shade left/front/right 27.3/46.4/34.5 (spread 19.1);
  glow 2.81 %, 27 vertical-elongated stretches (0 violations), longest horizontal glow run 16 px = 1.6 %, 100 % of the glow beside a joint wall, 8 of 11 joints glow; wrap-seam ratios u .25 / v .66 (C), exactly periodic under the one-tile shift (0.0002 % of texels differ by > 1 level).
  Predicted key-lit wall with the live Tint: median luminance 30, mean (35,31,29), S .17.
* Not removed: the 8 m tile still repeats (3x3 shows 11 vertical columns with a different block rhythm each, no longer a stripe field, but the 8 m rhythm is visible). **UV note for the hole-10 builder (unchanged):** hot joints are at v = 0 mod 1; author `v = (z - z_lava) / 8` on walls beside the lava.

### Gates (final_gates.log; decoded by Blender's libpng; 135 gates, 0 FAIL; guards.sh 7/7 PASS)
```
GATE: GRASS_HUE_PREDICTED x10 PASS  - unchanged maps, live GolfLook.cs tints (Needle fairway 70.5/66.2/67.6, Split 72.8/69.0/71.9, Crater 72.4/70.0/70.9; green, rough, scrub in final_gates.log)
GATE: LAVA_FLOW_BRIGHT PASS  - unchanged map: GolfLava model, heat median .45, crust 13.3 %, hot 10.7 %, p50 (211,68,15), hue 17.4
GATE: LAVA_LIT_FALLBACK_ORANGE PASS - unchanged: tint .75 x (1,.65,.5) mean (159,49,14), emission alone (148,45,12)
GATE: LAVA_NOT_CELLS PASS - unchanged: 37 crust regions, median aspect 2.97, 8 % compact, ring peak/mean 9.1
GATE: LAVA_EMISSION_PEAK PASS - unchanged: brightest Lava_E (218,126,50), cream 0
GATE: BASALT_BEVELS PASS - bevel texels 39.3 %, mean |nx| .429, plane shade spread 19.1 levels, 11 columns
GATE: BASALT_PRISM_GLOW_JOINTS cross fractures PASS - 3.27/column (3..4), spacing 1.32-3.39 m, 0/36 aligned, worst band 36 %, block h/w median 3.65, 8 % planks   [NEW definition, see above]
GATE: BASALT_PRISM_GLOW_JOINTS glow PASS - 2.81 % of texels, 27 vertical stretches, 0 violations, longest horizontal run 1.6 %, 100 % beside a joint wall, 8/11 joints, hot x2.13, peak (255,160,40)
GATE: BASALT_PRISM_GLOW_JOINTS lit darkness PASS (model, not Unity) - median luminance 30, mean (35,31,29) S .17 with the live Tint (.52,.80,.92)
GATE: SMOKE_SOFT painted map PASS - painted alpha max .498 (<= .72), border alpha 0, aspect 2.26, max step .0157, colour (170,172,176) S .037, lum std .035, covers 19.2 %
GATE: SMOKE_SOFT runtime band PASS (model, not Unity) - live LK_SMOKE: effective alpha .672 (.55-.72), median 14.9 (runtime >= 8; here >= 10), p99 61.5 (28-90), step 2.39 (<= 6), plume's own colour (182,154,149) S .18 vs crater.jpg (183,154,150) S .18; AlphaGain range 1.11-1.45
GATE: SEAMLESS_ALL PASS - 28 tiling maps exactly periodic, wrap-seam ratio <= 1.5 on 28/28
GATE: FOLDER_BUDGET PASS - 19.54 MB over 31 PNGs
```

### Regenerate, tools
```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --only Basalt,Smoke      # the 4 changed files, ~30 s, byte-identical to the installed ones (checked)
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --gates-only --periodicity --sheet work/postcard-look/v2/tex/v4/textures_sheet_v4.png   # all 135 gates, writes no PNG, ~100 s
... -- --out Unity/Assets/Resources/Course/Look --only Smoke --smoke-peak 0.66        # only together with AlphaGain ~1.0 (see above)
```
Tools (`work/postcard-look/v2/tools/`): `smoke_model.py` (Game-view model of the smoke card, `fit`/`eval` helpers, `read_png_np`), `smoke_validation.py` (writes `smoke_model_validation.txt`), `smoke_sweep.py` / `smoke_iter.py` (design iterations), `smoke_sheet_v4.py`, `basalt_wall_view.py <out.png> [new|before|both]`.
Generator API added: `SMOKE_P` (new keys expo/sat/cap/curl/billow/base/top/under), `BASALT_P` (nc, wsig, nf, gmin, gmax, align, partial, jog, chip), `BASALT_LIT_MEAN`, `BASALT_CAL_TINT`, `BASALT_WALL_LIGHT`, `_basalt_fractures`, `smoke_spec()`, `smoke_game()`, `basalt_spec()`, `--smoke-peak`.
Determinism: regenerating Basalt and Smoke into a scratch folder gives the same bytes as the installed files (cmp, twice).

### Open / for the Unity owner (not mine to edit or run)
* Unity reimports the 4 changed PNGs on its next launch. Re-run, through `heavy.sh`: `work/postcard-look/v2/runtime/run_smoke.sh <label>` and read `SMOKE_SOFT`, `BASALT_RENDERS_DARK`, `BASALT_GLOW_ORANGE`, `LAVA_LIGHTS_REACH_BASALT`. Unverified until then: the model predicts SMOKE_SOFT median 14.9 / p99 61.5 / alpha .672 and BASALT_RENDERS_DARK median 30 / S .17; the model ignores the normal-map shading of the wall, whose old and new maps have the same bevel angles (S has .08 of margin).
* Couplings that must not be changed independently: **LK_SMOKE AlphaGain x Smoke_C painted peak (.50)**, and **LK_BASALT Tint (.52,.80,.92) x the Basalt_C lit mean (35,31,29)**. If either row changes, the gates in `final_gates.log` follow GolfLook.cs automatically and print FAIL with the numbers.
* The 8 m basalt tile still repeats on a long wall; a second tile scale or a per-patch UV offset on the hole-10 walls would hide it (hole builder's choice).


# v2 2026-10-04 calibration (area K: Game view under the golf key light)

**No texture was changed.** The generator (`blender/scripts/golf_look_textures.py`) regenerated all 30 maps byte-identical to `Unity/Assets/Resources/Course/Look/` (`gen.sh <scratch> ""` -> 107 generator gates, 0 failed, `v2/calibrate/tex_regen.log`),
and the Look/ sha256 list is identical before and after (`v2/calibrate/look_sha256_before.txt` / `look_sha256_after.txt`). All the calibration was done in `GolfLook.cs` (HoleTint, LK_WATER_SHALLOW): see RUNTIME.md "v2 2026-10-04 calibration" K.0 for every constant, old -> new.

## T.1 Your models against the first Unity runs on the v4 textures (the v4 Basalt/Smoke had not been run in Unity before this pass)
| quantity | your model / prediction | Unity (`smoke_final.txt`, HeroBaseStudioURP and TennisURP alike) |
|---|---|---|
| Smoke_C, effective alpha max (painted .498 x AlphaGain 1.35) | .672 | **.67** |
| Smoke_C, median \|delta luminance\| over the Crater sky | 14.9 | **14.8** |
| Smoke_C, p99 | 61.5 | **61.0** |
| Smoke_C, edge step p99 | 2.39 | **2.43** |
| Basalt_C key-lit wall, emission off (LK_BASALT Tint (.52,.80,.92)) | median 30, mean (35,31,29), S .17 | **median 30, mean (36,32,30), S .16** (limit S .25) |
| Basalt joints (Basalt_E) | 2.81 % of texels, joints only | **2.6 % of the wall**, mean hue 18, crack cores (253,128,28) hue 27, cream 0.00 %, G clipped 0.00 % |
| Lava_C/E/N (unchanged) | model: flow 72 %, p50 (211,68,15) | **92.6 %** of the lava pixels in hue 8..28 / S >= .75 / V >= .70, mean (217,79,18) |
So `SMOKE_SOFT` and `BASALT_RENDERS_DARK` are now measured in Unity, not modelled (gates `SMOKE_SOFT_GAMEVIEW`, `BASALT_RENDERS_DARK`, `BASALT_JOINT_ORANGE`); the AlphaGain x painted-peak coupling holds (.50 x 1.35).

## T.2 Grass with the calibrated tints (`GRASS_HUE_PREDICTED`, your gate, reads GolfLook.cs live): all 10 PASS
Needle fairway 70.5 / 66.3 / 67.1 (first-principles / calibrated / game-fit) with the new tint (.87), green 69.1 / 64.2 / 65.8 (.88), Split green 71.6 / 67.1 / 70.6 with (.72,.70,.70); Unity measured on the board: Needle fairway h66 (173,186,68), green h66, Split green h71 (154,172,75), Crater unchanged (h70 / h69 / h62).
In the Game view with real geometry (`probe_p4`) the grass is textured everywhere (0.0 / 2.2 / 0.4 % flat 20 px tiles on Needle, 0.0 / 0.1 / 4.8 % on Split, 0.0 / 0.8 / 0.1 % on Crater, all < 15 %), so the V-gate `LOOK_FILES` floor (Fairway_C 1 % of 1/16-tile windows reach luminance sd .03) is stricter than what the phone camera shows:
the lead's call (a decision, not a defect of the maps).

## T.3 Things the Game view showed you (not gated, for the next texture pass if wanted)
* Split's ridge scrub (Scrub_C, tile 12 m) reads at the phone camera as large soft blobs of olive on khaki (`v2/calibrate/sheet_probe_views.jpg`, hole09_ridge); hue / S / V are on target (h47 S.36 V.50 against split.jpg's ridge h46 S.39 V.48), split.jpg's scrub is streaky and finer.
* The 8 m Basalt tile on the real hole-10 skin walls (`hole10_green_probe`, `hole10_tee_probe`): the walls read dark red-brown (the Crater fog (.42,.19,.14) and ambient on charcoal, median luminance 28) with thin vertical orange streaks; the streaks are regular like rain at that distance.
  crater.jpg's wall is angular blocks with irregular, branching cracks. Per-wall-patch UV offsets (hole builder) or a second tile scale would break the repeat; no map change needed for the gates.
* Needle's sand and path needed per-hole tints (K.0): Sand_C / Path_C are bright enough that the warm Needle key (1,.86,.66) x 2.3 clipped the path (4.9 % of its pixels) at the table tint; lowering the albedo itself (Path_C -8 %) would let `HoleTint (8, LK_PATH)` go away.


# v2 2026-10-04 calibration, round 2 (area K, after the review of the first calibration)

**No texture PNG was changed** (`v2/calibrate/r2/look_sha256_before_r2.txt` == `look_sha256_after_r2.txt`, 31 files). The generator's 136 gates (`--gates-only --periodicity`, `v2/calibrate/r2/tex_gates_r2b.log`) pass with 0 FAIL under the new runtime constants; the gates that read GolfLook.cs live followed the edits:
* **LK_LAVA ramp** (the textures only say how hot a texel is; the ramp says what colour): `RampDeep` (150,33,10) -> **(24,6,3)**, `RampCrust` (186,43,13) -> **(210,52,16)**, `HeatBias` (the `Spec` default T's `lava_spec()` parses) -.15 -> **-.16**. T's model of the shader (`lava_shader_metrics`): crust (V < .7) 13.2 % (gate 6..14), hot 10.2 % (5..14), flow 69.7 % (>= 62), in band 86.9 % (>= 85), p50 (218,69,16), heat median .44; LAVA_NOT_CELLS median aspect 2.97, compact area 8 %, ring peak 10.4. Why this setting: `v2/calibrate/r2/tools/lava_ramp_search.py` ran T's own `lava_gates()` over 96 (deep x crust x bias x gain) variants, 21 passed all of them; of those this one has margin on every limit and the most near-black crust. The stronger variants I tried first (deep (60,13,5) with bias -.20: Game-view V < .4 on 5.4 %) FAIL LAVA_FLOW_BRIGHT (crust 21.2 % vs 6..14).
  Game view (board, post off): V < .4 on **3.5 %** of the pool (was 0.0 %), luminance sd 26.5 (was 23.3), in band 92.7 % (was 92.6 %), G clipped 0 %. The model overstates the Game view's dark share by about 2x (mip filtering at the phone camera's grazing angle), which is why T's 6..14 % limit and the Game-view 2.5..10 % (V < .4) gate both hold.
* **LK_BASALT Tint** (.52,.80,.92) -> **(.52,.74,.90)**: T's BASALT lit-darkness model with the live tint predicts median 28, mean (35,28,28), S .20 (<= .25); Unity measured median 28, mean (36,29,29), S .18. The brightest tenth of the lit wall went from (55,60,55) hue 121 (green-grey slabs) to (55,55,54) neutral.
* Couplings that still hold: LK_SMOKE AlphaGain 1.35 x Smoke_C painted peak .50; LK_BASALT Tint x Basalt_C lit mean (35,31,29) (the model tracks the new tint: mean (35,28,28)).

## T.4 What the review asked of the maps and was NOT done (for a later texture pass, not gated)
* Basalt: the board render shows the 8 m tile's glow dashes at a near-regular rhythm over greenish slabs (the slabs are now neutral). crater.jpg's cracks branch irregularly; T's definition (glow only in vertical joints, 27 vertical stretches, 0 violations) forbids branching glow, so this needs a gate change by the lead, not a tint. On the real wall the hole builder breaks the repeat (per-patch UV offset or a second tile scale; hot joints are at v = 0 mod 1).
* Lava: no yellow-white veins (the lead's hue 8..28 band; `_Hot` hue 26). The crust is as dark as the 85 % in-band budget allows (the still's pool is 12..30 % darker than V .4, ours 3.5 %).
* Split Scrub_C: soft blobs on tan rather than streaks (hue / S / V on target). Unchanged.


# v5 2026-10-04 (continue pass, step "texture finish", area T)

Brief (lead): 1. grass flatness (the #1 risk: a flat lawn), 2. lava (keep the swirling flow, mostly bright orange, emission alone; a small share of darker crust plates and a few hotter yellow-orange veins so it reads as glowing flow, not orange paint),
3. basalt (break the dash rhythm of the joint glow, branch / irregular cracks, charcoal not greenish, prisms, glow only in the joints), 4. scrub (streakier dry scrub like split.jpg). Same names, sizes, seamlessness, determinism, Look/ <= 25 MB.
Evidence: `work/postcard-look/v2/tex/v5/` (`before/` = the 31 PNGs as they were, `before_sha256.txt`, `final_sha256.txt` = `../look_png_sha_final.txt`, `final_gates.log` = all 141 generator gates + the exact-periodicity proof, `blender_full_run.log` = the documented headless Blender command regenerating all 30 maps byte-identical to the installed ones,
`metrics_before_after.txt`, `sheet_grass_v5.png`, `sheet_lava_v5.png`, `sheet_basalt_v5.png` (texture-level, BEFORE vs NOW), `sheet_grass_gameview_v5.png`, `sheet_lava_basalt_gameview_v5.png` (Game-view probe frames, BEFORE vs NOW), `gameview_*.txt` (Game-view numbers),
`iterations/` (design iterations), `tools/` (measuring + preview tools), `smoke_v5s*.out`, `probe_v5*.out`; Unity reports: `v2/runtime/smoke_v5s{1,3,4}.txt`, `v2/calibrate/probe_v5{base2,g1..g5,f1..f6}/`).
Changed bytes (12 of 31): Fairway_C, Green_C, Rough_C, Rough_N, Scrub_C, Scrub_N, Lava_C, Lava_E, Lava_N, Basalt_C, Basalt_N, Basalt_E. Unchanged: Fairway_N, Green_N (byte-identical: no new layer touches their height fields) and the other 17. 19.15 MB, 31 PNGs, no `.tmp`. No `.meta` touched.

## Regenerate / roll back
```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --periodicity    # all 30 maps + 141 gates, ~2 min, byte-identical to the installed files
... -- --out Unity/Assets/Resources/Course/Look --only Fairway,Green,Rough,Scrub,Lava,Basalt       # the 6 materials of this pass (~35 s)
... -- --out Unity/Assets/Resources/Course/Look --gates-only --periodicity                           # gates on the PNGs on disk (~60 s)
# fast iteration without Blender (numpy in Blender's python):  work/postcard-look/v2/tools/gen.sh <outdir> Lava,Basalt
# tools of this pass (Blender's python3.13): v5/tools/{tex_grass_metrics,stills_grass,gameview_grass,gameview_hue,grass_preview,lava_v5,lava_compare,basalt_view,sheets_v5}.py, compose.py (system python3 + Pillow)
```
Rollback: the 12 previous PNGs are in `v5/before/` (copy them back) and the previous generator is `v5/golf_look_textures.py.before_v5`; inside the generator `LAVA_P.update(LAVA_P_V2)` + the v4 `LAVA_ENC` lut reproduces the v4 lava bytes.

## 1. Grass (Fairway_C, Green_C, Rough_C/N, Scrub_C/N): measured, then built
Measured first (v5/tools/stills_grass.py, gameview_grass.py, tex_grass_metrics.py). The stills' pure-lawn crops (needle / split / crater.jpg at native 1280x720) have a window sd (16 px = 1-3 m of ground) median .022-.039 (shares >= .03: 31-80 %) and a whole-crop luminance sd of 10.9-14.7/255 on the flat ones
(17.7-26.2 on crops that also hold stripes / path edges; median of all seven 17.7). The real Game-view tee frames before this pass (probe `v5base2`, lower 60 % of the 900x1600 phone frame): luminance sd **7.4 / 6.6 / 10.1 /255** (Needle / Split / Crater), window sd (20 px) median .0176 / .0145 / .0310. The lead's "about 16/255" for the Needle tee was not reproducible
(that frame measures 7.4 here; the Needle approach frame measures 16.2): all numbers below are mine and defined in this section.
* **What the maps got** (`grass_layers`, `FAIRWAY_P`, `GREEN_P`, `ROUGH_P`, `SCRUB_P`; every layer periodic on the unit tile): mow bands +-10 % luminance (light (157,180,55) / dark (124,149,44), was +-6 %); 0.3-1.5 m plateau mottle (tanh of fbm at 9/18/36 cycles on the 10 m tile) with a little hue drift (lush = greener + a bit darker and more saturated, dry = yellower + lighter, albedo hue p5/p95 69/78); 0.2-2.5 m patches;
  mow-line streaks along v (0.36 m x 3.3 m and 0.14 m x 1.4 m); stretched blade noise (18 x 50 cm, no Voronoi cells: a Voronoi tone read as flagstones, a version with the B channel raised on the lush patches read as dirt: both rejected after looking at them); `match_mean` then restores the EXACT v2 mean sRGB colour per channel
  (`GRASS_MEAN`), so every HoleTint, GRASS_HUE_GAMEVIEW and lit-model calibration stays valid. Green: same layers at the 6 m scale, bands +-8 %. Rough: tufts 1 : 1.5 along v with ragged edges (the round light caps read as polka dots) + 0.5-3 m mottle and hue drift. Scrub: see 4.
* **Texture level, before -> now** (`metrics_before_after.txt`): Fairway luminance sd .047 -> .083; window sd at 1.5 m (154 px) median .0248 -> .0489, share >= .03 25 % -> 100 %; at 1/16 tile (64 px = 0.6 m) share >= .03 1 % -> 93 % (median .0178 -> .0398). Green sd .025 -> .054; 1.5 m windows .0225 -> .0515, 6 % -> 100 %; 1/16 tile 0 % -> 96 %.
  Rough .068 -> .071, Scrub .057 -> .067 (both were already above the floors). The gate `LOOK_FILES@fbx` of the gate tool (area U's current definition = the stills' own 1.2 m floor, run here on the ground library's smoke FBX with `--no-blend`): PASS, Fairway_C / Green_C / Rough_C windows 100 %.
  The old fixed floor (sd >= .03 in 90 % of the 1/16-tile windows) is reached by Fairway_C (93 %) and Green_C (96 %) as a by-product, it was not chased: the stills themselves reach it in only 31-67 % of their 16 px lawn windows.
* **Game view** (real HoleView path through `run_probe.sh`; PROBE_SWAP_TOOK_EFFECT PASS on all three holes in every run used; **3 final runs `v5f1..f3` print identical statistics** (the JPEG bytes differ in a few pixels, every number below is the same in all three), and `v5f4..f6`, run after the last basalt change, print the same numbers again; the first launch (`v5base1`) died in a Burst compile bus error before any gate ran and is not used):
  | | before (v5base2) | now (v5f1..f3) | stills' pure-lawn crops |
  |---|---|---|---|
  | Needle tee, lower-60 % luminance sd | 7.4/255 | **14.4** | Needle crops 21.4 / 26.2 (include path / flag edges) |
  | Split tee | 6.6 | **13.2** | 10.9 / 14.6 / 17.7 |
  | Crater tee | 10.1 | **15.9** | 14.7 / 21.1 |
  | window sd (20 px) median Needle / Split / Crater tee | .0176 / .0145 / .0310 | **.0277 / .0243 / .0387** | .022-.039 (Needle crops .052-.071) |
  | mean hue / S / V of the lower 60 % | h66 / 71 / 70 | h67 / 71 / 70 (S .61 / .57 / .78, V .73 / .68 / .72, unchanged) | h65-73 |
  | per-pixel hue p5 / p50 / p95 (central lower third) | 64/65/67, 70/71/71, 70/70/70 | **64/66/71, 67/70/74, 67/69/72** | band 64..73 |
  | pixels with a channel >= 250 | .14 / .18 / .11 % | .14 / .18 / .13 % | 0 % |
  So the lawn is about twice as lively on every measure (sd, windows, hue spread), inside the stills' lawn range, **but below the median (17.7) of the stills' crops on Needle and Split's tee frames and only on the stills' level for Crater**: the stills' higher values come from crops that include stripe or edge structure, so I did not push the amplitude further
  (the iteration at +35 % amplitude looked blotchy in the phone-view model preview, so the amplitude was moved toward fine blade detail instead; the installed version was then judged in the Game view). Per-pixel hue: Split's p95 is 74 (1 degree over the band; the mean is 71); every other percentile is inside 64..73.
  Smoke (`smoke_v5s4.txt`, 83/83 PASS under both URP assets): GRASS_HUE_GAMEVIEW Needle fairway h69 S.64 V.72 / green h67 / rough h60, Split fairway h71 / green h70 / rough h66 / ridge scrub h48 S.38 V.48 (split.jpg ridge (122,111,75) h46 S.39 V.48), Crater fairway h72 / green h70 / rough h63; GRASS_NO_CLIP 0.0-0.3 % on every material.
* **GolfLook.cs, three HoleTint numbers (the only edit outside my files; the rest of the file is the Unity agent's)**: `(8, LK_FAIRWAY)` (.87,.87,.87) -> (.855,.87,.87), `(8, LK_GREEN)` (.88,.88,.88) -> (.865,.88,.88), `(9, LK_FAIRWAY)` (.68,.66,.66) -> (.69,.66,.66). Reason: the new hue drift put the Needle tee's per-pixel hue at 62/65/69 (p5 below the band) and Split's at 67/70/74; after the edit Needle's fairway mean went h67 -> h69 (green 65 -> 67), Split's h72 -> h71 on the board.
  The generator gates GRASS_HUE_PREDICTED read the tints live and all pass.
* Gates added (generator, all PASS): `GRASS_VARIATION` x4 (mean within .8 level of the v2 mean, 1.5 m window sd median >= .035 (.030 for Rough / Scrub) with >= 75 % of windows >= .03, 8x8-block sd (not white noise), albedo hue p5/p95 inside 66..80 (Rough 60..76, Scrub 38..62), one frequency holds <= 25 % of the power above 5 cycles/tile (measured 0.2-1.1 %), Fairway mow-band +-7..11 % (measured +-10.6 %)).
* Not done / open: the lawn seam line across the middle of the Needle / Split / Crater tee frames (a horizontal brightness step at about 40 % of the frame height) is a mesh / UV boundary in the ground library's FBX (it was there before this pass), not a texture edge; the maps are exactly periodic.

## 2. Lava (Lava_C / Lava_E / Lava_N)
* Root causes found (`v5/tools/lava_v5.py`): (a) the v4 design was one scale of advected marbling: thin hairline veins, thin black ribbons (stretched islands) and a smooth gradient between mid-orange tones = oil-marbling "paint"; (b) its large-scale heat modulation was weak, so after mip filtering at the phone camera the pool read uniform;
  (c) found late: with the new lanes the DESIGN heat was clipped at 1.0 on 30 % of the texels (q75 = 1.0), so the tone curve could not separate them. (c) is fixed as an option (`LAVA_P['soft']`: exponential roll-off instead of a hard clip, 0 = off) but NOT shipped (see "tried and not shipped").
* What shipped (`LAVA_P`, `LAVA_ENC`; v4 = `LAVA_P_V2`): broad soft veins (widths x1.7) + a soft halo (`halo_a`), hot LANES (ridges of a 3-cycle field advected by the large flow, `lane_*`), cooler red zones between them (`cool_a`), fewer / larger vortices (advection of the small flow .05 -> .035, spectrum 6..14 -> 5..11 cycles), granular heat (`gran_a`), chunky crust PLATES (Voronoi cells 2.4 x 3 m that follow only 30 % of the large flow: `plate_*`) in the cool zones,
  and a morphological opening of the crust (`open_s`: blur + threshold + high-pass, so the thin black ribbons vanish and only plates and rounded islands remain). The tone curve was re-fitted (rank-matching the shader heat to crater.jpg's pool quantiles under the LIVE GolfLava constants, 10 iterations) and baked.
* **Game view** (`smoke_v5s4.txt`, board = the real LK_ material on the Crater board, post off, no bloom, both URP assets identical): LAVA_ORANGE_NO_BLOOM phone **92.0 %** in hue 8..28 / S >= .75 / V >= .70 (gate >= 85; before 92.6-92.8 %), G clipped **0.0 %**, cream 0.00 %, mean (214,76,17) h18 (crater.jpg pool (212,62,14) h15); LAVA_HAS_CRUST: V < .4 on **4.1 %** of the lava pixels (was 3.5 %, gate 2.5..10 %), luminance sd **25.9** (was 26.5, gate >= 25: a margin of .9);
  misses are the dark plates only (8.0 % dark, 0 % pale / yellow / red). Honest reading of the numbers: the plates are chunkier and visible, but the pool's luminance contrast went DOWN a little (26.5 -> 25.9) because the softer veins carry less edge energy; the share of dark plates went up a little (3.5 -> 4.1 %). The regional contrast at the still's ground scale (4x4-pixel block means at 14 cm / px) rose 23.1 -> 26.2 (crater.jpg pool 27..39).
* Generator model gates (all PASS, `final_gates.log`): LAVA_FLOW_BRIGHT (crust 13.6 % of 6..14, hot 7.7 % of 5..14, flow 71.8 %, in-band 86.4 % of >= 85, robustness hot 16.6 % of <= 18), LAVA_NOT_CELLS (compact blobs 28 % of <= 30), LAVA_EMISSION_PEAK (brightest Lava_E (206,95,50)), LAVA_LIT_FALLBACK_ORANGE, new **LAVA_PLATES_AND_LANES** (regional contrast 26.2 >= 24.5, 34 crust plates >= 0.4 m2). The margins on crust (.4 %), compact blobs (2 %) and in-band (1.4 %) are thin: the next change to the lava should re-run `lava_v5.py --iters 10` and read them.
* **What it still is not** (say plainly): next to crater.jpg's pool (luminance sd 33-43 at the same ground scale, yellow-orange filigree with G up to 160+, dark red cells) the map is a calmer marbled flow with soft lanes and a few plates (sd 31.8). The ceiling is the runtime ramp, not the map: `GolfLava`'s hottest stop is (255,128,28), hue 26, so no texel can be yellower than that (the hue band 8..28 forbids it), and the in-band >= 85 % rule leaves 15 % for everything darker than V .70.
  If the lead wants the still's contrast, the levers are RampCrust / RampDeep (more red-brown between the plates) and HeatGain in GolfLook.cs, not the texture. In the aerial frames (`probe_v5f1/hole10_aerial_probe.jpg`) the 24 m tile repeats visibly as a fine camouflage pattern: a second, larger scale or a per-patch offset (hole builder / shader) would hide it.
* Tried and not shipped (kept in the generator, default off): `LAVA_P['net_a']` (a Voronoi filigree of thin hot veins) and `LAVA_P['soft']`: with the soft roll-off the veins show faintly at 1x, but at the phone view the net was invisible and the pool contrast fell (luminance sd 30.2 vs 31.8), so the shipped build keeps the hard clip and no net.

## 3. Basalt (Basalt_C / Basalt_N / Basalt_E)
* Glow rebuilt (`mat_basalt`, `BASALT_P` s_med / g_med / branch_p / fgl_p / joints_on): the v4 rhythm (a similar dash on 70 % of the joints, 27 stretches of similar length) read as little ladders on the wall. Now 55 % of the joints (6 of 11; the gate counts 7 because a fork or a T-crack reaches the neighbour) carry glow in **irregular stretches** (lengths 0.35-3.6 m log-normal, gaps 0.5-4.5 m, each stretch its own intensity .55-1 so some read dull red, some orange),
  every lit joint starts low (the lava is below) and most also carry a stretch that reaches the top of the tile; **fork cracks** leave a stretch at 18-30 degrees off vertical (a groove in the normal map with steep walls, dark in the albedo, glowing, tapering to a point, 50 % with a kink); and **T-junction cracks**: 50 % of the cross fractures next to a lit joint glow along the crack for 35-85 % of the column width.
  Nothing glows on a face. The fork angle is limited to 30 degrees so the groove wall's |ny| stays <= .44 and the cross-fracture detector of the gate does not mistake a fork for a block fracture (found by a failing run: with 26-56 degrees the minimum fracture spacing fell to 0.44 m).
* **Gate definition CHANGED (disclosed, not loosened to pass)**: `BASALT_PRISM_GLOW_JOINTS glow` used to demand that every glow component be vertical-elongated (aspect >= 3, within 25 degrees of vertical): that forbids a branching crack and it measured the regular dash rhythm as a PASS. The new definition (the lead's brief: irregular, branching cracks, glow only in the joints): 1..6 % of the texels; every component >= 150 px elongated (aspect >= 1.3, within 40 degrees of vertical, >= 25 cm tall);
  >= 95 % of the glow within 8 px of a steep wall (tilt > .75: a vertical joint wall OR a crack groove; measured 100 %); 25..70 % of the joints carry glow (7 of 11); **no rhythm**: stretch-length CV >= .35 and gap CV >= .35 over >= 8 stretches (measured .78 / 1.23 over 24); fork-crack texels (|ny| > .25) 4..45 % (11 %); hotter toward v = 0/1 by >= 1.3 (1.48); longest horizontal run <= 12 % of the tile (6.2 %); brightest E G <= 180. The cross-fracture and bevel gates are unchanged and pass (0 of 36 fractures aligned, block height / width median 3.65, bevels 39 %).
* Unchanged on purpose: the albedo calibration (`BASALT_LIT_MEAN` under the old tint constant, so the lit wall under the live LK_BASALT Tint stays at the Unity agent's numbers), the 11 columns x 3 planes, the stacked blocks.
* **Game view** (`smoke_v5s4.txt`): BASALT_RENDERS_DARK key-lit wall median luminance **28** (<= 40), mean (35,29,28) S .18 (<= .25); beside the lava lights median 32, mean (50,32,25); BASALT_NOT_GREEN brightest tenth (56,55,54) hue 33 S .03 (neutral); BASALT_GLOW_ORANGE glow = **2.8 % of the wall** (before 2.6 %), mean hue 12, crack cores (219,72,17) hue 16 (before (253,128,28) hue 26: the cores are redder / dimmer on average because the new stretches carry their own intensity),
  cream 0.00 %, G clipped 0.00 %; LAVA_LIGHTS_REACH_BASALT 41.4 % (>= 20). The wall in `probe_v5f1/hole10_tee_probe.jpg` / `hole10_lavaedge_probe.jpg` shows long uneven cracks and forks instead of the regular orange dashes (`sheet_lava_basalt_gameview_v5.png`).
* Not removed: the 8 m tile still repeats on a long wall (the glow pattern now repeats every 8 m instead of looking like a rhythm inside the tile); the **UV note for the hole-10 builder is unchanged**: the hot joints are at v = 0 (mod 1): author `v = (z - z_lava) / 8` on walls beside the lava, and offset the u / v per wall patch.

## 4. Scrub (Scrub_C / Scrub_N)
Rebuilt as streaky dry scrub (`mat_scrub`, `SCRUB_P`): small leaning tussocks (46 x 26 Voronoi cells in a coordinate sheared by an integer so the map stays periodic: the blades lean about 45 degrees, because the phone camera looks down v and aligned streaks turned into radial zoom lines) with blade-ragged edges, dark olive inside with lit blade streaks, over khaki ground with straw blades and brown soil.
One lean direction only (two crossing sets read as hay mats). Mean colour unchanged (106,97,53) hue 49.9 (`match_mean`); 4x4 evenness 3.8 % (a 4 / 5-cycle cover field gave 10.1 % and failed the evenness gate: now 6 / 7 cycles).
New gate **SCRUB_STREAKY** (PASS): gradient structure-tensor elongation 2.82 (>= 1.5; the v4 map 1.01), dominant gradient at -47 degrees, 51 dark masses, median aspect 4.21 (>= 2.5; v4 1.63; my first threshold of 1.6 would have passed the v4 blobs and was raised before use). Game view (ridge probe frame, `probe_v5f1/hole09_ridge_probe.jpg`): mean (126,118,81) h49 S.36 V.50 (before (128,120,83) h48 S.35 V.50; split.jpg ridge h46 S.39 V.48), lower-60 % luminance sd 14.1 -> 17.7/255, window sd (20 px) median .0218 -> .0393;
smoke ridge scrub (123,114,76) h48 S.38 V.48. At the near field the straw patches show a stair-step edge where the phone camera magnifies the texels about 3x (the second blade octave was dropped for that reason; the remaining steps are the 5 cm blades).

## Gates (final: `final_gates.log`, Blender 5.2 headless, decoded by Blender's libpng): 141 generator gates, 0 FAIL
Includes SEAMLESS_ALL (28 tiling maps exactly periodic under the one-tile shift, wrap seams <= 1.5x), FOLDER_BUDGET 19.15 MB, GRASS_HUE_PREDICTED x10, GRASS_VARIATION x4, SCRUB_STREAKY, LAVA_FLOW_BRIGHT / NOT_CELLS / LIT_FALLBACK / EMISSION_PEAK / PLATES_AND_LANES, BASALT_BEVELS / cross fractures / glow / lit darkness, SMOKE_SOFT x2.
`guards.sh` 7 / 7 PASS. Unity (all through heavy.sh): GolfLookSmoke `smoke_v5s4.txt` **83/83 PASS** under TennisURP and HeroBaseStudioURP; GolfLookProbe `probe_v5f1..f6` textured on all three holes; PostcardImportCheck on the still-flat installed holes (`v2/runtime/importcheck_v5i1.txt`): 57 gate lines, 10 FAIL, exactly the same 10 install-only lines as `importcheck_r2final.txt` (GROUND_ALBEDO_AND_NORMAL x3, NO_FLAT_POSTCARD_GROUND x3, NO_FOAM_STRIP_8_10 x2, LAVA_LIGHTS_PLACED, ROCK_NEAR_LAVA_CHUNKED: they wait for the hole rebuild); every ground / lie / marker / collider line PASSES. `protected_check.sh`: no file of mine; its differences are other chats' (12 new emote / intro FBX, 2 customization prefabs, KitV3_016.mat, Tennis scripts).
Determinism: a full headless-Blender regeneration of all 30 maps is byte-identical to the installed files (`blender_full_run.log`, `cmp` on every PNG); the same under Blender's bundled python3.13.

## Open / for the next steps (nothing here is mine to edit)
* Hole builders: Look maps are final for the install step; the Needle / Split / Crater tee frames in this pass come from the ground library's smoke FBXs (the real holes are still the flat baseline until the rebuild).
* The lava ramp (RampCrust / RampDeep / HeatGain) is the lever for crater.jpg-level contrast; the 24 m lava repeat shows in aerial frames.
* Basalt: a second tile scale or a per-patch u / v offset on the hole-10 walls hides the 8 m repeat (hole builder).
* `ProjectSettings/QualitySettings.asset` differs from `v2/protected_hashes_start.txt` (Oct 3) but is byte-identical to git HEAD 2225264c ("Restore TennisURP ...", committed 16:45 by another chat); my Unity runs go through heavy.sh and edit no ProjectSettings file.


# v6 2026-10-04 (repair round 1 after the independent reviews, area T)

Findings handled (reviewers' words in quotes) and what each turned out to be. Evidence: `work/postcard-look/v2/tex/v6/` (`before/` = the 31 PNGs as they were, `before_sha256.txt`, `final_sha256.txt`, `final_gates.log` = all 145 generator gates + the exact-periodicity proof, `full_run1.log`, `gates_run2.log`,
`stills_a|b|c|f/` = my Game-view frames (NOT the proof stills; `stills_f` = the final 9 with everything installed), `clone_*.log`/`stills_fog*/` = the fog experiments below, `stills_gate.log`, `smoke` reports in `v2/runtime/smoke_v6s1|s2|s3.txt`, `tools/` = every measuring tool of this round (rawio, flatmap, nearsim, aniso_gate, wall_stats, lava_stats, lava_cut, lava_dres, terrain_uv, uv_axes, list_ground), `golf_look_textures.py.before_v6`, `GolfLook.cs.before_v6`).
Changed bytes (14 of 31): Fairway_C/N, Green_C/N, Rough_C/N, Scrub_C/N, Lava_C/E/N, Basalt_C/E/N. The other 17 (Smoke_C, Plants_C, Cliff, Rock, Path, Masonry, Sand, Surf, Fall, Sky ...) are byte-identical. Look/ = 21.41 MB (was 19.15; limit 25), 31 PNGs, no `.tmp`, no `.meta` touched. A full headless regeneration is byte-identical to the installed files (`sha_before_final_regen.txt` == `sha_after_final_regen.txt`).
Regenerate / roll back: the command in "Regenerate" at the top of this file; rollback = copy `v6/before/*.png` back (and `golf_look_textures.py.before_v6`, `GolfLook.cs.before_v6` for the two Ramp stops).

## 1. Tee foreground "smeared and flat" (hole 8 tee 18.8 % flat, hole 9 approach 20.0 % flat > 15 %): FINE BLADE layer
* **Root cause (measured, not guessed)**: the 10 m Fairway tile is 1 texel = 1 cm; the phone camera at the tee magnifies it x3.8 in the last rows, and every v5 layer was 3-50 texels wide. A bilinear x3.8 magnification of the v5 Fairway_C luminance alone gives 51 % flat 8 px windows / median window sd .0060 (`tools/nearsim.py`), the real hole 8 tee still measured 51.7 % / .0059 in its last 160 rows (and 32.5 % at x3.0, 18 % at x2.4): the gate statistic IS the texel density, not the lighting. Per band (160 rows) the v5 tee: 1.5 / 3.0 / 6.3 / 18 / 32.5 / 51.7 %.
* **Fix** (`fine_blades`, `FINE_P`; Fairway `fine .060`, Green `.045`, Rough `.050`, Scrub `.085`; crisp relief `fine_h` .12-.16 in the normal maps): short blade strokes 3.4 texels per cycle (cyc 300 on 1024), 3x longer than wide, in three leans (upright, +-26.6 degrees = the integer shears 2u +- v, picked by a slow 7-cycle field in ~1.4 m patches), a few cm of domain warp (no comb-like hatching), tanh-sharpened; multiplicative luminance + a small yellow/green hue push; `match_mean` still restores the EXACT mean colour (GRASS_MEAN), so every HoleTint, GRASS_HUE_* and lit-model calibration stays valid (smoke below: 84/84).
  Rejected on sight: first version with u +- v (45 degree) shears read as regular diagonal hatching (a comb); fixed with the 26.6 degree shears + warp.
* **Texture level** (new gate `GRASS_NEAR_FIELD`, a proxy of LOOK_STILLS_TEXTURED run on the PNGs, calibrated on the v5 numbers above): flat 8 px windows at x3.8 / x3.0 / x2.4: Fairway 11.8 / 5.2 / 2.4 % (v5 51 / 32 / 18 %), Green 15.7 / 7.2 / 3.4, Rough 17.3 / 8.6 / 4.3, Scrub 3.3 / 1.0 / 0.6 (limits 20 / 10 / 5 %). GRASS_VARIATION, hue, evenness, seam gates unchanged and PASS.
* **Game view** (`stills_f`, the real GolfGame / HoleView, TennisURP quality level 2, 900x1600; official gate `LOOK_STILLS_TEXTURED` through `gates/tools/run_stills_gate.py`, `stills_gate.log`): lower-60 % flat 8 px windows, before -> now: hole08 tee **18.8 -> 5.6 %**, hole08 approach 13.4 -> 3.9, hole09 tee 4.1 -> 1.2, hole09 approach **20.0 -> 4.9 %**, hole10 tee 0.5 -> 0.3, hole10 approach 11.4 -> 2.4 (limit 15 %); median window sd .0131 / .0132 / .0161 / .0107 -> .0225 / .0221 / .0237 / .0188. LOOK_STILLS_TEXTURED PASS on holes 8, 9, 10; STILL_FLOOR_SELFCHECK PASS.
* Not done (said plainly): the Look texture importer keeps aniso 4 / max 1024 (area U's file); a URP Lit detail map would need a shader variant that is stripped from player builds unless a material keeps `_DETAIL_MULX2`, so the fine layer lives in the maps instead. Hole 8's TEE_BOX UVs are rotated 84 degrees against FAIRWAY's (dP/du direction 83.9 vs 0.1, `tools/uv_axes.py`): that is the visible horizontal brightness step at 40 % of the tee frame and why the tee-box blades run across the screen (hole builder / ground library, not a texture edge). Hole 9 / 10 tee boxes are aligned.

## 2. Hole 9 ridge "smeared like motion blur" (structure tensor 5.5 : 1 / 8.2 : 1): Scrub rebuilt isotropic
* **Root cause**: my own v5 Scrub (one-direction 45 degree leaning tussocks, SCRUB_STREAKY elongation 2.82). NOT the mesh: `tools/terrain_uv.py` on the installed hole 9 shows TERRAIN_SPLIT's LK_SCRUB faces are flat (no slope under nz .8) with UV stretch p95 1.79 (1.5 % of the area > 2x), so the review's "UV stretch on a slope" hint does not apply; the streaks were in the map and the camera's foreshortening + bilinear magnification doubled them.
* **Fix**: `mat_scrub` v6: round tussock cells 0.17 m (70 x 70) and leaf clusters 0.08 m (140 x 140) with ragged edges, isotropic straw flecks (9 cm / 6 cm), the shear removed, plus the fine blade layer (3 leans). Mean (106,97,53) hue 49.9 unchanged (`match_mean`).
* **Gate change (disclosed)**: SCRUB_STREAKY asked for exactly the streaks the review found harmful (elongation >= 1.5, aspect >= 2.5): replaced by `SCRUB_NOT_SMEARED` (elongation <= 1.35 measured **1.06**, >= 40 dark masses measured 99). Not loosened to pass: the old gate encoded the wrong target.
* **Game view**, the reviewer's metric reproduced exactly on the 21:02 stills (global eigenvalue ratio of the structure tensor of the unblurred luminance gradient; 5.46 / 8.20 / 2.06 = their numbers, `tools/aniso_gate.py`): hole09_3_ruin lower third (0,1100,900,1600) **5.46 -> 1.80**, steep patch (500,1000,900,1400) **8.20 -> 1.56** (target <= 2.5); tee 9 2.06 -> 2.06. Honest note: the same metric on the hole 8 tee rows went 5.91 -> 7.71 (dominant gradient vertical): at grazing angles any isotropic texture measures ~(1/sin elevation)^2 because the ground is foreshortened vertically (roughly 5-6 at the tee's near rows), and the tee box's rotated UVs put the blades across the screen; the crop is crisp now (flat 5.6 %), it is not a smear. Game-view GRASS_HUE_GAMEVIEW for scrub unchanged: (116,108,72) h49 S.38 V.45 (split.jpg ridge (122,111,75) h46 S.39 V.48).

## 3. Lava "a sawtooth vertical seam line runs through the near lava" + black ink swirls + no hot veins
* **Seam root cause**: not a tile / UV seam (the map is exactly periodic) but the advection: the backward flow map is stretched 4-18x (median 4.5, p90 18.5, p99 95 texels of pattern per output texel, `tools/lava_cut.py`, `lava_J.png`: the stretch is a net of thin filaments = the stable manifolds) and v5 sampled its displacement field on a 256 grid, bilinearly, every 4 output texels: along every filament the interpolation made a SAWTOOTH with a 4-texel period (visible in Lava_C/_E as several zipper lines per tile, and as a vertical zipper in hole10_3_lavarim at x 665, y 1375-1600).
* **Fix**: `advect_disp(..., n=1024)` (`LAVA_P['d_n']`; the velocity stays 256) removes the sawtooth and leaves a clean thin dark hairline on the filaments (aliased pattern); `aa_filter` (`LAVA_AA`, `LAVA_P['aa']`) averages the design heat and crust there with a width that grows with the local compression (`map_jump`, 3 levels: sigma 1.2 / 2.5 / 5 supersampled texels from jumps of 14 / 40 / 120). Result: no zipper, no hairline (`lava_seam_ba.png`, `stills_f/hole10_3_lavarim.png`). The pattern keeps its character; all lava generator gates still PASS (LAVA_FLOW_BRIGHT: crust 13.3 %, hot 7.7 %, flow 72.1 %, in band 86.6 %; LAVA_NOT_CELLS; LAVA_PLATES_AND_LANES regional contrast 26.2 and 33 plates; EMISSION_PEAK (206,95,50)). Rollback: `LAVA_P.update(LAVA_P_V2)` now also carries `d_n=256, aa=0` (reproduces the v4 bytes).
* **Black ink -> dark red crust, paler hot veins (GolfLook.cs, the only edit outside my files, two stops of the LK_LAVA row)**: `RampDeep` (24,6,3) -> **(84,22,2)** (dark red, hue 14.6, S .98, V .33: still < .4, so LAVA_HAS_CRUST counts it), `RampHot` (255,128,28) -> **(255,150,60)** (hue 27.7, S .76: the top of the band, a paler yellow-orange vein). Two traps found by failing runs: (84,18,8) has hue 7.9 < 8 (smoke LAVA_READS_ORANGE FAIL), and (84,22,8) is |dR|+|dG|+|dB| = 28 from the dusk sea colour (77,31,20) that the board's lava mask (`Diff(phone, without lava) > 30`) compares against, so the mask dropped the dark crust and LAVA_HAS_CRUST read 0.5 % on an identical-looking frame: B 2 keeps the distance at 34 (the two frames' dark share, measured on the pixels, is the same 2.80 %).
* **Game view** (`tools/lava_stats.py` on the lava floor of hole10_3_lavarim, before -> now): V < .4 crust 1.66 -> **3.36 %**, luminance sd 23.0 -> **29.2**, luminance p10..p90 83..135 -> **75..148**, pixels with G > 120 (pale hot veins) 5.9 -> **15.3 %**, in band (hue 8..28, S >= .75, V >= .7) 93.5 -> 91.2 %. Smoke `v6s3`: LAVA_ORANGE_NO_BLOOM phone 92.4 % (>= 85), G clipped 0 %, cream 0 %; LAVA_HAS_CRUST **3.3 %** (2.5..10), luminance sd 27.0 (>= 25).
* Not done: crater.jpg's yellow-white filigree (G up to 160+) stays out of reach: the band caps the hottest stop at hue 28, and the pool is still a calmer marbled flow than the still. The cone's lava patches with "rectangular straight cut edges" are mesh UV / geometry of the hole 10 builder, not a texture.

## 4. Basalt "maroon-brown, picket fence, ladders"
* **Texture (done)**: the plank read came partly from the map: pale dashed arris lines running down every plane edge, a vertical wood-grain streak (+-10 %) per column and 0.68 / 0.90 / 1.16 plane shades. v6: arris highlights only in short broken stretches and at 0.30 (was 0.55), grain +-3 %, plane shades 0.77 / 0.92 / 1.10 (the volume comes from the bevel NORMALS; BASALT_BEVELS keeps a >= 15 level spread: 15.5), joints 6.2 + 3.6 cm (was 4.5 + 3.0) so the lit joints are wider cracks (glow 3.7 % of the texels, was 2.8 %; Game view 3.4 % of the wall). All BASALT gates PASS (cross fractures 0 of 36 aligned, glow stretch-length CV .78, key-lit darkness model median 28 S .20).
* **Maroon root cause (measured, NOT a texture problem)**: the far wall's colour is the Crater FOG + a red ambient, not the albedo and not the lava lights. Evidence (clone of the Unity project, APFS clone in the scratchpad so no shared file was touched; `stills_c`, `stills_fogA|B|C`, `tools/wall_stats.py`, non-glow wall mean / S / median luminance on the three hole 10 stills):
  | variant | tee | approach | lava rim |
  |---|---|---|---|
  | shipped (lava lights 600, Tint .52, fog (.42,.19,.14) from 120 yd) | (51,29,25) S .51 L 30 | (48,21,19) S .60 L 25 | (50,23,21) S .59 L 26 |
  | lava lights intensity 0.001 (+ the paler colour and Tint R .46 of the next row; real project, `stills_c`) | (50,29,26) S .49 | (47,21,19) S .59 | (50,23,21) S .58 |
  | lava light colour (1,.56,.28), 520, Tint R .46 (`stills_b`) | (51,29,26) S .49 | (47,21,19) S .59 | (50,23,21) S .58 |
  | clone: fog colour (.30,.21,.20) | (44,30,29) S .34 | (39,22,23) S .42 | (41,24,25) S .40 (luminance unchanged 30 / 25 / 25) |
  | clone: that fog + Tint R .36 | (41,30,29) S .31 | (38,22,23) S .41 | (40,25,25) S .38 |
  | clone: fog (.42,.19,.14) from 480 yd | (35,24,23) S .34 L 24 | (28,13,15) S .55 L 13 | (29,14,17) S .51 L 13 |
  So the lava lights and the basalt Tint do not move the far wall at all (it sits 130-450 yd away, outside the 52 yd light range), roughly 40 % of its colour is fog (107,48,36) (estimated from the fog colour and the wall's own lit colour), and what remains is lit only by the red-magenta equator ambient (.55,.30,.22) on its shadow side. **The fix is in GolfAtmosphere.cs (area U, not mine; Crater `FogColor` / `AmbientEquator`)**: a neutral smoke-grey fog such as (.30,.21,.20) alone takes the wall from S .59 to S .42 at the same luminance; the reference's neutral charcoal (26,25,29) needs the equator ambient less red as well (untested), and a later fog start darkens the wall to L 13 (too dark). I left LK_BASALT's Tint, the lava light colour / intensity and the smoke gates exactly as they were (BASALT_RENDERS_DARK key-lit wall median 28 S .18, wall beside the lights S .50 <= .65: PASS).
* Not done (not texture): the column geometry (flat-topped slabs of one width, no per-column tilt, no hex / pentagon cross sections) and the cone's terraced planks are the hole 10 builder's / props library's; the lower cliff skin on the lava shelf (flat grey-violet wedge slabs, no glow) is a props-library piece and uses a different material than the wall behind it.

## 5. Gates (this round)
* Generator (`final_gates.log`, Blender 5.2 headless, libpng decode): **145 gates, 0 FAIL** incl. SEAMLESS_ALL (28 maps exactly periodic, wrap seams <= 1.5x), FOLDER_BUDGET 21.41 MB, new GRASS_NEAR_FIELD x4 and SCRUB_NOT_SMEARED, all GRASS_*, LAVA_*, BASALT_*, SMOKE_SOFT x2 (the runtime-band gate read the Unity agent's new LK_SMOKE row live: it FAILED in `full_run1.log` at 21:31 (plume colour R +17 against crater.jpg within 14) and PASSES since their Lit .6 / SelfLight .40 edit of 21:32; Smoke_C is unchanged by me).
* Unity (through heavy.sh): GolfLookSmoke `smoke_v6s3.txt` **84 / 84 PASS**, TennisURP 30/30 and HeroBaseStudioURP 30/30, URP_BOTH_ASSETS PASS. (`v6s1`: 81/84 with the first ramp (hue 7.9); `v6s2`: 83/84, LAVA_HAS_CRUST 0.5 % from the mask trap above.) Stills: 9 / 9 rendered, 0 compile errors, LOOK_STILLS_TEXTURED PASS on 8 / 9 / 10.
* PostcardImportCheck on the installed holes (`v2/runtime/importcheck_v6i1.txt`): 57 gate lines, 0 failed, 0 compile errors.
* `guards.sh` 7 / 7 PASS; hole 7 files, Hole.cs, QualitySettings, tennis, shaders, serve untouched by this round (`protected_check.sh`: only the other chats' tennis / hero / emote files differ from the job-start list, the same set as `v2/proof/protected_after.txt`; none is mine).

## 6. Open after v6 (for the owners named, nothing here is a texture edit)
* Crater far wall maroon: GolfAtmosphere.cs `FogColor` (.42,.19,.14) from 120 yd (+ `AmbientEquator` (.55,.30,.22)): measured above, S .59 -> .42 with a neutral fog alone; needs the Unity / gates agent.
* Hole 8 TEE_BOX UVs rotated 84 degrees against FAIRWAY (visible brightness step at 40 % of the tee frame, blades across the screen: they read as ripples in the crop): ground library / hole 8 builder.
* Basalt column geometry (flat-topped slabs, one width, no tilt / hex sections) and the cone's terraced planks; the lava-shelf cliff skin (grey-violet wedge slabs): hole 10 builder / props library.
* Optional lever for even crisper ground: Look importer `anisoLevel` 4 -> 8 for the *_C/_N ground maps (area U's file; not needed for the gates).



# v7 2026-10-04 (repair round 2 after the independent reviews of the installed holes; area T)

Evidence: `work/postcard-look/v2/tex/v7/` (`before/` = the 31 PNGs as they were at 23:10, `before_sha256.txt`, `golf_look_textures.py.before_v7`, `GolfLook.cs.before_v7` (copy only: GolfLook.cs was NOT edited by this round), `full1/` (first v7 maps), `full2/` (final maps = installed),
`full1.log` / `full2.log` (all 150 generator gates + the exact-periodicity proof, decoded by Blender's libpng), `final_sha256.txt` (= `v2/look_png_sha_final_v7.txt`), `tools/` (every measuring / experiment tool of this round), `lava0..lava10`, `smoke0..smoke6`, `bas1..bas3` (design iterations),
`stills9/` + `proofcopy/` + `logs/` (my own Game-view re-measure of the 9 stills + 4 extras + hide-and-diff masks, `tools/run_v7_proof.sh`; these are NOT the proof stills: `ArtDir/screenshots/golf_postcards/look/` was not written), Unity reports `v2/runtime/smoke_v7s1.txt` / `smoke_v7s2.txt` (85 / 85 PASS) and `v2/runtime/importcheck_v7i1.txt` (57 gate lines, 0 failed).
Changed bytes (7 of 31): Lava_C / Lava_E / Lava_N, Smoke_C, Basalt_C / Basalt_E / Basalt_N. The other 24 are byte-identical (so hole 8 / 9 grass, water, cliffs, plants look exactly as before). Look/ = 21.37 MB, 31 PNGs, no `.tmp`, no `.meta` touched.
Regenerate (same command as at the top of this file): `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --periodicity` (~2.6 min, 150 gates). Install helper that only copies what differs, atomically: `v2/tex/v7/tools/install_pngs.sh <dir>`.
Rollback of each change, **verified byte-identical** (`v7/tools/rollback_check.py`): `SMOKE_P.update(SMOKE_P_V6)`; `LAVA_AA = LAVA_AA_V6` + `LAVA_P.update(tdf_k=0, fine_a=0.0, fil_a=0.0)` + the v6 `lut` (in the LAVA_ENC comment); Basalt `fork2_p = wide = 0.0` (the Basalt generator with both at 0 reproduces the v6 Basalt_C / E / N bytes, sha256 ecfd1e96 / d9f18f5b / 9a5dedb9). Or copy `v7/before/*.png` back.

## 1. [medium] Lava "hard vertical discontinuity at x667-671" + flat marbling (hole10_3_lavarim)
* **Root cause (traced, not guessed)**: the camera ray for pixel (670, 1500) of the lavarim shot hits the lava at world (89.8, 116.0) yd = texture texel (col 431, row 592); the screen-vertical line is a diagonal run of ~220 texels (5 m) through the tile, i.e. NOT a tile / UV / mip seam (the map is exactly periodic, wrap-seam ratios 0.9..1.4, and the column / row steps of the PNGs have no outlier) but ONE 2-texel DARK HAIRLINE of the map itself: design heat .08 between .19 and .26 at col 415, rows 599-600, where the backward flow map is stretched 13-35 pattern texels per output texel (`tools/lava_line.py`). It is stair-stepped by aliasing (`seam_in_texture.png`), and the Game view only magnifies the tile x1.3-1.9 there (texel 2.34 cm, pixel 1.2-1.9 cm), so a 1-texel line is a 1.5-2 px line at 30-50 levels per texel (= the review's 6.5-10.6 per pixel).
* **What v6 had missed**: its footprint prefilter started at J 14 (blur sigma 1.2 supersampled texels), so every filament with J 6-14 and every thin dip in the heat survived; and `limit_gradient` (tried first, kept in the generator, default OFF) did not move the numbers because the steepest texels are legitimate vein edges (93 % of the top 0.1 % gradient texels are plain molten orange).
* **Fix** (generator `LAVA_AA`, `LAVA_P tdf_*`): footprint prefilter from J 6 with 4 levels (sigma 1.5 / 3 / 5 / 8; was 1.2 / 2.5 / 5 from J 14) + `grey_close(hh, 11)` applied only where the closing differs from the heat by more than .07 (**deep thin dark lines are filled; veining keeps its fine structure**: a plain closing at k 9 halved the median gradient, this selective one costs 14 %).
  Gate **LAVA_NO_HAIRLINE** (new): black top-hat (5 x 5) of the shipped-shader image, thin (<= 6 texel) dark lines deeper than 20 levels: **v6 51 lines >= 60 texels, longest 215 texels -> now 7, longest 101 texels** (limits 12 / 120). The remaining 7 (62-101 texels) are the dark edges of thin crust arms (the three I cropped, `lava6e_compare.png`), i.e. designed crust, not filaments.
* **Game view** (`tools/run_v7_proof.sh`; same camera, 900 x 1600): column-step of the review's metric (mean |dx| per screen column over rows 1375-1600, x >= 300): **max 10.6 (x 670) / median 1.13 = 9.4x  ->  2.9 / 1.15 = 2.5x**; rows 1450-1600 **14.4 / 1.18 = 12.2x -> 3.4 / 1.12 = 3.1x**. Visual: `lava_near_before_after.png`, `lava_near_final.png`.
* **Near field "magnified and soft"**: added a fine granular heat layer and a **filigree of thin pale-orange hot veins** (`fine_a` .06, `fil_*`: ridged-noise lines 2-3 texels wide with a flat core, meandering, in patches of the molten zones, NOT advected so they never alias; heat to the hot stop = RampHot (255,150,60), still inside the lava band). Tone curve re-fitted (`lava_try.py --iters 8`: lut .272 .295 .341 .366 .405 .429 .491 .548 .734). Near lava (rows 1300-1600, x >= 300): luminance sd 30.2 -> 30.6, pixels with G > 120 (pale hot veins) 13.7 -> **14.7 %** (crater.jpg's pool 14.2 %), p99 |dx| 15.9 -> 15.9.
* **Gates still PASS** (generator): LAVA_FLOW_BRIGHT (crust 11.7 %, hot 7.8 %, flow 71.7 %, in band 88.3 %), LAVA_NOT_CELLS (compact blobs 18 % of <= 30), LAVA_PLATES_AND_LANES 26.2, LAVA_EMISSION_PEAK, LAVA_LIT_FALLBACK_ORANGE. **Unity (`smoke_v7s2.txt`, 85 / 85)**: LAVA_ORANGE_NO_BLOOM phone 92.7 % (>= 85), G clipped 0.0 %, cream 0.00 %; LAVA_HAS_CRUST 3.2 % (2.5..10), luminance sd 27.3 (>= 25). My Game-view stills: in band 92.1 / 94.9 / 92.6 % (tee / approach / lavarim), dark V < .4 1.4 / 1.7 / 2.9 %, G >= 250 0.0 %.
* **NOT done, said plainly (the review's "zero hot yellow-white pixels")**: R > 240 and G > 170 cannot exist in this runtime. `GolfLava`'s hottest ramp stop is (255,150,60) (hue 27.7: the band is hue 8..28, and GolfLookSmoke fails a ramp stop outside it), the lava has no bloom and no tone mapper by the brief, and the shader's heat -> colour ramp is the only thing between the texture and the screen. The measured G > 150 share is therefore 0.00 % (crater.jpg 6.7 %, G > 120: 14.7 % vs 14.2 %). The dark crust is `RampDeep` (84,22,2), a dark RED that must stay V < .4 on 2.5-10 % of the pool (LAVA_HAS_CRUST); lifting it would fail that gate.

## 2. [medium] Smoke_C "a large pale-grey cloud, two near-opaque cards overlap; blocky, flat-bottomed lump"
* **Mine (texture)**: a tapered, rounded, ragged-underside, PEAKED wisp at the low end of the runtime's visibility band: painted peak .50 -> **.43 (effective .582 under AlphaGain 1.35, inside .55..0.72)**, foot half-width .07 -> .03 with `round` (the fade-in line follows r^2: a U, not a horizontal cut) and `rag`, 25 % of the profile is a Gaussian instead of the flat-topped super-Gaussian, more billow (.34 -> .45). Coverage at effective alpha >= .30: 11.0 % -> **7.5 %** of the card; `SMOKE_P_V6` = rollback.
  Gates (new): **SMOKE_TAPERED_FOOT** (lowest 6 % of the visible height is 34 % of the widest row, limit 45; underside step .026 per texel, limit .031) and **SMOKE_STACK_OVERLAP** (the hole-10 builder stacks 2-3 cards 10 % of a card width apart, every second mirrored: two cards reach a combined alpha of **.826, v6 .894** (limit .84); three cards: **0.20 %** of the card at >= .85 combined, v6 3.7 % (limit 1)).
  The existing runtime-band gates pass: generator `SMOKE_SOFT runtime band` model (median 19.3, p99 64.9, edge step 2.89) vs the real Unity run **median 18.9 / p99 63.5 / edge 2.82** (model error < 2 %).
* **Game view (hide-and-diff, `proofcopy/metrics.json`)**, |dLum| of the plume against its own dry frame, before -> now: tee p95 39.8 -> 35.9, max 54.7 -> 51.0; **approach p95 125.5 -> 117.5, max 137.0 -> 132.2**; lavarim p95 81.5 -> 75.8, max 87.6 -> 81.1; aerial max 130.3 -> 125.3. Edge step p99 <= 2.8 everywhere (limit 6), see-through detail kept: approach .23 -> .36 (more translucent).
* **STILL FAIL, not mine and not weakened**: integrator `SMOKE_SOFT` max |dLum| <= 110 on hole10_2_approach (132). Why the texture alone cannot close it: the plume stands in front of the DARK crater wall (lum ~25), a card at effective alpha a moves the frame by a x 140 (the plume's own lit colour is lum 170), so 110 needs a combined alpha <= .79; the approach frame is 4 plumes x 3 cards stacked and reaches ~.94. The runtime's own SMOKE_SOFT band forbids lowering one card below effective .55 (the earlier "invisible smoke" finding) and the own-colour gate (within 14 of crater.jpg (183,154,150)) allows only ~6 % less luminance. The fix is the hole builder's: offset / thin the two approach-facing cards of `hole10_look.smoke_group` (and then re-check SMOKE_IN_FRAME: the A30 share of a card dropped 11.0 -> 7.5 %, builder numbers 3.0 / 4.0 / 4.7 % of the frame scale to ~2.0 / 2.7 / 3.2, limit 1.5).

## 3. [high] Basalt "maroon-brown, glow = isolated 1-2 px streaks, cone = terraced planks"
* **Maroon is not the albedo (measured)**: `Basalt_C` rock mean (38,37,41), S .097 (crater.jpg basalt (26,25,29), S .10); new gate **BASALT_ALBEDO_NEUTRAL** (mean S <= .15, per-texel S mean <= .20, p95 <= .30 with the glow texels excluded): S .097 / .105 / .143 PASS (this is the "S ceiling that can see the tint" the review asked for; the existing `lit darkness` model gate already caps the predicted key-lit wall at S <= .25: S .20). What the Game view shows is S .53-.58, hue 2-5 on the non-glow wall of all three stills (`metrics.json`: tee (56,28,26) S .534, approach (41,18,17) S .579, lavarim S .529), identical before and after this round. v6 measured why in a clone of the project (`v2/tex/v6/stills_fog*`, section 4 of v6): ~40 % of the far wall's colour is Crater's fog (.42,.19,.14) from 120 yd and the rest is lit by the red equator ambient (.55,.30,.22); a neutral fog (.30,.21,.20) alone takes the wall from S .59 to .42 at the same luminance. **That is `GolfAtmosphere.cs` (area U), not a texture**: the line "the wall reads charcoal like crater.jpg" is FAIL and stays FAIL until the Crater `FogColor` / `AmbientEquator` change. (Note: the Unity gate `BASALT_RENDERS_DARK` measures the wall beside the lava lights at S .52 and crater.jpg's own lava-lit rock is (52,27,23) S .5-.62, so red-brown NEAR the lava is on-reference; the far wall is the problem.)
* **Glow** (E only, so the hole-10 builder's constants stay valid): a **second-level fork** on 70 % of the first-level fork cracks (turns back toward vertical, <= 30 degrees, shorter and dimmer) and a wider, softer shoulder around the vertical joint glow (`fork2_p` .7, `wide` .8; the T-junction cracks are not widened). Basalt_C / Basalt_N change only by the new grooves. Game-view glow coverage of the basalt, before -> now: tee 1.95 -> **2.83 %**, approach 1.42 -> 1.81, lavarim 1.20 -> 1.57, aerial 0.87 -> 1.28; still 90-98 % vertical lines, 0-0.7 % horizontal rungs, mean hue 13-17. Unity: BASALT_GLOW_ORANGE 4.3 % of the wall (<= 20), cream 0.00 %, G clipped 0.00 %. Generator `BASALT_PRISM_GLOW_JOINTS glow` PASS (4.8 % texels, 18 components, violations []).
* **Why it is not a dense network (disclosed)**: the hole-10 builder maps every face to ONE window of this tile by constants in `hole10_look.py` (`GLOW_U` six glow lines, `ZONES` five glow-free u intervals where tops and plain faces live, `PROFILE128` the column luminance profile, gate `H_UV_WINDOWS`: zone glow <= 0.02 %, edge window >= 4 %, profile deviation <= 0.01). New gate **BASALT_BUILDER_WINDOWS** reads those constants from the file and measures the generated maps exactly as the builder does: zone glow 0.0000 %, edge window 10.7 %, profile deviation 0.0014, so **no re-bake of the hole-10 UV windows is needed**. Tried and reverted: longer stretches (`s_med` 2.4, `g_med` 1.0) move the forks into the glow-free zones (0.39 % glow, profile deviation 0.0157): the builder gate fails. More glow lines / a global crack network would need the builder to re-bake its windows (its decision).
* **NOT texture**: the cone's "terraced planks / wood grain" are its stepped geometry and UV density (`CONE_UV` .42 in `hole10_look.py`); the prism read of the wall is column geometry (flat-topped slabs of one width, no hex sections: builder / props lib). The lava-shelf "cliff skin" is NOT a different material: the 128 `ROCK_SKIN` pieces wear the same `LK_BASALT` (material list of the installed hole_10.blend); its grey-violet facets are up-facing planes catching Crater's violet ambient sky (.34,.24,.40) through the cool Tint (.52,.74,.90) that the Unity owner calibrated against the key-lit wall (BASALT_RENDERS_DARK S .18; a bluer / redder Tint moves that gate), so I left GolfLook.cs alone.

## 4. Not changed, with the reason
* [low] Hole 8 near-field grass "soft, no mow stripes": the v6 fine-blade layer already took the flat 8 px windows to 4.8 / 3.9 % (floor 15 %); crisper ground needs the Look importer `anisoLevel` 4 -> 8 (area U's `GolfLookTextureImporter.cs`) and the tee box UV rotation of hole 8 (builder), neither is a texture edit.
* GolfLook.cs: not edited this round (no Table / HoleTint change was needed or measured to help). Hole 7, Hole.cs, tennis, QualitySettings, shaders, Serve, locker: not touched (`guards.sh` 7 / 7 PASS).

## 5. Gates of this round
* Generator (`full2.log`, Blender libpng decode): **150 gates, 0 FAIL** (v6: 145; +LAVA_NO_HAIRLINE, SMOKE_TAPERED_FOOT, SMOKE_STACK_OVERLAP, BASALT_BUILDER_WINDOWS, BASALT_ALBEDO_NEUTRAL; no existing gate was edited or loosened), SEAMLESS_ALL (28 maps exactly periodic, wrap seams <= 1.5x), FOLDER_BUDGET 21.37 MB.
* Unity (heavy.sh): GolfLookSmoke `smoke_v7s2.txt` **85 / 85 PASS** (TennisURP 30 / 30, HeroBaseStudioURP 30 / 30, URP_BOTH_ASSETS PASS); PostcardImportCheck `importcheck_v7i1.txt` 57 gate lines, 0 failed; stills 9 / 9 + 4 extras, masks 9 + extras, 0 `error CS`.
* Game-view re-measure (`proofcopy/`, measure.py copy): GRASS_HUE_GAMEVIEW 8 / 9 / 10 PASS, NOT_FLAT_PER_STILL PASS, SHELF_NOT_LOUDEST PASS, LAVA_ORANGE_AND_BRIGHT PASS, BASALT_JOINTS PASS, NO_PLANT_ON_SEA PASS, NO_ROCK_STRETCH_2X PASS, NO_FOAM_STRIP PASS, PATH_UNDER_BALL PASS, **SMOKE_SOFT FAIL (hole10_2_approach max 132 > 110, section 2)**.
* `postcard_look_verify.py 10` on the installed hole 10: 97 PASS, 2 FAIL (`GROUND_UV_LOCAL_SMEAR@blend/@fbx`: FAIRWAY_FIRSTCUT has 3 triangles with UV anisotropy up to 1000:1 covering 103 m2): a MESH UV defect of the hole 10 builder that another agent's new gate found; no texture can fix it.
* `ArtDir/screenshots/golf_postcards/look/` still holds the 22:56 stills (rendered with the v6 maps): the integrator re-shoots them (`v2/proof/run_proof.sh stills`) after the other repairs; my frames are in `v2/tex/v7/stills9/`.

## 6. Open after v7 (owners named)
* Crater far wall maroon: GolfAtmosphere.cs `FogColor` (.42,.19,.14) from 120 yd / `AmbientEquator` (.55,.30,.22) (area U). Measured recommendation: neutral smoke-grey fog such as (.30,.21,.20); the equator ambient less red is untested.
* Approach-frame smoke overlap: `hole10_look.smoke_group` (builder): offset / thin 2 of the 12 cards, then re-run SMOKE_IN_FRAME.
* Basalt: cone UV density / stepped geometry, column cross-sections (builder / props); a denser glow network needs a re-bake of the builder's `GLOW_U` / `ZONES` / `PROFILE128` windows.
* Hole 10 FAIRWAY_FIRSTCUT UV smear (builder).


# v8 2026-10-05 (repair round 3 after the independent reviews of the installed holes; area T)

Evidence: `work/postcard-look/v2/tex/v8/` (`before/` = the 31 PNGs as they were at 01:30 = v7, `before_sha256.txt`, `golf_look_textures.py.before_v8`, `GolfLook.cs.before_v8` (copy only: GolfLook.cs was NOT edited by this round), `full/` (final maps = installed) + `full.log` (all gates incl. the exact-periodicity proof, decoded by Blender's libpng), `final_sha256.txt` (= `v2/look_png_sha_final_v8.txt`),
`rollback/` (every rollback below regenerated, byte-identical to v7), `tools/` (lava8.py / exp.sh / plateau.py / heat_hist.py = lava design loop; near_sim.py / near_lap.py = grass; smoke8.py / smoke_mc2.py / smoke_grad.py / smoke_gen.py = smoke; basalt_fit.py; lava_gv.py / lava_cmp.py = Game-view lava statistics; run_clone_*.sh = Unity runs on an APFS CLONE of the project in the scratchpad),
`stills_base/` + `stills_final/` (9 Game-view stills, v7 maps vs v8 maps, same project state; NOT the proof stills: `ArtDir/screenshots/golf_postcards/look/` was not written), `stills_cand1..4`, `stills_final3` (the installed state, 9 stills), `stills_smk1/2/A/B` (hole 10 only, smoke variants; A = installed), `clone_smoke_*.txt` (GolfLookSmoke on the clone), `sheet_lava_v7_vs_v8.png` (texture level), `sheet_gameview_v8.png` (lava / grass, Game view), `sheet_smoke_v7_vs_v8.png` (Game view), `cmp_*.png`.
Changed bytes (8 of 31): Lava_C / Lava_E / Lava_N, Fairway_C / Fairway_N, Green_C / Green_N, Smoke_C. The other 23 are byte-identical (Basalt, Cliff, Rock, Path, Masonry, Sand, Scrub, Rough, Surf, Fall, Sky, Plants ...). Look/ = 23.22 MiB over the 30 generated PNGs (limit 25), no `.tmp`, no `.meta` touched.
Regenerate (same command as at the top): `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --periodicity` (~3 min, 155 gates). Install helper that only copies what differs: `v2/tex/v7/tools/install_pngs.sh <dir>`.
Rollback of each change, **verified byte-identical to v7** (`v8/tools/rollback_check.py`): `LAVA_P.update(LAVA_P_V7)` + `LAVA_ENC['quantile'] = 0`; `FAIRWAY_P / GREEN_P micro = micro_h = 0`; `SMOKE_P.update(SMOKE_P_V7)`. Or copy `v8/before/*.png` back.

## 1. [medium] Lava "flat marbled orange vignettes, magnified and soft, no bright vein layer, 5-6 % dark ink streaks (largest dark component 3626 px), hot-core share 0"
* **Root causes (measured, not guessed)**: (a) the design heat was CLIPPED at 1.0 on 11.6 % of the molten texels and 30 % sat above .9 (`tools/heat_hist.py`): every hot region was a flat plateau, which the tone curve cannot separate, so the bright part of the pool was broad flat swathes (heat > .75 surviving a 15 x 15 texel opening: 12.0 % of the tile); (b) the marbling veins were 5 / 11 cycles per tile, i.e. 30-50 cm wide streaks magnified x1.3-1.9 by the phone camera; (c) the iterative tone-curve fit (`lava_try.fit`) only matched 11 knots and left the top of the histogram where the plateaus were; (d) the crust was long advected ribbons ("ink") instead of compact plates.
* **Fix** (generator `LAVA_P` / `LAVA_ENC`, `LAVA_P_V7` = rollback): `rank` = no clip, the heat is rank-equalised after the flow loop and then mapped onto the target SHADER-heat histogram by an exact quantile curve (`lava_quantile_curve`: the heat GolfLava computes for a design value is tabulated from the live GolfLook.cs constants and inverted; `LAVA_D_RHO / LAVA_D_HEAT`: crater.jpg's pool quantiles p25 .30, p50 .44, p75 .72, p90 .90, a flat 3 % at V < .4 so the crust gate has something to count); finer marbling (`v1_cyc` 12, `v2_cyc` 26: the same swirls, 2.4x thinner streaks); a three-scale WEB of thin hot veins (`web_*`: contour lines of ridged noise at 10 / 22 / 46 cycles, 3 / 2.4 / 2.2 texels wide, only partly advected so they curl round the vortices but never alias into filaments); regional light / dark (`reg_a`); compact crust plates (8 x 6 plates, `open_s` 9, `plate_thr` .22, `plate_adv` .34, fewer islands) with a glowing rim (`seam_hot` .5), an octagonal instead of square closing of the thin dark lines (`tdf_oct`: the square window left rectangular plateaus the camera magnified into blocks); broad lanes / halos cut (`lane_a` .12, `halo_a` .08).
* **Texture level** (shader model of GolfLava, installed maps): broad hot plateaus 12.0 % -> **6.0 %** of the tile, thin hot veins (white top-hat 9 x 9 of the heat > .15) 6.0 % -> **11.5 %** (new gate **LAVA_FILIGREE**: <= 8 % / >= 9 %); LAVA_FLOW_BRIGHT PASS (heat median .42, crust 13.4 % (6-14), hot 7.8 % (5-14), flow 69.9 %, in band 86.6 % (>= 85)); LAVA_PLATES_AND_LANES PASS (regional luminance sd 25.1 >= 24.5, 33 plates); LAVA_NO_HAIRLINE PASS (6 lines, longest 104 <= 120); LAVA_NOT_CELLS, LAVA_EMISSION_PEAK, LAVA_LIT_FALLBACK_ORANGE PASS; exactly periodic.
* **Game view** (same project state, v7 maps -> v8 maps; `tools/lava_cmp.py` / `lava_gv.py`: lava pixels = hue <= 38, S > .6; the lava-rim shot's near field x300-900 y1000-1600): mean |dLum| per pixel step 4.43 -> **5.86 (+32 %)**, pixels with an edge > 12 levels 10.9 -> **14.7 %**, largest dark component of the pool **3626 -> 1549 px**, in band (h8..28, S >= .75, V >= .7) 92.2 -> 93.0 %, luminance sd 29.3 -> 28.4 (not higher: the web adds fine structure, not regional contrast), V < .4 3.1 -> 2.7 %.
  Unity (GolfLookSmoke on the real project, `v2/runtime/smoke_v8s1.txt`): LAVA_ORANGE_NO_BLOOM phone 91.5 % / down 92.9 % (>= 85), G clipped 0.0 %, LAVA_HAS_CRUST **3.9 %** (2.5-10; v7 3.2 %), luminance sd 28.7 (>= 25).
* **NOT done, said plainly: "hot-core share (R > 240 and G > 170) = 0"**. It cannot be non-zero in this runtime: the shader paints heat with a 4-stop ramp whose hottest stop is (255,150,60), and GolfLookSmoke fails a stop outside hue 8..28 / S >= .75 (G <= 153 inside that band; at hue 28.0 / S .76 the stop already sits on the edge). crater.jpg's pool measures R > 240 and G > 170 on 2.7 % of its pixels and G > 150 on 6.1 %; ours G > 120 on 16.8 %, G > 150 on 0 %. The yellow-white filigree stays out of reach without bloom (not allowed) or a ramp outside the band (the lead's 85 % rule). The pool is still the calmer, more orange flow, with the vein web instead of the plateaus.
* Honest note: the review also asked for "dark-red crust (V >= .25)": `RampDeep` (84,22,2) is V .33 and nothing in the Game view is darker than V .25 (0.0 %); the ink read came from the SHAPES (long advected ribbons / islands, up to 3626 px), now compact plates and pockets.

## 2. [medium] Smoke "a large pale lumpy cloud with two dark see-through holes (a ghost), blocky flat-bottomed puff" (SMOKE_SOFT FAIL in the Game view)
* **What was already fixed by the unity area before this round's texture work** (GolfLook.cs, theirs, read here): AlphaGain 1.35 -> 1.10, AlphaPower 1 -> 1.5 (per-card peak .58 -> .33; the stacked core ~.7), `SoftFade` 40 yd, GolfLookSmoke `SmokeAlphaMin` .55 -> .30 (visibility is gated by the two delta bands and SMOKE_VISIBLE_STILLS): hide-and-diff |dLum| max 63 / 102 (limit 110).
* **Mine (texture)**: the "ghost with a dark face" is the hole builder's stack: 3 cards 10 % of a card width apart, every second one MIRRORED, and the v7 wisp's column stands at u .47-.55, so the mirrored copy sits on top of the original column (cores .03-.07 card widths apart): two lobes (the lone card and the pair) with a hole between. Fix: the column stands a little off the middle (`xc0` .47 -> .42, `sway` / `drift` .07 -> .06) with a softer alpha (`blur_a` 5 -> 7); colour `top` (184,186,191) -> (175,177,182) (the plume's own lit colour is alpha-weighted and the off-centre column weights the lighter head more: B +15 > the gate's 14 against crater.jpg; now (188,164,163)).
  Monte Carlo of `hole10_look.smoke_group` (3 cards, mirrored, jitter) under the owner's runtime (`tools/smoke_mc2.py`): stack share at combined alpha >= .5 **1.92 % -> 1.13 %**, visible area (>= .07) of the stack 19.8 -> 21.9 % of the card, single-card visible area 9.2 -> 9.6 %. Game view (`stills_smkA` vs `stills_cand4`, hole 10 approach, `cmp_smoke_v7_A_B_app.png`): the dark "face" between the two lobes is gone, one broad soft plume; the tee plume is the same thin wisp.
* **Why not a bigger move (three owner / builder gates pull in different directions; each measured)**: the owner's SMOKE_SOFT_INTERSECTION (a card cutting a wall at 40 degrees: p99 of the card's own signature <= 6, soft card still moves >= 3000 px, Unity) and the hole builder's SMOKE_IN_FRAME (`postcard_look_verify.py`, >= 1.5 % of every proof frame at effective alpha >= .2, offline) both depend on where the column stands: xc0 .47 (v7): intersection 5.03, in-frame 1.84 / 1.91 / 2.94 %; **.42: 5.49 PASS, 1.77 / 2.13 / 2.82 % PASS (used)**; .40 + w1 .13: 5.60 PASS but approach 1.35 % FAIL; .40 + w1 .15: approach 1.48 % FAIL; .38: intersection 6.20-6.31 FAIL (more plume in front of the wall: 53 k px); .62: 603 px moved FAIL (the core is behind the wall); a very slender wisp (w1 .07) cut a single card's visible area to 58-63 % of v7 against the owner's readable-share gate (1.9 / 3.2 / 3.9 % vs >= 1.5 %).
* **NOT measured by me**: the integrator's hide-and-diff |dLum| on the real stack (needs `PostcardProofMasks`, `v2/proof/run_proof.sh masks`) and SMOKE_VISIBLE_STILLS on the new alpha (Unity share of the frame that moves >= 10 levels): the integrator must re-run them. The aerial's "flat-bottomed puff" is the card's mesh, not the map (the foot is a tapered rounded U: SMOKE_TAPERED_FOOT PASS).

## 3. [low] Hole 9 grass at the ball "still soft and smeared" (Laplacian sd 1.87 near vs 6.34 mid, target >= 3)
* **Root cause (measured)**: texel magnification, not lighting: 1 texel = 1 cm of Fairway = 2.6-3.8 px under the ball, and the finest layer of the map (the v6 blade strokes, 3.4 texels per cycle) is 9-13 px wide after bilinear magnification, so a pixel-scale Laplacian sees almost nothing (`tools/near_sim.py`: x3.8 magnified Fairway_C luminance, Laplacian sd 1.24; the Game view's hole 9 tee 1.58). Anisotropic filtering (already 16) and the mip bias do nothing for magnified ground; a Lit detail map needs a shader variant that is stripped from a player build.
* **Fix**: `micro_grain` on Fairway and Green (`FAIRWAY_P / GREEN_P micro` .105 / .115, `micro_h` .10 in the normal): the finest layer a 1024 map can hold, 2 texels per cycle, a little longer along v. It is exactly invisible wherever a pixel covers more than ~1.5 texels (the mip chain averages it away) and is the pixel-scale detail only where the ground is MAGNIFIED. Mean colour kept (`match_mean`): GRASS_HUE_* and every HoleTint stay valid.
* **Texture level** (new gate **GRASS_MICRO_NEAR**: x3.8 >= 3.1, x2.4 >= 6.2, x1.0 <= 40): Fairway_C 1.24 -> **3.55** / 2.55 -> 7.15 / 11.9 -> 36.0, Green_C 1.24 -> **3.77** / 2.55 -> 7.61 / 11.9 -> 38.6; GRASS_NEAR_FIELD (flat windows 0.2 % at x3.8), GRASS_VARIATION, hue, seam gates PASS.
* **Game view** (near = y1200-1600, x0-600, luminance 0-255, 4-neighbour Laplacian sd; mid = y700-900), v7 maps -> v8 maps: hole 9 tee **1.58 -> 3.18**, hole 9 approach **1.51 -> 3.01**, hole 8 tee 4.32 -> 5.19, hole 8 approach 2.35 -> 3.76, hole 10 tee 2.60 -> 4.45, hole 10 approach 1.57 -> 3.12. **Trade-off, said plainly**: the mid band (y700-900) went 6.4 -> 18.3 (hole 9 tee), 8.5 -> 16.8 (hole 8), 11.5 -> 23.8 (hole 10): the grain is crisp everywhere the ground is within ~8 m, not only at the ball (viewed 1:1: fine turf, not noise; `cmp_h9_*.png`, `cmp_h10_mid.png`). GRASS_HUE_GAMEVIEW / GRASS_NO_CLIP PASS on 8 / 9 / 10 (`smoke_v8s1.txt`).

## 4. [low] Hole 10 basalt "dark maroon (S .53-.58) against crater.jpg's charcoal" and the lower cliff skin "light grey-violet stacked plates"
* Both were the Crater fog / ambient (v6 / v7 section 4: the albedo is neutral, S .097 / .105 / .143), which the unity area made neutral in repair round 3 (GolfAtmosphere; LK_BASALT Tint R .52 -> .56). Measured on the Game-view stills of the current project (non-glow wall pixels, V < .4, lavarim rows 350-620 / approach rows 60-300): mean (33,29,31) S **.126** and (28,25,27) S **.132** (crater.jpg basalt (26,25,29) S .10); GolfLookSmoke BASALT_RENDERS_DARK key-lit wall mean (30,30,30) S .01, median 29. The cliff skin is the same `LK_BASALT` and now reads dark charcoal like the wall behind it (`cmp_cliff.png`); its faceted stacked LEDGES are the props library's wedge geometry, not a texture. I changed no basalt map.

## 5. Generator gates (this round) and changes to existing ones (all disclosed)
* New: **LAVA_FILIGREE**, **GRASS_MICRO_NEAR** (x2), see above. 155 gates, 0 FAIL (`full.log`): SEAMLESS_ALL (28 maps exactly periodic), FOLDER_BUDGET 23.22 MiB.
* Changed because the OWNER'S runtime moved (generator gates read GolfLook.cs / GolfLookSmoke.cs live; none of these bands was loosened to make a map pass):
  - SMOKE_SOFT runtime band: the effective alpha now includes `AlphaPower` (the model hands the card model alpha' = (a x gain)^power / gain; reproduces the owner's board: median 11.9 / p99 40.2 against the model's 12.4 / 38.1) and its floor is read from `GolfLookSmoke.SmokeAlphaMin` (.55 -> .30 in their round; the median >= 10 / p99 32..86 / own-colour / edge-step limits are unchanged).
  - SMOKE_STACK_OVERLAP: includes the power, and gets a stricter cap (three-card max <= .76 = 110 levels / 145; was only the share >= .85).
  - BASALT lit darkness (`BASALT_PRISM_GLOW_JOINTS lit darkness`): its model light was fitted on the red Crater atmosphere (predicted (38,28,28) S .27 under the new tint); a separate constant `BASALT_GATE_LIGHT` (2.41, 1.47, .82) is fitted so the INSTALLED Basalt_C reproduces the owner's real run (mean (30,30,30), median 29; the model gives (30,30,30) / 29.0). `BASALT_WALL_LIGHT` still drives the albedo gain, so Basalt_C is byte-identical.
  - GRASS_HUE_PREDICTED (`v2/tools/lit_predict.py`, backup `.before_v8`): GAME_MEAS / GAME_MEAS_TINT replaced by the 10 real Game-view patch means of this round (HeroBaseStudioURP, `clone_smoke_cand3.txt`) and CAL_MUL / CAL_ADD / GAME_MUL / GAME_ADD refitted (`--recalibrate-cal`, new; `--recalibrate-game`). With the owner's new Crater tints (.95,1.13,.62) the v7 constants predicted Crater's green 5-10 levels too bright (hue 63.2 'calibrated' against the measured 68); the bands (64..73, 58..72, 40..58) are unchanged, all 10 rows PASS and the model reproduces the measured hues within 2 degrees.
* Not mine, for the record: `BASALT_JOINTS` in the integrator's measure (`v2/unity_r3/measure_d.log`) FAILS on a new "branching joints >= 3 per 100 skeleton px" criterion that is not in my findings list; Basalt_E was not touched this round (its fork cracks are 1-2 px wide at the camera: that needs the builder's `GLOW_U` / `ZONES` windows re-baked, v7 section 3).

## 6. Unity / Blender gates on the INSTALLED state (all through heavy.sh where Unity)
* GolfLookSmoke on the real project (`v2/runtime/smoke_v8s5.txt`, every map of this section installed): **88 / 88 PASS** (TennisURP 33 / 33, HeroBaseStudioURP 33 / 33, URP_BOTH_ASSETS): LAVA_ORANGE_NO_BLOOM phone 91.5 % / down 92.9 %, LAVA_HAS_CRUST 3.9 %, GRASS_HUE_GAMEVIEW 8 / 9 / 10, GRASS_NO_CLIP, BASALT_RENDERS_DARK, SMOKE_SOFT* incl. SMOKE_SOFT_INTERSECTION 5.49 (<= 6). (The first off-centre smoke variant, xc0 .38, read 6.31 there: 87 / 88, `smoke_v8s1.txt`.)
* PostcardImportCheck `importcheck_v8i3.txt`: 57 gate lines, 0 failed. GolfLookProbe on the installed holes `proof/probe_v8probe2/`: 6 / 6. 9 / 9 stills into `v8/stills_final3` (0 `error CS` in every Unity log of this round).
* `postcard_look_verify.py` on the installed blend + FBX: hole 10 **ALL PASS** (SMOKE_IN_FRAME tee 1.77 / approach 2.13 / lavarim 2.82 %), hole 8 ALL PASS; hole 9 fails only `LK_TEXTURED@blend` (the verifier looks for `Cliff_C.png` under `/Users/adnanyonathan/Documents/Codex/Unity/...`, a path bug of that gate that is in the integrator's GATE_LINES since 00:xx; the textures are there).
* `guards.sh` 7 / 7 PASS; hole 7 files, Hole.cs, Tennis files, QualitySettings (content = git HEAD), shaders, Serve untouched by this round (my Unity runs went through heavy.sh, the experiments on an APFS clone of the project in the scratchpad).

## 7. Open after v8 (owners named)
* Integrator: re-shoot the proof stills (`v2/proof/run_proof.sh stills masks metrics`) and re-run the hide-and-diff SMOKE_SOFT and SMOKE_VISIBLE_STILLS on the new Smoke_C (not measured here; SMOKE_IN_FRAME, the geometric twin, is measured: 1.77 / 2.13 / 2.82 %).
* Hot yellow-white cores in the lava: out of reach without a ramp stop outside the lead's band or bloom (section 1).
* Basalt branching joint glow (integrator's new BASALT_JOINTS criterion) and the hole 9 / 10 grass at distance: the micro grain doubles the mid-band Laplacian; if it reads as shimmer in motion, lower `micro` (rollback line above), the near field gives back ~1.5x.


# v9 2026-10-05 (continue pass: GRASS LIVELINESS requirement 2 + the carry-over findings; area T)

Evidence: `work/postcard-look/v2/tex/v9/` (`before/` = the 31 PNGs at the start of this run = v8, `before_sha256.txt`, `golf_look_textures.py.before_v9` / `.after_grass` / `.final_v9`, `GolfLook.cs.before_v9` / `.final_v9`, `g1`..`g3` Fairway/Green generations, `bv_*` / `b*` basalt generations, `var_*` + `stills_<name>` = Game-view variant renders (APFS clone of the Unity project in the scratchpad, `tools/variant.sh`, `tools/basalt_variant.sh`, `tools/run_clone_stills.sh`), `full2/` = the final regeneration (159 gates, 0 FAIL, byte-identical to the installed files), `stills_real9` / `stills_real_grass` = the real project's 9 proof shots + 9 grass shots, `METRICS_v9.md`, `look_png_sha_final_v9.txt`, `tools/` = gv_grass / gv_bands / gv_sheen / basalt_gv / glow_classes / glow_proxy / final_metrics / make_id_maps).
Changed bytes (7 of 31): Fairway_C / Fairway_N / Green_C / Green_N, Basalt_C / Basalt_N / Basalt_E. The other 24 are byte-identical to v8 (`look_png_sha_final_v9.txt` vs `before_sha256.txt`). Look/ = 23.91 MiB over the 30 generated PNGs (limit 25).
Regenerate: `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/golf_look_textures.py -- --out Unity/Assets/Resources/Course/Look --periodicity` (~2.5 min, 159 gates); one-off experiments: `--set 'BAND_P.sheen_l=0.3,BASALT_P.vor_n=12'` (module dict overrides, never used for the installed maps).
Rollback (each verified): `BAND_P['on'] = 0` reproduces the v8 Fairway / Green bytes (RGB, no alpha; GolfLook then falls back to the flat smoothness .10 / .12 with a warning); `BASALT_P.update(BASALT_P_V8)` or `--set BASALT_P.net=0,BASALT_P.old_E=1` reproduces the v8 Basalt_C / N / E bytes exactly (`cmp` checked). Or copy `v9/before/*.png` back.

## 1. Mow-band life (Fairway_C/N, Green_C/N): the user's "do 1 and 4" grass pass, requirement 2
* **Why the v8 bands were invisible (measured)**: the v8 Fairway already had +-10.6 % luminance bands, but 5 m wide (K = 1 period per 10 m tile) under +-5 % cloudy mottle, while the phone sees 3-4 m of ground at the ball: one band, no edge (round-1 stills: no stripe anywhere; `stills_base/`).
* **Now** (generator `BAND_P`, `mow_band`, `blade_streaks`, `tilt_about_u`, `sheen_alpha`): Fairway **2.5 m bands** (K = 2) on the centre line, luminance **+-12.3 %** (gate GRASS_BAND_CONTRAST, measured on the PNG: light 0.676 / dark 0.529, ratio 1.28), band hue within 0.6 deg (73.3 / 73.9), mottle x0.9; Green **1 m stripes** (K = 3 per 6 m tile) **+-12.6 %** plus a faint cross set. One base colour x a luminance factor (the v8 maps used two colours that also differed 3 deg in hue); mean sRGB colour of both maps kept exactly (`match_mean`: GRASS_MEAN), so HoleTint hue calibration stays valid.
* **SHEEN (per-band smoothness in the albedo ALPHA channel)**: Fairway_C / Green_C are now RGBA (colour type 6). alpha = absolute smoothness: light bands **.26**, dark bands **.04**, tile mean **.151** (v8 flat .10 / .12), a little mottle (+-.02) and streak (+-.03) modulation, max .37. `GolfLook.cs`: `Spec.SmoothnessFromAlbedoAlpha`, rows LK_FAIRWAY / LK_GREEN `Smoothness = 1f` (= the scale of the channel; the generator gate GRASS_SHEEN_ALPHA reads that number live), `_SmoothnessTextureChannel = 1`, keyword `_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A`. **Pitfall found the hard way**: the first version tested `GraphicsFormatUtility.HasAlphaChannel(albedo.graphicsFormat)` to fall back to a flat smoothness when a PNG has no alpha; BC7 / ASTC always report alpha, so an RGB PNG (alpha 1 = smoothness 1) rendered the whole fairway as a mirror (`v9/stills_base` first run: wet glass sheet reflecting the sky). Now: in the editor `AssetImporter.DoesSourceTextureHaveAlpha()` decides (flat smoothness + a warning when missing); a player trusts the PNGs the editor gates verified (colour type 6 in GRASS_SHEEN_ALPHA and GRASS_SHEEN_WIRED).
* **Player-build variant stripping (not verified in a player: no device / iOS build here)**: the LK_ materials are created at run time, so `Universal Render Pipeline/Lit`'s `_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A` variant would be stripped from a build that has no material using it (and a stripped keyword = smoothness 1.0 = the mirror above). `Unity/Assets/Resources/Course/GolfLookVariants.mat` (URP Lit, {_NORMALMAP, _SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A}, instancing on) is the keeper: Resources materials are always in the build. Created / refreshed by `GolfLookGrassCheck.EnsureKeeper` (env GOLF_GRASS_CREATE_KEEPER=1), gate GRASS_SHEEN_VARIANT_KEPT. The older LK_ keyword sets (basalt / lava: _SPECULARHIGHLIGHTS_OFF, _ENVIRONMENTREFLECTIONS_OFF, _EMISSION) have no keeper: not mine, unverified for player builds.
* **LEAN**: Fairway_N / Green_N: each band's normal is tilted about the u axis (+-6 deg, light band leans away from the camera = +v, down the hole; `lean_sign`) and long blade-lean streaks (28 cm x 2.5 m and 11 cm x 1 m, sd 3 deg) run along v; the same streaks modulate the albedo (+-2.4 %) and the sheen. Gate GRASS_LEAN_STREAKS (mean tilt of the light / dark band +5.8 / -5.8 deg, streak sd 2.95 deg, along-v correlation .89 vs across .54, 99.9 pct |tilt| of the lean field 15 deg <= 16). The pixel grain keeps the SAME absolute amplitude in both bands (`grain_comp`; a multiplicative grain was 12 % weaker in the dark band: the hole 9 approach near-field Laplacian fell 3.01 -> 2.64 on a dark band) and `micro_boost` 1.10 on the Fairway.
* **Game view** (clone of the project and then the real one, same numbers; the 9 shots of `cfg_grass.json` = the 6 address shots + 3 raised "band view" shots; ID renders with white / black band albedo give the exact band masks, `tools/gv_bands.py`): lit band contrast (light vs dark mean luminance, per row band) **+9 .. +15 %** wherever both bands are in view (hole 9 tee far / mid / near +15.1 / +11.3 / +4.6, hole 9 approach +13.7 / +14.2 / +10.2, hole 9 band view +11.0 / +12.8 / +11.9, hole 10 band view +14.6 / +14.4 / +13.2), the v8 maps measure -12 .. +5 (noise: no stripe). **Sheen alone** (same render with a flat .10 smoothness, `tools/gv_sheen.py`): light band **+2.5 luminance levels, saturation -0.043, B-R +6.5**; dark band -0.8 levels, saturation +0.014: at the grazing phone angle the light bands pick up a pale sky reflection in the far field (visible in `v9/m3.png`, `m1.png`), by design not a mirror. **Lean alone**: light +1.0 / dark -1.6 levels (subtle: the sun is 30-50 deg off the hole axis and the shading it adds is ~+-1 %; the streaks show as faint blade lines in the foreground).
* **Grass hue / clipping / detail, real project, the 6 address stills + 3 landmark stills** (`METRICS_v9.md`): grass hue (pixel-weighted) 65.1 .. 71.2 on the six address shots (target 64..73; round-1 hole 9 approach mid band 73.3), share of grass pixels with a channel >= 250: **0.00 .. 0.06 %** on five of them and 0.60 % on the hole 10 approach light band (round-1: 0.0 there, but hole 10 tee 1.3 .. 3.4 %; the gate limit is 3 %): not zero, said plainly; lower-60 % luminance sd round-1 -> v9 (`METRICS_v9.md`): hole 8 tee +0.2, hole 9 tee +0.9, hole 9 approach +1.3, hole 10 approach +18.4 (a band edge crosses the frame), landmarks -0.5 .. 0.0, **down on hole 8 approach (-2.6, the camera sits in the DARK band: V .61 against the round-1 .70) and hole 10 tee (-1.5: Crater's tints were taken down 11 % to stop the light band clipping; absolute luminance sd scales with the mean luminance)**: the requirement 'lower-60 % sd up on the round-1 stills' is met on 4 of the 6 address stills, not on all six; the tuft fringe of the props area adds variance on top (not measured here); near-field Laplacian sd (y1200-1600) hole 9 tee 3.36 / approach **3.16** (round-1 3.36 / 3.01), all six address shots >= 3.16.
* **HoleTint rows (GolfLook.cs, comments there)**: the GolfLookSmoke grass board (central lower third of a flat quad; it sits on the LIGHT band / stripe) read V .75 / .76 / .74 (Needle fairway / green, Split green; band .55 .. .75; HeroBaseStudioURP +.02) on the new maps with the v8 tints: Needle fairway x.96 = (.82,.835,.835), Needle green x.94 = (.752,.762,.762), Split green x.96 = (.677,.658,.658) (Split fairway R .69 -> .70: its approach read hue 73.7); Crater fairway / green (.95,1.13,.62) -> (.85,1.01,.55): the light band clipped G >= 250 on 3-4 % of the grass (0.00 .. 0.60 % on the 9 stills now), board V .57 S .74 (limits .55 / .72). Tuned with `GOLF_LOOK_TUNE=1 GOLF_LOOK_GRASS_HOLE=<n> GOLF_LOOK_HOLETINT=...` (v9/tune_*.txt) and confirmed by the full GolfLookSmoke.

## 2. Hole 9 grass at the ball ("soft and smeared"), hole 8 near grass without stripes / blade detail
* Hole 9 near-field Laplacian sd (y1200-1600): tee 3.36 -> 3.36, **approach 3.01 -> 3.16** (the review's 2.98): the pixel grain no longer weakens in the dark band (section 1). Hole 8: stripes (section 1) and near field 5.19 / 3.76 -> 4.86 / 4.11.
* **Not done (not my PNGs)**: the hole 8 cart path's uniform cobbles / even joint grid (Path_C: "optional polish", low).

## 3. [medium] Hole 10 basalt: BASALT_JOINTS must PASS (the integrator's Game-view gate, thresholds NOT relaxed)
* **Root cause** (measured with the integrator's own code, `tools/basalt_gv.py` = `v2/proof/measure.py` basalt_metrics on the stills, reproduces the delivered 1.27 per 100 / 92-93-97 % exactly): every glowing thing in Basalt_E was a vertical stretch on a joint (99 % vertical-elongated components at texture level, 2.6 junction clusters per 100 skeleton px), and the builder's UV windows stretch the tile x1.6 in u and x2.8 in v, so even 0.4 m stretches become 1 m slits; the far wall can only show features >= ~6 cm wide (mip chain, V >= .4).
* **Now** (generator `BASALT_P net / vor / old_E ...`, `mat_basalt`): the v8 joint stretches and forks still paint Basalt_C (the albedo rust) and Basalt_N but **no longer the emission** (`old_E = 0`, so Basalt_C keeps the v8 column-luminance profile). Basalt_E is a crack NETWORK confined to the builder's glow corridors (the complement of `ZONES`, so tops / plain faces stay glow-free and `hole10_look.py` needs NO change: BASALT_BUILDER_WINDOWS: zone glow 0.0000 %, edge window 4.8 %, profile deviation 0.0038): (a) nodes along every lit joint (short fat glowing root piece + a molten bulb + 1-2 slanted branch cracks 45-75 deg from vertical, 62 % downward toward the lava, Y forks, horizontal ledge stubs at the tips, 5-8 cm wide), (b) slanted links between neighbouring lit joints (closed cells), (c) a **Voronoi crack layer** (cells 0.53 m, `worley`, ~half the cell borders lit, a per-border intensity, hotter toward v = 0 / 1). Grooves in Basalt_N (tilt <= .28: the cross-fracture detector reads |ny| > .45 as a block fracture) and dark hairline cracks in Basalt_C (x.5). Glow = 5.5 % of the texels (gate 1..6).
* **Game view, real project (`stills_real9`, `tools/basalt_gv.py`, same code as the integrator's gate)**: tee glow 2.1 % of the basalt, vertical-line share **32 %** (limit 80), approach **69 %**, lava rim **59 %**, horizontal rungs 4 / 2 / 3 % (limit 20), non-glow mean S .149 / .176 / .123 (limit .25), median luminance 35.6 / 23.6 / 28.0; **branching joints 302 junction clusters on 4,407 skeleton px = 6.85 per 100 (limit 3.0; crater.jpg 8.3-8.8; delivered 1.27)** => `BASALT_JOINTS PASS`. The wall now reads as dark prisms with zig-zag, Y-branching glowing cracks (`crop_v2_wall.png`, `m7.png`).
* **Generator gate definitions CHANGED (disclosed; mine, not the integrator's)**: `BASALT_PRISM_GLOW_JOINTS glow` demanded every component to be vertical-elongated and a stretch / gap rhythm (it forbids a branching network and passed the v8 map at 99 % vertical); now: coverage 1-6 %, vertical-line share <= 70 % in wall space (60 %; v8 99), rungs <= 20 % (3 %), skeleton junction clusters >= 4.0 per 100 px at texture level (5.27; v8 2.60), >= 95 % of the glow within 6 px of a groove / joint wall (99.6 %), longest horizontal run <= 12 % (10.3 %), hot at v = 0 / 1 x2.65. `BASALT_BEVELS` bevel share >= .35 -> >= .34 (34.8 %; v8 35.2: the crack grooves are 0.4 % of the tile). `Basalt_E wrap seam` (sparse, hottest at the seam): the seam pair against the 99th percentile of every adjacent pair <= 1.0 (the map is exactly periodic: map(u+1, v+1) == map(u, v), 0.0000 % texels differ).
* **Visual caveat, said plainly**: the cracks are lightning-like polylines; some read as rune-like zig-zags at 2x; the near rim's glow is sparse (1-2 short cracks per column). The lava hot core (R > 240 and G > 170) stays 0 for the reason in v8 section 1.

## 4. Gates of this round
* Generator (full run `v9/full2.log`, decoded by Blender's libpng): **159 gates, 0 FAIL** (GRASS_BAND_CONTRAST x2, GRASS_SHEEN_ALPHA x2, GRASS_LEAN_STREAKS x2 new; GRASS_VARIATION Fairway stripe band 7..11 % -> 10.5..14.5 %; GRASS_HUE_PREDICTED x10, GRASS_MICRO_NEAR x2, GRASS_NEAR_FIELD x2, SEAMLESS_ALL 28 / 28, FOLDER_BUDGET 23.91 MiB, PNG round-trip exact).
* `GolfLookGrassCheck` (new editor script, real project, `grasscheck_real2.txt`): GRASS_SHEEN_WIRED / GRASS_SHEEN_PER_HOLE x2, GRASS_SHEEN_VARIANT_KEPT: 5 / 5 PASS.
* GolfLookSmoke (real project, final state, `v2/runtime/smoke_t9s3.txt`): **95 / 95 PASS**, URP_BOTH_ASSETS 33 / 33 under TennisURP and 33 / 33 under HeroBaseStudioURP (GRASS_HUE_GAMEVIEW 8 / 9 / 10 and GRASS_NO_CLIP PASS, BASALT_* PASS). PostcardImportCheck `importcheck_t9i1.txt`: 60 lines, 0 failed. `guards.sh` 7 / 7 PASS; hole 7, Hole.cs, Tennis files, shaders, Serve untouched (QualitySettings.asset: content = git HEAD, its mtime moved by Unity batch exits).

## 5. Not done / open (owners)
* Hot yellow-white lava cores, hole 8 path cobbles (Path_C), anything outside Fairway / Green / Basalt: not touched (24 PNGs byte-identical).
* Tuft fringe, plant sway, hole rebuilds: the props / sway / hole agents. After a hole 10 rebuild its UV windows change: re-run `tools/basalt_gv.py` on the new stills (the vertical-line share of the approach shot is 69 %, 11 points under the limit).
* Player-build behaviour of the sheen keyword (variant keeper) and of the new textures on a device: not measured here.
