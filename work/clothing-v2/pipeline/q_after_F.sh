#!/bin/zsh
# chat 5 queue (one heavy job at a time): wait for the F chain, then E8 re-cover (footwear rule) + suite with pair attribution, then the shoes to the male pack sheets 13/14
cd ${0:A:h}
while pgrep -f "garment_fit MatchHero_Female" >/dev/null; do sleep 20; done
./garment_fit MatchHero_Male dump:Kit_Bottom dump:Kit_Top run=E8 resume > logs/E8r2.log 2>&1
cd .. && CV2_OUT=$PWD/out_gp3 shoes/run_shoe3.sh MatchHero_Male male_tennis > logs/run_shoe3_m13.log 2>&1
CV2_OUT=$PWD/out_gp3 shoes/run_shoe3.sh GolfKitHero_Male male_golf > logs/run_shoe3_g14.log 2>&1
echo QUEUE DONE >> pipeline/logs/E8r2.log
