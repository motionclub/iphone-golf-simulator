# Measured cuff mask2

Source-only mask extension; root owns opt-in runtime integration and actual validation.

The current tailored polo sleeve was measured in the original UpperArm→LowerArm bind frame, using 16 angular sectors around each arm. Within each sector the distal 10/1000 axial-length cuff band was extracted from actual source sleeve vertices. The shortest circumferential extent is .4325–.4328 male and .42899–.42902 female. A 5 mm inset from that shortest edge gives Left/Right mask limits .411809/.411516 male, .409416/.409385 female. Upper-arm bind lengths are .238287 m male and .254990 m female. Circumferential measurements are recorded in circumferential-cuff-envelope.json.

Compared with the previous .30/.32 mask limit, this extends coverage by about 26.6 mm male /22.8 mm female. It adds only triangles whose three vertices satisfy the covered upper-arm field and remain before the inset cuff plane. Existing torso mask and exposed neck/head exclusion remain intact; no arbitrary longer sleeve threshold or broader torso removal was introduced.

Original Top and Body vertices, weights, morph arrays, UVs, normals, bind matrices and all named bones are unchanged. This is a derived render-face mask; complete editable Body remains preserved. Standard backface cloth is retained. No new cloth panels, shader clearance or two-sided materials are part of this candidate.

Runtime profiles have garmentVertexCount15401 male /13932 female; expectedRemovedFaceCount7072 male /3064 female. Added upper-arm faces788/172. Every requested physical triangle matches both default-source and current-matrix-canonical Body at10 micrometres, with0 unmatched. File hashes are in runtime-profiles/manifest.json.

Actual mask1 removed most sleeve skin penetration. Its paired two-sided version added dark shading artifacts without additional coverage and was rejected. Actual mask2 remains unverified: inspect male Serve1, female Forehand2, then both-body all33 motion samples for skin penetration, continuous forearm/cuff/neck silhouette and absent interior backdrop holes. Union silhouette contraction by removing protruding skin is not itself a failure. No visual completion is claimed from source measurement or correspondence.
