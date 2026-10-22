#!/bin/zsh
# chat 5 queue 32 (after the 45 GB cover incident): ONE Blender job at a time; cover/suite chunks now stop at 4 GB footprint
cd ${0:A:h}
./garment_new GolfKitHero_Female polo2 golf_female Kit_Top '{"raglan":{"under":[0.137,1.21],"neck":[0.115,1.37]},"sleeve_r":[0.070,0.062]}' run=R4_GF > logs/R4_GF.log 2>&1
echo done > logs/R4.done
mkdir -p runs/K8_MT/MatchHero_Male && cp runs/K7_MT/MatchHero_Male/Kit_{Bottom,Sock_L,Sock_R,Shoe_L,Shoe_R}.npz runs/K8_MT/MatchHero_Male/ && rm -f runs/K8_MT/MatchHero_Male/Kit_Top.npz
M=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/../../male-garments-refpack/out/MatchHero_Male/unity
GP_BULGE=.10 GP_SHAPES=32 ./garment_fit MatchHero_Male dump:Kit_Top npz:$M/Kit_Bottom_final.npz@Kit_Bottom npz:$M/Kit_Sock_L_final.npz@Kit_Sock_L npz:$M/Kit_Sock_R_final.npz@Kit_Sock_R npz:$M/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$M/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K8_MT resume > logs/K8_MT.log 2>&1
echo done > logs/K8M.done
