#!/bin/bash
set -u
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
v=work/postcard-look/v3
for n in 8 9 10; do
 nn=$(printf '%02d' "$n")
 for kind in installed staged; do
  if [ "$n" = 8 ] && [ "$kind" = staged ]; then continue; fi
  if [ "$kind" = staged ]; then b=work/postcard-look/v2/hole$nn/stage/hole_$nn.blend; f=work/postcard-look/v2/hole$nn/stage/hole_$nn.fbx; else b=blender/hole_$nn.blend; f=Unity/Assets/Resources/Course/hole_$nn.fbx; fi
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/postcard_look_verify.py -- "$n" --blend "$b" --fbx "$f" --json "$v/audit/verify_${kind}_$nn.json" > "$v/logs/verify_${kind}_$nn.log" 2>&1
  printf '%s hole%s exit %s\n' "$kind" "$nn" "$?"
  rg '^RESULT|^postcard_look_verify:' "$v/logs/verify_${kind}_$nn.log"
 done
done
