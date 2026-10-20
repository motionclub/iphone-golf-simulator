# P1 foundation
P1.1 PASS — P1_native.log / P1_native.xcresult. OnboardingTests: 6 passed; fresh account, either existing tutorial skip, persistence, ftue-only reset, legacy flags, all persisted steps, stable guest/name constraints.
P1.2 PASS — same proof. AnalyticsTests: 2 passed; actual single SportsDiagnostics log line plus props/time, monotonic time, 200-event bound and escaped values.
P1.3 FAIL(BLOCKED-OWNER): original-build SportsNavigationTests already fails at its obsolete Form assertion (P0_navigation_retry.xcresult); its owner must update the test. Full native baseline still running; regression comparison remains required in P10. No account UI is implemented in this phase.
Final comparison: P10_native_summary.json confirms the same eight existing native failures and same one navigation failure; no new existing native test fails. Navigation still cannot meet this gate's “still pass” requirement.
Generated isolated project using xcodegen --spec project.yml --project work/onboarding/native; no shared generated project changed. Absolute header/plist/entitlement overrides supply original build inputs. Dedicated fresh Simulator 03AEFA81-ACF7-4EDD-AE9C-842E8E90B902.
