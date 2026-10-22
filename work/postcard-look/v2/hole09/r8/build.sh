#!/bin/bash
# usage: build.sh <label> [extra build args]  -> builds into work/postcard-look/v2/hole09/r8/<label>/ (blend, fbx, overview), log r8/build_<label>.log
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; L=$1; shift
mkdir -p $R/$O/r8/$L
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/hole09_build.py -- --out $R/$O/r8/$L "$@" > $O/r8/build_$L.log 2>&1
echo "exit $?"; grep -E "Traceback|Error|^HOLE09|GATE:.*FAIL" $O/r8/build_$L.log | head -20
