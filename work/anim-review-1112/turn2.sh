#!/bin/bash
O=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/anim-review-1112
until grep -q done $O/rally_status.txt 2>/dev/null; do sleep 5; done
rm -f $O/after_status.txt; cd $O; ROWS_FILE=$O/rows_s2.txt ./after.sh
