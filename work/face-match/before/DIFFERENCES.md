# Locked face targets — baseline visual audit

Captured production court lighting with VISUAL_CHARACTER_SKIN_POLISH and VISUAL_BLINK_NORMAL_FIELD UNSET. No light, post-processing, skin-tone, map, or game-camera changes. Portrait camera follows the head anatomical axes; racket visibility is suppressed only for unobstructed portrait proof. Gameplay frame is untouched and shows the back of the near player's head.

Only FRONT references were supplied. Three-quarter and gameplay sheets retain the locked front reference on the left. They are not invented matching-angle references. Studio lighting cannot be reproduced exactly from a flat reference image; production lighting is retained as requested.

Priority order:
1. Head shape: male lower face reads too long/narrow with a tapered chin; female upper head is broad while chin reads sharper. Measure after uniform crown/chin registration before changing geometry. Bald silhouettes are otherwise close.
2. Eyes: male apertures/irises are small and narrow; female eyes are large but have a flatter, pale upper edge and weak upper-lid definition. Corner seams and angular skin normals weaken both eyelids. Eye height/spacing require front overlay measurements.
3. Brows: both have thick raised, block-like brow masses. Female reference is noticeably finer; male reference ends are softer and less pointed. Dark-brown tint is too warm relative to the target.
4. Nose: bridge/alar transitions look pinched or blurred by uneven normals. Female tip/nostril definition is weak; male nose shadow is heavy and asymmetric under court light.
5. Mouth: male mouth appears too narrow; both lack a defined continuous cupid's bow, readable mouth seam, and satin lower-lip highlight. Local tessellation shows radial creases and patchy shading. Female reference has a gentle smile; current lip corners are flatter.
6. Cheeks/jaw: male stubble tint is nearly absent; cheek and nasolabial normals look lumpy. Female cheek gradients lack warm soft volume; chin/neck junction has an abrupt dark line.
7. Ears: inner folds are coarse and pale; reference cartilage and ear rim carry more warm definition. No separately supplied side target establishes exact ear depth.
8. Hairline: both locked targets are bald; no hairline/hair additions needed.
9. Skin: large near-flat peach regions with grey left-side shadow; missing restrained satin highlight and regional warm/cool pigment variation. Male needs subtle lower-face stubble, female needs softer cheek/lip warmth. Preserve selectable skin tones.
10. Eye shine: existing catchlights work but resemble fixed white dots; reference iris/limbal contrast and wet-edge highlights have more depth. Avoid increasing eye size to simulate shine.

Baseline behavior issue: active OriginalSeam path accepts blink but returns before gaze/brow expressions. This is pre-existing, not a passing expression gate.
Baseline Unity/Tools/check.sh: 11 missing URP/Core assembly-reference errors; logged separately. Unity Editor compilation/capture succeeded without compile or shader errors.
