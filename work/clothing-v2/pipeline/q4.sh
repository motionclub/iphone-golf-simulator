#!/bin/zsh
# chat 5 queue 4 (ONE heavy job at a time via heavy.sh): every hero's full worn kit, fresh runs K_<hero> (coverage-limited weights, capped correctives,
# footwear cover rule, sheet 13/14 shoes for the men)
cd ${0:A:h}
./garment_fit MatchHero_Male dump:Kit_Bottom dump:Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K_MT resume > logs/K_MT.log 2>&1
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K_FT resume > logs/K_FT.log 2>&1
./garment_fit GolfKitHero_Male dump:Kit_Bottom dump:Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/out_gp3/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=K_GM resume > logs/K_GM.log 2>&1
./garment_fit GolfKitHero_Female dump:Kit_Bottom dump:Kit_Top dump:Kit_Shoe_L dump:Kit_Shoe_R dump:Kit_Belt run=K_GF resume > logs/K_GF.log 2>&1
echo Q4 DONE > logs/q4.done
