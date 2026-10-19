#!/bin/zsh
# build_all.sh [male|female]... : pristine copy of the source blend -> generate the five clips (numpy) -> bake -> verify.  Idempotent.
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
tags=("$@"); [ ${#tags[@]} -eq 0 ] && tags=(male female)
one() {
  tag=$1; H=$( [ $tag = male ] && echo Male || echo Female )
  cp ../match-anim-set/export/HeroBase_${H}_MatchAnims.blend export/HeroBase_${H}_MatchAnims.blend
  for c in walk runf runr runl; do $BP scripts/run_gait.py $c $tag > logs/gen_${c}_${tag}.log 2>&1; done
  $BP scripts/run_serve.py $tag > logs/gen_serve_${tag}.log 2>&1
  $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/bake_loco.py -- $tag Walk=walk RunForward=runf RunRight=runr RunLeft=runl Serve=serve > logs/bake_${tag}.log 2>&1
  $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/verify_blend.py -- $tag > logs/verify_${tag}.log 2>&1 || true
  echo "== $tag"; grep -E "VERIFY_FAIL|VERIFY_DONE|Error|Traceback" logs/verify_${tag}.log || true
}
for t in $tags; do one $t & done
wait
