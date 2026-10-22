# Integration 10-18 (chat 12) — GATE_RESULTS

**Status 22:25: INTEGRATED, installed in Unity/ + GolfArcade/ (unstaged, nothing committed), final phone build INSTALLED on Adnan's iPhone 17 Pro Max.**

Brief: `work/delegation-2026-10-17/12_integration_and_test.md`. Inventory and dry-runs: `INVENTORY.md`.
Combined project: `~/integration-work/Unity1`. Baseline (no pending installs): `~/integration-work/Unity2`. Both sit next to links to the repo's
`blender/`, `GolfArcade/` and `proof/`, so path-relative importers and tests behave as in the repo (see "Pitfalls").
Nothing committed. Lobby installed in GolfArcade/ (17:48, 20:07); Unity install 22:17 (252 files, 0 conflicts): rollback `python3 -I work/integration-1018/tools/install_real.py rollback` (all) or `rollback last`.

## Before integration: Adnan's requests in this chat (all built here)
| Item | Result | Proof |
|---|---|---|
| Leaving the app (AwayPolicy) | **PASS** (Editor + simulator): solo/local pause and resume, party keeps going, online tennis = CPU takes the absent player's side after 2 s and hands it back at the next point with the same score on both phones, golf turns pass after 10 s (+1 stroke), 180 s limit → out + back to the Plaza | `away/away1/takeover_sheet.jpg`, `away/away2_host/host_away_sheet.jpg`; Swift tests 170 + ClubHub 30; Unity rules 46/46 |
| Record the TV, one tap | **PASS (sim)**: bigger "Record TV" button; Control Center / Lock Screen / Action button control (iOS 18 widget extension) + Siri/Shortcuts | simulator screenshots; device NOT RUN |
| "Recordings disappear / stop randomly" | **FIXED in code**: failures no longer delete the file, one bad TV frame no longer ends a take, audio clock forward-only, Saving timeout, Recordings screen + recorder log | PartyChat/recording tests 32/32; `.mm` clang syntax check; device NOT RUN |
| Crash risk found | **FIXED**: unstaged 10-15 `SportsInfo.plist` had dropped the Game Center friends usage text (TCC kill on `loadFriends`) | |

## Per piece
| Piece | Status | Notes |
|---|---|---|
| 60 fps (frame-rate-60b) | INTEGRATED | in tree; RuntimeHoldsSixty below |
| Rendered skies | INTEGRATED | in tree (6 hooks "already patched") |
| Tennis anim integrity (14 strokes 60 Hz + contact times) | INTEGRATED | installed via `tools/tennis_install.sh`; test table patched by hand (path depth) |
| Hand clearance (bake-first) | INTEGRATED, re-baked | tennis tracks re-baked for chat 4's strokes (43 + 43); male re-bake for round-9 garments + 4-context sweep: PENDING |
| Garments: female tennis top + skirt K12_FT | INTEGRATED | + HeroShoulderDeformation `[gp]` skip (REQUESTS); driver 0.081 ms; mesh == chat 5's clone (bounds padding only) |
| Male garments + shoes round 9 (tennis polo + shorts = K7_MT fit) | INTEGRATED | 87 files + r9 prefab patch (+ chat 4 slot times kept) + shoe trim patch |
| Female + male face/shader, male caps | INTEGRATED | in tree |
| Character LOD | INTEGRATED | 4 new tests pass; cache re-bake after the last garment: second pass |
| Majestic layer (6 places) | INTEGRATED | in tree, 12/12 hashes |
| Majestic all maps + landmark kit | INTEGRATED | `install_majestic.sh`: 76 added, 5 patched; coast tiles off by default (coordinator fix) |
| Weather | INTEGRATED | shared patch 8/8; halo removed + ember comet + softer gusts (REQUESTS "FINAL BUILD") |
| Lobby re-sync | INTEGRATED + INSTALLED in GolfArcade/ | parity MAD tennis M 6.0 / F 7.0, golf M 7.2 / F 7.6 (10-13: 6.1 / 6.8 / 7.2 / 8.5) |
| VFX + sound research | NOT INTEGRATED (on hold, Adnan) | |

## Tests (combined vs baseline)
| Suite | Baseline | Combined | Different |
|---|---|---|---|
| EditMode | 607/608 (fixture path) | **617/617 final** (612 before the second pass) | + LOD, golf pace and track-fingerprint tests; no failure |
| PlayMode (241/242 tests) | 145 pass, 43 fail, 51 skip | 144 pass, 44 fail, 52 skip | 1 NEW: `HubPartyTests.FourHeroesStaySmoothAndFriendsAreDrawnWhereTheyWere`: 50.8 fps vs its 55 floor (Editor, run while 4 heavy jobs ran; baseline passed on a quieter host). Re-run on a quiet Mac: follow-up. 0 fixed, 45 identical failures (pre-existing) |
| Golf swing chat's suites (combined + swing fix) | | 18/19 | the 1 failure (`HeroGolferTests.EveryLookBuilds`) fails the same on the baseline |
| Swift (sim) | | Multiplayer 91, ClubHub 30, Hub/Party, PartyChat 32: all pass; VisualOverhaulNative: freshness PASS, blink contract FAIL (pre-existing, same bones/shapes before) | |

## Key checks on the combined project
| Check | Result |
|---|---|
| Smoke playthrough (tennis serve + rally, golf, plaza walk + emote) | PASS: 0 errors, 0 exceptions (`smoke/smoke_playthrough.mp4`, `smoke/smoke_sheet.jpg`). Golf segment landed on hole 1 without rain (test bug, fixed: re-film in the second pass) |
| 60 fps at 1920×1080 (Editor, RuntimeHoldsSixty, host loaded with 3 Unity + Blender) | median fps: tennis intro 62.5, match 60.5, golf intro 59.7, golf hole **57.9**, plaza 59.8; p05 36–54 (chat 1, quiet host: 49–59). Device NOT RUN |
| Majestic budget (443 views) | median 0.860 M tris (chat 10 r37: 0.889), >1 M views 175 (192), worst tee 3.53 M (5.38): character LOD helps; tee views still over 1 M |
| Weather gates (W01/W03/W09/X16) | corridor + fog PASS; ball contrast W03 3.63 PASS, W01 2.51 / W09 2.84 / X16 2.72 FAIL vs 3:1 — the halo Adnan had removed was what lifted it (round 3: 5–11:1); still ~2× pre-weather. Tennis W12/W14: second pass |
| Clearance bake + gate (chat 3 staged v1, HCT3 fingerprints; golf on Unity3, tennis on Unity4, one launch each) | BODY fail frames 586 (round 3: 526), CLOTH 1,078 (800, now against tonight's new garments), CONTACT drift max 0.23 mm PASS, flips 18 (14), pops 281 (247), solver 0.027 ms mean / 0.12 ms p95 PASS. Per context: golf F body 615→214 cloth 1283→334, golf M 1044→107 / 1589→166, tennis F 673→126 / 2133→393, tennis M 1049→139 / 2520→185. `clearance_golf/`, `clearance_tennis/` |
| Garment stress suite | Not re-run here: the installed garment assets are byte-identical to chat 5's / male-garments' suite inputs (K12_FT 60,667 tears; male round 9 per its GATE_RESULTS) |

## Pitfalls found
- A Unity clone outside `<repo>/Unity` imports `StandardCharacters/standard_*_tennis.fbx` with NO clips (GolferModelImporter reads `../../blender/tennis-clips.json`) and fails two tests that look for `../GolfArcade`, `../proof`. Fix: put clones next to links to those folders.
- Lobby sheets must be rendered after `compress_maps.py` (the SceneKit garment shader samples the `.ktx`), or new garments show old maps.
- `HeroClearanceBake.Corrected` on lobby clips lifted the racket in front of the face (parity 16–25): now opt-in `LOBBY_CLEARANCE=1`.

## Decisions and follow-ups (10-18 evening)
- **Hand clearance:** chat 3's staged gate v1 is in the combined bake (truth-gated body step). It fixes the first-drive "body angled" posture: UpperChest yaw at address 79.5° = clearance-off (round 3: 72.9°). Cost: tennis_male body+cloth fail frames 262 → 327 (v2 rejected at 369). Follow-up: a mixed gate (real-mesh gate only in long locked windows, the old body step in tennis contact).
- **Lobby clearance:** `LOBBY_CLEARANCE=1` stays off until the lobby parity is re-checked on the fresh HCT3 tracks (chat 3's diagnosis: the stale tracks on chat 4's re-keyed clips gave the old corrections).
- **Garments:** tear work paused by Adnan. Golf female ships today's top unchanged (206k tears beat R4's 427k). The male tennis polo + shorts ship the K7_MT fit (male-garments round 9). The male polo K8 is available (polo tears 136.8k vs 139.3k, shorts through the polo 1.7k vs 8.4k): `tools/tennis_polo.sh K8_MT` + prefab patch + lobby sync, needs Adnan's OK.
- **Weather:** tennis-ball gold ring for rain approved by Adnan and in the build (W12 ball read stays ~1.6 at the luminance ceiling, separated by colour; W14 4.64).
- **golfer.look.v1** is an Editor PlayerPrefs key (~/Library/Preferences/unity.aloniewski.Golf Arcade.plist), shared by every Editor on the Mac and flipped by golf films. Not part of the install or the phone. It currently reads Body 1.
- **Device NOT RUN:** away rules, recording fixes, Control Center control, 60 fps, AirPlay.

## Phone build (final)
- From `~/integration-work/phone/root`, an APFS copy of the final combined state (= `Unity/` after the 22:17 install) + repo `GolfArcade/` with both lobby syncs + `MotionClubControls` + the `blender` link (the standard tennis rig keeps its 60 clip names).
- Export `BuildMenu.BuildIOS` 93 s, 0 errors. xcodebuild Release **BUILD SUCCEEDED** (`com.aloniewski.GolfArcade` + `.controls` extension, Game Center friends usage text present).
- Installed on the iPhone 17 Pro Max (devicectl) 22:2x. Launch was refused only because the phone was locked.
- On-device checks NOT RUN yet: away rules, recording/Recordings/log, Record TV control, AirPlay, 60 fps on device.

## Follow-ups (one list)
1. Device pass of tonight's app changes (away rules, recorder, Control Center control) + read `Documents/Recordings/recorder-log.txt` after the first recording.
2. `HubPartyTests` four-heroes fps 50.8 vs 55: re-run on a quiet Mac (host was loaded).
3. Lobby clearance: re-check parity with `LOBBY_CLEARANCE=1` on the fresh HCT3 tracks; on if it holds MAD 6–7.
4. Hand clearance mixed gate (chat 3): win back tennis_male 327 vs 262 fail frames without losing the golf posture fix.
5. Male polo K8 (needs Adnan's OK); garment tear work paused by Adnan (golf female sleeve).
6. Weather ball contrast in rain without the halo (golf 2.5–2.8:1, tennis W12 ~1.6:1 with the gold ring).
7. Majestic tee views still over 1 M tris (worst 3.5 M).
8. Character LOD cache not re-baked after the final garments (runtime worker-thread compute meanwhile; correct look).
9. Disk: `~/integration-work` (Unity1–4, sync clone, phone root + DerivedData) and the other chats' `~/*-UnityClone` can be deleted once Adnan is happy with the build.

## Staging (22:35, nothing committed)
- **Staged by explicit path (271):** every installed file whose pre-install copy equalled the index (246, `logs/stage_clean.txt`), plus this chat's own clean edits (away rules, recorder, Record TV control + extension, tests, tools, this report).
- **Left UNSTAGED on purpose (other chats' unstaged work in the same file):**
  - 137 installed files (`logs/stage_mixed.txt`): lobby CharacterAssets/goldens, the 10-16 MatchHeroes stroke FBX, and the hero prefabs carrying male-garments' unstaged patches.
  - My edits inside `MultiplayerModels.swift`, `MultiplayerTests.swift`, `TennisGame.Versus.cs`, `TennisHud.cs`, `SportsInfo.plist` (restored friends + local-network usage texts) and `project.yml` (APP_BUNDLE_ID + controls target). Each of these already had another chat's 10-14/15 unstaged edits.
- A commit therefore needs Adnan's call on those unstaged files (stage them as they are, or review them first).
