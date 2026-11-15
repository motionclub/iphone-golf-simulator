#!/bin/bash
# sweep_legs.sh "LEGS READ" ...: the placement balance (TennisFunTests) for each rival-legs setting, on the dev project copy.
cd "$(dirname "$0")/.."
for lr in "$@"; do
  set -- $lr
  echo "== LEGS=$1 READ=$2"
  CLONE=final-plan-dev TENNIS_LEGS=$1 TENNIS_READ=$2 ./utest.sh sweep EditMode "TennisFunTests" 2>&1 | sed -n 2p
  ./testout.py logs/sweep.xml PlacementBeats | grep ": corner"
done
