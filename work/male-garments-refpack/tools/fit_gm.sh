#!/bin/zsh
# golf male fit (after MG_MT): new tucked polo + fixed belt + shoe4 from out/, trousers from the dump
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline
while pgrep -f "garment_fit MatchHero_Male" >/dev/null; do sleep 20; done
export GP_FOOT_ALL=1
./garment_fit GolfKitHero_Male dump:Kit_Bottom npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Top_final.npz@Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Belt_final.npz@Kit_Belt npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM.log 2>&1
echo "GM $?" >> logs/MG.done
