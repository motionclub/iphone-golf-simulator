#!/bin/zsh
# chat 5 queue 27: golf female G3_GF = today's top mesh refit with an 8 cm sleeve->torso weight transition (+ today's skort/belt weights), after q25 + the Blender part of q26
cd ${0:A:h}
while pgrep -f "zsh ./q25.sh" >/dev/null || ! grep -q "Kit_Top" ../logs/maps-female-top-ao.log 2>/dev/null; do sleep 20; done
./garment_fit GolfKitHero_Female dump:Kit_Bottom dump:Kit_Top dump:Kit_Shoe_L dump:Kit_Shoe_R dump:Kit_Belt keep=Kit_Bottom,Kit_Belt transition=8 run=G3_GF > logs/G3_GF.log 2>&1
echo done > logs/G3.done
