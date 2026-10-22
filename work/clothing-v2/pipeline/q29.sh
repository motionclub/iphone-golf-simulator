#!/bin/zsh
# chat 5 queue 29: female K6 cover without rest_poke -> reinstall (maps kept) -> film + COLOURS swatches; after G3 (q27)
cd ${0:A:h}
while [ ! -f logs/G3.done ]; do sleep 20; done
GP_LIMB_ROOT=1 ./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R keep=Kit_Bottom run=K6_FT resume > logs/K6_FT_d.log 2>&1
GP_FOCUS=torso GP_VIEWS=0,90,180,45 GP_STEP=.1 GP_SWATCH_LIST=F4F4F1,1B1C22,D8102E,1F5BFF,2FA84F,FFD200 ./garment_install_batch MatchHero_Female:K6_FT:../out_gp \
  film=Female_Serve,Female_ForehandArmCorrected,Female_BackhandArmCorrected,Female_Emote_Victory,Female_Emote_Slump look=target > logs/q29_install.log 2>&1
echo "Q29 DONE $?" > logs/q29.done
