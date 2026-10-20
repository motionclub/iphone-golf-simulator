#!/bin/zsh
# usage: scripts/xcode_stage.sh <label> <build|test> [-only-testing:... ...]   one xcodebuild behind the shared heavy.sh lock
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/e6a7ae79-f7d7-42dd-b152-50de544740e5/scratchpad
label=$1; action=$2; shift 2
cd $R
$S/heavy.sh "dress-xcode-$label" xcodebuild $action -project GolfArcade.xcodeproj -scheme GolfArcade -destination 'id=88A5F840-AF09-4E3F-AF23-089D85AF4F25' "$@" > work/hero-dressed/logs/xcode_$label.log 2>&1
echo "xcode $label exit $?"
