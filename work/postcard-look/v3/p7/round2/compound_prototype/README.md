# P7 round 2: H9 genuine shared whole-tuft clump prototype

Scratch only. No production source, frozen stage, installed asset/meta, validator, or design was changed. Root reviews the immutable `apply_plan.json` before any production application. Its old source hashes are deliberately strict; a concurrent H9 change must stop the plan rather than silently replacing the baseline.

The measured prototype replaces 400 actual tuft instances with 180 actual shared clump renderers. Twenty-one different real clump meshes are each used at least twice. A clump holds three whole cheap fillers (108 polygons) or one whole tall tuft plus one filler (108–117 polygons), retaining the 120-polygon tuft cap. All source template vertices/polygons/UVs/Col channels are copied, including every original root's sway weight. The scatter uses an existing valid rough-land pivot, retains the original singles, and rejects candidates whose actual component roots leave rough land, fall within 1.1m of shore, lack ground within 6cm, exceed the group's old exact top cap, or approach the safe route within 2m. Original unsafe candidates remain as their original visible instances. There are no empty meshes, invisible keepalive nodes, renamed shrub objects, or counter padding.

Actual scene measurements:

| Measure | Before | Prototype |
|---|---:|---:|
| Mesh renderers | 1417 | 1197 |
| Plants | 940 | 720 |
| Tuft renderers | 798 | 578 |
| Real whole source-copy tufts | 798 | 798 |
| Source triangles | 248868 | 248868 |
| Shared plant fraction | 100% | 100% |
| Largest tuft mesh | <=120 polygons | 117 polygons |

The original prototype check set passes 20/20. Independent checks cover every one of the 51 actual template tuft ranges rather than relying on a compound's global lowest vertex: exact original RGBA, root R<=.05, and actual component support. The unchanged original full verifier passes 96/96 on the scratch blend and LINEAR FBX; H9 QA passes 27/27. Its image-presence gate uses the existing H9 gate images, whose exact file hashes are recorded in `existing_stills_provenance.json`; those are not fresh candidate renders. The full geometry checks include 100% shared instancing, one LK_PLANTS material, root/phase/cap channels, UV density, every actual connected piece's support, rough-land/shore placement, route/pin clearance, shrub thickets, scrub-boundary cover and required ridge object counts. The scoring blend's exact world-vertex maximum delta is 0m with identical triangle topology. The standard full verifier also passes scoring and marker tests on the exported FBX; final independent zero-tolerance FBX/marker proof remains required on the actual rebuilt candidate.

The exact proposed reusable helper is tested separately: 7/7 checks PASS, identical 720 plants/180 compounds/248868 triangles, with 578 live unique tuft references. It remaps scenery lists while all original Blender wrappers remain valid, then deletes replaced instances. Returned inventories distinguish actual renderer counts from real whole-tuft counts. Its source draft adds one opt-in build call and stores actual per-build evidence.

The original phase-6 draw counter was 793. The prototype's 220 fewer author renderers does not prove 220 fewer native draw calls; frustum, shadow, shader and instancing behavior still require actual Unity measurements. **Draw<=250, native sway decorrelation, fresh appearance and six frozen-camera masks are UNMEASURED.** They cannot be called PASS. Existing two-island topology, straight shoreline, framing and eye failures are not repaired by this prototype.

Evidence: `result.json`, `prototype.log`, `compound_unverified.blend/.fbx`, `verifier.json/.log`, `hole_qa.json/.log`, `check_export_results.json`, `helper_fixture.json/.log`, `helper.py`, two exact draft source files, original source snapshots, and `apply_plan.json`. No unsuccessful geometry candidate was discarded; this was one finite design. A failed missing-import dependency from round1 and the separate smoke attempts remain in their original round1 history.
