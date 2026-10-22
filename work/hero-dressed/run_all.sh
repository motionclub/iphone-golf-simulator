#!/bin/zsh
# DRESS_MATCH_HEROES - rebuild and re-prove everything (~25 minutes, most of it Unity import + xcodebuild).
#   cd work/hero-dressed && ./run_all.sh
# Prerequisites: the staged inputs are untouched (hashes in baseline/source_blends_sha256.txt) and the Unity project is not open elsewhere. Every Unity batch run and every xcodebuild goes through the
# shared lock heavy.sh (scripts/unity_stage.sh, scripts/xcode_stage.sh): they never overlap each other (Burst SIGSEGV) and wait while another session has Unity / xcodebuild running.
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed
cd $W
# 1. Blender (headless, ~2 min): kit -> hero rig skinning, gate 1 / 3 / 8 measurements, kit FBXs, FBX round trip, Blender proof sheets
./scripts/blender_stage.sh
# 2. Unity (edit mode): import the kit FBX, rebuild PlayerMale / PlayerFemale (hash guard on the 32 clip FBXs), run the Unity checks, fingerprint, regenerate the Swift mirror assets
./scripts/unity_chain.sh
python3 scripts/compare_fp.py
python3 scripts/verify_repo.py
# 3. Swift: project (new test file), the snapshot / maths / mirror tests, and the plain app build
(cd ../.. && xcodegen generate --spec project.yml)
./scripts/xcode_stage.sh dressed test -only-testing:GolfArcadeTests/DressedHeroSnapshotTests -only-testing:GolfArcadeTests/MatchHeroLockerTests
./scripts/xcode_stage.sh build build
# 4. Unity play-mode proof (locker, pixel test, campaign, rally) - graphics batch mode
./scripts/unity_stage.sh proof MatchHeroKitProof.Run graphics
# 5. roll-up -> checks.json (GATE_RESULTS.md is written by hand from it)
python3 scripts/final_report.py
