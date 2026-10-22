#!/bin/zsh
# review-1019 (copy of chat G shoot.sh): install the built app on the G simulator, launch with args, wait, screenshot.  shoot.sh <out.png> <wait s> [launch args...]
REPO=${0:A:h:h:h:h}; UDID=$(cat $REPO/work/review-capture-1019/tools/sim_udid.txt); APP=${TMPDIR:-/tmp}/review-1019-app/dd/Build/Products/Debug-iphonesimulator/GolfArcade.app
OUT=$1; WAIT=$2; shift 2
BID=$(/usr/libexec/PlistBuddy -c "Print CFBundleIdentifier" $APP/Info.plist)
[[ -n $NOINSTALL ]] || xcrun simctl install $UDID $APP
xcrun simctl terminate $UDID $BID 2>/dev/null
xcrun simctl launch $UDID $BID "$@" >/dev/null
sleep $WAIT
xcrun simctl io $UDID screenshot $OUT >/dev/null 2>&1 && echo $OUT
