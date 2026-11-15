#!/bin/zsh
# base_suite.sh <hero> <run>: the stress suite on the garments installed in the game today (the dump, no candidates), same poses as the fits.
P=${0:A:h}; cd $P; HERO=$1; RUN=$2; mkdir -p runs/$RUN/suite
BL=($P/../../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender)
for chunk in $(seq 1 150); do
  $BL -b --factory-startup --python gp/suite.py -- $HERO runs/$RUN/suite > logs/${RUN}_suite_$HERO.log 2>&1 && break
  grep -q "SUITE chunk done" logs/${RUN}_suite_$HERO.log || { tail -20 logs/${RUN}_suite_$HERO.log; exit 1; }
done
grep "SUITE $HERO" logs/${RUN}_suite_$HERO.log | cut -c1-300
