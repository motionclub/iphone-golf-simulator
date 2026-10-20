# Paused for face priority

User reprioritized faces before a wrist candidate was implemented. No Assets edits, Unity runs, or new wrist tests from this lane. Nothing in this folder is ready to integrate.

Current evidence: `actual-wrist-sections.png`, `section_analysis.py`, `initial-sections.txt` compare active OriginalSeam Body wrist sections from continuous3 Female/Male Putter address and Driver top. HeroContinuousHandMesh is not called in the active runtime; HeroHandWeights only changes thumb-root weights; HeroSkinNormals affects head/neck. Actual bone tail to Hand agreement is 0.00012 mm. Thus the visible wrist S bend is not a dislocated joint or normal-only artifact.

Important dump convention: BakeMesh posedVertices include scale1.0936 while skinMatrices do not. Divide posedVertices by1.0936. Female Putter full-body affine replay then agrees below0.000374 mm; raw bakeOracle~0.13m is a scale comparison artifact.

The active wrist is roughly60 mm in diameter, with most LowerArm-to-Hand weight transfer across~40 mm. Mixing rotations about a shared pivot pushes proximal, partly-Hand-weighted sections opposite the distal palm bend (negative rest-axis distance times the Hand weight), producing a compensating bend/pinch. This mechanism is supported by section plots, but no candidate actual has yet isolated how much of the visible defect it removes.

Proposed single candidate, NOT implemented: replace only the wrist-band skin mapping with a smooth Hermite section centerline between retained rigid forearm/palm sections (approximately -80 to+30 mm relative to wrist); transport original radial section geometry, preserve all bone/Club/digit transforms. Avoid merely broadening LBS weights, which retains the shared-pivot counterbend. A runtime band could bind to Hand and pre-transform its output into Hand bind space to avoid unstable inverse blended skin matrices. Requires body+glove composition, per-instance ownership, normal transport, native parity, and a first tiny actual before any broad gate.
