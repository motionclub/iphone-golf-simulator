# Eye repair handoff — held for gameplay recording

The current production assets remain unchanged by this lane. Root is recording the requested gameplay films and owns all later Unity/Assets work.

## Established causes

1. Female brown blink blocks were bad imported blink normal deltas added to a replacement continuous base-normal field. Actual normal0 and coherent1 captures remove the blocks without changing positions. The actual posed lid vertices match authored positions to max0.001135mm. `HeroBlinkNormalField.cs` is the actual-tested opt-in normal repair, applied after `HeroSkinNormals.Prepare` with `VISUAL_BLINK_NORMAL_FIELD=1`.
2. The old lid surface and its fixed transition could not be repaired reliably by local harmonic smoothing. The new ordered annulus uses constrained triangulation to preserve the exact inner and outer boundary edges. `ordered-strip1/JOIN_AUDIT.json` records zero inconsistent shared-edge orientations and zero non-manifold edges for both sexes. Original point prefix, body rig and outside source polygons are retained.
3. Male left eye sheets protruded through the Half lid. Exact depth query: BodyY−121.17mm versus iris/pupil≈−124.7mm at x−37.5,z1589mm. `ordered-strip1/apply-corneal-clearance.py` constrains local skin depth against the exact curved eye feature sheets with0.35mm ease. No eye part moves. Basis/Half/Full are checked individually; Full includes existing runtime2×feature retreat. `apply-half-clearance.py` is superseded and should not be used alone.

## Final staged source

Use `ordered-surface1/{Male,Female}_Face30OrderedSurface.blend` and the corresponding FBXs/manifest exported by the forms agent. These compose the forehead correction, constrained eyelid topology, smooth MLS/harmonic outer transition, corneal clearance before smoothing, and final exact clearance guard. Do not install the earlier `Face30Lids` or raw `ordered-strip1` exports.

Source counts: Male46,780/Female37,246 vertices (original prefixes43,900/34,366;2,880 local appended points). Source CPU culling previews for0/50/100 are in ordered-surface1. Main serrated rims, folded outer spokes and Half iris overlap are resolved in source. Small male rim speckles and female temple join dimples/shallow closed-lid ripples remain visible. This is READY FOR ONE ACTUAL REVIEW, not final art acceptance.

Root capture queue: `ordered-strip1/held-actual-queue.json`. It uses coherent blink normals, current satin material and front/threequarter blink review. Run only after gameplay filming is complete and root installs the final surface exports. No broad pose/numeric rerun is requested before this visual check.
