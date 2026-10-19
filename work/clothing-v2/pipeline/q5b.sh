#!/bin/zsh
# chat 5 queue 5: after q4, ONE Unity session (heavy.sh) installs all four fitted kits into ~/garments-UnityClone + perf at 1080p + 1080p film
cd ${0:A:h}
while pgrep -f "zsh ./q4b.sh" >/dev/null; do sleep 30; done
GP_STEP=.2 ./garment_install_batch MatchHero_Male:K2_MT:../out_gp3 MatchHero_Female:K2_FT:../out_gp GolfKitHero_Male:K2_GM:../out_gp3 GolfKitHero_Female:K2_GF \
  film=Emote_Thrust,Intro_Pushups,Serve,Drive,Emote_Shock look=target > logs/q5b_install.log 2>&1
echo "Q5 DONE $?" > logs/q5b.done
