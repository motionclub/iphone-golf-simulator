#!/bin/zsh
# ONBOARDING: build the working tree in a scratch xcodegen project and run the onboarding tests on this chat's own simulator
# (loading-action-snap, an iPhone 17 Pro). Snapshots land in work/loading-action-1113/snap. A hung `xcodebuild test` is killed after its verdict.
#   ONLY="-only-testing:GolfArcadeTests/HubSessionTests/testLoadingShotSnapshots" work/loading-action-1113/native_tests.sh
set -e
REPO=${0:A:h:h:h}; W=${LA_WORK:-$HOME/loading-action-native}; LOG=$REPO/work/loading-action-1113/logs/native.log
mkdir -p $W $REPO/work/loading-action-1113/logs $REPO/work/loading-action-1113/snap
SIM=$(xcrun simctl list devices | grep -m1 "loading-action-snap (" | sed -E 's/.*\(([0-9A-F-]{36})\).*/\1/')
if [[ -z $SIM ]]; then SIM=$(xcrun simctl create loading-action-snap "iPhone 17 Pro"); fi
xcrun simctl boot $SIM 2>/dev/null || true
sed -e "s#CODE_SIGN_ENTITLEMENTS: GolfArcade#CODE_SIGN_ENTITLEMENTS: $REPO/GolfArcade#" -e "s#INFOPLIST_FILE: GolfArcade#INFOPLIST_FILE: $REPO/GolfArcade#" -e "s#SWIFT_OBJC_BRIDGING_HEADER: GolfArcade#SWIFT_OBJC_BRIDGING_HEADER: $REPO/GolfArcade#" -e "s#: MotionClubControls/#: $REPO/MotionClubControls/#g" $REPO/project.yml > $W/project.yml
xcodegen generate --spec $W/project.yml --project-root $REPO --project $W > $W/xcodegen.log 2>&1
( TEST_RUNNER_MENU_SNAP_DIR=$REPO/work/loading-action-1113/snap xcodebuild test -project $W/GolfArcade.xcodeproj -scheme GolfArcade -destination "platform=iOS Simulator,id=$SIM" -derivedDataPath $W/dd \
   ${=ONLY:--only-testing:GolfArcadeTests/HubSessionTests} \
   CODE_SIGNING_ALLOWED=NO > $LOG 2>&1 ) &
PID=$!
until grep -qE "^\*\* TEST (SUCCEEDED|FAILED) \*\*|BUILD FAILED" $LOG 2>/dev/null || ! kill -0 $PID 2>/dev/null; do sleep 10; done
sleep 5; pkill -P $PID 2>/dev/null || true; kill $PID 2>/dev/null || true
grep -E "error:|Test Case .* (failed|passed)|Executed|TEST (SUCCEEDED|FAILED)|BUILD FAILED" $LOG | grep -E "error:|failed|Executed|TEST|BUILD" | sort -u | tail -40
