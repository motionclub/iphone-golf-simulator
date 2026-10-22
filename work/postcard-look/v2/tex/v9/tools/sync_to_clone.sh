#!/bin/bash
# usage: sync_to_clone.sh <dir with Fairway_C.png ...> : copy the grass maps of <dir> into the clone's Look folder (Unity imports them at the next run)
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
D="$SC/UnityClone/Assets/Resources/Course/Look"
for f in Fairway_C Fairway_N Green_C Green_N Rough_C Rough_N; do [ -f "$1/$f.png" ] && cp "$1/$f.png" "$D/$f.png" && echo "synced $f"; done
