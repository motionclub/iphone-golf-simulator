#!/bin/zsh
# chat 5 queue 15: after q14 -> female tennis with the limb-root remap (arm weight under the straps moves to the shoulder), fresh run K3_FT
cd ${0:A:h}
while pgrep -f "zsh ./q14.sh" >/dev/null; do sleep 20; done
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K3_FT > logs/K3_FT.log 2>&1
echo Q15 DONE > logs/q15.done
