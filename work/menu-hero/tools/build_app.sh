#!/bin/zsh
# chat G: build the phone app (no Unity) for the G simulator from a scratch xcodegen project; never touches GolfArcade.xcodeproj.
set -e
REPO=${0:A:h:h:h:h}; W=${TMPDIR:-/tmp}/menu-hero-app; UDID=$(cat $REPO/work/menu-hero/tools/sim_udid.txt); LOG=$REPO/work/menu-hero/logs/build_${1:-app}.log
mkdir -p $W
sed -e "s#CODE_SIGN_ENTITLEMENTS: GolfArcade#CODE_SIGN_ENTITLEMENTS: $REPO/GolfArcade#" -e "s#INFOPLIST_FILE: GolfArcade#INFOPLIST_FILE: $REPO/GolfArcade#" -e "s#SWIFT_OBJC_BRIDGING_HEADER: GolfArcade#SWIFT_OBJC_BRIDGING_HEADER: $REPO/GolfArcade#" -e "s#INFOPLIST_FILE: MotionClubControls#INFOPLIST_FILE: $REPO/MotionClubControls#" $REPO/project.yml > $W/project.yml
xcodegen generate --spec $W/project.yml --project-root $REPO --project $W > $W/xcodegen.log 2>&1
xcodebuild build -project $W/GolfArcade.xcodeproj -scheme GolfArcade -destination "platform=iOS Simulator,id=$UDID" -derivedDataPath $W/dd CODE_SIGNING_ALLOWED=NO > $LOG 2>&1 || { tail -30 $LOG; grep -E "error:" $LOG | head -20; exit 1; }
APP=$(find $W/dd/Build/Products -maxdepth 2 -name "*.app" | head -1); echo "$APP"
