#!/bin/zsh
# last steps once both turntables exist: decode check, sources + art-directory snapshots (after), gates.
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/dressed-look
BL=/Applications/Blender.app/Contents/MacOS/Blender
S=$W/scripts
cd $W
$BL -b --factory-startup --python $S/check_video.py -- data/video_check.json proof/Turntable_Male_White.mp4 proof/Turntable_Female_White.mp4 2>&1 | grep -E "VIDEO_CHECK_DONE|Error|Traceback"
python3 $S/compose_sheets.py > /dev/null
python3 $S/verify_sources.py data/sources_after.json
python3 $S/artdir_snapshot.py data/artdir_after.json
python3 $S/final_report.py
