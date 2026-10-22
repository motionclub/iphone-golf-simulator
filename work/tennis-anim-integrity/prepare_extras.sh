#!/bin/zsh
# Stage the comparison clips into the chat-4 clone: approved 30 Hz strokes (match-anim-set export + ArmCorrected backups) and the
# 60 Hz resample (match60), each with a copy of the installed .meta under a fresh GUID.
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
X=${TAI_CLONE:-/Users/adnanyonathan/tai-films/UnityClone}/Assets/TAI_Extra
cd $REPO; rm -rf $X
G() { uuidgen | tr -d '-' | tr 'A-F' 'a-f' }
for sex in Male Female; do
  mkdir -p $X/$sex/approved30 $X/$sex/resampled60
  for f in work/match-anim-set/export/fbx/${sex}_*.fbx; do b=$(basename $f); cp $f $X/$sex/approved30/$b
    git show HEAD:Unity/Assets/Characters/MatchHeroes/$sex/$b.meta | sed -E "s/^guid: .*/guid: $(G)/" > $X/$sex/approved30/$b.meta; done
  for f in work/frame-rate-60/backup_armcorrected/${sex}_*.anim; do b=$(basename $f); cp $f $X/$sex/approved30/$b; sed -E "s/^guid: .*/guid: $(G)/" $f.meta > $X/$sex/approved30/$b.meta; done
  for f in work/tennis-anim-integrity/match60/export/fbx/${sex}_*.fbx; do b=$(basename $f); cp $f $X/$sex/resampled60/$b
    sed -E "s/^guid: .*/guid: $(G)/" Unity/Assets/Characters/MatchHeroes/$sex/$b.meta > $X/$sex/resampled60/$b.meta
    [[ $b == *ReadyIdle.fbx ]] && sed -i '' -E 's/^( *lastFrame:) 66$/\1 132/' $X/$sex/resampled60/$b.meta || true; done   # the base model's meta cuts the take at 30 Hz frame 66
done
echo extras staged
