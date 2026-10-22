#!/bin/zsh
# chat 5 queue 11: A/B for the female top - TODAY's installed tank through the pipeline (same mesh as BEFORE), after q10c
cd ${0:A:h}
while pgrep -f "zsh ./q10c.sh" >/dev/null; do sleep 20; done
./garment_fit MatchHero_Female dump:Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R run=K2_FD resume > logs/K2_FD.log 2>&1
