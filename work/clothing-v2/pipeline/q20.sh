#!/bin/zsh
# chat 5 queue 20 (10-18): female tennis rips A/B, ONE Blender job at a time via heavy.sh
#   K4_FT  : no limb-root remap (cloth keeps the shoulder-blade skin's arm weight) + 2 mm seam weld + wrap-based limb filter + today's skirt
#   K4r_FT : same with the limb-root remap
cd ${0:A:h}
SRC=(npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R keep=Kit_Bottom)
GP_LIMB_ROOT=0 ./garment_fit MatchHero_Female $SRC run=K4_FT > logs/K4_FT.log 2>&1
GP_LIMB_ROOT=1 ./garment_fit MatchHero_Female $SRC run=K4r_FT > logs/K4r_FT.log 2>&1
echo Q20 DONE > logs/q20.done
