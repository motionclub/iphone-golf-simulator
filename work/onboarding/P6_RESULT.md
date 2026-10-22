# Phase 6

| Gate | Result | Proof / exact check |
|---|---|---|
| P6.1 | PASS | P6_editmode.xml: new order, all goals one, Skip exactly one, index-two resume. Full EditMode 257/257. |
| P6.2 | FAIL | P6_PlayMode_final/playmode.log first actual contact 5.686 seconds without steering; required physical-device recording missing. Full lesson later fails at Aim. |
| P6.3 | FAIL(BLOCKED-OWNER) | Owned TennisRacketController hides both sliders at steps 0–1 and fixes power .7; actual forehand contact without steering is logged. Locked SportsDisplays preview still installs a separate slider overlay, so the requested on-phone snapshot cannot pass. |
| P6.4 | FAIL(BLOCKED-OWNER) | No completed motion/TV walkthrough. Real full-lesson PlayMode test fails at Aim; owners of gameplay/rig are required. |
| P6.5 | FAIL | Store unit test resumes index 2 and bridge reads tutorialStart; no actual resumedAt=2 runtime/video proof. |
| P6.6 | FAIL(BLOCKED-OWNER) | P6_Points/playmode.log: all ten seeded attempts recorded, zero wins; genuine no-swing attempt stays unfinished after 90 simulated seconds. |

Commands: `OUT=../work/onboarding/P6_PlayMode_final zsh Unity/Tools/run-playmode-windowed.sh TennisTutorialPlayTests` (0/4); `OUT=../work/onboarding/P6_Points zsh Unity/Tools/run-playmode-windowed.sh TennisTutorialPlayTests.TenSeededPoints` (0/1). Tests use public swings and real physics; no success events were fabricated. The failing on-time harness also needs serve-owner review before attributing all failures to production physics.
