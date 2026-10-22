"""Run one explicit integrated-app benchmark and collect only its actual evidence."""
import argparse
import csv
import datetime as dt
import json
import math
import pathlib
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--device', required=True)
p.add_argument('--sport', choices=['golf', 'tennis'], required=True)
p.add_argument('--venue', default='resort', choices=['resort', 'skyscraper', 'volcano'])
p.add_argument('--course', default='cliffside', choices=['cliffside', 'postcards', 'wildisles', 'magma'])
p.add_argument('--fps', type=int, choices=[60, 120], default=60)
p.add_argument('--female', action='store_true')
p.add_argument('--postgame', action='store_true')
p.add_argument('--seconds', type=int, default=165)
p.add_argument('--output', type=pathlib.Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
bundle = 'com.aloniewski.GolfArcade'
started = dt.datetime.now(dt.timezone.utc)

def run(name, arguments):
    result = subprocess.run(['xcrun', 'devicectl'] + arguments,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (a.output / (name + '.log')).write_text(result.stdout)
    print(name + ': exit=' + str(result.returncode), flush=True)
    if result.returncode:
        print(result.stdout[-3000:], flush=True)
        raise SystemExit(result.returncode)

flags = ['-benchGolf' if a.sport == 'golf' else '-benchTennis', '--visual-fps', str(a.fps)]
flags += ['--visual-course', a.course] if a.sport == 'golf' else ['--visual-venue', a.venue]
if a.female:
    flags.append('--visual-female')
if a.postgame:
    flags.append('--postgame-check')
run('launch', ['device', 'process', 'launch', '--device', a.device,
               '--terminate-existing', '--json-output', str(a.output / 'launch.json'), bundle] + flags)
for elapsed in range(0, a.seconds, 5):
    time.sleep(min(5, a.seconds - elapsed))
    if (elapsed + 5) % 30 == 0:
        print('Actual device run: ' + str(elapsed + 5) + ' seconds', flush=True)
run('collect', ['device', 'copy', 'from', '--device', a.device,
                '--domain-type', 'appDataContainer', '--domain-identifier', bundle,
                '--source', 'Documents/visual-overhaul', '--destination', str(a.output / 'data'),
                '--json-output', str(a.output / 'collect.json')])

def current(report):
    try:
        timestamp = dt.datetime.fromisoformat(report['startedUtc'].replace('Z', '+00:00'))
        return timestamp >= started - dt.timedelta(seconds=3)
    except (KeyError, ValueError):
        return False

runtime, thermal, postgame = [], [], []
for path in (a.output / 'data').rglob('*.json'):
    try:
        report = json.loads(path.read_text())
    except (ValueError, OSError):
        continue
    if not current(report) or report.get('sport') != a.sport:
        continue
    if 'windows' in report:
        runtime.append({'path': str(path), 'report': report})
    if 'samples' in report:
        thermal.append({'path': str(path), 'report': report})
    if 'matchComplete' in report:
        postgame.append({'path': str(path), 'report': report})
summary = {'startedUtc': started.isoformat(), 'launchArguments': flags,
           'scope': 'Actual integrated phone run; no synthetic clock or substitute render.',
           'runtime': runtime, 'thermal': thermal, 'postgame': postgame, 'failures': []}
if not runtime and not a.postgame:
    summary['failures'].append('No new Unity runtime report from this launch.')
for item in runtime:
    report = item['report']
    if report.get('status') != 'complete' and not a.postgame:
        summary['failures'].append('Unity recording did not complete120seconds.')
    if report.get('initialTargetFps') != a.fps:
        summary['failures'].append('Unity frame-rate target differs from requested launch.')
    requested = a.venue if a.sport == 'tennis' else a.course
    if report.get('venue', '').lower() != requested:
        summary['failures'].append('Actual venue/course differs from requested launch: '+str(report.get('venue')))
    item['actualScreenshots'] = [str(path) for path in pathlib.Path(item['path']).parent.glob('gameplay-*.png')]
    if not a.postgame:
        parent = pathlib.Path(item['path']).parent
        for second in [8, 30, 60, 120]:
            photo = parent / ('gameplay-'+str(second).zfill(3)+'s.png')
            if not photo.is_file() or photo.stat().st_size < 1000:
                summary['failures'].append('Missing actual gameplay screenshot at '+str(second)+'seconds.')
        try:
            with (parent / 'frames.csv').open() as handle:
                intervals = [float(row['elapsed_frame_ms']) for row in csv.DictReader(handle)]
            if not intervals or not all(math.isfinite(value) and value > 0 for value in intervals):
                raise ValueError('Invalid frame interval.')
            item['measuredSeconds'] = sum(intervals) / 1000
            if item['measuredSeconds'] < 119.99:
                summary['failures'].append('Actual CSV frame intervals cover less than120seconds.')
        except (OSError, ValueError, KeyError) as error:
            summary['failures'].append('Actual gameplay CSV is missing or invalid: '+str(error))
if not thermal:
    summary['failures'].append('No new native thermal/process-footprint report.')
for item in thermal:
    report = item['report']
    samples = report.get('samples', [])
    if not samples or any(sample.get('processFootprintBytes', -1) <= 0 for sample in samples):
        summary['failures'].append('Native process-footprint samples are missing or invalid.')
    if not a.postgame and (report.get('status') != 'complete' or max((sample.get('seconds', 0) for sample in samples), default=0) < 150):
        summary['failures'].append('Native thermal evidence did not complete150seconds.')
    if a.postgame:
        item['scope'] = 'Match-finish evidence; thermal span is reported separately, not certified as a sustained150second run.'
if a.postgame:
    if not postgame:
        summary['failures'].append('No actual match-finish evidence from this launch.')
    for item in postgame:
        report = item['report']
        screenshot = pathlib.Path(item['path']).parent / report.get('screenshot', '')
        if not report.get('matchComplete') or not report.get('phoneVisible'):
            summary['failures'].append('Native match completion or visible phone result was not confirmed.')
        if not screenshot.is_file() or screenshot.stat().st_size < 1000:
            summary['failures'].append('Actual native result screenshot is missing.')
        item['actualScreenshot'] = str(screenshot)
summary['status'] = 'EVIDENCE_COLLECTED' if not summary['failures'] else 'FAIL'
(a.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'status': summary['status'], 'runtimeReports': len(runtime),
                  'thermalReports': len(thermal), 'failures': summary['failures']}), flush=True)
raise SystemExit(1 if summary['failures'] else 0)
