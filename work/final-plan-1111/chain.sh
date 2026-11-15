#!/bin/bash
# chain.sh: the rest of the Phase 0 / Phase 1 runs, strictly one Unity at a time (two at once took the disk to 14 GB free through swap).
#   1. wait for the baseline PlayMode batches (playmode_chunks.sh pm-base, already running)
#   2. PlayMode batches on the changed code (dev copy), intro-rule tests included (golf3)
#   3. frame times per scene on the quiet Mac editor, baseline copy then changed copy
#   4. golf landings filmed in the real game, old code then new
cd "$(dirname "$0")"
while pgrep -f "playmode_chunks.sh pm-base" > /dev/null; do sleep 30; done
CLONE=final-plan-dev ./sync.sh > logs/chain-sync.out 2>&1
CLONE=final-plan-dev bash playmode_chunks.sh pm-new tennis1 tennis2 golf3 golf1 golf2 heroes hub
mkdir -p phase0/frames-base phase0/frames-new phase1/golf-film/before phase1/golf-film/after
FR60B_DIR=$PWD/phase0/frames-base ./utest.sh frames-base PlayMode "FrameRate60bTests.RuntimeHoldsSixty" > logs/frames-base.out 2>&1
CLONE=final-plan-dev FR60B_DIR=$PWD/phase0/frames-new ./utest.sh frames-new PlayMode "FrameRate60bTests.RuntimeHoldsSixty" > logs/frames-new.out 2>&1
for c in final-plan final-plan-dev; do cp phase1/ZGolfLandingFilm.cs.txt $HOME/unity-clones/$c/Unity/Assets/Tests/PlayMode/ZGolfLandingFilm.cs; done
GOLF_FILM_OUT=$PWD/phase1/golf-film/before ./utest.sh golf-film-before PlayMode "ZGolfLandingFilm" > logs/golf-film-before.out 2>&1
CLONE=final-plan-dev GOLF_FILM_OUT=$PWD/phase1/golf-film/after ./utest.sh golf-film-after PlayMode "ZGolfLandingFilm" > logs/golf-film-after.out 2>&1
echo "CHAIN DONE"; tail -3 logs/frames-base.out logs/frames-new.out logs/golf-film-before.out logs/golf-film-after.out
