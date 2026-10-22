# Revision2 actual gate

GATE: Actual wrist/grip appearance FAIL. GATE: Dense source continuity FAIL. Keep VISUAL_GOLF_WRIST_ROLL=0. Do not run broad GPU validation or promote this candidate.

Actual comparison uses tiny-control and revision2-candidate Body skin matrices and the same exact bind matrices. Geometry counts differ by11 male vertices due independently updated head source, so body indexwise geometry/weights equality is not claimed; all53 named bone matrices remain comparable.

Top: all30 finger matrices relative to their Hand match within0.000015 degrees /0.00046mm. Thus the last shaft roll itself carries those digits correctly. Top appearance still fails: rigid transport exposes the existing baseline's open distal-pad geometry.

Address: the canonical baseline differs from the actual control. Male relative-Hand finger rotations change up to157.187 degrees; female150.391 degrees. RightLittleProximal control rest delta is identically [[.407,.342,-.847],[-.914,.152,-.377],[0,.927,.375]], which is the authored source Rz(-66 degrees)*Rx(68 degrees) in the imported frame. matchhero_golf.py:511 finger_pose applies gamma fan to every proximal, followed by the original curl about its own localX. HeroGripPolish.CanonicalGolfFingers resets to rest*anatomical-hinge curl, discarding the authored fan. The synchronous hook applies that reset consistently; the old control's address capture retained the raw authored clip rather than that canonical output. The exact reason its first LateUpdate output was absent at address is not recorded by current capture diagnostics, so it is not asserted.

This identifies a source/runtime baseline mismatch, not a failure of the mathematical last rigid rotation. The earlier source-preservation proof used a final control pose that the new synchronous path had already overwritten before rolling. Matching the authored digit contract requires preserving the actual sampled finger locals; adding another post-roll closure solver would repeat the error. The output cache currently tests seven arm/Hand/Club matrices and excludes digits, so it also cannot certify a complete final finger pose after a same-arm finger resample.

Dense CPU review:10,550 accepted pre-roll adaptive source samples /20 sex-clip-hand tracks. Roll search has discontinuous opposite signed minima. Male Driver Left at2.44188755s has an87degree sub-frame branch step,68.88094mm wrist-correction step and72.46816mm elbow-correction step. Maximum adjacent recorded roll change is90degrees, wrist-correction change70.372998mm. This is not a one-degree quantization issue. The40mm per-pose displacement bound does not bound pose-to-pose jumps. Smooth35-50degree activation does not remove these branch swaps.

Precise next contract if continued: original sampled/authored digit locals must survive the wrist carry, and roll branch selection must be continuous across the recorded track. No new mesh, skin weights, Club path, or rest hierarchy required. The current candidate does not satisfy either appearance or continuity, so no further candidate is staged here without a resolved source contract.

Files: actual-finger-relative-hand.json, dense-continuity.json, dense-continuity.py, ordering-source-proof.json (ideal final rigid carry only), HeroGripPolish.cs.patch (rejected opt-in candidate). No Assets/Unity/GPU changes by this lane.
