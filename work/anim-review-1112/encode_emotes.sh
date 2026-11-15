#!/bin/bash
# Each emote folder -> game view | front view side by side (2000x720, 30 fps), then all joined into emotes.mp4.
O=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/anim-review-1112
FF=$HOME/tai-films/ffmpeg
cd $O/emotes || exit 1
rm -f list.txt
for d in emote_*; do
  [ -f $d/game_00000.jpg ] || continue
  $FF -y -loglevel error -framerate 30 -i $d/game_%05d.jpg -framerate 30 -i $d/front_%05d.jpg \
    -filter_complex "[0:v]scale=1280:720[a];[1:v]scale=720:720[b];[a][b]hstack" -c:v libx264 -pix_fmt yuv420p -crf 20 $d.mp4
  echo "file '$d.mp4'" >> list.txt
done
$FF -y -loglevel error -f concat -safe 0 -i list.txt -c copy $O/emotes.mp4
