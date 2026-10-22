#!/bin/zsh
# chat G: plaza proof stills in ~/unity-clones/menu-hero.  plaza.sh <tag> <golf_bag|racket_back>  -> work/menu-hero/proof/plaza/
REPO=${0:A:h:h:h:h}; C=~/unity-clones/menu-hero; OUT=$REPO/work/menu-hero/proof/plaza; mkdir -p $OUT $REPO/work/menu-hero/logs
for f in Scripts/Hub/HubHeroAnimator.cs Scripts/Hub/HubPlayer.cs Scripts/Hub/HubWorld.cs Scripts/Tennis/HeroAccessories.cs Scripts/Game/NativeSportsSession.cs Scripts/Game/NativeSportsSession.Hub.cs Editor/MatchHeroLockerExport.cs Tests/EditMode/HeroAccessoriesTests.cs; do cp $REPO/Unity/Assets/$f $C/Assets/$f; done
cp $REPO/work/menu-hero/unity/MenuHeroPlazaProof.cs $C/Assets/Tests/PlayMode/
GOLF_MUTE=1 MH_OUT=$OUT MH_TAG=$1 ${2:+MH_BACK=$2} $REPO/work/menu-hero/tools/unity_heavy.sh -batchmode -projectPath $C -runTests -testPlatform PlayMode -testFilter GolfArcade.Tests.MenuHeroPlazaProof -testResults $REPO/work/menu-hero/logs/plaza_$1.xml -logFile $REPO/work/menu-hero/logs/plaza_$1.log
grep -o 'result="[A-Za-z]*"' $REPO/work/menu-hero/logs/plaza_$1.xml | head -3; grep -m5 -E "error CS" $REPO/work/menu-hero/logs/plaza_$1.log
