# Phase 8

| Gate | Result | Proof / exact check |
|---|---|---|
| P8.1 | PASS | P8_P9_retry.xcresult testFirstTutorialFillsLevelTwoAndReplayPaysNothing: partial existing XP tops up exactly to L2; reward_claimed once; same sport replay zero; other sport +50 once. |
| P8.2 | FAIL | Unit test proves finish routes to chosen sport hub; no screenshot after an actual completed tutorial. Seeded reward-step screenshot is resume proof only. |
| P8.3 | FAIL(BLOCKED-OWNER) | Persisted white-headband reward and requested equip path exist; public Player/catalog/renderer APIs cannot equip it. Native reward screen does not falsely claim a worn headband. NEEDS_OWNER.md. |
| P8.4 | FAIL | Other-sport first selection routes directly to tutorial and unit reward logic grants +50; required full tutorial → reward → hub proof missing. |

Command: test_sim `-only-testing:GolfArcadeTests/OnboardingTests -only-testing:GolfArcadeTests/AnalyticsTests -only-testing:GolfArcadeUITests/OnboardingUITests -resultBundlePath work/onboarding/P8_P9_retry.xcresult`. 17 passed, 1 failing UI selector subsequently corrected and passed in P9_replay.xcresult.
