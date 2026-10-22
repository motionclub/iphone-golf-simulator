#!/bin/zsh
# chat G: native hero + locker tests on the G simulator from a scratch xcodegen project (same build dir as build_app.sh). -> logs/native.log
REPO=${0:A:h:h:h:h}; W=${TMPDIR:-/tmp}/menu-hero-app; UDID=$(cat $REPO/work/menu-hero/tools/sim_udid.txt); LOG=$REPO/work/menu-hero/logs/native.log
xcodebuild test -project $W/GolfArcade.xcodeproj -scheme GolfArcade -destination "platform=iOS Simulator,id=$UDID" -derivedDataPath $W/dd CODE_SIGNING_ALLOWED=NO \
  ${=ONLY:--only-testing:GolfArcadeTests/VisualOverhaulNativeTests -only-testing:GolfArcadeTests/MatchHeroLockerTests -only-testing:GolfArcadeTests/LockerMirrorTests -only-testing:GolfArcadeTests/LockerTests} > $LOG 2>&1 &
PID=$!
until grep -qE "^\*\* TEST (SUCCEEDED|FAILED|FAILED BUILD)|TEST BUILD FAILED|BUILD FAILED" $LOG 2>/dev/null || ! kill -0 $PID 2>/dev/null; do sleep 10; done
sleep 5; pkill -P $PID 2>/dev/null; kill $PID 2>/dev/null
grep -E "error:|Test Case .* failed|Executed|TEST (SUCCEEDED|FAILED)" $LOG | sort -u | tail -40
