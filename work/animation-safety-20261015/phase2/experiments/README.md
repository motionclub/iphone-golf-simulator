# Rejected skirt experiments — do not install

These files are outside Unity/Assets and deliberately use `.cs.txt` extensions. The generated profiles belong to the existing authored Clothing V2 skirt topology. No experimental surface solver is active in the game.

- Panels / radial wrapping: stiff fan or apron shape; failed silhouette.
- Direct native cloth: separated seams and detached layers.
- Connected native cage: loops and deep-crouch instability. The dynamically assembled golf palette also exposed a seam-index bug; fixing that index did not fix the visual gate.
- Surface solver: preserved actual garment topology, outer/inner wall correspondence, then used Burst and cached matrices to reduce desktop cost from multi-millisecond CPU projection to approximately 0.8 ms p95 before later edge constraints. Native arrays were disposed and the dynamic golf binding was checked.
- Dual-quaternion skirt support and matched layer weights: kept both walls together but did not solve all upper-skirt attachments.
- Final strain/edge candidate: 8 of 84 captured frames still intersected the full body and pushup transitions changed the silhouette. Rejected despite clean key kneel frames.

The final three HeroSkirt*.cs.txt files are the last candidate, with separate earlier union/radial snapshots retained. `FemaleSkirtBindingTests.cs.txt` is its runtime binding regression, not an active product test. Preserve these as diagnostics, not as a shipping implementation. Revalidate body clearance, layer separation, waistband continuity, all transition frames, rest shape, dynamic golf bindings, and device cost before any future installation.
