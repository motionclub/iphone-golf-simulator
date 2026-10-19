# Female hero implementation

Implemented in the Unity game and the native iPhone lobby. Stage only; no commits.

The original face is retained. The rejected teeth/mouth/expression layer is excluded. The user removed the requirement for new dynamic facial expressions and owns visual acceptance from the actual images.

## Changes
- Tennis tank: broader shaped straps, bound edges, independent waist ease, settled cloth and a turned hem. Binding follows the selected shirt color.
- Golf polo: continuous torso/sleeve sewing surface, separate substantial cuffs, loose torso, collar and two-button placket. Drafted on a relaxed A25 mannequin with garment-only bindposes. The accepted body rig and its binds remain unchanged.
- Both skorts: broad pleats, real returns, thickness, waistband and fitted liners. The user liked this silhouette; it remains intact. Lower-garment color controls the liner/waistband.
- Female shoulder correction follows full chest-relative upper-arm rotations. Twenty-four unilateral shapes affect 1,873 sparse vertices. The old self-intersecting compression is bypassed only for the new female garments.
- Fine matte knit on the new tops. All clothing colors remain customizable; reference lime/coral/navy are example picks, not saved palette replacements.
- Native manifests, rig/morph tracks, compressed garment maps and goldens were regenerated for the three female variants. Male payloads are preserved.

## Review
`proof/review/implemented-female-kits.jpg` shows the two current kits in Unity. `tennis-current.jpg`, `polo-current.jpg`, `polo-back.png` and `tennis-overhead.jpg` show the requested areas. `native-tennis.png` / `native-golf.png` are actual SceneKit lobby renders with example picks.

Muted clips: `compare-idle-detail.mp4`, `compare-wave-detail.mp4`, `compare-joy-detail.mp4`, `compare-slump-detail.mp4` compare actual Unity poses. `golf-current.mp4` is the full 13.53-second game capture at the unchanged gameplay camera, without flight compression or retiming.

## Sources and rebuild
`source/` contains four editable independently constructed Blender garments. `build_garments.py`, `drape.py`, `stitch.py`, `pipeline.py` and `rebuild.py` retain the construction/export steps. `unity/` contains the runtime changes and isolated capture/authoring helpers. The accepted body is a clearance/weight source; garments do not originate from its surface.

The working Unity Editor is `/private/tmp/female-soulful-UnityClone`. Do not run batch Unity on the shared project. Use Unity CLI with caller plugin / skill unity-cli. Blender batch uses the installed Blender 5.2 binary. Source dumps/out files and raw captures are ignored working data; regenerate them with ClothingV2Dump and FemalePoloAuthoringPose on the accepted rig. For golf top construction/export, dump-polo contains the posed mannequin and garment inverse binds, retaining the original clip tracks. Never apply those binds to the body.

`IMPLEMENTATION_MANIFEST.json` records the explicit Unity paths and before/after hashes. `native-changed-paths.json` records the native outputs. `proof/production-parity.json` checks the protected baseline outside those Unity paths. Only these scoped files are installed/staged.

Device frame timing and memory remain unverified at the user's request. The inherited body is 68,476 triangles; it was not remeshed. No claim is made that every possible pose or future garment is free of clipping. Appearance is for the user's review.
