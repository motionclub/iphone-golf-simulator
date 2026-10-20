# REFERENCE STUDY - Spike / Scuba / Thrust overhaul (2026-10-04)

Research and plan only. Nothing in the clips, FBX, Unity or Swift was touched. Work lives in `work/emote-overhaul/`:
`REFERENCE_STUDY.md` (this file) and `pose_preview.html` (a 4-angle schematic of the proposed poses; open it in the Browser pane or any browser).
Clips are cited by video id and second stamps only. Nothing was downloaded or saved; frames were stepped in the Browser pane and the overlay was removed afterwards.
"Not found" means not found at that sampling.

## 0. What was asked (Adnan, 2026-10-04)
* Spike: "close, but it has a 2 arm motion, it's supposed to be a 1 arm spike of the racket".
* Scuba: "isn't even close, he doesn't hold his nose or extend his other arm with a swimming motion of the hand".
* Thrust: "isn't close, it should look provocative and demeaning, like the Waluigi thrust or different ones shown throughout culture".
* Mid-job: "don't waste too much time trying to find all angles, you can create them yourself" (so the extra angles come from the pose model, not from more videos).
* Mid-job: "for the thrust, we need more hip action. The hips should go from back to front when the arms hit the hips, so the hips are thrusting with the arms".

## 1. Why the current clips miss (from `NOTE_EMOTES.md`, `WATCH_EMOTES.md`, the sheets in `work/emotes/proof/`)
* Scuba: the racket hand is raised beside the face and waves the racket; the "wave" was read from a clip where the free hand sits beside the face and flicks from the wrist. The real dance has the free arm EXTENDED forward and the hand sweeping side to side, with the knees opening and closing. No extended arm, so it reads as a guard pose, and from behind (game camera) the nose hold is invisible anyway.
* Spike: the free arm is flung out at 0.28 s (an active counterbalance), the whip is 0.06 s (about 10 m/s, a snap rather than a swing) and both hands go to the hips afterwards. Together that reads as a two-arm move.
* Thrust: the pelvis travels 0.19 m forward but the hands never come near the pelvis ("no hand goes near the pelvis" is in the class docstring), the fists pump forward and up, and the pelvis tilt swings only 30 degrees. The hips and the arms are not one gesture.

## 2. Reference index
Used (what was read):

| id | what it is | read | used for |
|---|---|---|---|
| `Sn2JA4sN4lM` | adult front-view cover, 5.5 s, bust to hips, about 15 fps effective | 2.0-2.43 (every frame), 3.0-3.73 (1/15 s) | Scuba: hand over nose and mouth, other arm extended toward the camera, hand sweeping side to side, body leaning in, head dropped |
| `uoIibBzTrds` | adult front-view cover, 9.9 s, bust to knees | 0.2-9.56 (0.85 s steps) | Scuba: free arm sweeps across the chest, wide knee-bent stance, arm also reaches out to the side at the end of a sweep |
| `nJO_pws_VEE` | broadcast, high and behind the baseline, 27.5 s | 22.6-25.9 (0.1 s steps) | Spike: one-arm overhead cock, drop behind the head, whip, fold, repeated hits; free arm hangs |
| `75yS2JOT0FU` | broadcast, side-on medium shot, 11.1 s | 0.2-10.8, 1.95-3.22 (1/15 s) | Spike: arm lifts overhead 2.08-2.22, trunk folds to near horizontal 2.22-2.55, hit at about 2.4, re-lift 2.82-2.95, re-hit about 3.1; free arm passive |
| `djNEYPkWxeo` | broadcast replay, rear 3/4 close, 30.9 s | 10.3-13.0 (0.16 s steps) | Spike from behind (the game-camera angle): arm up 11.26, fold and hit 11.4-11.7, re-lift 12.06-12.38, re-hit 12.5-12.9 |
| `FNxElmg3flU` | Waluigi goal celebration (2005 game) in the top half of a reaction Short, 15.1 s | 5.2-9.0 (top half only) | Thrust: lands 5.9, arms up, then both arms sweep in and cross in front of the pelvis 6.04-6.88 while the hips push forward and the torso leans back |
| `aiXGmHcA4LA` | Waluigi goal celebration (Battle League), 6.2 s | whole clip | Thrust: wide-legged, hips-forward flourish 4.35-5.9 |
| `edASxDuAo5E` | commentary Short with real "crotch chop" clips, 27.4 s | 0.2, 11.9-12.55 (0.13 s steps), 24.67 | Thrust: forearms swing from raised elbows down into an X across the pelvis; very wide stance; hands-above-belly-button variant |
| `fqZmnxHjMwU` | wide-stance hip dance in an end zone, 12.6 s | 8.8-12.2 | Thrust: wide squat stance, pelvis rocking, hands low (human version of the stance) |

Looked at and NOT used: `RbDv5fU7HUY` (full choreography, not the signature move), `PqQx9i85o4c` (mixed compilation with children), `O6vFZ_irAr4` (youth match), `xYcT4VVFD4A` (a different celebration), `8KRuDN_4RWw` (close-up bust only), `CW_ujYw1qpQ` (8-minute tutorial; the seeks stalled before the demo was found), `oyKU2n54DrU` (low-res generated loop), `19GvBInjet0` (a store UI recording), `h4JFUW3v-10` (2005 game victory poses: arms-out gloat, not the thrust), `9tBIXjJpwfg` and `aGZaf-eb_yI` (cinematic and low-res versions of the same chop, seen but not needed), `FA6ux8D5nUM` (comedy sketch, waist-up on a blue screen), `HLgHvHft3bU` (talk show), `iFOFBJbQMSs` (long shots), `2_Iy7ZbaZI4` and `umj56pSijbE` (the character is a few pixels tall).
Text sources (no video): the Scuba description (one hand plugs the nose, free arm extended forward and waved back and forth, knees open and close to the beat; created October 2025 for a track at 163 BPM, B minor) comes from Know Your Meme and the track's Beatport page; the Waluigi chop description (arms waved toward the crotch with a forward hip thrust, cackling at the sky) from the game's director interview coverage; the list of other thrust gestures (a wrestling faction's crotch chop, Crash Bandicoot's victory dance, Incineroar's pelvic thrust, Unreal Tournament's taunt, the "three pumps" end-zone sketch, NFL and MLB pelvic-thrust celebrations that were fined or retired) from TV Tropes and sports news.

## 3. Camera facts that drive the design (`TennisShoulderCamera.cs`)
Own device: over-the-shoulder, behind and to the hero's right: position = hero + (0.8 right, 2.2 up (2.4 portrait), 4.0 back (4.8 portrait)), FOV 62/66, looking down court. That is about 11 degrees right of straight behind and about 17 degrees above, with the hero roughly a third of the screen height. So the hero's own taunt is mostly seen from BEHIND. Opponent device: from the front, far away. Intros, replays, locker: chest-height full-body, front or 3/4.
Consequences: design the silhouette from behind first (arms and legs must carry it; faces and hands in front of the body are hidden), then check the front (the signature gestures live there).

## 4. SCUBA

What it is: one hand holds the nose, the other arm is held out in front and the hand sweeps side to side like a fish tail ("swimming"), the knees open and close on the beat, the body leans in and the head peers down at the hand.
Tempo: 163 BPM means a beat of 0.368 s. The hand crosses the body in about 0.35-0.4 s in `Sn2JA4sN4lM`, so one full sweep out-and-back is about 2 beats = 0.736 s (1.36 Hz); knees do one open-close per sweep. This is an inference from the song tempo plus a 15 fps clip, not a measurement.

Beats (preview timings): 0-0.45 enter (racket tucks under the right arm, feet widen, nose hand rises, free arm reaches out); 0.45-3.40 four loops of 0.736 s; 3.40-3.90 exit (arms drop, racket back in the hand). Clip length 3.9 s.

Numbers (male proportions, authoring frame):
* stance: feet +-0.36 m, toes out 34 degrees, pelvis 0.735 m high (bob 0.03 m with the knees), forward lean 20 degrees total (pelvis 10, lumbar 5, chest 5), head pitched -14 degrees (looks down at the hand), small head roll and chest twist (+-5 degrees) with the sweep.
* nose hand: wrist in head space about (0.04 right, 0.14 below, 0.14 ahead of the head centre), thumb and index pad on the nose tip. The existing contact solver (`pad_point`, `solve_contact`, 1 mm) already does this.
* free arm (the clip hand that is not the racket hand): wrist in chest space 0.47 m ahead, 0.15 m below the neck line, sweeping laterally across about 0.24 m in chest space (about 0.36 m in the world frame once the chest twists with it), palm down and in, fingers together and slightly cupped; the hand lags the forearm by a quarter cycle (about 35 degrees of yaw), which is what makes it look like a fish tail instead of a wave goodbye.
* knees: abduction alternates (knees out on the open half, in on the closed half).

Racket: a swimming hand and a pinching hand leave no hand for the racket. Recommended: tuck it under the racket-side upper arm (the racket hand is then the nose hand) and bring it back at the end; the existing "racket off the hand" machinery (`racket` dict, whole-frame steps) covers it. Alternatives: drop it (as in Thrust) or wave the racket itself (loses the hand).

Angles:
* front: all three read (pinch, reach, wave, knees). This is the reference view.
* game camera, behind-right: the nose hand is hidden by the head; what reads is the elbow flared out on the nose side, the free arm out ahead of the head moving left and right, the knees opening and closing and the hips bobbing. Keep the elbow flare and the lean generous.
* side: arm reach and lean read; the sweep reads only as a small depth motion.
* 3/4 front: everything reads.

## 5. SPIKE

What it is: a one-arm racket slam into the court. The racket arm does everything; the free arm only hangs and swings back a little. The player is not trying to be graceful: arm over the head, drop behind it, chop down, fold at the waist, hit the court, bounce, hit again.

Observed timing (all three views agree): lift from the side to overhead about 0.4-0.5 s; top to impact about 0.28-0.33 s (the old build used 0.06 s); trunk folds 60-90 degrees during the strike; hips go back and down; impact lands beside or just ahead of the racket-side foot; the racket bounces and the player re-slams 1-5 times with decreasing amplitude (cycle about 0.8-0.9 s); then stands up, racket still in hand.
Free arm in all three views: hangs from the shoulder and swings back a little during the whip; never raised. In `djNEYPkWxeo` 12.22-12.38 it trails behind as a counterweight, which is the most it does.

Beats (preview timings, clip 3.0 s): 0-0.3 set; 0.3-0.8 wind-up (raise 0.5 s, drop behind the head, chest arches about 24 degrees, head up); 0.8-1.08 strike (trunk line 73-77 degrees from vertical at the two impacts: joint angles pelvis 32, lumbar 28, chest 24; knees flexed about 55 degrees, hips pushed back about 0.10 m); 1.08 impact; 1.08-1.3 rebound; 1.45-1.72 second hit (smaller); 1.85-2.6 aftermath (stand up, one hard head shake, glare); 2.6-3.0 reset.
Racket: stays in the hand the whole time (no release), authored for the 1.0 scale the match heroes really use (`RK_AUTHOR`), head height equals court height at impact.

Angles:
* behind (game camera): the overhead arc and the fold read; the impact is hidden behind the body unless it lands beside the right foot and the racket bounces up outside the silhouette, so keep the contact point lateral, not between the feet.
* side: the cleanest read of the arc, fold and contact.
* front: the racket comes toward the camera; the head drop and the post-hit head shake carry the anger (faces are painted, no angry expression exists).

## 6. THRUST

What it is: a cocky pelvic-thrust taunt aimed at the opponent. Cultural pattern across the references: very wide, bowlegged stance; hips driven forward hard and repeated; torso leaning back, chest out; head thrown back or chin up; hands brought to the crotch or hips (crossed forearms in the Waluigi and wrestling-faction chops); the move is read as "in your face", not as a dance.

Rule from Adnan: the hips go from back to front exactly when the arms hit the hips, so hips and arms are one gesture. In the preview this is a single driver (`th`): fists cocked at the shoulders while the hips are back, then both forearms slam down and cross at the pelvis in the same 0.14 s the pelvis drives forward, landing on the same frame.

Beats (preview timings, clip 3.5 s): 0-0.5 enter (racket dropped to the side, feet wide, fists up, hips settle back); hits at 0.60, 1.15 and 1.70 (each: rise 0.14 s, hold 0.06 s, return 0.26 s, 0.09 s dwell with the hips back); the last hit is held 0.5 s with the head thrown back and the shoulders shaking (cackle); 2.55 strut (fists to the hips, chest out, smug head tilt); 3.05-3.5 racket back in the hand, reset.
Numbers (male proportions): pelvis forward-back travel from 0.13 m behind the feet (back) to 0.29 m ahead (front) = 0.42 m on the biggest hit (0.36 m on the first); pelvis height 0.67 m (knees bent) to 0.76 m (legs straight); pelvis pitch +14 degrees (butt out) to -26 degrees (tucked under); lumbar +2 to +12; chest +12 (leaning in) to -10 (leaning back); head +2 to -32; feet +-0.44 m, toes out 42 degrees. Hands: cocked fists at chest space (+-0.26, 0, 0.14) to crossed wrists at pelvis space (+-0.06, -0.05 to -0.08, 0.15). The old clip's numbers for comparison: forward 0.19 m, pitch swing 30 degrees, hands never near the pelvis.
Racket: dropped at 0.22-0.56 s (hand opens, the racket falls to the court on the right in whole-frame steps), snapped back into the hand at 3.05-3.2 s. The chop needs both forearms free, so tucking is not an option here.

Angles:
* front: the X of the forearms at the pelvis plus the hips forward is the signature; everything reads.
* game camera, behind-right: the X is hidden. What reads is the pelvis driving away from the camera and back (butt out when back, tucked when front), the lean-back of the shoulders, the head tilt, the elbows flaring as the arms cock and slam, and the wide bowlegged stance. Exaggerate the back-to-front hip travel and the elbow flare so the move works with the X hidden.
* side: the "C" shape (hips ahead of the feet, chest leaning back) is the clearest read of the thrust.
* 3/4 front: both the X and the C read.

## 7. Cross-cutting
* The rig has all the fingers (3 joints each), so the pinch (thumb and index on the nose), a flat cupped swimming hand, and chop hands are all authorable; faces are painted, so expressions are body language only.
* Only `Emote_Scuba`, `Emote_Thrust` and `Emote_Spike` (6 FBX, both heroes) change. The three intros and the Unity wiring stay. New clips are longer (Spike 3.0 s, Scuba 3.9 s, Thrust 3.5 s versus 2.0 s): check that `GameEndedTaunt` / the next-serve cutoff leaves room.
* Authoring lives in `work/emotes/scripts/emo_clips.py` (classes `Scuba` ~L150, `Spike` ~L313, `Thrust` ~L978) on `emo_solver.py`; scale arm targets with `k = H.A / 0.505` as the existing clips do, so the female hero follows from the same keys.
* Facing: the clips are in-place, the Root never turns. Keeping the hero facing the net is the baseline; an optional turn of the Root toward the shoulder camera for the hold would help Scuba and Thrust read from behind but changes the driver, not just a clip.

## 8. Proposed gates for the implementation phase (binary, to be pre-registered before the first run)
Measure each threshold against READY and the pipeline noise floor first (lesson from the last build: R1 and T4 were unsatisfiable by definition).
* Spike: S1 the free wrist stays below the free shoulder and within 0.25 m of its hang point in every frame, free-wrist speed relative to its shoulder <= 2 m/s; S2 racket-wrist top-to-impact time 0.25-0.35 s; S3 racket head reaches court height within 1 cm at impact (scale 1.0) and there are >= 2 contacts; S4 trunk flexion at impact 65-90 degrees; S5 the racket stays in the right hand every frame.
* Scuba: C1 pinch pad within 1 cm of the nose tip in every loop frame; C2 free wrist >= 0.35 m ahead of the neck and 0.10-0.35 m below the shoulder line (hand at chest height, as in the clips); C3 wrist lateral sweep >= 0.2 m peak to peak with period 0.736 s +- 0.04 s over >= 3.5 cycles; C4 knee lateral peak to peak >= 0.12 m at the same period with feet sliding <= 1 cm; C5 the tucked racket does not pass through the body by more than 1 cm.
* Thrust: T1 pelvis forward-back travel >= 0.35 m on each of 3 hits; T2 the frame of max pelvis forward and the frame the wrists reach the pelvis differ by <= 1 frame; T3 wrist-to-pelvis-origin distance <= 0.20 m at the hits and >= 0.35 m between hits; T4 pelvis >= 0.08 m behind the feet midpoint in the back position; T5 knee flexion at each hit <= 25 degrees and at least 30 degrees less than in the back position.
* All: Root fixed, starts and ends on READY, feet slide <= 1 cm, racket re-attach lands on a whole frame.

## 9. Decisions needed from Adnan before building
1. Racket during Scuba: tuck under the arm (recommended), drop it, or wave it?
2. Racket during Thrust: drop it at the opponent's side (recommended, it is part of the taunt) or tuck?
3. Spike: one big slam plus one smaller re-slam, racket kept (recommended), or a single hit, or release the racket?
4. Longer clips (3.0 / 3.9 / 3.5 s): fine, or cap them?
5. Thrust hands: crossed forearms at the pelvis (Waluigi / wrestling chop, recommended) or flat hands slapped on the hip bones?
6. Facing: keep facing the net, or turn toward the camera for the holds?
7. Content level: the thrust plus chop is cartoon-level and clothed, in the same territory as a 2005 console sports game, but the pelvic-thrust gesture could count as mild suggestive content in the App Store age-rating questionnaire. Worth a look if it was not planned for.

## 10. What I could not verify
* The viewer is a schematic on stick proportions, not the real rig or solver; it shows intent and timing, not final poses.
* Scuba hand shape and sweep plane come from two 15 fps front clips and the written description; no good side or back clip was found (by instruction, the other angles are derived).
* The Waluigi hip push is seen from one low front 3/4 camera; the pelvis travel numbers are mine, scaled up on purpose after the "more hip action" note.

## 11. Preview self-check (`node check_poses.js` in this folder)
Runs the pose model of `pose_preview.html` headlessly and prints the numbers the gates in section 8 would look at. Last run: Spike top-to-impact 0.333 s, racket tip 0.00-0.02 m from the court at the two impacts, trunk line 73-77 degrees, right knee flexion 54-57 degrees, free wrist never above its shoulder (at least 0.47 m below) and moving at most 1.25 m/s relative to the shoulder; Scuba sweep period 0.733 s over 3 cycles, knee spread 0.15 m peak to peak, fingertip within 3 cm of the nose (the real solver's 1 mm contact fix is not in the preview); Thrust pelvis travel 0.355 / 0.399 / 0.42 m for the three hits, wrists reach the pelvis on the same frame the pelvis peaks (0 frames apart on all three), wrist-to-pelvis distance 0.15 m at the hits and at least 0.58 m between hits. These are properties of the schematic, so they show the plan is internally consistent, not that the rig will pass.
