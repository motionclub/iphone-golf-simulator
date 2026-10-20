#!/bin/zsh
# snap.sh <name> : screenshot the review simulator into stills/menu/<name>.png
REPO=${0:A:h:h:h:h}; UDID=$(cat $REPO/work/review-capture-1019/tools/sim_udid.txt)
xcrun simctl io $UDID screenshot $REPO/work/review-capture-1019/stills/menu/$1.png >/dev/null 2>&1 && echo $1
