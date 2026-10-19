#!/bin/zsh
# final_sheets.sh : Blender review sheets of the five final clips (both heroes): behind + side views, every Nth frame -> blender_sheets/<hero>_<clip>.png
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
one() {
  tag=$1; H=$( [ $tag = male ] && echo Male || echo Female )
  for spec in Walk:3 RunForward:2 RunRight:2 RunLeft:2 Serve:4; do
    clip=${spec%%:*}; n=${spec##*:}
    RES=260x340 $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/render_sheet.py -- $tag $clip /tmp/sf_sheets/${tag}_${clip} every:$n behind,side > /dev/null 2>&1
    cols=$(python3 -c "import json;print(min(10,len(json.load(open('/tmp/sf_sheets/${tag}_${clip}_cells.json'))['cells'])))")
    python3 scripts/tile_sheet.py /tmp/sf_sheets/${tag}_${clip}_cells.json blender_sheets/${H}_${clip}.png $cols "${H}_${clip}" > /dev/null
    rm -f /tmp/sf_sheets/${tag}_${clip}_f*.png
  done
}
one male &
one female &
wait
echo sheets done
