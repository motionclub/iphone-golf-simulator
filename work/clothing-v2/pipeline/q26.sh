#!/bin/zsh
# chat 5 queue 26 (10-18): female top AO smudge + rest-poke cover -> re-bake maps -> ONE Unity session: install, film, COLOURS swatches
cd ${0:A:h}
while pgrep -f "zsh ./q25.sh" >/dev/null || [ ! -f logs/G1.done ]; do sleep 20; done
GP_LIMB_ROOT=1 ./garment_fit MatchHero_Female npz:../out_gp/MatchHero_Female/unity/Kit_Top_final.npz@Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R keep=Kit_Bottom run=K6_FT resume > logs/K6_FT_c.log 2>&1
python3 - <<'PY'
import sys, numpy as np; sys.path.insert(0, 'gp')
import rig, scene
h = rig.Hero('MatchHero_Female'); items = scene.items_from_dump(h); body = items[0]
z = np.load('runs/K6_FT/MatchHero_Female/body.npz'); hid_t = ~z['drawn']; bits = z['bits'].astype(np.int64)
out = {}
for k, it in enumerate(items):
    if not it.tag.startswith('Kit_'): continue
    m = np.zeros(body.n, bool); m[body.tri[hid_t & (((bits >> k) & 1) == 1)].ravel()] = True; out[it.tag] = m
np.savez('../out_gp/MatchHero_Female/unity/cover.npz', **out); print('cover.npz', {k: int(v.sum()) for k, v in out.items()})
PY
cd .. && CV2_OUT=$PWD/out_gp CV2_PIECES=Kit_Top ${GP_HEAVY:-$PWD/../delegation-2026-10-17/heavy.sh} blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python py/maps.py -- MatchHero_Female > logs/maps-female-top-ao.log 2>&1; grep -E "Kit_Top|Traceback" logs/maps-female-top-ao.log | head -3
cd pipeline && GP_FOCUS=torso GP_VIEWS=0,90,180,45 GP_STEP=.1 GP_SWATCH_LIST=F4F4F1,1B1C22,D8102E,1F5BFF,2FA84F,FFD200 ./garment_install_batch MatchHero_Female:K6_FT:../out_gp \
  film=Female_Serve,Female_ForehandArmCorrected,Female_BackhandArmCorrected,Female_Emote_Victory,Female_Emote_Slump look=target > logs/q26_install.log 2>&1
echo "Q26 DONE $?" > logs/q26.done
