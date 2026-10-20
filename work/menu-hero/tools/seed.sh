#!/bin/zsh
# chat G: seed the G simulator's profile: seed.sh <tennis|golf> [backCarry]
REPO=${0:A:h:h:h:h}; UDID=$(cat $REPO/work/menu-hero/tools/sim_udid.txt); BID=com.adnanandrew.motionsports
ID=6A1F3C2E-0000-4000-8000-00000000000G; ID=${ID%G}1
CARRY=${2:+,\"backCarryValue\":\"$2\"}
JSON="[{\"id\":\"$ID\",\"name\":\"Player 1\",\"colorIndex\":0,\"handedness\":\"right\",\"shirt\":2,\"shorts\":5$CARRY}]"
HEX=$(printf '%s' "$JSON" | xxd -p | tr -d '\n')
xcrun simctl terminate $UDID $BID 2>/dev/null
xcrun simctl spawn $UDID defaults write $BID players.v1 -data $HEX
xcrun simctl spawn $UDID defaults write $BID sports.lastSport.$ID $1
