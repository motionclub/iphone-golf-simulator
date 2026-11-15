#!/bin/bash
# film.sh: the tennis apex frames and arcs, new ball then the 10-26 ball, on the dev project copy.
cd "$(dirname "$0")/.."
CLONE=final-plan-dev TENNIS_FILM_OUT=$PWD/phase1/film/flat ./utest.sh film-flat PlayMode "ZTennisFlightFilm" 2>&1 | sed -n 1,4p
CLONE=final-plan-dev TENNIS_CLASSIC=1 TENNIS_FILM_OUT=$PWD/phase1/film/classic ./utest.sh film-classic PlayMode "ZTennisFlightFilm" 2>&1 | sed -n 1,4p
ls phase1/film/flat phase1/film/classic
