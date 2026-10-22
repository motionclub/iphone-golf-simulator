#!/bin/bash
# usage: dev.sh <label>  -> build to r6/<label>/, render views_arch.json to r6/<label>_views/, print masonry stats
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; L=$1; B=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p $O/r6/$L; rm -rf $O/r6/${L}_views
STAGE=$R/$O/r6/$L $O/tools/run_build.sh r6$L 2>&1 | tail -4 | cut -c1-200
grep -E "ruin|masonry|chip" $O/logs/build_r6$L.log | cut -c1-400
$B -b --factory-startup --python $O/tools/render_views.py -- --blend $R/$O/r6/$L/hole_09.blend --json ${VIEWS:-$R/$O/r6/views_arch.json} --out $R/$O/r6/${L}_views --samples 24 2>&1 | grep -E "RENDERED|Error|Traceback"
