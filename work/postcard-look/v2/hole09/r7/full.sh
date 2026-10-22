#!/bin/bash
# full dev cycle: build with QA + render into r7/<label>, then every gate -> r7/gates_<label>. usage: full.sh <label>
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; B=/Applications/Blender.app/Contents/MacOS/Blender; export LBL=$1
mkdir -p $R/$O/r7/$LBL
$B -b --factory-startup --python blender/scripts/hole09_build.py -- --out $R/$O/r7/$LBL > $O/r7/build_$LBL.log 2>&1
grep -E "Traceback|Error|^HOLE09|GATE:.*FAIL" $O/r7/build_$LBL.log | head -20
bash $O/r7/run_gates.sh $R/$O/r7/$LBL > $O/r7/gates_$LBL.out 2>&1
cat $O/r7/gates_$LBL.out | cut -c1-260
