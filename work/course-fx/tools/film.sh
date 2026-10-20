#!/bin/zsh
# film.sh <mode> [label] : syncs every changed script/test from the main checkout into ~/unity-clones/course-fx, then
#   mode tests -> runs the EditMode suites this chat touches (results in work/course-fx/logs/tests.xml)
#   mode film  -> runs the CourseFxFilm harness (rock audit + captures) into work/course-fx/proof/<label>
# Every Unity launch goes through heavy.sh, batch mode, muted.
REPO=${0:A:h:h:h:h}; W=$REPO/work/course-fx; C=$HOME/unity-clones/course-fx
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mode=$1; label=${2:-run}
for f in $(git -C $REPO status --porcelain --untracked-files=all -- Unity/Assets/Scripts Unity/Assets/Tests Unity/Assets/Editor | awk '{print $NF}' | grep -E '\.cs$'); do
  [[ " ${=SKIP:-GolfGame.Mannerisms.cs} " == *" ${f:t} "* ]] && { rm -f $C/${f#Unity/}; continue; }   # other chats' half-written files
  mkdir -p $C/${${f#Unity/}:h}; cp $REPO/$f $C/${f#Unity/}
done
# clone-only stand-ins for hooks into other chats' unfinished files (never copied back)
grep -q "HookMannerisms" $REPO/Unity/Assets/Scripts/Game/GolfGame.cs && [[ ! -f $C/Assets/Scripts/Game/GolfGame.Mannerisms.cs ]] && \
  print -r -- 'namespace GolfArcade.Game { public partial class GolfGame { void HookMannerisms() { } } }' > $C/Assets/Scripts/Game/CFXStubMannerisms.cs
mkdir -p $C/Assets/Editor/CFXLocal $W/logs
cp $W/tools/CourseFxFilm.cs $C/Assets/Editor/CFXLocal/
print -r -- '[UnityEditor.InitializeOnLoad] static class CFXMute { static CFXMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/CFXLocal/CFXMute.cs
if [[ $mode == tests ]]; then
  env GOLF_MUTE=1 $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -runTests -testPlatform EditMode \
    -testFilter "GolfArcade.Tests.ObstacleTests|GolfArcade.Tests.RoundEventsTests|GolfArcade.Tests.DreamIntegrationTests|GolfArcade.Tests.ChallengeTests" \
    -testResults $W/logs/tests.xml -logFile $W/logs/tests.log
  echo "unity exit $?"
  grep -o 'testcasecount="[0-9]*" result="[A-Za-z()]*" total="[0-9]*" passed="[0-9]*" failed="[0-9]*"' $W/logs/tests.xml | head -1
  grep -B1 -A6 'result="Failed"' $W/logs/tests.xml | grep -E 'name=|message' | head -40
  grep "error CS" $W/logs/tests.log | sort -u | head -20
else
  env GOLF_MUTE=1 FILM_OUT=$W/proof/$label $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.CourseFxFilm.Run -logFile $W/logs/$label.log
  echo "unity exit $?"
  grep "\[CourseFxFilm\]\|error CS\|Exception" $W/logs/$label.log | head -60
fi
