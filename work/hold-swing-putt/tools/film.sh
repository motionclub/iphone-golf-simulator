#!/bin/zsh
# film.sh <label> : builds ~/unity-clones/hold-swing-putt's scripts as HEAD + an allowlist (wave-1's finished files A/D/F/I
# + chat C's), takes the wave-2 siblings' hooks back out of GolfGame.cs, adds the PuttMarksFilm harness, and films a putt
# (batch mode, muted) through heavy.sh into work/hold-swing-putt/proof/<label>. EXEC=<method> runs another entry point.
REPO=${0:A:h:h:h:h}; W=$REPO/work/hold-swing-putt; C=$HOME/unity-clones/hold-swing-putt
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
label=$1; shift
ALLOW=(Game/GolfGame.cs Game/GolfGame.Native.cs Game/GolfGame.PuttMarks.cs Game/PuttDistanceMarks.cs Game/NativeSportsSession.cs
  Multiplayer/SportsMultiplayer.cs UI/ControllerSheet.cs UI/Hud.cs
  Game/GolfGame.Presentation.cs Game/GolfGame.Results.cs Game/GolfGame.HoleOut.cs Game/GolfGame.Broadcast.cs Game/CameraRig.cs Game/GolferFade.cs UI/ShotResultPanel.cs
  Game/GameAudio.cs Game/GameMusic.cs Game/GolfSounds.cs Game/EventSounds.cs Game/PresentationStinger.cs
  Tennis/TennisSounds.cs Tennis/TennisAnnouncer.cs Tennis/TennisAmbience.cs Tennis/TennisAudioDirector.cs Tennis/MaleFaceFinish.cs Tennis/HeroFaceReferenceFit.cs)
# NO_F=1: chat F's male face files at HEAD (its invariant error log fails any PlayMode test that loads a hero)
[[ $NO_F == 1 ]] && ALLOW=(${ALLOW:#Tennis/MaleFaceFinish.cs}) && ALLOW=(${ALLOW:#Tennis/HeroFaceReferenceFit.cs})
for f in $(git -C $REPO status --porcelain -uall -- Unity/Assets/Scripts Unity/Assets/Tests | awk '{print $1":"$2}'); do
  st=${f%%:*}; p=${f#*:}; rel=${p#Unity/Assets/Scripts/}; dst=$C/${p#Unity/}
  if (( ${ALLOW[(Ie)${rel%.meta}]} )) || [[ $p == */GolfMotionReadyTests.cs ]]; then mkdir -p ${dst:h}; cp $REPO/$p $dst
  elif [[ $st == '??' ]]; then rm -f $dst
  else git -C $REPO show HEAD:$p > $dst; fi
done
python3 $W/tools/unpatch_e.py $C/Assets/Scripts/Game/GolfGame.cs
mkdir -p $C/Assets/Editor/HSPLocal
cp $W/tools/PuttMarksFilm.cs $C/Assets/Editor/HSPLocal/
print -r -- '[UnityEditor.InitializeOnLoad] static class HSPMute { static HSPMute() { UnityEditor.EditorUtility.audioMasterMute = true; UnityEditor.EditorApplication.playModeStateChanged += _ => UnityEditor.EditorUtility.audioMasterMute = true; } }' > $C/Assets/Editor/HSPLocal/HSPMute.cs
rm -f $C/Temp/UnityLockfile
if [[ -n $TESTS ]]; then
  env GOLF_MUTE=1 $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -runTests -testPlatform PlayMode -testFilter "$TESTS" -testResults $W/logs/$label.xml -logFile $W/logs/$label.log
  echo "unity exit $?"; grep -o 'result="[A-Za-z]*"[^>]*name="[A-Za-z]*"' $W/logs/$label.xml | head -20; grep "error CS" $W/logs/$label.log | sort -u | head
else
  env GOLF_MUTE=1 FILM_OUT=$W/proof/$label "$@" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.PuttMarksFilm.Run -logFile $W/logs/$label.log
  echo "unity exit $?"; grep "\[PuttMarksFilm\]\|error CS\|Exception" $W/logs/$label.log | sort -u | head -30
fi
