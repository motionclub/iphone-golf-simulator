#!/bin/zsh
# chat 5 queue 17: after q16 -> female tennis K3b: K3_FT top (limb-root remap) + TODAY's skirt weights (--keep-weights, + correctives) + shoes
cd ${0:A:h}
while pgrep -f "zsh ./q16.sh" >/dev/null; do sleep 20; done
mkdir -p runs/K3b_FT/MatchHero_Female
cp runs/K3_FT/MatchHero_Female/Kit_Top.npz runs/K3_FT/MatchHero_Female/Kit_Shoe_?.npz runs/K3b_FT/MatchHero_Female/
python3 gp/fit.py MatchHero_Female dump:Kit_Bottom runs/K3b_FT --tag Kit_Bottom --keep-weights >> runs/K3b_FT/MatchHero_Female/fit.log 2>&1
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K3b_FT resume > logs/K3b_FT.log 2>&1
echo Q17 DONE > logs/q17.done
