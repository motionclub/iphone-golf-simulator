# Phase 3

| Gate | Result | Proof |
|---|---|---|
| P3.1 | PASS | P3_final.xcresult: scripted fresh-onboarding guest run saves Female/Ray and reaches connection in under 60 seconds. Test body records wall time; combined UI test took 20.899s. Existing roster API persistence unit test passes. |
| P3.2 | FAIL(BLOCKED-OWNER) | Saved body/name survive relaunch (P3_final_attachments screenshot); selected haircut Bob does not render in preview. Locked character renderer and unavailable integrated simulator prevent the required preview/match pair. NEEDS_OWNER.md. |
| P3.3 | PASS | OnboardingTests name sanitizer checks blank→Player 1, long→40 characters; P1_native.xcresult and P3_native.xcresult. |

Command: test_sim `-only-testing:GolfArcadeUITests/OnboardingUITests/testCharacterSavesInSixtySecondsAndKeepsNameAndBody -only-testing:GolfArcadeTests/OnboardingTests/testCharacterLookPersistsWithExistingRosterAPI -resultBundlePath work/onboarding/P3_final.xcresult`. 2 passed, 0 failed.
