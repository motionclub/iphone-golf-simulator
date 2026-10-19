#!/bin/zsh
# chat 5 queue 13 (male heroes moved to the male-garments chat) (ONE heavy job at a time, heavy.sh): limb-filtered cover + suite for every hero, BEFORE re-measured with the same
# metric, then ONE Unity install of all four + film, then the timed new-garment test and the female tank A/B
cd ${0:A:h}
HV=${GP_HEAVY:-$PWD/../../delegation-2026-10-17/heavy.sh}
while pgrep -f "garment_fit GolfKitHero_Female" >/dev/null; do sleep 15; done
./garment_fit GolfKitHero_Female dump:Kit_Bottom dump:Kit_Top dump:Kit_Shoe_L dump:Kit_Shoe_R dump:Kit_Belt run=K2_GF resume > logs/K2_GF_b.log 2>&1
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K2_FT resume > logs/K2_FT_c.log 2>&1
for H in MatchHero_Male MatchHero_Female GolfKitHero_Male GolfKitHero_Female; do
  for c in $(seq 1 10); do $HV blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python gp/suite.py -- $H runs/before_v3 > logs/before_v3_$H.log 2>&1 && break; grep -q "SUITE chunk done" logs/before_v3_$H.log || break; done
  python3 gp/report.py runs/before_v3/$H runs/before/$H > /dev/null 2>&1
done
GP_STEP=.2 ./garment_install_batch MatchHero_Female:K2_FT:../out_gp GolfKitHero_Female:K2_GF \
  film=Emote_Thrust,Intro_Pushups,Serve,Drive,Emote_Shock look=target > logs/q13_install.log 2>&1
echo "INSTALL DONE $?" > logs/q13_install.done
T0=$(date +%s); echo "START $(date +%H:%M:%S)" > logs/new_ls.time
./garment_new MatchHero_Male polo2 tennis_male Kit_Top '{"sleeve":{"t":[0.05,0.20,0.30],"r":[0.086,0.072,0.060]}}' run=new_ls > logs/new_ls.log 2>&1
echo "END $(date +%H:%M:%S) wall $(( $(date +%s) - T0 )) s" >> logs/new_ls.time
./garment_fit MatchHero_Female dump:Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K2_FD resume > logs/K2_FD.log 2>&1
echo Q12 DONE > logs/q13.done
