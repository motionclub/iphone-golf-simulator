# Coastal World Reskin pilot — 2026-10-15

Scope: exactly golf hole 12 (coastal) and Resort tennis. User requests ambitious joyful visual overhaul, matched actual before/after images, and a 60 fps target with 30 fps fallback accepted. Physical-device testing was explicitly waived in the latest reply. Preserve characters, animation, rules, collision surfaces and production camera behavior. Stage only; no commits. Other ongoing work exists in this checkout.

Direction: Luminous Coast. Sculpted limestone/headlands, clear turquoise cove, layered island silhouettes, monumental summer cumulus, warm sun and cool open shadows. Deliberate foreground/midground/horizon separation, coherent resort architecture and planted edges. Keep ball corridor quiet.

Research:
- Nintendo Switch Sports developer interview: https://www.nintendo.com/ph/interview/as8s/03.html — inviting aspirational facilities and coherent emotional context; avoid spectacle that conflicts with casual sports.
- Tobias Koepp / Epic, Riverfall: https://www.unrealengine.com/tech-blog/creating-a-stylized-world-with-unreal-engine-4?lang=de — shape language, landmark silhouettes, composition and environmental art workflow.
- Unity 6000.3 URP performance: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/configure-for-better-performance.html — measure passes, shadow cost, render texture traffic and target hardware, not editor FPS.

Execution:
1. Capture unmodified runtime baselines from identical gameplay and reveal views.
2. Build scoped pilot environment assets and runtime attachment. Prefer authored sky and opaque batched scenic meshes, bounded detail and no additional realtime shadow lights.
3. Iterate actual game captures. Generated artwork is source/concept, never after-proof.
4. Check collision/gameplay invariants and other-venue isolation. Capture portrait and landscape readability.
5. Target 60 fps with a scoped, sustained-load fallback to 30 fps. Test the decision policy. Physical-device profiling is skipped at the user’s explicit request; do not claim a measured frame rate.
6. Publish matched before/after boards and GATE_RESULTS.md with explicit unresolved gates.

Physical device discovered: paired iPhone 17 Pro Max. Baseline Unity version 6000.3.24f1, URP17.3.0. Runtime renderer already contains existing environment/ACES work; preserve it.

Current status: user rejected the first coastal pass and selected dreamlike fantasy. Golf12 now has the second pass’s actual3D arches, floating gardens, modeled architecture, detailed flowering foliage, revised surfaces/lighting and a scoped portrait tee composition. See revision2/PLAN.md and revision2/GATE_RESULTS.md. Tennis remains the first coastal pass. Physical-device testing stays waived; no measured FPS claim.
