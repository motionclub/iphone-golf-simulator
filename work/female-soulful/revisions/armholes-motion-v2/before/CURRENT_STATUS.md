# Current status — implementation installed

The female garment/shoulder implementation is installed in production Unity and the native iPhone lobby. Original face retained; no new teeth/mouth/dynamic expressions. Male, source body/rig/clips, maps, lights and cameras preserved. Four editable garment sources are in source/. No commits.

The user is the visual reviewer and wants actual images in chat at milestones. They liked the skirt shape; preserve it. Latest images: proof/review/implemented-female-kits.jpg, tennis-current.jpg, polo-current.jpg, polo-back.png, tennis-overhead.jpg. Latest muted motion clips are in proof/review/.

The polo is authored on a relaxed A25 mannequin and has its own garment bindposes. Its accepted body rig/bindposes are unchanged. Do not revert to the failed hanging-arm sleeve loft or Solidify even-offset miter. stitch.fair_sleeve provides smooth torso/arm clearance; sleeves join the thin shell before thickness and weight transfer. The old shoulder compression is disabled for FemaleSoulful garments; FemaleShoulderFit supplies 24 full-rotation-driven local corrections. FemaleGarmentFinish supplies fine knit and matching-color tennis binding, mirrored by optional native bindingTone metadata.

Current source assets, maps and resources are recorded in IMPLEMENTATION_MANIFEST.json. Native changed paths are in native-changed-paths.json; female exports/goldens were refreshed while preserving male payloads. Existing female tests: 17/17. Native renderer compiles and renders both kits. Phone performance remains unverified per user instruction. The inherited body remains 68,476 triangles; no remesh.

Unity Editor runs in /private/tmp/female-soulful-UnityClone via Unity CLI (caller plugin, skill unity-cli). Use that clone for further renders; never run batch Unity on the shared project. Blender batch requires escalation. Raw dumps/out/captures are ignored local work data. Never dump full git status; the pre-existing index is enormous. Preserve unrelated work and stage explicit paths only.
