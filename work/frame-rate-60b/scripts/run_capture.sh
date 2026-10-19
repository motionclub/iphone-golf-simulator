#!/bin/zsh
# FRAME_RATE_60B captures: run_capture.sh before|after [test filter]
# Makes an APFS clone of Unity/ (before = my changes backed out to the index versions; after = with the 60 Hz files),
# then runs FrameRate60bTests windowed and MUTED (GOLF_MUTE=1 + Editor audio master mute) into proof/<mode>/.
set -e
MODE=$1; FILTER=${2:-GolfArcade.PlayTests.FrameRate60bTests}
REPO=${0:A:h:h:h:h}; W=$REPO/work/frame-rate-60b; C=/private/tmp/fps60b-$MODE-UnityClone
rm -rf $C; cp -cR $REPO/Unity $C
mkdir -p $C/Assets/Editor/FR60BLocal
print -r -- '[UnityEditor.InitializeOnLoad] static class FR60BMute { static FR60BMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/FR60BLocal/FR60BMute.cs
if [[ $MODE == before ]]; then
  for f in Assets/Scripts/Game/SignatureShot.cs Assets/Scripts/Game/FrameProbe.cs Assets/Scripts/Tennis/TennisQuality.cs; do (cd $REPO && git show :Unity/$f) > $C/$f; done
  rm -f $C/Assets/Tests/EditMode/FrameRate60bEditTests.cs*   # (it tests the new step-down / floor API)
else
  for f in $W/emotes60/fbx/*.fbx $W/readyidle60/*.fbx; do b=${f:t}; s=${b%%_*}; cp $f $f.meta $C/Assets/Characters/MatchHeroes/$s/; done
  cp $W/hole12/hole_12_cinematic.fbx $C/Assets/Resources/Course/
  cp $W/golf/out/golfer_?.fbx $W/golf/out/golfer_?_clips.json $C/Assets/Resources/Hero/
fi
mkdir -p $W/proof/$MODE
cd $C
GOLF_MUTE=1 FR60B_DIR=$W/proof/$MODE FR60B_FRAMES=1 /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -projectPath $C -runTests -testPlatform PlayMode \
  -testFilter "$FILTER" -testResults $W/logs/capture_$MODE.xml -logFile $W/logs/capture_$MODE.log
grep "\[FR60B\]" $W/logs/capture_$MODE.log
