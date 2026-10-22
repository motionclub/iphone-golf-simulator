#!/bin/zsh
# Chat 12 second pass on the COMBINED clone, one launch per step (heavy.sh fast lane): chat 3's r5 clearance code -> ONE bake + gate of all four
# contexts (the tracks that ship) -> golf smoke re-film in rain -> tennis weather slots. Waits for the clone to be free first.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; I=$R/work/integration-1018; C=$HOME/integration-work/Unity1
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
P=$I/logs/second_pass.progress; mark() { echo "$(date +%H:%M) $*" >> $P; }
while pgrep -f "projectPath $C " > /dev/null || pgrep -f "projectPath $C\$" > /dev/null; do sleep 30; done
mark "clone free"
# chat 3: the STAGED copies (the working tree may hold an unvalidated body-step gate v2)
for f in Scripts/Tennis/HeroPoseSafety.cs Scripts/Tennis/HeroClearanceTracks.cs Editor/AnimationSafetyAuditSweep.cs Editor/HeroClearanceFilm.cs Tests/EditMode/HeroClearanceTests.cs; do (cd $R && git show :Unity/Assets/$f) > $C/Assets/$f || mark "COPY FAILED $f"; done
cp $I/unity/Assets/Tests/PlayMode/IntegrationSmokeFilm.cs $C/Assets/Tests/PlayMode/
# golf swing speed fix (golf-swing-faster-smooth, installed in the repo working tree): into BOTH clones, so the final 3-way install leaves it alone
for f in Scripts/Game/GolferView.cs Scripts/Game/GolfGame.Native.cs Scripts/Swing/MotionSwingDetector.cs Tests/EditMode/GolfSwingPaceTests.cs Tests/EditMode/GolfSwingPaceTests.cs.meta; do
  cp $R/Unity/Assets/$f $C/Assets/$f; cp $R/Unity/Assets/$f $HOME/integration-work/Unity2/Assets/$f; done
mark "chat 3 r5 code + smoke test copied"
# chat W: tennis-ball gold ring in rain (Adnan OK'd for tonight) + every earlier chat W file (the halo is already gone from this clone)
bash $R/work/majestic-weather/tools/install.sh $C > /dev/null
for f in Scripts/Majestic/MajesticWeatherComet.cs Resources/Majestic/MajesticWeatherComet.shader; do cmp -s $R/Unity/Assets/$f $C/Assets/$f || mark "COMET MISMATCH $f"; done
mark "chat W tennis ember installed"
# 1. clearance: bake + gate, TENNIS contexts here (golf bakes in parallel on Unity3, tools/side_lane2.sh), one launch
O=$HOME/integration-work/hc/r5; rm -rf $O; mkdir -p $O
SWEEP_TRACKS=bake SWEEP_TRACKS_FRESH=1 SWEEP_TRACK_HZ=30 SWEEP_ROUNDS=2 SWEEP_BAKE_DIAG=0 SWEEP_BEFORE=1 SWEEP_RENDER=1 SWEEP_WORST=6 SWEEP_FREE=1 SWEEP_BAKE=1 SWEEP_HZ=60 \
  SWEEP_CONTEXTS=tennis_male,tennis_female SWEEP_OUT=$O GOLF_MUTE=1 \
  $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.AnimationSafetyAudit.Sweep -logFile $O/unity.log
mark "clearance bake+gate rc=$? $(grep -c 'SweepTrack\] wrote' $O/unity.log) track files"
# the golf half from Unity3 (wait for it), so the tracks that ship are all here
while [ ! -s $HOME/integration-work/hc/r5_golf/unity.log ] || ! grep -q "golf clearance bake" $I/logs/side_lane2.progress 2>/dev/null; do sleep 30; done
for x in Male Female; do cp $HOME/integration-work/Unity3/Assets/Resources/HeroClearance/Tracks_${x}_Golf.bytes $C/Assets/Resources/HeroClearance/; done
mark "golf tracks copied from Unity3"
python3 $R/work/hand-clearance/tools/summarize.py $O $I/clearance --label integration > $I/logs/clearance_summary.txt 2>&1; mark "summarize rc=$?"
# 2-4 (golf rain re-film, tennis weather, golf PlayMode suites) moved to tools/side_lane.sh (4th slot, snapshot clone Unity3)
$I/tools/tests.sh comb_edit3 $C EditMode; mark "comb_edit3 $(head -1 $I/tests/comb_edit3/summary.txt)"
mark done
