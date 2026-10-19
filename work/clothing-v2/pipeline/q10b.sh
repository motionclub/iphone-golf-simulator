#!/bin/zsh
cd ${0:A:h}
while pgrep -f "zsh ./q10a.sh" >/dev/null; do sleep 15; done
# 3. female tennis refit (top + skirt with the limb-wrap rule, shoes without riding), golf female full kit
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K2_FT resume > logs/K2_FT_b.log 2>&1
./garment_fit GolfKitHero_Female dump:Kit_Bottom dump:Kit_Top dump:Kit_Shoe_L dump:Kit_Shoe_R dump:Kit_Belt run=K2_GF resume > logs/K2_GF.log 2>&1
./garment_fit MatchHero_Male dump:Kit_Bottom dump:Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K2_MT resume > logs/K2_MT_c.log 2>&1
# 4. ONE Unity session: all four heroes + body film
GP_STEP=.2 ./garment_install_batch MatchHero_Male:K2_MT:../out_gp3 MatchHero_Female:K2_FT:../out_gp GolfKitHero_Male:K2_GM:../out_gp3 GolfKitHero_Female:K2_GF \
  film=Emote_Thrust,Intro_Pushups,Serve,Drive,Emote_Shock look=target > logs/q10_all_install.log 2>&1
echo "ALL DONE $?" > logs/q10_all.done
# 5. timed NEW_GARMENT_30MIN
T0=$(date +%s); echo "START $(date +%H:%M:%S)" > logs/new_ls.time
./garment_new MatchHero_Male polo2 tennis_male Kit_Top '{"sleeve":{"t":[0.05,0.20,0.30],"r":[0.086,0.072,0.060]}}' run=new_ls > logs/new_ls.log 2>&1
echo "END $(date +%H:%M:%S) wall $(( $(date +%s) - T0 )) s" >> logs/new_ls.time
