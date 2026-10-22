#!/bin/zsh
# film.sh <label> : copies chat A's owned sources from the main checkout into ~/unity-clones/golf-flow-camera, adds the
# GolfFlowFilm harness, and films the golf flow (batch mode, muted) through heavy.sh into work/golf-flow-camera/proof/<label>.
REPO=${0:A:h:h:h:h}; W=$REPO/work/golf-flow-camera; C=$HOME/unity-clones/golf-flow-camera
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; shift
if [[ ${SYNC:-1} == 1 ]]; then
  # every script changed in the shared checkout (other chats edit GolfGame.cs too: their changes must come along to compile)
  for f in $(git -C $REPO status --porcelain -- Unity/Assets/Scripts | awk '{print $2}' | grep -E '\.cs(\.meta)?$'); do mkdir -p $C/${f:h:s/Unity\//}; cp $REPO/$f $C/${f#Unity/}; done
fi
mkdir -p $C/Assets/Editor/GFCLocal
cp $W/tools/GolfFlowFilm.cs $C/Assets/Editor/GFCLocal/
print -r -- '[UnityEditor.InitializeOnLoad] static class GFCMute { static GFCMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/GFCLocal/GFCMute.cs
mkdir -p $W/logs
env GOLF_MUTE=1 FILM_OUT=$W/proof/$label "$@" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.GolfFlowFilm.Run -logFile $W/logs/$label.log
echo "unity exit $?"
grep "\[GolfFlowFilm\]\|error CS\|Exception" $W/logs/$label.log | head -30
