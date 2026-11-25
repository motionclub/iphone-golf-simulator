# Gate results — Clubhouse cosmetics

- GATE: Canonical size PASS — all 16 native club variants retain original per-family length within 0.01 mm and fit inside the original width/depth envelope, with uniformly scaled decorative heads; `size-gate.json`.
- GATE: Imported rig and size PASS — Unity EditMode checks all 32 style/family/sex combinations, original bind matrices, envelope containment and length within 1 mm, original grip vertices within 0.2 mm, and absence of cosmetic colliders; `unity-tests.xml`.
- GATE: Offline resource and ID validation PASS — Unity tests confirm all four ball maps and Poly Haven detail maps load, unknown IDs fall back safely, and each club stays below the declared 16k prop budget. The wood-bearing submeshes have nonconstant authored UVs rather than sampling one texel.
- GATE: Mesh data PASS — finite positions/normals/UVs and valid indices across all native variants; `asset-validation.json`.
- GATE: Native app build PASS — iOS simulator build succeeded; `ios-build-final.log`.
- GATE: Saved equip and native locker tests PASS — 18 tests passed, including profile round-trip, default/fallback IDs, colour preservation, shelf navigation and real native shelf rendering; `ios-locker-tests-verified.log`.
- GATE: Visual proof PASS — actual Unity product/detail views, both hero rigs at address/impact, four balls and three outfit/accessory palettes are recorded in `proof/`. The final uniformly fitted heads retain their proportions. The rejected early designs and the AI concept are not acceptance proof.
- GATE: Animation-source preservation PASS — no rig, body, head, hair, skin, animation source, map or gameplay camera assets edited. Original club geometry remains the contact/arc reference.
- GATE: Device installation / device FPS NOT RUN — Unity player export and physical-device review were not performed.

The last Unity compile/test used a complete tracked menu baseline in the isolated clone because concurrent menu edits temporarily did not compile. No workspace menu file was reverted or staged by this task. These are technical gates; subjective user approval of the final art and native-vs-game pose parity are not claimed. The optional final native recapture was stopped; the completed 18-test native run remains recorded.

- GATE: Capture save isolation PASS — the final capture uses a temporary worn look and asserts that `golfer.look.v1` remains byte-for-byte unchanged.
