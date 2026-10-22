#!/bin/zsh
# chat 5 queue 16 (after the 20:55 OOM; ONE Blender job at a time, single hero per run, via heavy.sh)
cd ${0:A:h}
NEW=$PWD/../out_gp/new_ls/MatchHero_Male/unity/Kit_Top_final.npz
T0=$(date +%s)
./garment_fit MatchHero_Male npz:$NEW@Kit_Top run=new_ls resume > logs/new_ls_resume.log 2>&1
echo "RESUME cover+suite wall $(( $(date +%s) - T0 )) s ($(date +%H:%M:%S))" >> logs/new_ls.time
./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K3_FT > logs/K3_FT.log 2>&1
./garment_fit MatchHero_Female dump:Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K2_FD > logs/K2_FD.log 2>&1
echo Q16 DONE > logs/q16.done
