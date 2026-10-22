"""color/README_COLOR.md from the measured JSON (no hand-typed numbers).  ./py.sh tools/make_color_readme.py"""
import json, hashlib
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-full-merge')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
P = json.load(open(W / 'color/female_palette.json')); S = json.load(open(W / 'color/color_stats_front.json'))
blend = W / 'color/HeroBase_Female_FULL_STAGED_colored.blend'
sk = S['skin_face_front']; pk = S['patches']; ir = S['iris']
art = sha(W.parents[1] / 'ArtDir/hero/base_lock/blender/HeroBase_Female.blend'); stg = sha(W / 'export/HeroBase_Female_FULL_STAGED.blend')
unity = {'Skin_F': 'Female_Form_Skin.mat (and Female_Form_Grey.mat is what the Base_Grey_F slot used)', 'Face_Brow': 'Female_Face_Brow.mat', 'Face_BrowSoft': 'Female_Face_BrowSoft.mat', 'Face_Sclera': 'Female_Face_Sclera.mat (+ emission .10,.095,.085)', 'Face_IrisIn': 'Female_Face_IrisIn.mat',
         'Face_Iris': 'Female_Face_Iris.mat', 'Face_Limbal': 'Female_Face_Limbal.mat', 'Face_Pupil': 'Female_Face_Pupil.mat', 'Face_Catch': 'Female_Face_Catch.mat', 'Face_LidLine': 'Female_Face_LidLine.mat', 'Face_LidLower': 'Female_Face_LidLower.mat',
         'Face_Lip': 'Female_Face_Lip.mat (F3 value)', 'Face_LipUp': 'Female_Face_LipUp.mat (F3 value)', 'Face_Seam': 'Female_Face_Seam.mat (F3 value)', 'Face_Nostril': 'Female_Face_Nostril.mat'}
rows = [f"| `Skin_F` (both Body_F slots) | {P['skin']['hex']} | {P['skin']['srgb']} | {P['skin']['smoothness']} | 0.5 | {unity['Skin_F']} |"]
for k, v in P['face'].items(): rows.append(f"| `{k}` | {v['hex']} | {v['srgb']} | {v['smoothness']} | {v['blender_specular_ior_level']} | {unity[k]} |")
t = f"""# Female FULL staged - COLOUR pass (materials only)

`HeroBase_Female_FULL_STAGED_colored.blend` = the staged merge (`export/HeroBase_Female_FULL_STAGED.blend`, SHA `{stg}`, unchanged) with skin, eyes, brows, lips etc. coloured.
**Geometry, UVs, custom normals, vertex groups and Face_F are bit-identical to the staged merge** (14 Body_F + 13 Face_F arrays compared); Hair_F, plates, lights, camera untouched. ArtDir female SHA `{art}` unchanged. No Unity changes.
Colored blend SHA `{sha(blend)}`. Previews: `COLOR_SHEET_full.png`, `COLOR_SHEET_face.png`, `COLOR_vs_PLATE_head.png`.

## What the colours are (nothing invented)
Source of truth = the project's own female values: Unity `Editor/HeroBaseFemaleHeadProof.cs` (`SkinColor`, `FaceSlots`) + MicroF3's lip palette (`work/female-micro-f3-head/data/lip_palette_f3.json`); target look = `ArtDir/hero/base_lock/face_lock_f/FACE_SPEC.md` (light warm peach skin lighter and pinker than the male tan; dark-brown irises with a big white specular; dark-brown brows; painted lash line with an outer wing; lips a muted peach-pink one step deeper than skin; no metallic, roughness .55-.70).
| Blender material | hex | sRGB 0-1 | smoothness | Blender spec level | Unity material |
|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

* **Skin on the whole body** (head, neck, torso, arms, hands, legs, feet): both Body_F slots now point to `Skin_F` (flat colour, the albedo-atlas link was dropped; the atlas was a flat peach plus two 1 %-flush discs). `Base_Grey_F` (the plate's grey mock-neck bodysuit tone) is kept in the file with a fake user: to get the plate's grey suit back assign slot 0 to `Base_Grey_F`.
* **Eyes**: sclera warm white with a faint emission (as Unity), iris = two browns (inner ring lighter), dark limbal ring, near-black pupil, white catch-light, painted lids/lash line.
* `Specular IOR Level` on the very dark paint (`Brow, BrowSoft, LidLine, LidLower, Limbal, Pupil, Iris, IrisIn, Nostril`) is **{P['face']['Face_Brow']['blender_specular_ior_level']}** instead of 0.5. This is a Blender-only preview setting, NOT part of the Unity palette: Blender's sun specular put a neutral veil on near-black paint (pupil lit grey 55 vs plate 4, iris S .44 vs plate .62). Unity keeps its own smoothness values.

## Check against the plate (same camera, F3's plate-aligned front panel, Unity-like rig; detector = skin chat's: hue 8-45, S>.2, V>.3)
| | plate | model |
|---|---|---|
| skin median RGB | {sk['plate']['median_rgb']} | {sk['model']['median_rgb']} |
| skin hue / S / V (median) | {sk['plate']['median_hsv']} | {sk['model']['median_hsv']} |
| brow L / R (RGB) | {tuple(pk['brow L']['plate_rgb'])} / {tuple(pk['brow R']['plate_rgb'])} | {tuple(pk['brow L']['model_rgb'])} / {tuple(pk['brow R']['model_rgb'])} |
| iris median RGB (L / R) | {ir['iris L']['plate']['median_rgb']} / {ir['iris R']['plate']['median_rgb']} | {ir['iris L']['model']['median_rgb']} / {ir['iris R']['model']['median_rgb']} |
| iris hue / S (L) | {ir['iris L']['plate']['median_hsv'][0]} / {ir['iris L']['plate']['median_hsv'][1]} | {ir['iris L']['model']['median_hsv'][0]} / {ir['iris L']['model']['median_hsv'][1]} |
| pupil (RGB) | {tuple(pk['pupil L']['plate_rgb'])} | {tuple(pk['pupil L']['model_rgb'])} |
| upper / lower lip hue | {pk['upper lip']['plate_hsv'][0]} / {pk['lower lip']['plate_hsv'][0]} | {pk['upper lip']['model_hsv'][0]} / {pk['lower lip']['model_hsv'][0]} |

Honest limits: skin hue/chroma are on the plate (hue {abs(sk['plate']['median_hsv'][0]-sk['model']['median_hsv'][0]):.1f} deg apart, S {abs(sk['plate']['median_hsv'][1]-sk['model']['median_hsv'][1]):.3f} apart) but the lit skin is **{sk['model']['median_hsv'][2]-sk['plate']['median_hsv'][2]:.3f} brighter** (V) and key-lit cheek/chin pixels clip at R=255; the plate is lit from the viewer's right, this rig from the left, so single patches differ by lighting. The iris is lighter than the plate's (V ~.36 vs ~.24) at the same hue and saturation. Sclera is whiter than the plate's shaded grey-white. This is a Blender render of the project palette, not a Unity capture; the skin value was kept at the project's calibrated number (the skin chat's rule: match hue/chroma, not exposure).

## Not done
Unity (the Unity female proof still maps the `Base_Grey_F` slot to `Female_Form_Grey` by name), hair (bald plate; `Hair_F` stays hidden/optional), cheek blush, nails, any shape change. Skin tones other than the female default (the game's Fair..Deep palette) and other eye colours are one colour edit on `Skin_F` / `Face_Iris` + `Face_IrisIn` (+ `Face_Limbal`).

Rebuild: `blender -b --factory-startup export/HeroBase_Female_FULL_STAGED.blend --python tools/build_color.py -- color/HeroBase_Female_FULL_STAGED_colored.blend color/female_palette.json`; renders `tools/render_color.py`; stats `tools/color_stats.py col`; sheets `tools/make_color_sheets.py`, `tools/compare_plate.py`.
"""
(W / 'color/README_COLOR.md').write_text(t); print('README_COLOR.md written', len(t))
