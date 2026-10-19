#!/bin/zsh
# chat 5 queue 18: golf female K3_GF = today's weights for top/skort/belt (they beat the transfer there) + pipeline correctives + cover + suite
cd ${0:A:h}
./garment_fit GolfKitHero_Female dump:Kit_Bottom dump:Kit_Top dump:Kit_Shoe_L dump:Kit_Shoe_R dump:Kit_Belt keep=Kit_Top,Kit_Bottom,Kit_Belt run=K3_GF > logs/K3_GF.log 2>&1
echo Q18 DONE > logs/q18.done
