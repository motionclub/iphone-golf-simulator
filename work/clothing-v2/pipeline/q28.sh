#!/bin/zsh
# chat 5 queue 28: male K5b_MT (no hem-layer rule, no GP_FOOT_ALL) after G3_GF
cd ${0:A:h}
while [ ! -f logs/G3.done ]; do sleep 20; done
M=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/../../male-garments-refpack/out/MatchHero_Male/unity
./garment_fit MatchHero_Male dump:Kit_Top npz:$M/Kit_Bottom_final.npz@Kit_Bottom npz:$M/Kit_Sock_L_final.npz@Kit_Sock_L npz:$M/Kit_Sock_R_final.npz@Kit_Sock_R npz:$M/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$M/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K5b_MT > logs/K5b_MT.log 2>&1
echo done > logs/K5b.done
