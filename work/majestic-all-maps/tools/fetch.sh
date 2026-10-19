#!/bin/bash
# fetch.sh <out.jpg> <url> : download a generated PNG (curl), save as ≤2560-wide JPG q90.
set -e
T=$(mktemp -t mamref).png; curl -sfL -o "$T" "$2"
python3 -c "
import sys; from PIL import Image
im=Image.open(sys.argv[1]).convert('RGB')
if im.width>2560: im=im.resize((2560,round(im.height*2560/im.width)),Image.LANCZOS)
im.save(sys.argv[2],quality=90); print(sys.argv[2],im.size)" "$T" "$1"; rm -f "$T"
