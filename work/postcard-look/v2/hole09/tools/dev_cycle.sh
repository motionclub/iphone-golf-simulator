#!/bin/bash
# dev loop (repair round 1): build into r5/dev (no render, no QA) and render the ruin / gap previews. usage: dev_cycle.sh [views json] 
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; B=/Applications/Blender.app/Contents/MacOS/Blender
J=${1:-$O/r5/views_ruin.json}
$B -b --factory-startup --python blender/scripts/hole09_build.py -- --out $R/$O/r5/dev --no-render --no-qa 2>&1 | grep -E "\[hole09\] ruin|Traceback|Error|File \"|^HOLE09 stats|line [0-9]+" | cut -c1-300
$B -b --factory-startup --python $O/tools/render_views.py -- --blend $R/$O/r5/dev/hole_09.blend --json $R/$J --out $R/$O/r5/dev_views --samples 16 2>&1 | grep -E "RENDERED|Error|Traceback" | cut -c1-100
