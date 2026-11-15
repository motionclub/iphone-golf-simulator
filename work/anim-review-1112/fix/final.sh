#!/bin/bash
# final.sh: compose the four before/after reels and join them into empty_hands_before_after.mp4 (1620 wide).
O=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/anim-review-1112; F=$O/films; FF=$HOME/tai-films/ffmpeg
cd $O
fix/compose_ab.sh $O/hands_golfall $F/golf_m_after "GOLF · HIM ·" $O/ab/golf_m.mp4
fix/compose_ab.sh $F/golf_f_before $F/golf_f_after "GOLF · HER ·" $O/ab/golf_f.mp4
fix/compose_ab.sh $F/hub_m_before $F/hub_m_after "PLAZA · HIM ·" $O/ab/hub_m.mp4
fix/compose_ab.sh $F/hub_f_before $F/hub_f_after "PLAZA · HER ·" $O/ab/hub_f.mp4
printf "file '%s'\n" $O/ab/golf_m.mp4 $O/ab/golf_f.mp4 $O/ab/hub_m.mp4 $O/ab/hub_f.mp4 > $O/ab/list.txt
$FF -y -loglevel error -f concat -safe 0 -i $O/ab/list.txt -vf scale=1620:-2 -c:v libx264 -crf 25 -pix_fmt yuv420p -an $O/empty_hands_before_after.mp4
ls -la $O/empty_hands_before_after.mp4
