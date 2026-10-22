#!/bin/zsh
# chat 5 queue 8 (10-17 19:00 push, shoes first; ONE heavy job at a time via heavy.sh)
cd ${0:A:h}
GP_FOCUS=feet GP_STEP=.15 ./garment_install_batch MatchHero_Male:K2_MT:../out_gp3 GolfKitHero_Male:K2_GM:../out_gp3 film=Serve,Run,ForehandOpen,Drive look=target > logs/q10_shoes_install.log 2>&1
echo "SHOES DONE $?" > logs/q10_shoes.done
