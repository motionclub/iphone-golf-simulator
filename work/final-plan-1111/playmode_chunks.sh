#!/bin/bash
# playmode_chunks.sh <label> [chunk ...]: the PlayMode suite in batches, one fresh Unity per batch (a single run of all 94
# files grew to 16 GB on 2026-11-11 and had to be stopped). A batch whose Unity passes 9 GB is stopped and reported.
# golf2 must not name ClassicConditionsForTests: it is the suite-wide SetUpFixture, and naming it runs every test (that is what ran out of memory twice on 2026-11-11).
# CLONE picks the project copy (default final-plan). Capture/film/probe tools are not tests and are left out (see CAPTURE below).
cd "$(dirname "$0")"
label=$1; shift
chunk() {
  case "$1" in
    tennis1) echo "TennisGameplayTests|TennisPolishPlayTests|TennisTimingBalancePlayTests|TennisSpatialContactPlayTests|TennisAbilitiesPlayTests" ;;
    tennis2) echo "TennisGameplayImprovementPlayTests|TennisMatchStatsTests|TennisReceiveCameraTests|TennisTutorialPlayTests|TennisVenueTests|ReceivingRegressionTests|ControllerTimingRegressionTests|LocalVersusTests|NativeTennisSetupTests" ;;
    heroes) echo "AnimationContactPresentationTests|StandardCharacterGameplayTests|MatchHeroClipMapTests|HeroGarmentRuntimeOrderTests|NativeLaunchHeroTests|PlayerBaseTests|HeroGolferTests|GolferClipTests|GolferFacingTests|GolferSelectTests" ;;
    golf1) echo "GolfAnimationFlowTests|GolfBroadcastTests|GolfCourseStandardPlayTests|GolfLessonPlayTests|GolfMotionReadyTests|GolfPolishTests|GolfPresentationTests|HoleFlowTests|NativeGolfFlowTests" ;;
    golf2) echo "NewHolesPlayTests|PlaythroughTests|RoundEventsPlayTests|RoundSmokeTests|SolidPropsPlayTests|SwingSmoothnessTests|ReplayTests|ArcadeCardsTests" ;;
    golf3) echo "MagmaOpenTests|WildIslesPlayTests|DreamGolfPilotTests|DreamRuntimeTests|IntroRulesPlayTests|PresentationFlowTests|CourseReviewTests" ;;
    hub) echo "BigScreenFlowTests|ErrorHandlingTests|ExperienceFlowTests|FrameRate60bTests|HomeScreenTests|HubBayTests|HubPartyTests|HubPhoneOnlyTests|HubPlazaTests|MenuArrowFocusTests|MenuPointerTests|MultiplayerRuntimeTests|NativeSessionTests" ;;
  esac
}
ORDER="tennis1 tennis2 heroes golf1 golf2 golf3 hub"
[ $# -gt 0 ] && ORDER="$*"
# CAPTURE (not run): BowlingFilmTests BrollCaptureTests DemoVideoTests GolfReadCaptureTests HubPreviewCapture IntroCaptureTests IntroReviewFilm
#   MenuHeroCapture MenuSetupCapture MultiplayerExploreCapture PresentationFilmTests RenderedBackgroundsHubProof ReviewCaptureTests
#   Score80CaptureTests Score80ClipProbeTests Score80EnvAuditTests SolidPropsFilmTests TennisCameraOptionsCaptureTests
#   TennisChaseCameraProofTests TennisFullMatchCaptureTests TennisMultiAngleCaptureTests TennisOverheadProbeTests
#   TennisReferenceCaptureTests TennisSinglePointCaptureTests TennisStanceCaptureTests TennisTempoCaptureTests TennisVenueFilmTests
#   VersusPeerCapture HitchProbe TennisLobCinematicTests TennisMotionReferenceTests
C=$HOME/unity-clones/${CLONE:-final-plan}/Unity
sum=logs/$label-summary.txt; : > $sum
for c in $ORDER; do
  ( ./utest.sh "$label-$c" PlayMode "$(chunk $c)" > "logs/$label-$c.out" 2>&1 ) &
  job=$!
  while kill -0 $job 2>/dev/null; do
    sleep 15
    pid=$(pgrep -f "Unity -projectPath $C " | head -1)
    [ -z "$pid" ] && continue
    mb=$(top -l 1 -pid $pid -stats mem | tail -1 | awk '{m=$1; if (m ~ /G/) {sub("G","",m); print int(m*1024)} else {sub("M","",m); print int(m)}}')
    if [ "${mb:-0}" -gt 9216 ]; then echo "$c: STOPPED at ${mb} MB" >> $sum; kill $pid; fi
  done
  echo "== $c" >> $sum; cat "logs/$label-$c.out" >> $sum
done
echo "CHUNKS DONE" >> $sum
