#!/bin/zsh
# golf male refit with the slim trousers (out/ Kit_Bottom_final.npz) on top of the MG_GM fit: only Kit_Bottom is re-fitted (resume),
# then cover + stress suite. BOT_NPZ=<file> fits another trouser export (control runs). Rollback copy of the previous MG_GM bottom/cover/report: build/MG_GM_before_slim/
ME=${0:A:h:h}; O=$ME/out/GolfKitHero_Male/unity
cd $ME/../clothing-v2/pipeline
rm -f runs/MG_GM/GolfKitHero_Male/Kit_Bottom.npz
export GP_FOOT_ALL=1
export GP_MAX_LIFT=${GP_MAX_LIFT:-.025}           # pipeline default .025; the golf hip needs more in swings (see GATE_RESULTS gate 9)
./garment_fit GolfKitHero_Male npz:${BOT_NPZ:-$O/Kit_Bottom_final.npz}@Kit_Bottom npz:$O/Kit_Top_final.npz@Kit_Top npz:$O/Kit_Belt_final.npz@Kit_Belt \
  npz:$O/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$O/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > $ME/logs/MG_GM_slim.log 2>&1
echo "GM_slim $?" >> $ME/logs/MG.done
