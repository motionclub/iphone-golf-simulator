# Optional nape-lump patch (NOT installed)

The nape lump = C7 bump (+2.5 mm) with a crease (-1.8 mm) under it at the centre of the nape base (z 1.375-1.395, |x| < 20 mm).
It lies BELOW the Micro1j zone (z >= 1.40), so it was left bit-identical. This patch flattens it:

* `D_strip.npy` : per-vertex delta (30296 x 3, metres) relative to the INSTALLED blend 72fc6465... (`V_inst.npy`)
* 60 vertices, z 1.352 .. 1.3987, |x| <= 60 mm, back side; max move 1.74 mm (midline: y 88.54 -> 86.80 at z 1.3855, 88.20 -> 87.05 at 1.378, 86.64 -> 86.58 at 1.3706, 86.82 -> 85.55 at 1.394)
* nothing at z >= 1.40; the torso chat's moves reach z <= 1.385 (overlap risk only if they edit the same strip)

Preview (installed vs patched): `preview_installed_vs_patched_hard_light.png`, `..._unity_like.png`, blend `preview_installed_plus_strip.blend`.

Apply (after Adnan's OK), on the CURRENT shared blend:
    blender -b --factory-startup --python work/male-micro1j-head/merge_j.py -- <current ArtDir blend> work/male-micro1j-head/optional_nape_strip/D_strip.npy <out.blend> work/male-micro1j-head/optional_nape_strip/V_inst.npy
(merge_j.py refuses if the base differs from V_inst on the patched vertices), then export the FBX with work/male-micro1h/export_final.py, install, and run HeroBaseMaleFormProof.Run once.
