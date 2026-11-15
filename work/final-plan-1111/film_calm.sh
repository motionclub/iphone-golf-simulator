#!/bin/bash
# film_calm.sh: golf landings filmed again in still air (the first film's two runs had different random wind), old code then new.
cd "$(dirname "$0")"
while pgrep -f "hubbay_rerun.sh|golf2_both.sh" > /dev/null; do sleep 20; done
mkdir -p phase1/golf-film/before phase1/golf-film/after
for c in final-plan final-plan-dev; do cp phase1/ZGolfLandingFilm.cs.txt $HOME/unity-clones/$c/Unity/Assets/Tests/PlayMode/ZGolfLandingFilm.cs; done
GOLF_FILM_OUT=$PWD/phase1/golf-film/before ./utest.sh golf-film-before PlayMode "ZGolfLandingFilm" > logs/golf-film-before.out 2>&1
CLONE=final-plan-dev GOLF_FILM_OUT=$PWD/phase1/golf-film/after ./utest.sh golf-film-after PlayMode "ZGolfLandingFilm" > logs/golf-film-after.out 2>&1
echo "FILM DONE"; tail -2 logs/golf-film-before.out logs/golf-film-after.out; cat phase1/golf-film/before/summary.txt phase1/golf-film/after/summary.txt
