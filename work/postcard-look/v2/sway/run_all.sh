#!/bin/bash
# The plant-sway gates, end to end (area U, 2026-10-05). usage: run_all.sh <label> [testcolors]
#   testcolors: the installed hole FBXs predate the sway colours -> the Game-view frame pairs use IN-MEMORY synthetic colours (flagged "test_colours"); omit it once the rebuilt plant meshes are installed.
# steps (Unity ones through heavy.sh, never overlapping another Unity / xcodebuild run):
#   1 guards.sh (7 PASS: hole 7, Hole.cs, scoring untouched)       2 GolfPlantSwayCheck (shader, material, mirror vs GPU, wind, caps, real meshes)
#   3 postcard_look_verify.py on the INSTALLED holes 8, 9, 10 (PLANT_SWAY_COLORS / PLANT_SWAY_CAPS / SHADERS_STATIC, blend + FBX re-import)
#   4 Game-view frame pairs x2 runs (fixed 12 mph wind, frozen clock, +1.2 s pair, real-time pair 1.2 s), sway_gates.py on run 1 and run1-vs-run2
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; cd "$R" || exit 2
L="${1:-x}"; TC=""; [ "$2" = "testcolors" ] && TC="GOLF_STILLS_SWAY_TESTCOLORS=1"
S=work/postcard-look/v2/sway; B=/Applications/Blender.app/Contents/MacOS/Blender; mkdir -p $S/logs
echo "== guards";  work/postcard-look/guards.sh | grep -c PASS | sed 's/^/guards PASS count: /'
echo "== unity sway check"; $S/run_swaycheck.sh $L > $S/logs/all_check_$L.out 2>&1; tail -1 $S/logs/all_check_$L.out; grep -E "^GATE.* FAIL|^SUMMARY" $S/swaycheck_$L.txt | cut -c1-260
echo "== verifier on the installed holes"
for n in 8 9 10; do $B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- $n --json $S/verify_installed_hole${n}_$L.json > $S/logs/verify_installed_hole${n}_$L.log 2>&1; echo "hole $n: $(grep -E '^RESULT' $S/logs/verify_installed_hole${n}_$L.log | cut -c1-200)"; grep -E "^GATE: (PLANT_SWAY|SHADERS_STATIC)" $S/logs/verify_installed_hole${n}_$L.log | cut -c1-230; done
echo "== game-view frame pairs (two runs)"
for r in 1 2; do $S/run_swaystills.sh ${L}_r$r $R/work/postcard-look/v2/proof/stills_cfg_9.json GOLF_STILLS_REALTIME_PAIR=1.2 $TC > $S/logs/all_stills_${L}_r$r.out 2>&1; tail -1 $S/logs/all_stills_${L}_r$r.out; done
python3 $S/sway_gates.py $S/stills_${L}_r1 --other $S/stills_${L}_r2 | tee $S/sway_gates_$L.txt | cut -c1-260
