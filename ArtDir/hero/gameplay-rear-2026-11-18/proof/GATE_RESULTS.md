# Motion Club rear gameplay study

- **GATE: GAMEPLAY EVIDENCE PASS.** The six views are crops from recorded Unity gameplay. Full source frames are preserved in `captures/`.
- **GATE: GOAL STUDIES PASS.** The three generated pairs keep each sport's kit, palette, rear action and equipment recognizable at the same approximate framing. The images are art mockups. Pose, lighting and background details vary slightly from the source frames.
- **GATE: FRESH UNITY CAPTURE FAIL.** The isolated Editor repeatedly lost its licensing connection before it produced frames. The comparisons use November 11 and 13 recordings. [Capture log](unity-capture.log)

## Frames and art direction

| Sport | Recorded source | Goal |
| --- | --- | --- |
| Golf | November 13 production driver follow-through, frame 74 of `work/final-plan-1111/anim/films_1113/golf_swing/{male,female}_Driver/game_00074.jpg` | Keep the teal and rose polos and navy bottoms. Show the cloth pulling across the shoulders during rotation, the tucked waist and belt on him, and distinct pleat depth on her. |
| Bowling | November 13 Club Lanes approach, frames 103 and 1133 of `work/final-plan-1111/anim/films_1113/bowling/frames/` | Keep the red and lime bowling kits and ball position. Give each top a sewn back yoke and clean armholes. Let the trousers and capris crease with the step. The gameplay viewport crops the trailing feet in these frames. |
| Tennis | November 11 Resort serve hold, `work/hero-build-1111/shots/final_film_{m,f}/back_0006_PlayerServeHold.jpg` | Keep the red polo with blue shorts and the chartreuse tank with a white skort. Close the visible sleeve gap, shape folds from the shoulder blades into the waist, and separate the skort's waistband, pleats and undershorts. |

## Image generation directions

The built-in image generation tool took each two-panel gameplay crop as its edit reference. Each prompt requested the same male-left and female-right layout, approximate character size, pose, body proportions, cap, equipment, palette, gameplay camera and venue. The goal was to replace hard plastic-like reflections with restrained cloth highlights, visible garment construction and warm, softly shaded skin. The tennis prompt also used the existing November 17 male and female design sheets as fit and fabric references. The three output images are saved in `targets/`.
