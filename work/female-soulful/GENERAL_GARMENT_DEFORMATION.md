# Garment deformation requirement — 2026-10-16

Adnan: "we need to have cloth that can survive all motions, i dont want this to be a case where we go through all animations and emotes and patch each one".

The accepted improvement to golf arm motion is frozen. Fix garment construction and deformation without introducing clip-name branches, frame windows, per-emote meshes, or a growing bank of pose-specific sleeve repairs. Animation clips are regression inputs, never the implementation's lookup keys. Preserve the original face, source body geometry and skeleton, accepted skirts, customization, maps, lighting and gameplay framing. Keep audio muted.

## Current experiments, not shipping results

1. A Cloth component directly on the detailed, thick polo fails visually. Its 10,175 simulation particles pucker and separate at the shoulder. Actual muted proof: `proof/golf-cloth-general-test/`. This is rejected.
2. `build_cloth_cage.py` now creates a separate clean 645-vertex, 1,199-triangle surface and barycentric detail mapping. The clean source is regenerated directly from the unchanged `source/golf_top.blend`; the discarded seam-projection version had introduced seven nonmanifold outer edges and six collapsed triangles. The clean source has neither. This is a topology result, not a visual pass.
3. Mode 2 uses Unity Cloth on the cage. It still fails the visual target. Pinned-particle measurements identified and corrected an initial scale conversion error; no native parity is established for Unity Cloth.
4. `bind_polo_harmonic.py` computes a continuous torso/arm weight field from garment construction alone. The normalized field is applied to the clean source; no pose bank or large garment morphs remain. Standard interpolation behaves better than the experimental torso/arm DQ arc, but the skinned-only garment still fails a raised-arm view.
5. Mode 3 is a deterministic cage constraint experiment. Every evaluation starts from the current skeleton, constrains sewn-edge lengths and projects against simple torso/arm capsules. The collar, placket, buttons and cuff detail retain their source binding; cuff mouths are anchored by construction. There are no named animation or time inputs. Latest actual muted proof is `proof/golf-clean-cage-cuffs-test/`; shoulder fit and detail folds still FAIL. Runtime allocation/performance and native SceneKit parity remain unresolved. Keep this out of production.
6. Accepted body motion, body DQ, original face, skirts and world presentation were not changed during these garment experiments. Production installation and staging were not performed.

## Required evidence before replacing the current garment

- Connected armholes and cuffs; outer surface, lining and detail travel together.
- Stable rest silhouette and actual in-game golf swing, including raised and crossed arms.
- The same implementation tolerates a continuous shoulder rotation/twist sweep and animation transitions. Test existing clips/emotes as coverage, and do not respond to failures with named-clip patches.
- No body penetration, inverted shoulder flaps, open seams or implausible stretch in the visible garment.
- Preserve color changes and existing outfit behavior.
- Resolve native renderer behavior as part of delivery: Unity Cloth alone is not a completed SceneKit implementation. No native parity claim until demonstrated.
- Target-device performance remains unverified by the user's instruction. Dense editor cloth is not phone performance evidence.

GATE: General garment deformation FAIL — experiments in progress, no candidate is ready for installation.
