#!/bin/zsh
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-face-body
until grep -qE "MEASURE DONE|Error|Traceback" logs/measure_m0.log; do sleep 15; done
tools/unity_run.sh GolfArcade.EditorTools.MaleFaceReview.Run review_m0_views FACE_REVIEW_OUT=$PWD/unity_out/m0 FACE_REVIEW_SET=views
tools/unity_run.sh GolfArcade.EditorTools.MaleFaceReview.Run review_m0_body FACE_REVIEW_OUT=$PWD/unity_out/m0_body FACE_REVIEW_SET=body
tools/unity_run.sh GolfArcade.EditorTools.MaleFaceMeshCount.Run meshcount_m0 MESH_COUNT_OUT=$PWD/eval/meshcount_before.txt
echo BEFORE_DONE
