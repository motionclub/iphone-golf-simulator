#!/bin/zsh
# chat 5 queue (ONE heavy job at a time, all Blender through heavy.sh): refit with capped corrective fields, cover (footwear rule) + suite, then shoes to the male pack sheets 13/14
cd ${0:A:h}
./garment_fit MatchHero_Male dump:Kit_Bottom dump:Kit_Top run=E8 resume > logs/E8c.log 2>&1
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top run=F resume > logs/Fc.log 2>&1
cd .. && CV2_OUT=$PWD/out_gp3 shoes/run_shoe3.sh MatchHero_Male male_tennis > logs/run_shoe3_m13.log 2>&1
CV2_OUT=$PWD/out_gp3 shoes/run_shoe3.sh GolfKitHero_Male male_golf > logs/run_shoe3_g14.log 2>&1
echo QUEUE DONE > pipeline/logs/q2.done
