#!/bin/zsh
# trousers_proof.sh <tag> [botdir]: full-length front/side/back of the golf trousers on the dumped body (+ refpack top/belt/shoes), next to sheet 11
cd ${0:A:h:h}; T=$1; O=out/GolfKitHero_Male/unity
BOTDIR=${2:-$O} TOPDIR=$O BELTDIR=$O ARGS="w=520 h=900" tools/onbody.sh GolfKitHero_Male $T front:0:2,side:90:2,back:180:2 0,-0.02,.53 1.12 >/dev/null
python3 tools/compose_pairs.py build/${T}_vs11.jpg "$T vs sheet 11 trousers (front / side / back)" \
  11-shorts-trousers-construction:300,670,560,1220=build/${T}_front.png 11-shorts-trousers-construction:900,670,1120,1220=build/${T}_side.png \
  11-shorts-trousers-construction:1440,670,1700,1220=build/${T}_back.png
