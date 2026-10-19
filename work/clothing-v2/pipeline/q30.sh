#!/bin/zsh
# chat 5 queue 30: K5b_MT cover+suite again with GP_FOOT_ALL=1 (refpack shoes have a low upper under a taller cartoon forefoot)
cd ${0:A:h}
while [ ! -f logs/K5b.done ]; do sleep 20; done
M=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/../../male-garments-refpack/out/MatchHero_Male/unity
GP_FOOT_ALL=1 ./garment_fit MatchHero_Male dump:Kit_Top npz:$M/Kit_Bottom_final.npz@Kit_Bottom npz:$M/Kit_Sock_L_final.npz@Kit_Sock_L npz:$M/Kit_Sock_R_final.npz@Kit_Sock_R npz:$M/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$M/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K5b_MT resume > logs/K5b_MT_fa.log 2>&1
echo done > logs/K5bfa.done
