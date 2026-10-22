#!/bin/zsh
# usage: run_fit.sh <iters> <seed> <outname> [start.json]
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers
./py.sh fit_f.py $1 $2 $4 > data/fit_log_$3.txt 2>&1
cp data/fit_best.json data/fit_best_$3.json
