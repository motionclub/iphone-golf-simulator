#!/bin/zsh
# film.sh <label> [fresh] [ENV=val ...] : GolfSwingSpeedFilm in ~/golf-swing-speed-UnityClone through heavy.sh, muted.
#   fresh = re-clone Unity/ from the working tree first (cp -c, APFS). Overlay files: OVERLAY_DIR=<dir with Assets/...> copied over the clone.
REPO=${0:A:h:h:h:h}; W=$REPO/work/golf-swing-speed; C=$HOME/golf-swing-speed-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; shift
if [[ ${1:-} == fresh ]]; then shift; rm -rf $C; cp -cR $REPO/Unity $C; fi
mkdir -p $C/Assets/Editor/GSSLocal
cp $W/scripts/GolfSwingSpeedFilm.cs $C/Assets/Editor/GSSLocal/
rm -rf $C/Assets/GSSLocalRuntime $C/Assets/GSSLocalRuntime.meta; mkdir -p $C/Assets/Scripts/GSSLocal; cp $W/scripts/GSSPhoneFeed.cs $C/Assets/Scripts/GSSLocal/
[[ -n ${OVERLAY_DIR:-} ]] && rsync -a $OVERLAY_DIR/ $C/
print -r -- '[UnityEditor.InitializeOnLoad] static class GSSMute { static GSSMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/GSSLocal/GSSMute.cs
mkdir -p $W/logs
env GOLF_MUTE=1 GSS_OUT=${GSS_OUT:-$HOME/golf-swing-speed-frames/$label} "$@" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.GolfSwingSpeedFilm.Run -logFile $W/logs/$label.log
echo "unity exit $?"
grep "\[GSSFilm\]\|error CS" $W/logs/$label.log | tail -20
