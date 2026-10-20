# Female FULL staged - COLOUR pass (materials only)

`HeroBase_Female_FULL_STAGED_colored.blend` = the staged merge (`export/HeroBase_Female_FULL_STAGED.blend`, SHA `a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1`, unchanged) with skin, eyes, brows, lips etc. coloured.
**Geometry, UVs, custom normals, vertex groups and Face_F are bit-identical to the staged merge** (14 Body_F + 13 Face_F arrays compared); Hair_F, plates, lights, camera untouched. ArtDir female SHA `200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd` unchanged. No Unity changes.
Colored blend SHA `34ce10539d6db5be8d6d48e3ba9501b0a6dc40a9229ed17ef6fd90028ac2411c`. Previews: `COLOR_SHEET_full.png`, `COLOR_SHEET_face.png`, `COLOR_vs_PLATE_head.png`.

## What the colours are (nothing invented)
Source of truth = the project's own female values: Unity `Editor/HeroBaseFemaleHeadProof.cs` (`SkinColor`, `FaceSlots`) + MicroF3's lip palette (`work/female-micro-f3-head/data/lip_palette_f3.json`); target look = `ArtDir/hero/base_lock/face_lock_f/FACE_SPEC.md` (light warm peach skin lighter and pinker than the male tan; dark-brown irises with a big white specular; dark-brown brows; painted lash line with an outer wing; lips a muted peach-pink one step deeper than skin; no metallic, roughness .55-.70).
| Blender material | hex | sRGB 0-1 | smoothness | Blender spec level | Unity material |
|---|---|---|---|---|---|
| `Skin_F` (both Body_F slots) | #E6B295 | [0.9, 0.7, 0.585] | 0.4 | 0.5 | Female_Form_Skin.mat (and Female_Form_Grey.mat is what the Base_Grey_F slot used) |
| `Face_Brow` | #332218 | [0.2, 0.135, 0.095] | 0.34 | 0.06 | Female_Face_Brow.mat |
| `Face_BrowSoft` | #543B2B | [0.33, 0.23, 0.17] | 0.3 | 0.06 | Female_Face_BrowSoft.mat |
| `Face_Sclera` | #DBD9D6 | [0.86, 0.85, 0.84] | 0.62 | 0.5 | Female_Face_Sclera.mat (+ emission .10,.095,.085) |
| `Face_IrisIn` | #5E361B | [0.37, 0.21, 0.105] | 0.2 | 0.06 | Female_Face_IrisIn.mat |
| `Face_Iris` | #4C2B16 | [0.3, 0.17, 0.085] | 0.2 | 0.06 | Female_Face_Iris.mat |
| `Face_Limbal` | #1F0F08 | [0.12, 0.06, 0.03] | 0.22 | 0.06 | Female_Face_Limbal.mat |
| `Face_Pupil` | #050403 | [0.02, 0.015, 0.012] | 0.25 | 0.06 | Female_Face_Pupil.mat |
| `Face_Catch` | #FFFFFF | [1.0, 1.0, 1.0] | 0.9 | 0.5 | Female_Face_Catch.mat |
| `Face_LidLine` | #120D0A | [0.07, 0.05, 0.04] | 0.4 | 0.06 | Female_Face_LidLine.mat |
| `Face_LidLower` | #4C2B21 | [0.3, 0.17, 0.13] | 0.35 | 0.06 | Female_Face_LidLower.mat |
| `Face_Lip` | #E0967D | [0.88, 0.59, 0.49] | 0.45 | 0.5 | Female_Face_Lip.mat (F3 value) |
| `Face_LipUp` | #D1876B | [0.82, 0.53, 0.42] | 0.4 | 0.5 | Female_Face_LipUp.mat (F3 value) |
| `Face_Seam` | #7A3D2E | [0.48, 0.24, 0.18] | 0.3 | 0.5 | Female_Face_Seam.mat (F3 value) |
| `Face_Nostril` | #54261C | [0.33, 0.15, 0.11] | 0.15 | 0.06 | Female_Face_Nostril.mat |

* **Skin on the whole body** (head, neck, torso, arms, hands, legs, feet): both Body_F slots now point to `Skin_F` (flat colour, the albedo-atlas link was dropped; the atlas was a flat peach plus two 1 %-flush discs). `Base_Grey_F` (the plate's grey mock-neck bodysuit tone) is kept in the file with a fake user: to get the plate's grey suit back assign slot 0 to `Base_Grey_F`.
* **Eyes**: sclera warm white with a faint emission (as Unity), iris = two browns (inner ring lighter), dark limbal ring, near-black pupil, white catch-light, painted lids/lash line.
* `Specular IOR Level` on the very dark paint (`Brow, BrowSoft, LidLine, LidLower, Limbal, Pupil, Iris, IrisIn, Nostril`) is **0.06** instead of 0.5. This is a Blender-only preview setting, NOT part of the Unity palette: Blender's sun specular put a neutral veil on near-black paint (pupil lit grey 55 vs plate 4, iris S .44 vs plate .62). Unity keeps its own smoothness values.

## Check against the plate (same camera, F3's plate-aligned front panel, Unity-like rig; detector = skin chat's: hue 8-45, S>.2, V>.3)
| | plate | model |
|---|---|---|
| skin median RGB | [224, 177, 147] | [243, 190, 161] |
| skin hue / S / V (median) | [23.5, 0.337, 0.878] | [21.4, 0.332, 0.953] |
| brow L / R (RGB) | (53, 39, 29) / (64, 47, 38) | (64, 47, 37) / (60, 43, 34) |
| iris median RGB (L / R) | [65, 39, 24] / [59, 35, 23] | [93, 56, 33] / [90, 54, 32] |
| iris hue / S (L) | 23.2 / 0.62 | 22.5 / 0.645 |
| pupil (RGB) | (4, 3, 2) | (19, 18, 18) |
| upper / lower lip hue | 22.2 / 18.8 | 20.2 / 16.3 |

Honest limits: skin hue/chroma are on the plate (hue 2.1 deg apart, S 0.005 apart) but the lit skin is **0.075 brighter** (V) and key-lit cheek/chin pixels clip at R=255; the plate is lit from the viewer's right, this rig from the left, so single patches differ by lighting. The iris is lighter than the plate's (V ~.36 vs ~.24) at the same hue and saturation. Sclera is whiter than the plate's shaded grey-white. This is a Blender render of the project palette, not a Unity capture; the skin value was kept at the project's calibrated number (the skin chat's rule: match hue/chroma, not exposure).

## Not done
Unity (the Unity female proof still maps the `Base_Grey_F` slot to `Female_Form_Grey` by name), hair (bald plate; `Hair_F` stays hidden/optional), cheek blush, nails, any shape change. Skin tones other than the female default (the game's Fair..Deep palette) and other eye colours are one colour edit on `Skin_F` / `Face_Iris` + `Face_IrisIn` (+ `Face_Limbal`).

Rebuild: `blender -b --factory-startup export/HeroBase_Female_FULL_STAGED.blend --python tools/build_color.py -- color/HeroBase_Female_FULL_STAGED_colored.blend color/female_palette.json`; renders `tools/render_color.py`; stats `tools/color_stats.py col`; sheets `tools/make_color_sheets.py`, `tools/compare_plate.py`.
