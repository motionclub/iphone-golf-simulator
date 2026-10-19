#!/bin/zsh
# chat 5 queue 3 (ONE heavy job at a time via heavy.sh): the full worn kit of every hero, after q2 (refits + shoe builds) finishes
cd ${0:A:h}
while pgrep -f "q2.sh" >/dev/null; do sleep 20; done
O3=${0:A:h:h}/out_gp3
mkdir -p runs/M2/MatchHero_Male runs/F2/MatchHero_Female
cp runs/E8/MatchHero_Male/Kit_Top.npz runs/E8/MatchHero_Male/Kit_Bottom.npz runs/M2/MatchHero_Male/ 2>/dev/null
cp runs/F/MatchHero_Female/Kit_Top.npz runs/F2/MatchHero_Female/ 2>/dev/null
./garment_fit MatchHero_Male dump:Kit_Bottom dump:Kit_Top npz:$O3/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$O3/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=M2 resume > logs/M2.log 2>&1
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=F2 resume > logs/F2.log 2>&1
./garment_fit GolfKitHero_Male dump:Kit_Bottom dump:Kit_Top npz:$O3/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$O3/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=G resume > logs/G.log 2>&1
./garment_fit GolfKitHero_Female dump:Kit_Bottom dump:Kit_Top dump:Kit_Shoe_L dump:Kit_Shoe_R dump:Kit_Belt run=H resume > logs/H.log 2>&1
echo Q3 DONE > logs/q3.done
