#!/bin/zsh
# films (1080p cost with the tracks), lobby bake check, EditMode tests
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$HOME/hand-clearance-work
cd $R
rm -rf $W/film/tennis $W/film/golf
UNITY_WHAT="tennis film 1080p cost + lobby bake check (tracks)" UNITY_MINUTES=20 FILM_BAKE=1 FILM_EMOTES=EmoteDefeat,EmoteShock,EmoteFistPump FILM_OUT=$W/film/tennis work/hand-clearance/tools/unity.sh $W/logs/film_tennis_bf.log -executeMethod GolfArcade.EditorTools.HeroClearanceFilm.Tennis
echo "film tennis $(tail -1 $W/logs/film_tennis_bf.log) $(date +%H:%M)" >> $W/logs/final.progress
UNITY_WHAT="golf film 1080p (tracks)" UNITY_MINUTES=12 FILM_OUT=$W/film/golf work/hand-clearance/tools/unity.sh $W/logs/film_golf_bf.log -executeMethod GolfArcade.EditorTools.HeroClearanceFilm.Golf
echo "film golf $(tail -1 $W/logs/film_golf_bf.log) $(date +%H:%M)" >> $W/logs/final.progress
UNITY_WHAT="EditMode tests clearance" UNITY_MINUTES=10 work/hand-clearance/tools/unity.sh $W/logs/tests_bf.log -runTests -testPlatform EditMode -testResults $W/logs/tests_bf.xml -testFilter "GolfArcade.Tests.HeroClearanceTests|GolfArcade.Tests.AnimationSafetyTests|GolfArcade.Tests.FemaleDeformationTests"
echo "tests $(tail -1 $W/logs/tests_bf.log) $(date +%H:%M)" >> $W/logs/final.progress
