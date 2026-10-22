# Ordered eye transition candidate — held for actual after filming

Source transition is substantially cleaner and approved by both geometry agents for one actual diagnostic. **Do not promote while root is filming. This is not final art acceptance.** Root owns production Assets, serial Unity/GPU and native adoption.

Use `{Male,Female}_Face30OrderedSurface.blend` / `.fbx`; exact hashes in STAGED_EXPORT.json. Body counts46,780 Male /37,246 Female; triangles90,026 /69,086. Generic53-bone hierarchy/rest/weights retained from frozen input. ReferenceFeatures unchanged. Do not apply the old sparse female operation.

Composition already present, in this order:
1. Frozen ordered-strip1 constrained annulus retopology. Its JOIN_AUDIT.json has0 same-directed shared edges and0 non-manifold edges. Connectivity and X/Z remain exactly unchanged by this lane.
2. `ordered-strip1/apply-corneal-clearance.py` on original inner rim and new strip. This repairs the old male left deep pocket against actual feature triangles (no eye-part movement).
3. Female local forehead correction from `face-finish30/forehead-check` on retained original prefix, with matching broad reference for new outer-strip points.
4. `finish.py: finish_transition(body,sex,ref)`: regularized MLS reference over the original smooth broad head; positive-cotangent harmonic residual on the valid annulus. Corrected inner boundary/first2rows and outer boundary are fixed; outer2rows match actual original broad surface. Corneal clearance is a constraint during the solve, so it cannot create a new terminal step.
5. Exact corneal guard again; final corrections are only floating-point noise (see SOURCE_REPORT.json). New strip/join geometric normals rebuilt; outside authored normals preserved, including repaired female forehead.

`finish.py` main reproduces outputs from frozen ordered-strip1 blends. `make_reference(sex)` loads original Ears male / repaired Forehead female authority. `render.py` matches backface culling, UV pigment and runtime full eye retreat×2. CPU front previews include0/50/100; threequarter previews include0/50.

What improved: main V/spoke creases below the eyes and across the cheek/socket are removed; male closed arc is smooth; female cheek flow is much cleaner. First2supportrows retain their corrected source coordinates exactly; all X/Z coordinates unchanged. Separate topology and corneal operations supply the new rim/closure, not this surface solver.

Remaining source concerns for actual to arbitrate: tiny male left upper/lower rim speckles, small original outer-boundary scars beside nose, female small temple join facets and shallow closed-lid mound. No more broad source changes are justified before the actual coherent-normal check. Keep root's HeroBlinkNormalField correction; raw imported blendshape normal deltas previously produced false brown blocks.

Small next actual queue after films: male/female open+half+closed front and male/female open3q, exact staged FBX hashes. Judge rim clearances, closed arc and outer join before further edits. No broad before/after proof expansion needed.
