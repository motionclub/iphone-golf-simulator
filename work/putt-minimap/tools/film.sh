#!/bin/zsh
# film.sh <label> : mirrors the working tree's Unity/Assets into ~/unity-clones/hold-swing-putt (whole tree, all 10/19 work),
# adds the PuttMarksFilm harness (tee still, then putts at 0/30/55/85 % and a rolling putt), and films batch-mode, muted,
# through heavy.sh into work/putt-minimap/proof/<label>.
REPO=${0:A:h:h:h:h}; W=$REPO/work/putt-minimap; C=$HOME/unity-clones/hold-swing-putt
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; shift
rsync -a --delete --exclude 'Editor/HSPLocal/' --exclude 'Editor/HSPLocal.meta' $REPO/Unity/Assets/ $C/Assets/
rsync -a $REPO/Unity/Packages/ $C/Packages/
mkdir -p $C/Assets/Editor/HSPLocal; rm -f $C/Assets/Editor/HSPLocal/*.cs
cp $W/tools/PuttMarksFilm.cs $C/Assets/Editor/HSPLocal/
print -r -- '[UnityEditor.InitializeOnLoad] static class HSPMute { static HSPMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/HSPLocal/HSPMute.cs
rm -f $C/Temp/UnityLockfile
env GOLF_MUTE=1 FILM_OUT=$W/proof/$label "$@" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.PuttMarksFilm.Run -logFile $W/logs/$label.log
echo "unity exit $?"; grep "\[PuttMarksFilm\]\|error CS\|Exception" $W/logs/$label.log | sort -u | head -30
