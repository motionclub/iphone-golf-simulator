#!/bin/zsh
# chat 5 queue 31: holes split for the male-garments chat: K5b (FOOT_ALL cover) suite re-measure, then K5c with GP_FOOT_ALL=1
cd ${0:A:h}
HV=${GP_HEAVY:-$PWD/../../delegation-2026-10-17/heavy.sh}
while [ ! -f logs/K5c.done ]; do sleep 20; done
for c in $(seq 1 10); do $HV blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python gp/suite.py -- MatchHero_Male runs/K5b_MT/suite --cand runs/K5b_MT > logs/K5b_split_suite.log 2>&1 && break; grep -q "SUITE chunk done" logs/K5b_split_suite.log || break; done
python3 gp/report.py runs/K5b_MT/suite/MatchHero_Male runs/before_v3/MatchHero_Male > /dev/null
echo done > logs/K5bsplit.done
M=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/../../male-garments-refpack/out/MatchHero_Male/unity
mkdir -p runs/K5d_MT/MatchHero_Male && cp runs/K5c_MT/MatchHero_Male/Kit_*.npz runs/K5d_MT/MatchHero_Male/
GP_FOOT_ALL=1 ./garment_fit MatchHero_Male dump:Kit_Top npz:$M/Kit_Bottom_final.npz@Kit_Bottom npz:$M/Kit_Sock_L_final.npz@Kit_Sock_L npz:$M/Kit_Sock_R_final.npz@Kit_Sock_R npz:$M/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$M/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K5d_MT resume > logs/K5d_MT.log 2>&1
echo done > logs/K5d.done
