# Run 28b — candidate v30; not installed

Goal remains active. Every gate must pass before runtime installation. No commit. Adnan’s eye review is still required; G12 records package readiness only.

Fresh production baseline: `before_r2_final` (16 cases). Candidate: `after_r2_v30` (same seeds, frame counts and scripted inputs). Every case has `source.json` with the actual runtime and recorder hashes. Raw 60 Hz traces preserve Refeed and all motion; only flagged opponent fixture root teleports and their derivative frame are excluded from G5. G1 includes all pre-toss frames and the first 0.2 s after first release. G5 also checks every frame with nonzero hand IK, including post-release fades.

| Gate | Result | Evidence |
|---|---|---|
| G1 | FAIL | Exact depth and vertex counts below. Actual baked skin measured; no bone/mesh modification. |
| G2 | PASS | Held-ball distance only; bounce flight, stale Refeed until rebind and release exclusions in exclusion-ranges.json. |
| G3 | PASS | RH carry visibility measured in game/front/side views. |
| G4 | FAIL | Walking elbow 15–60 degrees; wrist at/below actual pelvis-top skin marker. |
| G5 | FAIL | 3.0 cm/frame and 0.6 m/s delta caps unchanged; all failing frames retained. Player baseline-return ownership question remains pending. |
| G6 | FAIL | No-walk first-release wrist/palm/elbow <=5 mm plus identical release/contact frames; directional comparison below. |
| G7 | PASS | Final target/root/yaw/Unity frame equality measured after driver transforms. |
| G8 | PASS | Four real production SetLateralInput Play-mode captures, both directions; real-input-final.json. |
| G9 | PASS | LEFTY_GAP.md; archive LH films explicitly UNSUPPORTED and excluded from RH matrix. |
| G10 | PASS | GAME_TIMES_UNCHANGED.json; actual signed-contact transitions and protected source/assets compared. |
| G11 | PASS | Only owned Editor recorder installed; runtime candidate remains patch. Exact staging manifest and global status/stat saved. Concurrent other-chat changes preserved. |
| G12 | PASS | 12 RH half-speed paired films, six sheets including exact f547; unsupported LH examples; four real-input films. Look approval is not claimed. |

## Case measurements

Control visibility/elbow is N/A when no carry frames occur. G5 values below use the stricter entire-IK result, so phase changes are not hidden. The full JSON retains the narrower pre/toss-start scope too.

| Case | Before depth mm | After depth mm @frame | Held cm | Game/front/side % | Elbow degrees | Wrist above belt mm | Wrist step cm @frame | Delta speed m/s @frame | Failed checks |
|---|---:|---|---:|---|---|---:|---|---|---|
| opponent-female-rh-ad-control | 100.211 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 32.84–56.27 | -18.196 | 2.9834 @f86 | 0.500089 @f80 | none |
| opponent-female-rh-ad-walk | 92.901 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 19.96–55.94 | -16.925 | 2.9835 @f168 | 0.624259 @f112 | G5,G5_ALL_IK |
| opponent-female-rh-deuce-control | 104.769 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 21.98–62.07 | -17.113 | 2.9834 @f86 | 0.500089 @f80 | G4 |
| opponent-female-rh-deuce-walk | 92.901 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 19.97–55.94 | -11.984 | 2.9835 @f168 | 0.624180 @f112 | G5,G5_ALL_IK |
| opponent-male-rh-ad-control | 120.931 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 30.60–54.57 | -19.607 | 2.9835 @f106 | 0.500054 @f80 | none |
| opponent-male-rh-ad-walk | 139.344 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 18.06–55.08 | -24.939 | 2.9834 @f7 | 0.500059 @f833 | none |
| opponent-male-rh-deuce-control | 138.434 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 28.18–60.50 | -25.135 | 2.9835 @f106 | 0.500054 @f80 | G4 |
| opponent-male-rh-deuce-walk | 139.304 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 18.06–55.08 | -18.018 | 2.9834 @f5 | 0.500054 @f142 | none |
| player-female-rh-ad-control | 1.531 | 0.000000 @f0 | 3.400 | N/A/N/A/N/A | N/A | N/A | 2.9834 @f228 | 0.500070 @f345 | none |
| player-female-rh-ad-walk | 81.829 | 0.000000 @f0 | 3.400 | 98.99/100.00/100.00 | 28.57–54.89 | -17.644 | 18.8001 @f788 | 9.510801 @f789 | G5,G5_ALL_IK,G6_RIGHT_NO_WORSE |
| player-female-rh-deuce-control | 1.531 | 0.000000 @f0 | 3.400 | N/A/N/A/N/A | N/A | N/A | 2.9834 @f228 | 0.500070 @f345 | none |
| player-female-rh-deuce-walk | 81.831 | 14.437020 @f773 | 3.400 | 100.00/100.00/100.00 | 28.57–53.95 | -13.474 | 25.1632 @f788 | 13.347960 @f789 | G1,G5,G5_ALL_IK |
| player-male-rh-ad-control | 27.175 | 0.000000 @f0 | 3.400 | N/A/N/A/N/A | N/A | N/A | 2.9834 @f250 | 0.500032 @f261 | none |
| player-male-rh-ad-walk | 104.889 | 2.488048 @f768 | 3.400 | 92.62/100.00/100.00 | 29.71–54.88 | -18.320 | 20.2759 @f797 | 10.392690 @f798 | G1,G5,G5_ALL_IK |
| player-male-rh-deuce-control | 27.175 | 0.000000 @f0 | 3.400 | N/A/N/A/N/A | N/A | N/A | 2.9834 @f250 | 0.500032 @f261 | none |
| player-male-rh-deuce-walk | 105.208 | 0.000000 @f0 | 3.400 | 100.00/100.00/100.00 | 29.71–48.99 | -20.197 | 25.6017 @f798 | 13.621770 @f799 | G5,G5_ALL_IK |

## Smoothness fixes and remaining boundary

Fixed within the candidate: the false opponent reset at f350 was caused by comparing against the last active IK root instead of the preceding rendered frame; post-release opponent pops at f174–176 came from replaying the source crouch; release jumps near f476 came from the wrong release offset and insufficient deceleration; player post-release fades near f678 needed a reachable contracted endpoint. The raw traces and source snapshots preserve these experiments.

The player return after Refeed (f768 onward) still moves the root toward baseline at `dt * 4f` in `Unity/Assets/Scripts/Tennis/TennisGame.cs:1150`. This exceeds the wrist travel cap while the hand must remain anatomically reachable. The requested ownership expansion to use `ServeWalkPace` is pending. `PLAYER_DEPTH_SPEED_SCOPE_REQUEST.patch` is reviewable and unapplied; slowing this line alone may still require an owned hand transition correction at the first Refeed frame. No player Refeed frame is exempted.

## Changed files

- HeroTennisDriver.cs candidate: shared player/opponent carry/guard/outward pole; final-frame ordering; camera-side grip, physical belt marker, velocity-limited transitions and reachable post-release arm target.
- TennisServeRoutine.cs candidate: frame-current serve sample and logical held-ball state; original phase constants retained.
- TennisGame.cs candidate: opponent serve approach/readiness and shared visual reach resolution only. Player return line remains unchanged.
- ServeWalkFilm.cs installed Editor proof tool: extends run 28 with actual skin, visibility, held ranges, raw motion, frame ordering, source hashes and real production input injection.
- TennisActor.cs unchanged; no serve FBX/import, skeleton, garments, golf, multiplayer/lobby, or quality changes.

## Left-handed gap and proof

LH mapping remains unsupported. LEFTY_GAP.md identifies arm/finger mapping, sampled serve points, contact geometry and opponent configuration; estimated separate effort 200–400 lines plus a visual/timing matrix. No mirroring added.

`film_r2/manifest.json` indexes films and six sheets. `before_r2_plant547` and `after_r2_film_v30` contain the exact f547 captures. `input_r2_v30` retains all real-input images/traces. `after_r2_v30-matrix.json` contains per-case ranges and directional checks.

**Install decision: NOTHING installed into production runtime. Candidate saved as CANDIDATE_R2_GATES_FAIL.patch.**
