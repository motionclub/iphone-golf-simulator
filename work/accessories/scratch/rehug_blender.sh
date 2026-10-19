#!/bin/zsh
# cap re-hug (male, 10-17): measure the old caps on the new head, re-hug both caps (kept socket fit), measure again
set -e
A=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/accessories; cd $A
BL=/Applications/Blender.app/Contents/MacOS/Blender
export ACC_DUMP=$A/dump_1017
$BL -b --factory-startup --python py/rehug_measure.py -- $A/scratch/measure_before_newhead.json tennis_before=$A/scratch/before_1017/tennis_cap golf_before=$A/scratch/before_1017/golf_cap > logs/rehug_measure_before.log 2>&1
for v in tennis golf; do $BL -b --factory-startup --python py/cap_export.py -- $v Male --keep-fit > logs/rehug_export_$v.log 2>&1; done
$BL -b --factory-startup --python py/rehug_measure.py -- $A/scratch/measure_after.json tennis_before=$A/scratch/before_1017/tennis_cap golf_before=$A/scratch/before_1017/golf_cap tennis_after=$A/out/Male/tennis_cap golf_after=$A/out/Male/golf_cap > logs/rehug_measure_after.log 2>&1
echo done
