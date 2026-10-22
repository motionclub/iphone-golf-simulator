#!/bin/zsh
# Chat 12, 4th heavy slot: second-pass items that do not need the clearance bake, on a snapshot of the combined clone (~/integration-work/Unity3,
# + the golf swing fix). Two launches (a test run cannot share a launch with an editor method): golf rain re-film + the golf swing chat's 4
# PlayMode suites, then the tennis weather slots.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; I=$R/work/integration-1018; C=$HOME/integration-work/Unity3
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
P=$I/logs/side_lane.progress; mark() { echo "$(date +%H:%M) $*" >> $P; }
mark start
O=$I/tests/side_play; mkdir -p $O $I/smoke
SMOKE_OUT=$I/smoke SMOKE_ONLY=golf GOLF_MUTE=1 $H unity $U -projectPath $C -runTests -testPlatform PlayMode \
  -testFilter "GolfArcade.PlayTests.IntegrationSmokeFilm;GolfArcade.PlayTests.SwingSmoothnessTests;GolfArcade.PlayTests.GolfMotionReadyTests;GolfArcade.PlayTests.HeroGolferTests;GolfArcade.PlayTests.NativeGolfFlowTests" \
  -testResults $O/results.xml -logFile $O/log.txt
mark "golf smoke + golf suites rc=$?"
python3 - $O/results.xml > $O/summary.txt <<'PY'
import sys, xml.etree.ElementTree as E
try: r=E.parse(sys.argv[1]).getroot()
except Exception as e: print("no results", e); sys.exit()
print("result", r.attrib.get('result'), "total", r.attrib.get('total'), "passed", r.attrib.get('passed'), "failed", r.attrib.get('failed'), "skipped", r.attrib.get('skipped'))
for t in r.iter('test-case'):
    if t.get('result') not in ('Passed','Skipped'):
        m=t.find('.//message'); print("FAIL", t.get('fullname'), "|", ((m.text or '').strip().split('\n')[0][:200] if m is not None else ''))
PY
O=$I/weather_tennis; mkdir -p $O; MW_OUT=$O MW_JOBS=refs,read MW_SLOTS=W12,W14 MW_ORIG_DIR=$R/work/majestic-weather/proof/orig GOLF_MUTE=1 $H unity $U -projectPath $C -executeMethod GolfArcade.EditorTools.MajesticWeatherShots.Run -logFile $O/unity.log
mark "weather tennis rc=$?"
mark done
