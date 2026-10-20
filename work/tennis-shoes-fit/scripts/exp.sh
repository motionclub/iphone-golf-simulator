#!/bin/bash
# usage: exp.sh <gender> <tag> '<json params for this gender>' [view=1]   -> builds data/shoe{R,L}_<g><tag>.npz, runs a quick fit check summary, renders 4 views of the right foot
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit
G=$1; T=$2; J=$3; B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
SHOE_TAG=$T SHOE_PARAMS="{\"$G\": $J}" $B -b --factory-startup --python scripts/shoe.py -- $G 2>&1 | grep -E "Error|Trace|File \"|AssertionError|shell tris" | cut -c1-200
mkdir -p tmp/exp
PART_TAG=$T VDIST=${VDIST:-0.8} VTZ=${VTZ:-0.10} VRES=${VRES:-640,640} $B -b --factory-startup --python scripts/viewparts.py -- $G White tmp/exp/${G}${T}_R foot feet=R 2>&1 | grep -E "Error|Trace|File \"" 
python3 scripts/sheet.py tmp/exp/${G}${T}_sheet.png 4 tmp/exp/${G}${T}_R_side.png tmp/exp/${G}${T}_R_front.png tmp/exp/${G}${T}_R_heel.png tmp/exp/${G}${T}_R_q3.png
