#!/bin/zsh
# ua_eval.sh <run> [fit.py options...]: polo underarm experiment (11-14). Re-fits ONLY his Kit_Top from today's dump (other pieces + skin cover
# = today's game), then the stress suite on the 33 underarm / overhead / serve poses (runs/ua_subset_male.json). Env GP_* as garment_fit.
P=${0:A:h}; cd $P; RUN=$1; shift; H=MatchHero_Male; RD=runs/$RUN; mkdir -p $RD/$H
HV=$P/../../delegation-2026-10-17/heavy.sh
python3 gp/fit.py $H dump:Kit_Top $RD --tag Kit_Top $@ > logs/${RUN}_fit.log 2>&1 || { tail -5 logs/${RUN}_fit.log; exit 1; }
grep -E "^FIT DONE|correctives:" logs/${RUN}_fit.log
for c in $(seq 1 60); do GP_SUITE_SUBSET=$P/runs/ua_subset_male.json $HV blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python gp/suite.py -- $H $RD/suite --cand $RD > logs/${RUN}_qsuite.log 2>&1 && break; grep -q "SUITE chunk done" logs/${RUN}_qsuite.log || { tail -5 logs/${RUN}_qsuite.log; exit 1; }; done
grep "SUITE $H" logs/${RUN}_qsuite.log | cut -c1-400
