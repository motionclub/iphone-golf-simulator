#!/bin/zsh
# Chat 4 (tennis animation integrity) -> integration chat 6.  usage: install_for_chat6.sh install|rollback <Unity project dir>
# install: (1) the 14 approved match strokes resampled to 60 Hz over Assets/Characters/MatchHeroes/<Sex>/ (same .meta, 60 Hz lastFrame
#          already there) and the prefab slot contact / leftRelease times back to the approved table (FrameRate60Wire.Run with the
#          30 Hz table: Forehand .667, ForehandWide .867, Return .433, VolleyBackhand .300, left releases), (2) the approved ArmCorrected
#          clips and the ReadyIdle60 clips in Resources/Tennis/Performance. Driver / inertia / grip polish .cs are installed by chat 4 itself.
#          (3) the MatchHeroClipMapTests contact table updated to those times (install/MatchHeroClipMapTests.approved_contacts.patch).
# rollback: puts back what this script replaced (copies taken at install time under install/backup_<timestamp>).
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
P=${2:?Unity project dir}; W=$REPO/work/tennis-anim-integrity; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
STROKES=(SplitToForehand SplitToBackhand RecoverCenter Forehand ForehandOpen ForehandWide ForehandShort Backhand BackhandWide SliceApproach Return VolleyForehand VolleyBackhand Overhead)
case $1 in
install)
  B=$REPO/work/integration-1018/backup/tennis_$(basename $P)_$(date +%Y%m%d%H%M%S); mkdir -p $B/prefabs $B/perf $B/fbx
  cp $P/Assets/Resources/Tennis/Customization/PlayerMale.prefab $P/Assets/Resources/Tennis/Customization/PlayerFemale.prefab $B/prefabs/
  cp $P/Assets/Resources/Tennis/Performance/*ArmCorrected.anim $B/perf/
  for s in Male Female; do for c in $STROKES; do cp $P/Assets/Characters/MatchHeroes/$s/${s}_$c.fbx $B/fbx/; done; done
  echo $B > $REPO/work/integration-1018/backup/tennis_last_$(basename $P).txt
  cp $W/install/perf/*.anim $W/install/perf/*.anim.meta $P/Assets/Resources/Tennis/Performance/
  GOLF_MUTE=1 FR60_REPO=$REPO FR60_SOURCE=$W/match60/export/fbx/ FR60_TABLE=$REPO/work/frame-rate-60/clip_table_30_original.json \
    $U -batchmode -projectPath $P -executeMethod GolfArcade.EditorTools.FrameRate60Wire.Run -logFile $B/wire.log
  cp $P/Assets/Tests/PlayMode/MatchHeroClipMapTests.cs $B/
  (cd $P/.. && patch -p0 --forward < $W/install/MatchHeroClipMapTests.approved_contacts.patch) || echo "MatchHeroClipMapTests patch did not apply: set Forehand .667, VolleyBackhand .300, ForehandWide .867, Return .433 by hand"
  echo "installed; backup $B" ;;
rollback)
  B=$(cat $REPO/work/integration-1018/backup/tennis_last_$(basename $P).txt)
  cp $B/prefabs/*.prefab $P/Assets/Resources/Tennis/Customization/
  cp $B/perf/*.anim $P/Assets/Resources/Tennis/Performance/
  rm -f $P/Assets/Resources/Tennis/Performance/{Male,Female}_ReadyIdle60.anim{,.meta}
  cp $B/MatchHeroClipMapTests.cs $P/Assets/Tests/PlayMode/
  for f in $B/fbx/*.fbx; do s=${${f:t}%%_*}; cp $f $P/Assets/Characters/MatchHeroes/$s/; done
  GOLF_MUTE=1 $U -batchmode -projectPath $P -executeMethod GolfArcade.EditorTools.FrameRate60Wire.Reimport -logFile $B/rollback.log
  echo "rolled back from $B" ;;
esac
