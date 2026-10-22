B=/Applications/Blender.app/Contents/MacOS/Blender
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
for n in 08 09 10; do echo "== $n"; $B -b --factory-startup blender/hole_$n.blend --python work/postcard-look/v2/review3_gates/rr/imgpaths.py 2>&1 | grep IMG | head -3; done
