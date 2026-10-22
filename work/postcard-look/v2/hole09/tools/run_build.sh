#!/bin/bash
# usage: run_build.sh <label> [extra build args]   -> stage dir work/postcard-look/v2/hole09/stage (or STAGE=dir env), log logs/build_<label>.log
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; L=$1; shift
S=${STAGE:-$R/$O/stage}
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/hole09_build.py -- --out "$S" "$@" > $O/logs/build_$L.log 2>&1
echo "exit $?"; grep -E "Traceback|Error|^HOLE09|GATE:.*FAIL" $O/logs/build_$L.log | head -20
