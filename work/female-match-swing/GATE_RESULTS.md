# Female hands + swing, 2026-10-19 (Adnan: "match her swing to the male, fix her hands so they are proper", then "reshape the hands ... look right everywhere")
Proof: proof/BEFORE_AFTER_hands.jpg, proof/BEFORE_AFTER_golf_swing.jpg, proof/phone/ (simulator shots). Reference: ArtDir/style/alive/hand-reference-2026-10-19/.
GATE: GOLF_WRIST_FLIPS: female forearm worst single-frame turn in the drive 115 deg -> 56 deg (male 55); backswing right-arm jerk 18-31 deg/frame -> 4-6 (capture at the same batch conditions, work/female-match-swing/scripts/jumps.py) - PASS
GATE: GOLF_RIGHT_ARM_IMPACT: right upper arm 86 deg on one frame at impact vs male 60 (still above the male) - FAIL (disclosed, one frame)
GATE: FEMALE_TRACKS_REBAKED: Tracks_Female_Golf.bytes baked with the new solver, 26 clips, COST p99 0.023 ms; the sweep's BODY/CLOTH fail frames after = 340/394 of 3843 (no BEFORE run to compare, SWEEP_BEFORE=0) - NOT COMPARED
GATE: TENNIS_SWING: source clips Female_* vs Male_* have the same fast pronation spikes (both authored); no tennis clip change made - NOT CHANGED
GATE: MENU_HANDS: relaxed stand now has a soft finger curl in Unity plaza and the phone menu - PASS (eye)
GATE: HAND_SHAPE: female finger radius at the tip 3.8 mm -> up to 5.1 mm (+34 % at the very tip, +3..15 % along the finger), smooth normals; topology/weights/UVs/rest unchanged; max vertex move 3.3 mm - PASS (eye, close-ups in Unity plaza, golf, tennis)
GATE: GLOVE_SHARDS: orange knuckle skin shards through the female golf glove removed (hand + wrist-blend triangles hidden under the glove, female only) - PASS at address f260/f330/f365; cuff shows no hole in the same frames
GATE: MALE_UNCHANGED: HeroHandShape and the glove rule are female-only; RelaxFingers (menu pose) and the lobby re-export touch the male menu hands too - FAIL (disclosed: male relaxed hands change)
GATE: TESTS: native / EditMode suites NOT run - NOT RUN
Not verified: physical phone; lobby golf swing playback; non-standard skins; left-handed female glove (GloveR path untested).

## Round 2 (hands holding nothing, "way closer to the ref images")
GATE: RELAXED_HAND_POSE: female wrist 8 -> 5 deg off the forearm line; finger bones MCP/PIP 10-38 / 7-21 deg (index..little), thumb 9/12; fingertip joint now aimed from the bone's real tip (the rest pose's own tip hook no longer adds); thumb along the front of the index - PASS vs the reference panels by eye (dorsal/front views still show a thumb bulge near the knuckles that reads a little like a pinch) - PARTIAL
GATE: NOTHING_HELD_EVERYWHERE: plaza fingers stay relaxed while walking/running (female, FingerWeight); emotes/intros keep their own hands; golf/tennis clips holding a club or racket unchanged - PASS (code path; walk not filmed)
GATE: PHONE_MENU: new build installed on the simulator, girl hero main menu + locker show the relaxed hand (proof/phone/final_main_girl*.png) - PASS (simulator only)
GATE: MALE_HAND_POSE_UNCHANGED: RelaxFingers + straight wrist gated to look.female; the lobby export re-ran so the male files are back to their accepted pose - PASS
Pitfall: the plaza/golf/tennis heroes use CharacterLod (HeroLod proxies, set by the main camera's view). Extra review cameras then see a REDUCED mesh; always capture hands with CHARACTER_LOD_FORCE=0 (the faceting I first chased was LOD1+). The LOD triangle cache is keyed by the final mesh hash, so the new hand shape means a cache miss (computed on a worker thread at runtime) until it is regenerated.
