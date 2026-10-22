#!/bin/zsh
# tests.sh <label> <clone> <EditMode|PlayMode> [filter]: one batch test run through heavy.sh, results in work/integration-1018/tests/<label>
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
OUT=$R/work/integration-1018/tests/$1; mkdir -p $OUT
F=(); [[ -n ${4:-} ]] && F=(-testFilter $4)
CLONE=$2 UNITY_WHAT="chat 12 tests $1 ($3)" UNITY_MINUTES=40 $R/work/integration-1018/tools/unity.sh $OUT/log.txt -runTests -testPlatform $3 $F -testResults $OUT/results.xml
python3 - $OUT/results.xml > $OUT/summary.txt <<'PY'
import sys, xml.etree.ElementTree as E
try: r=E.parse(sys.argv[1]).getroot()
except Exception as e: print("no results", e); sys.exit()
print("result", r.attrib.get('result'), "total", r.attrib.get('total'), "passed", r.attrib.get('passed'), "failed", r.attrib.get('failed'), "skipped", r.attrib.get('skipped'))
for t in r.iter('test-case'):
    if t.get('result') not in ('Passed','Skipped'):
        m=t.find('.//message'); print("FAIL", t.get('fullname'), "|", ((m.text or '').strip().split('\n')[0][:200] if m is not None else ''))
PY
head -3 $OUT/summary.txt
