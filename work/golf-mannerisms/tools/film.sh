#!/bin/zsh
# film.sh <label> [Male|Female] : syncs every changed script from the main checkout into ~/unity-clones/golf-mannerisms, adds the
# GolfMannerismFilm harness and films address/drive/hole-outs (batch mode, muted) through heavy.sh into work/golf-mannerisms/proof/<label>.
REPO=${0:A:h:h:h:h}; W=$REPO/work/golf-mannerisms; C=$HOME/unity-clones/golf-mannerisms
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; sex=${2:-Male}
# Other wave-2 chats (C, E, G) are editing shared scripts mid-way, so the main checkout's Scripts don't always compile. The clone's
# Scripts are chat A's last filmed (compiling) snapshot, plus this chat's own files and chat F's finished male face/garment files.
A=$HOME/unity-clones/golf-flow-camera/Assets/Scripts
if [[ ${SYNC:-1} == 1 ]]; then
  rsync -a --delete $A/ $C/Assets/Scripts/
  for f in Scripts/Game/GolferView.cs Scripts/Game/GolfGame.HoleOut.cs Scripts/Game/GolferFootwork.cs Scripts/Game/GolfGame.Mannerisms.cs Scripts/Game/GolfGame.Mannerisms.cs.meta \
           Scripts/Tennis/MaleFaceFinish.cs Scripts/Tennis/HeroFaceReferenceFit.cs Characters/KitsV2/GolfKitHero_Male/Kit_Top.asset Resources/Golf/KitsV2/Male/KitV2_Golf_Male_Bottom_hide.bytes; do
    [[ -f $REPO/Unity/Assets/$f ]] && cp $REPO/Unity/Assets/$f $C/Assets/$f
  done
  # the one-line hook in GolfGame.Awake (main checkout) applied to the snapshot's GolfGame.cs
  grep -q "HookMannerisms();" $REPO/Unity/Assets/Scripts/Game/GolfGame.cs && ! grep -q "HookMannerisms();" $C/Assets/Scripts/Game/GolfGame.cs && \
    python3 -c "import sys;p=sys.argv[1];s=open(p).read();i=s.index('void Awake()');j=s.index('{',i)+1;open(p,'w').write(s[:j]+'\n            HookMannerisms();   // chat B: post-shot watch, waggle, hole-out clean-up (GolfGame.Mannerisms.cs)'+s[j:])" $C/Assets/Scripts/Game/GolfGame.cs
fi
mkdir -p $C/Assets/Editor/GMLocal
cp $W/tools/GolfMannerismFilm.cs $C/Assets/Editor/GMLocal/
print -r -- '[UnityEditor.InitializeOnLoad] static class GMMute { static GMMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/GMLocal/GMMute.cs
env GOLF_MUTE=1 FILM_SEX=$sex FILM_OUT=$W/proof/$label $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.GolfMannerismFilm.Run -logFile $W/logs/$label.log
echo "unity exit $?"
grep "\[GolfMannerismFilm\]\|error CS\|Exception" $W/logs/$label.log | head -30
