#!/bin/zsh
# chat 5 queue 6: after q4b -> refit shoes without hem riding (K2_MT, K2_FT) + female top with the limb-wrap rule, then ONE Unity session
cd ${0:A:h}
while pgrep -f "zsh ./q4b.sh" >/dev/null; do sleep 30; done
mkdir -p runs/_old && rm -f runs/K2_MT/MatchHero_Male/Kit_Shoe_?.npz runs/K2_FT/MatchHero_Female/Kit_Shoe_?.npz && mv runs/K2_FT/MatchHero_Female/Kit_Top.npz runs/_old/K2_FT_Kit_Top.npz; mv runs/K2_FT/MatchHero_Female/Kit_Bottom.npz runs/_old/K2_FT_Kit_Bottom.npz
./garment_fit MatchHero_Male dump:Kit_Bottom dump:Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K2_MT resume > logs/K2_MT_b.log 2>&1
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K2_FT resume > logs/K2_FT_b.log 2>&1
GP_STEP=.2 ./garment_install_batch MatchHero_Male:K2_MT:../out_gp3 MatchHero_Female:K2_FT:../out_gp GolfKitHero_Male:K2_GM:../out_gp3 GolfKitHero_Female:K2_GF \
  film=Emote_Thrust,Intro_Pushups,Serve,Drive,Emote_Shock look=target > logs/q6_install.log 2>&1
echo "Q6 DONE $?" > logs/q6.done
