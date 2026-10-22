#!/bin/zsh
# Chat 12: every remaining check on the COMBINED clone, one Unity job at a time (heavy.sh), in priority order. Muted. Progress in logs/lane_a.progress.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; I=$R/work/integration-1018; C=$HOME/integration-work/Unity1
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
P=$I/logs/lane_a.progress; mark() { echo "$(date +%H:%M) $*" >> $P; }
win() { local out=$1; shift; mkdir -p $out; GOLF_MUTE=1 "$@" > /dev/null 2>&1; }
mark start
# 1. EditMode on the final combined state (round 9 + weather delta + coast fix)
$I/tools/tests.sh comb_edit2 $C EditMode; mark "comb_edit2 $(head -1 $I/tests/comb_edit2/summary.txt)"
# 2. smoke film (windowed, 1080p Game view)
O=$I/smoke; mkdir -p $O; SMOKE_OUT=$O GOLF_MUTE=1 $H unity $U -projectPath $C -runTests -testPlatform PlayMode -testFilter GolfArcade.PlayTests.IntegrationSmokeFilm -testResults $O/results.xml -logFile $O/unity.log; mark "smoke rc=$?"
# 3. 60 fps at 1080p (chat 1's RuntimeHoldsSixty, windowed)
O=$I/fps; mkdir -p $O; FR60B_DIR=$O GOLF_MUTE=1 $H unity $U -projectPath $C -runTests -testPlatform PlayMode -testFilter GolfArcade.PlayTests.FrameRate60bTests.RuntimeHoldsSixty -testResults $O/results.xml -logFile $O/unity.log; mark "fps rc=$?"
# 4. weather gates (chat W's harness: refs + readability on the rain / ash / tennis slots, with the maps layer on)
O=$I/weather; mkdir -p $O; MW_OUT=$O MW_JOBS=refs,read MW_SLOTS=W01,W03,W09,X16,W12ball,W14ball MW_ORIG_DIR=$R/work/majestic-weather/proof/orig GOLF_MUTE=1 $H unity $U -projectPath $C -executeMethod GolfArcade.EditorTools.MajesticWeatherShots.Run -logFile $O/unity.log; mark "weather rc=$?"
# 5. majestic budget on every hole (chat 10's MajesticGolfBudget), now with character LOD in
O=$I/budget; mkdir -p $O; MAM_OUT=$O MAM_CAMS=$R/work/majestic-all-maps/audit/views_clear GOLF_MUTE=1 $H unity $U -projectPath $C -executeMethod GolfArcade.EditorTools.MajesticGolfBudget.Run -logFile $O/unity.log; mark "budget rc=$?"
# 6. hand clearance: re-bake the male tracks (round-9 garments), then the gate sweep on all four contexts
BAKE_CONTEXTS="tennis_male golf_male" $I/tools/hc_bake.sh; mark "hand clearance done"
# 7. PlayMode on the combined state
$I/tools/tests.sh comb_play $C PlayMode; mark "comb_play $(head -1 $I/tests/comb_play/summary.txt)"
mark done
