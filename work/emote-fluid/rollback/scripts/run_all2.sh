#!/bin/zsh
# run_all2.sh : the whole overhaul measurement chain: build (solve, bake, export 6 FBX) -> trace the FBX -> independent penetration gate (6 runs in parallel) -> pre-registered gates.  Logs in ../logs/run_all2_*.txt
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
J=$R/work/emote-overhaul
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $J/scripts
echo "== build $(date +%T)"; ./build_all2.sh > $J/logs/run_all2_build.txt 2>&1; tail -n 12 $J/logs/run_all2_build.txt
echo "== trace $(date +%T)"; for t in male female; do $B -b --factory-startup --python trace_fbx2.py -- $t 2>&1 | grep -E "TRACE|Error|Traceback" | tail -n 3; done
echo "== collide3 $(date +%T)"; rm -f $J/proof/collide/*.json
for c in Emote_Spike Emote_Thrust Emote_Scuba; do for t in male female; do ./col3.sh $t $c every:1 $J/proof/collide/${c}_${t}_c3.json > $J/logs/c3_${c}_${t}.txt 2>&1 & done; done; wait
tail -qn 2 $J/logs/c3_*.txt | grep MAX
echo "== gates $(date +%T)"; $B -b --factory-startup --python check_gates2.py -- both 2>&1 | grep -E "^GATE|GATES_DONE|Error|Traceback|File |line [0-9]+" | cut -c1-420 > $J/logs/run_all2_gates.txt
grep -c " PASS " $J/logs/run_all2_gates.txt; grep -E " FAIL |Error|Traceback" $J/logs/run_all2_gates.txt; tail -n 1 $J/logs/run_all2_gates.txt
echo "== done $(date +%T)"
