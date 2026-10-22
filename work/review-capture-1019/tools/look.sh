#!/bin/zsh
# look.sh <name> : wait, screenshot the review simulator to stills/menu/<name>.png and a small preview in the scratchpad
D=${0:A:h:h}; sleep ${WAIT:-1.5}; $D/tools/snap.sh $1 >/dev/null
python3 -c "
from PIL import Image; im=Image.open('$D/stills/menu/$1.png'); im.thumbnail((300,650)); im.save('$SCR/now.png')"
echo $1
