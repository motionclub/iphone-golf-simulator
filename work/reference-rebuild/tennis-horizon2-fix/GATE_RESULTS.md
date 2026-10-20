# Horizon visibility repair

GATE: Source/import cause PASS
- Actual candidate reference camera proof has no authored ridge; old islands have been removed, confirming pilot activation.
- FBX binary audit: geometry raw X[-488.05,422.62], Y[500.65,778.96], Z[-5.10,61.84]; object rotation X=-90.000009deg, export -Z forward / Y up.
- Existing TennisVenueArt.BuildCoast at line39 compensates the identical export with180deg world yaw. TennisResortVista omitted that yaw. The repair applies the same rotation composition, preserving prefab import scale and rotation.
- Resort gameplay camera farClip comes from TennisVenue.FarClip=600. Horizon crest resides beyond600;1000 covers the authored500–779m envelope while preserving camera lens/pose and all physics.

GATE: Unity visual acceptance PENDING
- Root must install both staged candidates/patches and capture the reference camera serially with TENNIS_HORIZON2=1.
- Runtime log prints every imported renderer world bounds, activity, layer, scale and shader support. Expected bounds X[-488.05,422.62], Y[-5.10,61.84], Z[500.65,778.96] (small import numeric tolerances allowed).
- No Unity process was run. No installed asset, FBX, shader, court, collider, gameplay or character source was edited.
