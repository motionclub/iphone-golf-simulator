#!/bin/bash
# encode_hands.sh <film dir> <out.mp4> <label>: per emote = game | front | left hand over right hand, name burned in; all joined.
FF=$HOME/tai-films/ffmpeg; D=$1; OUT=$2; L=$3
cd "$D" || exit 1; rm -f list.txt
FONT=/System/Library/Fonts/Supplemental/Arial\ Bold.ttf
for d in emote_* result_*; do
  [ -f $d/game_00000.jpg ] || continue
  name=${d#*_Emote_}; name=${name#result_Emote_}; name=${name#result_}
  $FF -y -loglevel error -framerate 30 -i $d/game_%05d.jpg -framerate 30 -i $d/front_%05d.jpg -framerate 30 -i $d/handL_%05d.jpg -framerate 30 -i $d/handR_%05d.jpg \
    -filter_complex "[2:v][3:v]vstack[h];[0:v][1:v][h]hstack=inputs=3,drawtext=fontfile='$FONT':text='$L  $name':x=24:y=h-60:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10,drawtext=fontfile='$FONT':text='LEFT HAND':x=2000+10:y=10:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.5,drawtext=fontfile='$FONT':text='RIGHT HAND':x=2000+10:y=370:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.5" \
    -c:v libx264 -pix_fmt yuv420p -crf 23 $d.mp4 && echo "file '$d.mp4'" >> list.txt
done
$FF -y -loglevel error -f concat -safe 0 -i list.txt -c copy "$OUT"
