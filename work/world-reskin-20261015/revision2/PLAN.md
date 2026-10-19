# Revision 2 — Dream Coast

User rejected the first pass: trees lost quality, painted sky improved but the game otherwise looked the same. The first pass does NOT meet the requested artistic transformation.

User selected: **Dreamlike fantasy — spectacular landforms and more surreal color**. Rebuild the golf pilot first around real 3D monumental arches, floating garden islets, flowering leaf-detail trees, waterfalls, jewel water, and premium curved architecture. Keep golf surfaces quiet and readable. Keep one golf/one tennis scope; no broad map rollout. The accepted painted sky stays, but cannot carry the revision by itself.

Gates: actual gameplay and wide-angle before/after evidence; unmistakable change in foreground/midground geometry and material hierarchy; original collision/obstacle hashes; no leaked dressing on other holes; compile/regression checks; bounded mesh/draw cost. 60 target/30 fallback remains. Phone tests remain waived. No guarantee of device FPS.

Research carried forward: Nintendo's coherent aspirational sport setting, Guerrilla's layered environmental placement and atmospheric lighting, Unity PBR/ambient-occlusion guidance. Applied through real geometry, surface response and contact shading, not additional full-screen effects.
- https://www.guerrilla-games.com/read/gpu-based-procedural-placement-in-horizon-zero-dawn
- https://www.guerrilla-games.com/read/decima-engine-advances-in-lighting-and-aa
- https://learn.unity.com/tutorial/creating-physically-based-materials
- https://docs.unity.com/en-us/engine/6000.3/manual/materials-and-shaders/shaders/writing-custom-shaders-urp/use-built-in-shader-methods/lighting

Current state: fantasy golf revision implemented and rendered through four iterations. Final current proof is in proof/final and proof/comparisons. Compile, 63 EditMode tests, the real-scene PlayMode integration check, collider/obstacle invariants and automatic render-counter collection pass. User artistic acceptance is not asserted. Tennis remains on the first coastal pass.
