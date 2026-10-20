#!/bin/zsh
# usage: scripts/unity_stage.sh <label> <Class.Method> [nographics|graphics]   one Unity batch run behind the shared heavy.sh lock (never overlaps xcodebuild / another Unity)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/e6a7ae79-f7d7-42dd-b152-50de544740e5/scratchpad
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; method=$2; mode=${3:-nographics}
flags=(-batchmode)
# edit-mode tools quit themselves (-quit); the play-mode proof ends with EditorApplication.Exit
[[ $mode == nographics ]] && flags+=(-nographics -quit)
cd $R
$S/heavy.sh "dress-$label" $U $flags -projectPath Unity -logFile work/hero-dressed/logs/unity_$label.log -executeMethod GolfArcade.EditorTools.$method
echo "unity $label exit $?"
