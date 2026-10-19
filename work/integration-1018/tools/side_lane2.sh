#!/bin/zsh
# Chat 12, parallel lane on ~/integration-work/Unity3 (combined + golf swing fix + chat 3 staged r5/HCT3 + chat W gold ring):
# W12/W14 re-check with the gold ring, then the GOLF half of the clearance bake + gate (tennis bakes on Unity1). Golf tracks are then copied to Unity1.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; I=$R/work/integration-1018; C=$HOME/integration-work/Unity3
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
P=$I/logs/side_lane2.progress; mark() { echo "$(date +%H:%M) $*" >> $P; }
mark start
O=$I/weather_tennis2; mkdir -p $O; MW_OUT=$O MW_JOBS=refs,read MW_SLOTS=W12,W14 MW_ORIG_DIR=$R/work/majestic-weather/proof/orig GOLF_MUTE=1 $H unity $U -projectPath $C -executeMethod GolfArcade.EditorTools.MajesticWeatherShots.Run -logFile $O/unity.log
mark "weather tennis (gold ring) rc=$?"
O=$HOME/integration-work/hc/r5_golf; mkdir -p $O
SWEEP_TRACKS=bake SWEEP_TRACKS_FRESH=1 SWEEP_TRACK_HZ=30 SWEEP_ROUNDS=2 SWEEP_BAKE_DIAG=0 SWEEP_BEFORE=1 SWEEP_RENDER=1 SWEEP_WORST=6 SWEEP_FREE=1 SWEEP_BAKE=1 SWEEP_HZ=60 \
  SWEEP_CONTEXTS=golf_male,golf_female SWEEP_OUT=$O GOLF_MUTE=1 \
  $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep -logFile $O/unity.log
mark "golf clearance bake+gate rc=$? $(grep -c 'SweepTrack\] wrote' $O/unity.log) track files"
mark done
