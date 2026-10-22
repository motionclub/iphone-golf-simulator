#!/bin/bash
# shares.sh DIR : mask renders of the 4 aerials of DIR/hole_10.blend + lava / rock shares
D=$1
/Applications/Blender.app/Contents/MacOS/Blender -b $D/hole_10.blend --python /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/tools/render_views.py -- --shots /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/landmarks_with_aerial.json --out $D/mask --only aerial,aerial2,aerial3,aerial4 --res 1600x900 --mask --samples 1 > /dev/null 2>&1
python3 /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/tools/mask_stats.py $D/mask $D/shares.json
