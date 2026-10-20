# Broad Face30 staged source, Astra

Source-art review PASS; actual Unity pending. No production Assets writes. Staged exports and hashes: STAGED_EXPORT.json. build-face30.py and export-broad30.py reproduce the sources and FBX from frozen face29/smooth-mouth1.

Visible changes: male diagonal lower-cheek trenches and chin lumps are smoothed into a continuous rounded surface. Female jaw/chin surface and scalp outline are smoother. Complete original nose volume retained. No hair or identity replacement. Source before/after front/threequarter PNGs in this folder are matched CPU renders and were visually reviewed.

Recipe: positional-welded original mesh; area-weighted tangent quadratic surface fitting (30mm male /26mm female, five passes) of broad cheek/jaw/scalp; displacement along soft original normal frame, max6mm broad /3.5mm scalp. Feature guards prevent changes within4mm of blink-active geometry; mouth/nose loops exact and complete nose volume protected. Smooth derivative normals match the faired field. Refined scalp samples use circular Hermite arcs and exact parent-normal interpolation to avoid shallow scalloped shading.

Original vertex prefix remains33472 Male /22891 Female. Body final43900 Male /34366 Female. All original weights and shape DELTAS remain exact, all53 bones/rest/hierarchy exact, ReferenceFeatures object and shapes exact. Appended parent map can reference earlier appended vertices: recursively interpolate in ascending index. UVs/color/weights/shape positions use identical edge interpolation and preserved original corners. New scalp vertices never touch protected eye triangles. SOURCE_GATE.json records invariants, male/female-candidate.npz stores actual p/t,original,parents,sourceFace.

Eye lane /root/gusset_actual_repair owns sparse originalprefix Basis/Half/Full operation in face-finish30-lids; wait for its READY. Apply after this broad source to a separate composed output. Do not overwrite accepted broad exports until actual reviewed.

Root owns production import, serial Unity/GPU, actual proof, native integration. First actual queue requested: male/female front plus male threequarter, combined satin2 if ready. Accepted frozen Smooth1 and lip3 remain available for rollback.
