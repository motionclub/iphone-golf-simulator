#!/bin/zsh
# Chat 12 (max speed): the TENNIS half of the clearance bake + gate on ~/integration-work/Unity4 (snapshot of Unity3 = final combined state).
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; I=$R/work/integration-1018; C=$HOME/integration-work/Unity4
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
P=$I/logs/tennis_bake.progress; mark() { echo "$(date +%H:%M) $*" >> $P; }
mark start
O=$HOME/integration-work/hc/r5_tennis; mkdir -p $O
SWEEP_TRACKS=bake SWEEP_TRACKS_FRESH=1 SWEEP_TRACK_HZ=30 SWEEP_ROUNDS=2 SWEEP_BAKE_DIAG=0 SWEEP_BEFORE=1 SWEEP_RENDER=1 SWEEP_WORST=6 SWEEP_FREE=1 SWEEP_BAKE=1 SWEEP_HZ=60 \
  SWEEP_CONTEXTS=tennis_male,tennis_female SWEEP_OUT=$O GOLF_MUTE=1 \
  $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep -logFile $O/unity.log
mark "tennis clearance bake+gate rc=$? $(grep -c 'SweepTrack\] wrote' $O/unity.log) track files"
mark done
