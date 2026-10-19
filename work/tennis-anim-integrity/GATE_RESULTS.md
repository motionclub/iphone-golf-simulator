# Tennis animation integrity — GATE_RESULTS (chat 4, 2026-10-17)

**GATE: TENNIS_ANIM_INTEGRITY FAIL** — RATE, APPROVED, FEET (sole dip) and the Visual gate pass. CONTACT, SERVE, GRIP, FEET (slide),
NO_POP and REF_MATCH (2 of 5 lines) still fail. The fail lines are listed at the bottom; two of them need a gameplay-rule decision
(RULES_FOR_ADNAN.md).

How it was measured: real AutoPlay matches in the chat-4 Unity clone, telemetry of both heroes on every frame (`unity/Runtime/TaiRecorder.cs`),
and every clip sampled at 120 Hz on the real prefabs (`unity/EditorDump/TennisAnimClipDump.cs`). Scoring: `scripts/analyze.py`,
`clipcheck.py`, `gates.py`. BEFORE = the project as found on 10-17 (male + female 120 s filmed matches, male 300 s telemetry match).
AFTER = chat-4 changes in the clone (male + female 120 s filmed, male + female 300 s telemetry, ServeSweep per hero).
Raw data and films: `/Users/adnanyonathan/tai-films` (outside the repo, ~4 GB).

| gate (brief) | result | before → after |
|---|---|---|
| RATE: every tennis clip keyed at 60 Hz | **PASS** 42/42 tennis stroke / locomotion / ready clips (21 per hero). Not mine and not 60 Hz: the shared taunts Spike/Scuba/Thrust and the 3 intros (keys 16.7–33.3 ms, 12 clips) — flagged to chat 1 in REQUESTS.md | ReadyIdle (2) and the ArmCorrected torso curves were 30 Hz → all 60 Hz |
| APPROVED: hands / racket tip ≤ 1.5 cm of the approved clip at shared frames | **PASS** 28/28 strokes × heroes (14 per hero), all 0.0 cm | up to 87 cm off (10-16 re-solve) → 0.0 cm |
| CONTACT: strings ≤ 3 cm, speed at contact ≥ 70 % of peak, peak ± 2 frames | **FAIL** | player hits 3/106 → 74/135; rival hits 0/116 → 20/158 |
| SERVE: swing pace 0.9–1.1 × authored (ServeSweep) | **FAIL** (close for the player) | player 0.47–0.60 → 0.86–0.95 (ServeSweep) / 0.83–0.90 (matches); rival 1.75–1.91 → 1.25–1.36 |
| GRIP: racket hand closed in 100 % of frames, no thumb-up fist / claw / paddle free hand | **FAIL** (close) | male racket hand open 98.4 % → 0.1 % of on-racket frames; female 0.5 % → 0.8 % (two-hander); free hand splayed male 70 % → 0.9 %, female 2.4 % → 0.2 % |
| FEET: planted-foot slide ≤ 1.5 cm | **FAIL** | plants sliding > 1.5 cm: 43–45 % → 44–47 % (unchanged) |
| FEET: sole dip ≤ 5 mm | **PASS** | 41–62 mm (joint sink) → max 2.0 mm (shoe sole points) |
| NO_POP: no joint > 2 × clip peak across transitions | **FAIL** | player 187 → 171 spikes / min; rival 264 → 358 spikes / min |
| BUGS: every BUGS.md line FIXED with proof or OPEN with the reason | **PASS** | see BUGS.md (status column) |
| REF_MATCH (REFERENCES.md) | **FAIL** 2 of 5 lines pass (Forehand, Backhand shapes) | racket peak at contact 4/34 → 76/142 groundstrokes |
| Visual: filmed rally + serve per hero, before vs after | **PASS** | `proof/compare/*` (1080p gameplay, side view, hand close-ups) |

## What changed (files)
- `Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs` (installed, staged): stroke time from the render-time time-to-contact (no 1/120 s
  step judder); one time-warp per swing from the pose on screen to the contact (hold or compress, authored rate at contact); contact
  re-timing by the strings' path length (forward swing 0.14 s from the real-time reference; the serve keeps its own trophy → contact);
  path-aimed contact assist (no pinning, no ContactRecovery hold); exact contact pose on the contact frame; take-back held fully loaded;
  rival serve on the toss schedule; inertial blends on every clip / state switch and run-family flip; foot lock fades out; shoe-sole
  grounding; emotes ride walking legs while the body is moved; ReadyIdle60 in the Ready slot; base cross-fade 0.12 s.
- `Unity/Assets/Scripts/Tennis/HeroTennisInertia.cs` (+ .meta, new, installed, staged): pose inertialization.
- `Unity/Assets/Scripts/Tennis/HeroGripPolish.cs` (installed, staged): racket-hand curl direction measured per hero (the fixed sign
  opened the male fingers); off-hand relax (curl + de-splay) when off the racket.
- Clip assets + hero prefab slot times — **package for chat 6** (`install/install_for_chat6.sh install|rollback <Unity dir>`): the 14
  approved strokes resampled to 60 Hz (`match60/export/fbx`, exact at shared frames), the approved Forehand/Backhand ArmCorrected
  re-keyed at 60 Hz and the ReadyIdle60 clips (`install/perf`), prefab contact / leftRelease back to the approved table. These go
  together: the approved Forehand needs its approved contact (0.667 s, not 0.650 s).
- Staged: the 4 Unity code files and this folder's docs, scripts, harness and proof images. Not staged (large binaries, on disk for
  chat 6): `match60/` (approved strokes at 60 Hz, FBX + blends, 105 MB), `install/perf/` (clips, 92 MB), `proof/compare/` (before/after films, 33 MB).
- Rollback of the code: `work/tennis-anim-integrity/src/before/` holds the two files as found (HeroTennisInertia.cs is new: delete it).

## Per clip × hero (clip dump)

| hero | clip | RATE | APPROVED (hands / racket tip vs approved 30 Hz at shared frames) | before → after |
|---|---|---|---|---|
| Male | Male_BackhandArmCorrected | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 2.8 cm (R 0.5 L 0.8 tip 2.8)) |
| Male | Male_BackhandWide | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 9.8 cm (R 7.4 L 4.7 tip 9.8)) |
| Male | Male_ForehandArmCorrected | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 80.0 cm (R 14.7 L 3.5 tip 80.0)) |
| Male | Male_ForehandOpen | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 81.2 cm (R 44.1 L 8.4 tip 81.2)) |
| Male | Male_ForehandShort | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 55.0 cm (R 55.0 L 8.3 tip 32.0)) |
| Male | Male_ForehandWide | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 77.3 cm (R 53.9 L 1.8 tip 77.3)) |
| Male | Male_Idle | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Male | Male_Overhead | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 36.8 cm (R 11.1 L 0.6 tip 36.8)) |
| Male | Male_ReadyIdle60 | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE n/a→PASS, APPROVED n/a→n/a () |
| Male | Male_RecoverCenter | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 3.1 cm (R 0.9 L 0.8 tip 3.1)) |
| Male | Male_Return | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 39.7 cm (R 18.1 L 30.5 tip 39.7)) |
| Male | Male_RunForward | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Male | Male_RunLeft | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Male | Male_RunRight | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Male | Male_Serve | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Male | Male_SliceApproach | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 87.4 cm (R 22.4 L 14.0 tip 87.4)) |
| Male | Male_SplitToBackhand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 75.3 cm (R 16.9 L 18.2 tip 75.3)) |
| Male | Male_SplitToForehand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 15.8 cm (R 5.2 L 7.7 tip 15.8)) |
| Male | Male_VolleyBackhand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 65.2 cm (R 65.2 L 46.7 tip 54.2)) |
| Male | Male_VolleyForehand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 7.0 cm (R 2.6 L 3.4 tip 7.0)) |
| Male | Male_Walk | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Female | Female_BackhandArmCorrected | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 3.5 cm (R 0.5 L 0.7 tip 3.5)) |
| Female | Female_BackhandWide | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 6.7 cm (R 6.7 L 1.1 tip 5.1)) |
| Female | Female_ForehandArmCorrected | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 52.9 cm (R 13.6 L 2.4 tip 52.9)) |
| Female | Female_ForehandOpen | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 61.0 cm (R 39.6 L 10.3 tip 61.0)) |
| Female | Female_ForehandShort | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 67.8 cm (R 33.2 L 7.7 tip 67.8)) |
| Female | Female_ForehandWide | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 82.9 cm (R 18.1 L 9.1 tip 82.9)) |
| Female | Female_Idle | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Female | Female_Overhead | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 61.9 cm (R 15.0 L 0.8 tip 61.9)) |
| Female | Female_ReadyIdle60 | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE n/a→PASS, APPROVED n/a→n/a () |
| Female | Female_RecoverCenter | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 2.8 cm (R 0.8 L 0.4 tip 2.8)) |
| Female | Female_Return | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 43.0 cm (R 24.9 L 30.5 tip 43.0)) |
| Female | Female_RunForward | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Female | Female_RunLeft | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Female | Female_RunRight | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Female | Female_Serve | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |
| Female | Female_SliceApproach | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 64.3 cm (R 41.7 L 10.8 tip 64.3)) |
| Female | Female_SplitToBackhand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 70.1 cm (R 14.2 L 16.8 tip 70.1)) |
| Female | Female_SplitToForehand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 17.7 cm (R 5.8 L 4.3 tip 17.7)) |
| Female | Female_VolleyBackhand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 41.6 cm (R 19.1 L 26.4 tip 41.6)) |
| Female | Female_VolleyForehand | PASS (60 fps, keys 16.7-16.7 ms) | PASS max 0.0 cm (R 0.0 L 0.0 tip 0.0) | RATE PASS→PASS, APPROVED FAIL→PASS (max 10.2 cm (R 3.2 L 0.5 tip 10.2)) |
| Female | Female_Walk | PASS (60 fps, keys 16.7-16.7 ms) | n/a  | RATE PASS→PASS, APPROVED n/a→n/a () |

## Live matches

| run | hero | CONTACT | SERVE (visible swing rate) | FEET slide | FEET dip | NO_POP |
|---|---|---|---|---|---|---|
| BEFORE before_male | male_player | FAIL 2/24 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.53, 0.48, 0.57, 0.49, 0.53, 0.51, 0.53, 0.49, 0.58, 0.51, 0.44 | FAIL 101/257 plants slide > 1.5 cm | FAIL max sole dip 54.6 mm (joint sink only) | FAIL 445 transition spikes > 2x clip peak |
| BEFORE before_male | female_rival | FAIL 0/27 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.75, 1.87, 1.87, 1.87 | FAIL 88/208 plants slide > 1.5 cm | FAIL max sole dip 41.4 mm (joint sink only) | FAIL 489 transition spikes > 2x clip peak |
| BEFORE before_female | female_player | FAIL 1/25 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.51, 0.51, 0.49, 0.51, 0.61, 0.51, 0.50, 0.50, 0.55, 0.49 | FAIL 107/268 plants slide > 1.5 cm | FAIL max sole dip 318.9 mm (joint sink only) | FAIL 354 transition spikes > 2x clip peak |
| BEFORE before_female | male_rival | FAIL 0/27 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.87, 1.87, 1.87, 1.87 | FAIL 100/216 plants slide > 1.5 cm | FAIL max sole dip 61.6 mm (joint sink only) | FAIL 592 transition spikes > 2x clip peak |
| BEFORE before_tel_male | male_player | FAIL 0/57 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.53, 0.47, 0.56, 0.47, 0.54, 0.51, 0.53, 0.49, 0.51, 0.50, 0.53, 0.54 | FAIL 277/610 plants slide > 1.5 cm | FAIL max sole dip 55.5 mm (joint sink only) | FAIL 883 transition spikes > 2x clip peak |
| BEFORE before_tel_male | female_rival | FAIL 0/62 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.87, 1.87, 1.75, 1.87, 1.87, 1.91, 1.87, 1.87, 1.87, 1.91, 1.87, 1.87 | FAIL 257/555 plants slide > 1.5 cm | FAIL max sole dip 45.2 mm (joint sink only) | FAIL 1292 transition spikes > 2x clip peak |
| AFTER after_male | male_player | FAIL 12/21 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.88, 0.89, 0.83, 0.88, 0.84, 0.87, 0.89, 0.85, 0.88, 0.88, 0.88, 0.89 | FAIL 120/252 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 414 transition spikes > 2x clip peak |
| AFTER after_male | female_rival | FAIL 1/24 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.25, 1.32, 1.32, 1.36 | FAIL 74/173 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 564 transition spikes > 2x clip peak |
| AFTER after_female | female_player | FAIL 12/23 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.88, 0.89, 0.90, 0.87, 0.86, 0.88, 0.88, 0.88, 0.86, 0.85, 0.87 | FAIL 105/241 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 343 transition spikes > 2x clip peak |
| AFTER after_female | male_rival | FAIL 4/24 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.34, 1.31, 1.34, 1.31 | FAIL 92/190 plants slide > 1.5 cm | PASS max sole dip 1.9 mm (shoe sole points) | FAIL 837 transition spikes > 2x clip peak |
| AFTER after_tel_male | male_player | FAIL 23/38 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.88, 0.89, 0.87, 0.87, 0.88, 0.84, 0.87, 0.86, 0.87, 0.87, 0.88, 0.84 | FAIL 260/543 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 915 transition spikes > 2x clip peak |
| AFTER after_tel_male | female_rival | FAIL 4/51 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.29, 1.31, 1.29, 1.36, 1.27, 1.36, 1.25, 1.27, 1.30, 1.29, 1.29, 1.27 | FAIL 202/464 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 1534 transition spikes > 2x clip peak |
| AFTER after_tel_female | female_player | FAIL 27/53 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.88, 0.89, 0.87, 0.88, 0.87, 0.88, 0.88, 0.89, 0.87, 0.87, 0.88, 0.88 | FAIL 270/565 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 721 transition spikes > 2x clip peak |
| AFTER after_tel_female | male_rival | FAIL 11/59 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.26, 1.34, 1.31, 1.32, 1.34, 1.34, 1.34, 1.32, 1.33, 1.34, 1.26, 1.31 | FAIL 222/519 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 2077 transition spikes > 2x clip peak |
| AFTER servesweep_male | male_player | FAIL 9/12 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.92, 0.92, 0.90, 0.90, 0.89, 0.86, 0.86, 0.85, 0.87, 0.89, 0.86, 1.03 | FAIL 71/153 plants slide > 1.5 cm | PASS max sole dip 1.9 mm (shoe sole points) | FAIL 190 transition spikes > 2x clip peak |
| AFTER servesweep_male | female_rival | FAIL 0/13 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.36, 1.32, 1.27, 1.32 | FAIL 60/146 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 563 transition spikes > 2x clip peak |
| AFTER servesweep_female | female_player | FAIL 7/11 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 0.95, 0.94, 0.94, 0.91, 0.89, 0.89, 0.94, 0.83, 0.86, 0.86, 0.95 | FAIL 63/152 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 123 transition spikes > 2x clip peak |
| AFTER servesweep_female | male_rival | FAIL 5/16 hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames | FAIL serve swing rate (trophy hold release -> contact) 1.34, 1.32, 1.31, 1.32, 1.34, 1.34, 1.29 | FAIL 79/153 plants slide > 1.5 cm | PASS max sole dip 2.0 mm (shoe sole points) | FAIL 702 transition spikes > 2x clip peak |

## REF_MATCH (REFERENCES.md; clips cited by id + timestamp only)

| clip / behaviour | reference ids + timestamps | check | result |
|---|---|---|---|
| groundstroke timing (all strokes, both heroes) | YAAUOoMbrfM 12.20-12.97 (real time, end view) | forward swing (take-back end -> contact) 0.08-0.20 s AND racket speed peak within +-2 frames of contact AND finish <= 0.25 s after | FAIL - forward swing in range 77/142 (median 0.167 s), peak at contact 76/142, finish in time 142/142 |
| Forehand shape | t2hmOyh61_M 2.40-3.84 (back view) | our Forehand is the approved clip (APPROVED gate, 0.0 cm) whose finish wraps over the left shoulder, phase order take-back -> drop -> contact in front -> wrapped finish | PASS - ForehandArmCorrected = approved 30 Hz solve (0.0 cm at shared frames); the 60 Hz re-solve (racket straight up at the finish) is gone |
| Backhand (two hands) shape | UsR2o_koFyU 2.60-5.12 (back view), 7jW0JjnU-3M | both hands on the handle through contact; left hand released after contact (leftRelease >= contact) | PASS - BackhandArmCorrected approved (0.0 cm); prefab leftRelease 0.967 s > contact 0.633 s (both heroes) |
| Serve phase order + pace | c64ha9CGlE0 0.5-27 (front-right), aFPEB-PSp0c (back), mH_oHknF_Jo / -e9EsZthF7k (F) | bounce -> toss -> trophy (hold) -> drop -> contact -> landing; racket fastest at contact (peak within +-2 frames) | FAIL - serve peak at contact 86/118; phase order is the approved Serve clip's (unchanged keys) |
| free hand | t2hmOyh61_M, f7aHe4JHz3c, n1ilKdCCnpw (off hand loose, fingers softly curled) | off hand off the racket: no splayed paddle (index-little spread <= 30 deg) in >= 99 % of frames | FAIL - male_player: splay 47/5203, female_rival: splay 3/3012, female_player: splay 11/4754, male_rival: splay 49/3309, male_player: splay 95/13054, female_rival: splay 2/8138, female_player: splay 35/10949, male_rival: splay 99/9238 |


## Fail lines (what is left, and why)
1. CONTACT (player): the game gives a late phone swing ~50 ms to contact (`PaceToContact` 2–3×). The forward swing can't accelerate
   over 3 frames. Needs a rule change — RULES_FOR_ADNAN.md §1.
2. CONTACT (rival): the game switches the wing (prepared forehand → backhand) ~0.18 s before contact, so the arm crosses the body and
   peaks early (RULES_FOR_ADNAN.md §2). The rival's strings-to-ball gap is 2.5–10 cm (was 3–12 cm).
3. SERVE: the player's swing plays at 0.83–0.95×, just under 0.9 on some serves (the C1 hold-release corner counts in the measure);
   the rival serve is still 1.25–1.36× because it gets ~0.18 s of swing from the game.
4. GRIP: 0.1 % (male) / 0.8 % (female two-handed backhand) of on-racket frames below the wrapped curl; free hand splayed in 0.2–1.5 %.
5. FEET slide: unchanged at ~45 % of plants; mostly low-speed drift while the actor still moves (LockFeet stepping). Not fixed.
6. NO_POP: wrist / hand flips while ReadyIdle blends with a run clip (single-frame 2,000 deg/s with smooth weights). The rival got
   worse (264 → 358 / min). The cause isn't isolated yet (candidate: quaternion hemisphere flip in the blend, or the clearance solver
   on mixed poses).
7. REF_MATCH: groundstroke timing (racket peak at contact in 76/142 hits) and serve peak (86/118) — same causes as 1–3.

## Tests (A/B: chat-4 clone vs a baseline clone without chat 4, same machine, muted)
Baseline = `~/tai-films/UnityBase`: the same clone with the pre-chat-4 driver / grip polish (`src/before`), no HeroTennisInertia, and the
10-16 assets from the real Unity/ (prefabs, ArmCorrected, the 28 stroke FBX, MatchHeroClipMapTests). Results in `~/tai-films/tests_*`.
- **EditMode: 602 / 606 on both** — identical failures, none from chat 4: `NoCodeOutsideTheRegistryNamesAnOlderHero`,
  `TheOneTVFixtureWrittenBySwiftParsesAndIsValid` (look for repo paths next to the project; the clones sit outside the repo),
  `HeroClearanceTests.ProxyIsFittedForEveryBodyPart…` x2 (chat 3's solver).
- **PlayMode, 19 tennis / hero suites (69 tests): 54 / 69 on both, identical failure list, 0 differences** (tests_final vs tests_base).
  Suites: MatchHeroClipMap, SwingSmoothness, TennisMotionReference, TennisGameplay, ReceivingRegression, PlayerBase,
  AnimationContactPresentation, TennisSpatialContact, TennisTimingBalance, TennisAbilities, TennisGameplayImprovement, TennisPolish,
  ControllerTimingRegression, NativeTennisSetup, NativeLaunchHero, HeroGarmentRuntimeOrder, IntroRules, TennisMatchStats, TennisReceiveCamera.
  The 15 failures are pre-existing (they fail the same way on the baseline): 4 TennisGameplayTests (also in work/frame-rate-60/README.md),
  TennisPolish x6 (3 use WaitForEndOfFrame, not run in batchmode; Milo body; late confirmation; timing check), ControllerTiming serve,
  HeroGarmentRuntimeOrder, NativeLaunchHero (ArtDir path outside the repo), NativeTennisSetup point hold, and MatchHeroClipMap: on the
  baseline it fails on the Male slice/overhead mapping, with chat 4 on the pinned 10-16 contact 0.650 (the package's test patch sets
  the approved .667; the clip-map mismatch is the same pre-existing one).
- **Two chat-4 regressions found by this pass and fixed** (BUGS.md B19, B20), both in HeroTennisInertia, both visible only when the game
  steps many times per frame (TennisTimingBalancePlayTests.SweepSwingTimesOnBothWings):
  B19 the inertia offset compounded on runtime helper bones (HeroArmSkinning ArmBlend_*) to -Infinity; B20 the blend froze at its
  frame-start weight across sub-steps, leaving the previous point's pose on the racket the hit test uses (order-dependent: 7 returns,
  needs > 8). After the fixes: sweep 14 + 14 returns in the same test order (baseline 13 + 13), PASS. Telemetry matches re-run after
  B19: pops per 300 s unchanged within match noise (male-player run: player 915 → 889, rival 1534 → 1460; female-player run: player 721 → 695, rival 2077 → 2163); the gate
  numbers above come from the films before these two fixes (B20 changes only sub-step poses inside a blend's first 0.12 s).
- Not covered: the real Unity/ now also carries other chats' unstaged edits (TennisActor, TennisRules, TennisGame.Versus, …) that these
  clones don't have; chat 6 runs the integrated suite.
