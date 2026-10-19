#!/bin/zsh
# chat 5 queue 23 (female film before/after, then male K5_MT) (10-18): male tennis polo K5_MT for the male-garments chat, after q20. ONE heavy job at a time (heavy.sh).
# polo = dump:Kit_Top (mesh unchanged); shorts/socks/shoes = male-garments build; GP_FOOT_ALL=1; hem-over-waistband rule (GP_HEM_LAYER=1)
# order: shorts (inside the current polo) -> polo (over the new shorts) -> shorts again (inside the NEW polo) -> socks/shoes + cover + suite
cd ${0:A:h}
while pgrep -f "garment_fit MatchHero_Female" >/dev/null; do sleep 20; done      # K6_FT (started by q22)
# 1. female rip gate film: what the clone has (K3b) -> install K6 -> film again; Serve/Forehand/Backhand/Victory/Slump, torso, front/side/back/3-4
GP_FILM_BEFORE=1 GP_FOCUS=torso GP_VIEWS=0,90,180,45 GP_STEP=.1 ./garment_install_batch MatchHero_Female:K6_FT \
  film=Female_Serve,Female_ForehandArmCorrected,Female_BackhandArmCorrected,Female_Emote_Victory,Female_Emote_Slump look=target > logs/q23_film.log 2>&1
echo "FILM DONE $?" > logs/q23_film.done
# 2. male tennis K5_MT for the male-garments chat
M=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/../../male-garments-refpack/out/MatchHero_Male/unity
RD=runs/K5_MT; mkdir -p $RD/MatchHero_Male
export GP_FOOT_ALL=1
python3 gp/fit.py MatchHero_Male npz:$M/Kit_Bottom_final.npz $RD --tag Kit_Bottom >> logs/K5_MT_pre.log 2>&1
python3 gp/fit.py MatchHero_Male dump:Kit_Top $RD --tag Kit_Top >> logs/K5_MT_pre.log 2>&1
rm -f $RD/MatchHero_Male/Kit_Bottom.npz
python3 gp/fit.py MatchHero_Male npz:$M/Kit_Bottom_final.npz $RD --tag Kit_Bottom >> logs/K5_MT_pre.log 2>&1
./garment_fit MatchHero_Male dump:Kit_Top npz:$M/Kit_Bottom_final.npz@Kit_Bottom npz:$M/Kit_Sock_L_final.npz@Kit_Sock_L npz:$M/Kit_Sock_R_final.npz@Kit_Sock_R npz:$M/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$M/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K5_MT resume > logs/K5_MT.log 2>&1
echo Q23 DONE > logs/q23.done
