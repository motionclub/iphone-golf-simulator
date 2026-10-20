# Phase 9

| Gate | Result | Proof / exact check |
|---|---|---|
| P9.1 | PASS | P8_P9_retry.xcresult testEverySetupStepResumesAfterProcessDeath kills/relaunches account, character, connect, primer, choose, tutorial route and reward. Seven P9_attachments snapshots. DEBUG step seeding tests persistence; does not claim real Unity completion/resume. |
| P9.2 | PASS | P9_replay.xcresult seeds a completed tennis save, verifies no onboarding guest button and normal intro Play. Seed occurs only in DEBUG UI fixture; no live lesson is completed. |
| P9.3 | PASS | P9_replay.xcresult taps normal Settings → Replay onboarding → guest → prefilled character. Unit test asserts hero save, tutorial flag, level unchanged and replay XP zero. |
| P9.4 | FAIL | Existing online/Locker paths unchanged; no UI test opens both immediately after an actual completed onboarding tutorial. |

Command: test_sim `-only-testing:GolfArcadeUITests/OnboardingUITests/testExistingSaveSkipsAndReplayKeepsHero -only-testing:GolfArcadeTests/OnboardingTests/testReplayPreservesHeroProgressAndLevel -resultBundlePath work/onboarding/P9_replay.xcresult` — 2 passed, 0 failed.
