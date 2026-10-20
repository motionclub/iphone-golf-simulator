# Coastal hole12 obstacle-group source gate

GATE: Independent CPU/source audit PASS. Fresh Blender import of original hole_12.fbx and staged groups8/ReferenceHole12.fbx; original/candidate hashes match the staged manifest. No source edits and no Unity execution.

Both meshes replay ObstacleScan local1mm weld, Standing and TreeOf semantics as161 physical records:43trees,74bushes,43rocks,1wall. All161 have a unique one-to-one physical group match after the intended manifest whole-group sourceY translation; no merged/phantom/missing identity remains. Original pre-warp bounding pivots identify groups because equal-width shrub sorting ordinals are not a stable physical ID.

Descriptors (center/radius/Base/Top/TrunkRadius/CrownBase/Cone/pieceCount) stay within0.0000292yards (~0.0267mm). Every117 frozen tree/shrub group retains vertex, polygon and triangle counts and original vertex positions under its rigid translation; maximum source geometry displacement error0.0000308m (~0.0308mm). Original/candidate PIN/TEE/UP anchors differ by at most0.0000229m (~0.0229mm) after FBX quantization.

Evidence: group-preservation-report.json, original-obstacles.json, candidate-obstacles.json. Reproduction: dump-fbx.py (read-only background Blender import), then verify-groups.py (CPU). Blender startup requires the permitted unsandboxed Metal device enumeration on this host; no render/GPU work performed.

GATE: Actual Unity stored-vs-fresh obstacle scan PENDING root-authorized capture. The source replay is a strong independent check, but does not certify Unity importer ordering, readability or active runtime replacement state.
