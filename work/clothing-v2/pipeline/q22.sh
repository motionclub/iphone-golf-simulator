#!/bin/zsh
# chat 5 queue 22 (female K6_FT first, then male K5_MT) (10-18): male tennis polo K5_MT for the male-garments chat, after q20. ONE heavy job at a time (heavy.sh).
# polo = dump:Kit_Top (mesh unchanged); shorts/socks/shoes = male-garments build; GP_FOOT_ALL=1; hem-over-waistband rule (GP_HEM_LAYER=1)
# order: shorts (inside the current polo) -> polo (over the new shorts) -> shorts again (inside the NEW polo) -> socks/shoes + cover + suite
cd ${0:A:h}
while pgrep -f "zsh ./q20.sh" >/dev/null; do sleep 20; done
# 1. female tennis K6_FT: partial limb-root remap + 2 mm weld + wrap filter + corrective depth fade + lift smoothing; today's skirt weights
GP_LIMB_ROOT=1 ./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R keep=Kit_Bottom run=K6_FT > logs/K6_FT.log 2>&1
echo K6 DONE > logs/k6.done
# 2. male tennis K5_MT for the male-garments chat
M=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/../../male-garments-refpack/out/MatchHero_Male/unity
RD=runs/K5_MT; mkdir -p $RD/MatchHero_Male
export GP_FOOT_ALL=1
python3 gp/fit.py MatchHero_Male npz:$M/Kit_Bottom_final.npz $RD --tag Kit_Bottom >> logs/K5_MT_pre.log 2>&1
python3 gp/fit.py MatchHero_Male dump:Kit_Top $RD --tag Kit_Top >> logs/K5_MT_pre.log 2>&1
rm -f $RD/MatchHero_Male/Kit_Bottom.npz
python3 gp/fit.py MatchHero_Male npz:$M/Kit_Bottom_final.npz $RD --tag Kit_Bottom >> logs/K5_MT_pre.log 2>&1
./garment_fit MatchHero_Male dump:Kit_Top npz:$M/Kit_Bottom_final.npz@Kit_Bottom npz:$M/Kit_Sock_L_final.npz@Kit_Sock_L npz:$M/Kit_Sock_R_final.npz@Kit_Sock_R npz:$M/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$M/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K5_MT resume > logs/K5_MT.log 2>&1
echo Q22 DONE > logs/q22.done
