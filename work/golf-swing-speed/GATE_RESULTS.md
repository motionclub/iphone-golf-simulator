# Golf swing speed: gate results (2026-10-18)

**Method:** the in-game film, Cliffside hole 1, 60 fps game clock.
- The phone path is real: `GolfGame.NativeMotion` receives 100 Hz samples during the frame's Update, the detector fires the downswing and the impact, and Launch runs as normal.
- The phone swing is synthetic: 0.8 s backswing to 2.75 rad, a 0.06 s top, a constant-acceleration downswing of D s, then the follow-through.
- **Before** is the shared working tree at 18:00. **After** is the same tree plus `install.sh`.
- Numbers come from `scripts/measure.py`: `logs/measure_before.txt`, `logs/measure_before_tt.txt` (tap/touch) and `logs/measure_final.txt`.

GATE 1: DOWNSWING — the club reaches the ball on the frame the phone does, for every club and phone pace. **PASS**
- **Phone ball frame minus screen impact frame = 0** in all 11 motion takes:
  - driver at D = 0.20, 0.25, 0.32 and 0.40 s (male), and 0.25 s (female);
  - iron and wedge at 0.28 s, male and female;
  - putter at 0.35 s, male and female.
- **Before**, the club only reached the ball by snapping on the phone's impact frame. It started down 4–5 frames after the phone's top, on a fixed 0.25 s clock.
- **On-screen downswing**, from the club leaving the top to the ball:

| phone downswing | on screen |
|---|---|
| 0.20 s | **0.167 s** |
| 0.25 s | **0.20 s** |
| 0.32 s | 0.25 s |
| 0.40 s | 0.33 s |

- **Pro reference:** top to impact takes 0.19–0.23 s (7 pros measured, `work/swing-compare`). A phone swung at pro pace now gives a pro-pace swing on screen. Before, every swing was the fixed 0.25 s clock, cut short by the snap.

GATE 2: NO POPS — club-head step ≤ 2.5 × the larger neighbouring step + 30 mm (the `SwingSmoothnessTests` rule; putter + 10 mm), through the downswing, the impact and the follow-through. **PASS**

| take | before: worst step (frame) | after |
|---|---|---|
| male driver 0.25 | **2661 mm** (98; neighbours 765) POP | 885 mm, no pop |
| female driver 0.25 | **2636 mm** POP | 881 mm, no pop |
| male driver 0.20 | **3141 mm** POP | 1045 mm, no pop |
| male iron 0.28 | **1853 mm** POP | 865 mm, no pop |
| female iron 0.28 | **1835 mm** POP | 861 mm, no pop |
| male wedge 0.28 | **1593 mm** POP | 689 mm, no pop |
| female wedge 0.28 | **1577 mm** POP | 681 mm, no pop |
| male putter 0.35 | **52 mm** snap at impact (neighbours 12) | 44 mm, see note |

- **Rewinds** (clip time going back while swinging): none, before or after, in the filmed paces. The old code would send a club that got to the ball first back to the impact pose. That case is now handled (the follow-through carries on), but a slow-enough phone swing to show it was not filmed before.
- **Smoothness** (largest frame-to-frame change of the club-head step, downswing to follow-through): before 1159–2567 mm, after **239–297 mm** for driver, iron and wedge. The touch path, the accepted reference, measures 109 mm.
- **Club-head speed shape:** it now peaks at the ball and eases off after it, matching the accepted touch swing. Male driver 0.25, metres per frame: 0.79 → **0.89** → 0.78 → 0.70; touch 0.86 → **0.87** → 0.83 → 0.76.
- **Note:** the putter keeps a 44 mm one-frame jump in its BACKSWING at clip 0.70 s (male frame 67, female frame 60). It is there before and after, and with the clearance tracks off. It is in the Putt clip or a grip/clearance layer: a follow-up, not this change.

GATE 3: CONTACT AND BALL TIMING UNCHANGED. **PASS**
- **Ball launch frame:** before and after are identical in every take (98 / 99 / 95 / 102 / 103 …). The ball still leaves on the phone's impact sample.
- **Contact:** the club is at the clip's authored impact time on the phone's ball frame, and the ball leaves on that frame or the next. That is the same as the touch / replay path, which is 1 frame.
- **No clip, landmark, rig or track changes:**
  - `golfer_m/f.fbx` and `golfer_m/f_clips.json`: impact frames unchanged, files untouched by this job;
  - `Resources/HeroClearance` untouched.

GATE 4: PATHS NOT PACED BY A PHONE ARE UNCHANGED. **PASS**
- **Touch / replay / TV path** (`OnLoad` + `StrikeToward`), male: the event frames are identical before and after (strike 82, impact 96, ball 97, finish 137). Downswing 0.25 s, no pops. The female after-take shows the same frames; there is no female before-take.
- **Touch "tap"** (`NativeSwing`): identical before and after (82 → 92, ball 92).
- An early build of this change also altered the tap. That was reverted inside the patch (the rule only applies to a backswing the pose was following).

GATE 5: HAND-CLEARANCE TRACKS ARE NOT THE CAUSE AND STILL APPLY. **PASS**
- Before: male driver 0.25 with the baked tracks off measures exactly the same as with them on (the 2661 mm pop either way).
- No clip timing changes, so the clip-time-keyed tracks stay valid.

GATE 6: TESTS. **PASS (EditMode, offline), NOT RUN (PlayMode)**
- **EditMode:** 41/41 pass (`logs/editmode_offline.txt`), with the real test files compiled against the patched sources with Unity's Roslyn + NUnit and run on Unity's bundled .NET (`scripts/offline/`). That covers the new `GolfSwingPaceTests` (4 cases: driver fast/slow, iron, putter) and all 37 `MotionSwingDetectorTests`.
- **PlayMode** (`SwingSmoothnessTests`, `GolfMotionReadyTests`, `HeroGolferTests`, `NativeGolfFlowTests`): NOT RUN here, to stay within one Unity launch (coordinator). They are handed to the integration chat's suite run.
- **Compile:**
  - The patched working-tree `Assets/Scripts` compiles clean (`scripts/cscheck.sh`).
  - The index-only tree has compile errors, all in other sessions' staged tennis/environment files that need untracked files (`ExperienceTrace`, `LuminousCoastFrameBudget`). None are in this job's files.

GATE 7: BEFORE / AFTER FILMS. **PASS**
- `film/01_driver_before_after.mp4`: male + female driver at D = 0.25, TV game camera + face-on, synced on the phone reaching the ball, real speed then 0.25×.
- `film/02_iron_wedge_putter_fast_before_after.mp4`: male iron, female wedge, male fast driver (0.20 s), male putter.
- `proof/impact_window_faceon_male_driver_250.jpg`: frames 92–99, before vs after.

**Not run:**
- a phone / device build;
- AirPlay;
- a real phone's motion. The phone swing is synthetic, and a real player's gyro noise and downswing shape differ.

Pacing follows the measured phone progress monotonically, so jitter cannot run the club backwards. If the samples stop for more than 0.2 s mid-downswing, the old clock takes over.
