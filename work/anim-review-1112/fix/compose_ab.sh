#!/bin/bash
# compose_ab.sh <before dir> <after dir> <title> <out.mp4>
# Each emote folder present in both: [BEFORE front | L/R hands]  [AFTER front | L/R hands], 2160x720 @30, title burned in; joined.
FF=$HOME/tai-films/ffmpeg; B=$1; A=$2; T=$3; OUT=$4
FONT="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
TMP=$(mktemp -d); : > $TMP/list.txt
for d in $(cd "$A" && for g in result_* emote_* hub_Emote_* move_* hub_*; do [ -d "$g" ] && echo "$g"; done | awk '!s[$0]++'); do
  [ -f "$B/$d/front_00000.jpg" ] && [ -f "$A/$d/handL_00000.jpg" ] && [ -f "$B/$d/handL_00000.jpg" ] || continue
  nb=$(ls "$B/$d" | grep -c '^front_'); na=$(ls "$A/$d" | grep -c '^front_'); n=$(( nb < na ? nb : na ))
  name=$(echo $d | sed -E 's/^(result_|emote_|hub_)//; s/^Emote_//')
  $FF -y -loglevel error \
    -framerate 30 -i "$B/$d/front_%05d.jpg" -framerate 30 -i "$B/$d/handL_%05d.jpg" -framerate 30 -i "$B/$d/handR_%05d.jpg" \
    -framerate 30 -i "$A/$d/front_%05d.jpg" -framerate 30 -i "$A/$d/handL_%05d.jpg" -framerate 30 -i "$A/$d/handR_%05d.jpg" \
    -filter_complex "[1:v][2:v]vstack[hb];[4:v][5:v]vstack[ha];[0:v][hb]hstack,drawtext=fontfile='$FONT':text='BEFORE':x=20:y=20:fontsize=44:fontcolor=white:box=1:boxcolor=0xC0392B@0.85:boxborderw=12[b];[3:v][ha]hstack,drawtext=fontfile='$FONT':text='AFTER':x=20:y=20:fontsize=44:fontcolor=white:box=1:boxcolor=0x1E8449@0.85:boxborderw=12[a];[b][a]hstack,drawtext=fontfile='$FONT':text='$T  $name':x=(w-tw)/2:y=h-64:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=12" \
    -frames:v $n -c:v libx264 -pix_fmt yuv420p -crf 24 -r 30 $TMP/$d.mp4 && echo "file '$TMP/$d.mp4'" >> $TMP/list.txt
done
$FF -y -loglevel error -f concat -safe 0 -i $TMP/list.txt -c copy "$OUT" && echo "$OUT"
