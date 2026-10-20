#!/bin/bash
# usage: cmp_all.sh <tag> [tag2 ...]  -> tmp/<kind>_<tags>.png comparison sheets (plate | start | tags)
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin
unset PYTHONPATH
N=$(IFS=_; echo "$*")
args_locked() { local v=$1; local out=""; for t in start "$@"; do :; done; }
A=""; for t in "$@"; do A="$A $t"; done
mk() { # kind plate box scale view@rp [direct]
  local kind=$1 plate=$2 box=$3 sc=$4 view=$5 direct=$6; shift 6
  local panels=("start=r/start/$view"); for t in "$@"; do panels+=("$t=r/$t/$view"); done
  python3 cmpv.py tmp/${kind}_$N.png $plate $box $sc "${panels[@]}" $direct --boost 1.5 ${GRID:+--grid $GRID} | tail -1
}
GRID=bald_back mk glute_back bald 815,265,1015,410 3 back@4 "" "$@"
GRID=left mk glute_left sheet 745,130,845,250 5 left@4 "" "$@"
GRID= mk glute_q3bl sheet 730,480,860,620 5 reg_q3BL_730_860_480_620_8 --direct "$@"
GRID= mk glute_q3br sheet 1010,480,1140,620 5 reg_q3BR_1010_1140_480_620_8 --direct "$@"
GRID= mk groin_q3fl sheet 125,440,245,560 5 reg_q3FL_125_245_440_560_9 --direct "$@"
GRID= mk groin_q3fr sheet 420,440,540,560 5 reg_q3FR_420_540_440_560_9 --direct "$@"
GRID=bald_front mk groin_front bald 253,265,453,410 3 front@4 "" "$@"
GRID=bald_back mk nape_back bald 815,100,1015,240 3 back@4 "" "$@"
GRID= mk nape_q3bl sheet 745,372,855,452 6 reg_q3BL_745_855_372_452_10 --direct "$@"
GRID= mk nape_q3br sheet 1030,372,1140,452 6 reg_q3BR_1030_1140_372_452_10 --direct "$@"
