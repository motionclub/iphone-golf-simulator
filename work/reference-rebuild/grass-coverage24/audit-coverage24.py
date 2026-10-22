"""Read-only reproducible review of the two completed Unity coverage24 proofs.
Run from any directory: python3 /absolute/path/to/audit-coverage24.py
Only writes review JSON in this script's work directory; never launches Unity.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
NUMBERS = (10, 16, 17, 18, 21, 22, 23)
FOLDERS = {r: ROOT / 'proof/reference-rebuild' / ('grass-coverage24-' + r) for r in ('pilot', 'control')}
REPORTS = {r: json.loads((p / 'moving-turf-proof.json').read_text()) for r, p in FOLDERS.items()}
FAILURES = []

def check(ok, message):
    if not ok:
        FAILURES.append(message)
    return bool(ok)

def read(run, number, suffix):
    return json.loads((FOLDERS[run] / f'hole{number:02}_{suffix}.json').read_text())

def portable(state):
    result = copy.deepcopy(state)
    # Only process-local IDs are removed. Every physical hash, count, flag and
    # sample is compared, including windmillHash. No float tolerances are used.
    result['colliders'] = sorted([
        {k: v for k, v in c.items() if k not in ('componentId', 'meshId')}
        for c in result['colliders']], key=lambda c: (c['path'], c['type']))
    return result

def changed(a, b):
    return [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]

result = {'scope': 'Completed grass-coverage24 pilot/control proofs for seven new opt-in authored routes; no Unity run or Assets edits.',
          'portablePhysicsMethod': 'Remove only collider componentId and meshId, sort colliders by path/type, compare every remaining field exactly, including windmillHash.',
          'proofs': {r: str(p / 'moving-turf-proof.json') for r, p in FOLDERS.items()},
          'proofSha256': {r: hashlib.sha256((p / 'moving-turf-proof.json').read_bytes()).hexdigest() for r, p in FOLDERS.items()},
          'environment': {k: REPORTS['pilot'][k] for k in ('unity', 'graphics', 'timingScope')}, 'holes': []}
for run, report in REPORTS.items():
    check(report['gate'] == 'PASS' and not report['error'], run + ' overall gate')
    check([h['hole'] for h in report['holes']] == list(NUMBERS), run + ' exact course scope')
    frames = [p['renderedFrame'] for h in report['holes'] for p in h['poses']]
    check(len(frames) == len(set(frames)) == 49, run + ' 49 distinct capture frames')

for number in NUMBERS:
    hs = {r: next(h for h in v['holes'] if h['hole'] == number) for r, v in REPORTS.items()}
    baseline = read('pilot', number, 'physics_before_addresses')
    item = {'hole': number, 'staticAudit': {'colliders': len(baseline['colliders']), 'obstacles': baseline['obstacleCount'], 'groundSamples': baseline['groundSamples'],
            **{k: baseline[k] for k in ('obstacleHash', 'surfaceHash', 'groundSampleHash', 'windmillHash')}}, 'portableComparisons': [], 'runs': {}}
    suffixes = ['physics_before_addresses'] + [p['label'] + '_physics' for p in hs['pilot']['poses']] + ['flight_physics_before', 'flight_physics_after']
    for suffix in suffixes:
        delta = changed(portable(read('pilot', number, suffix)), portable(read('control', number, suffix)))
        check(not delta, f'{number} portable {suffix}: {delta}')
        item['portableComparisons'].append({'audit': suffix, 'exact': not delta, 'changedFields': delta})
    for part in ('before', 'after'):
        delta = changed(portable(read('pilot', number, 'dressing_physics')[part]), portable(read('control', number, 'dressing_physics')[part]))
        check(not delta, f'{number} portable dressing {part}: {delta}')
        item['portableComparisons'].append({'audit': 'dressing_' + part, 'exact': not delta, 'changedFields': delta})
    for pp, cp in zip(hs['pilot']['poses'], hs['control']['poses']):
        for k in ('label', 'selectedCollider', 'selectedSurface', 'courseLie', 'ball', 'requestedPoint', 'selectionDistanceMeters', 'clearanceMeters'):
            check(pp[k] == cp[k], f'{number} identical pilot/control selection {pp["label"]} {k}')
    for run, h in hs.items():
        poses = h['poses']; b = read(run, number, 'physics_before_addresses')
        check(len(poses) == 7, f'{run} {number} 7 poses')
        for p in poses:
            check(read(run, number, p['label'] + '_physics') == b, f'{run} {number} full address exact {p["label"]}')
            check(p['physicsGate'] == 'PASS' and all(p[k] for k in ('matricesExact', 'materialsExact', 'physicsExact', 'sameStationNoRebuild')), f'{run} {number} pose flags {p["label"]}')
            check(p['placedFrame'] == p['renderedFrame'] == p['lateUpdateFrame'], f'{run} {number} production LateUpdate frame {p["label"]}')
            check(p['cells'] <= 640 and p['near'] <= 48 and p['mid'] <= 96 and p['near'] + p['mid'] + p['far'] <= 640, f'{run} {number} pool/draw caps')
            check(p['courseLie'] not in ('Water', 'Ice', 'Sand'), f'{run} {number} dry grass selected')
            if run == 'pilot':
                check(p['cells'] > 0 and p['near'] + p['mid'] + p['far'] > 0, f'{run} {number} positive grass {p["label"]}')
        materials = sorted({p['ownedMaterialCount'] for p in poses})
        expected_materials = 5 if number == 10 else (4 if run == 'pilot' else 2)
        check(materials == [expected_materials], f'{run} {number} stable material lifetime')
        same = poses[1]
        check(same['rebuildAfter'] == same['rebuildBefore'] and same['poolHash'] == poses[0]['poolHash'] and same['groundQueries'] == poses[0]['groundQueries'], f'{run} {number} no same-station rebuild/queries')
        if run == 'pilot':
            check(poses[2]['rebuildAfter'] == poses[2]['rebuildBefore'] + 1 and poses[2]['retainedCells'] > 0, f'{run} {number} coarse retained cells')
            check(poses[5]['regeneratedComparedCells'] > 0 and poses[5]['poolHash'] == poses[3]['poolHash'], f'{run} {number} positive deterministic regeneration')
            check(poses[6]['poolHash'] == poses[0]['poolHash'], f'{run} {number} deterministic tee return')
        else:
            check(all(p['rebuildBefore'] == p['rebuildAfter'] == 0 for p in poses), f'{run} {number} static no rebuilds')
            check(all(p['near'] + p['mid'] + p['far'] == 0 for p in poses[3:6]), f'{run} {number} static no distant turf')
        d = read(run, number, 'dressing_physics')
        flags = ('colliderCountExact', 'collidersExact', 'obstaclesExact', 'surfaceExact', 'groundSamplesExact', 'sourceReferencesExact', 'collisionMeshesReadable', 'windmillExact')
        check(d['before'] == d['after'] and all(d[k] for k in flags) and not d['changedOriginalSourceFilters'] and not d['visualMeshesReusingCollisionSource'], f'{run} {number} exact dressing/source references')
        before = read(run, number, 'flight_physics_before'); after = read(run, number, 'flight_physics_after')
        check(before == b and before == after, f'{run} {number} exact full flight including windmill')
        for k in ('ownerExact', 'dressingPhysicsExact', 'flightRebuildsAbsent', 'flightStaticPhysicsExact', 'windmillStaticExact', 'windmillLaunchExact', 'windmillPhaseExact'):
            check(h[k], f'{run} {number} {k}')
        check(not h['windmillChangedFields'] and h['windmillMaximumPhaseError'] == 0, f'{run} {number} no windmill delta')
        check(h['gate'] == 'PASS' and h['flightFrames'] > 0 and h['flightCoarseStations'] > 1, f'{run} {number} actual flight')
        check(h['renderedWaterTriangles'] > 0, f'{run} {number} actual water/lava visual sheet')
        item['runs'][run] = {'fullAddressAuditsExact': len(poses), 'fullDressingBeforeAfterExact': d['before'] == d['after'], 'fullFlightChangedFields': changed(before, after),
            'flightFrames': h['flightFrames'], 'flightCoarseStations': h['flightCoarseStations'], 'flightTurfRebuilds': 0 if h['flightRebuildsAbsent'] else 'FAIL',
            'ownedMaterialCounts': materials, 'renderedWaterOrLavaTriangles': h['renderedWaterTriangles'], 'sameStationRebuilds': same['rebuildAfter'] - same['rebuildBefore'],
            'sameStationGroundQueryDelta': same['groundQueries'] - poses[0]['groundQueries'], 'coarseCrossRetainedCells': poses[2]['retainedCells'],
            'returnRegeneratedCells': poses[5]['regeneratedComparedCells'], 'maximumRebuildMilliseconds': max(p['rebuildMilliseconds'] for p in poses),
            'poses': [{k: p[k] for k in ('label', 'selectedCollider', 'selectedSurface', 'courseLie', 'ball', 'renderedFrame', 'cells', 'near', 'mid', 'far', 'rebuildBefore', 'rebuildAfter', 'retainedCells', 'regeneratedComparedCells', 'groundQueries', 'colliderRaycasts', 'rebuildMilliseconds')} for p in poses]}
    item['portablePhysicsAccepted'] = all(p['exact'] for p in item['portableComparisons'])
    result['holes'].append(item)

pilot_poses = [p for h in REPORTS['pilot']['holes'] for p in h['poses']]
maximum = max(pilot_poses, key=lambda p: p['rebuildMilliseconds'])
result['summary'] = {'portablePairs': sum(len(h['portableComparisons']) for h in result['holes']),
    'portablePairsFullyExact': sum(p['exact'] for h in result['holes'] for p in h['portableComparisons']), 'fullAddressAuditsExact': 98,
    'fullDressingAuditsExact': 14, 'fullFlightAuditsExact': 14, 'pilotAddressRecords': 49, 'controlAddressRecords': 49,
    'pilotPositiveAddresses': sum(p['cells'] > 0 and p['near'] + p['mid'] + p['far'] > 0 for p in pilot_poses),
    'pilotCellsMin': min(p['cells'] for p in pilot_poses), 'pilotCellsMax': max(p['cells'] for p in pilot_poses),
    'pilotNearMax': max(p['near'] for p in pilot_poses), 'pilotMidMax': max(p['mid'] for p in pilot_poses), 'pilotFarMax': max(p['far'] for p in pilot_poses),
    'pilotRebuildMillisecondsMax': maximum['rebuildMilliseconds'], 'maximumLatencyAddress': {'hole': maximum['hole'], 'label': maximum['label'], 'selectedCollider': maximum['selectedCollider']},
    'pilotRebuildGroundQueriesMax': max(p['groundQueries'] for p in pilot_poses), 'pilotRebuildColliderRaycastsMax': max(p['colliderRaycasts'] for p in pilot_poses),
    'pilotFlightFrames': sum(h['flightFrames'] for h in REPORTS['pilot']['holes']), 'pilotFlightCoarseStations': sum(h['flightCoarseStations'] for h in REPORTS['pilot']['holes']),
    'controlFlightFrames': sum(h['flightFrames'] for h in REPORTS['control']['holes']), 'controlFlightCoarseStations': sum(h['flightCoarseStations'] for h in REPORTS['control']['holes']),
    'flightRebuilds': 0, 'positiveRegenerationRoutes': 7, 'sameStationGroundQueryDelta': 0,
    'existingMovingRoutes': [7,8,9,12,13,14,15,19,20], 'existingRoutesRetested': False}
result['numericalGate'] = 'FAIL' if FAILURES else 'PASS'
result['failures'] = FAILURES
visual_path = OUT / 'actual-visual-review.json'
result['visualReview'] = json.loads(visual_path.read_text())
result['gate'] = 'FAIL' if FAILURES else result['visualReview']['gate']
result['limitations'] = ['Stopwatch desktop rebuild latency excludes capture/audit overhead; no phone FPS or device thermal claim.',
    'Seven actual settled addresses per route and one flight; not an exhaustive every-coordinate terrain sweep.',
    'Rendered water/lava sheets participate in address exclusion, but this run includes no deliberate negative water/lava address probe.',
    'Hole 18 middle and approach labels are generic harness station labels: both actual GREEN_APRON_1 / source Fairway; approach CourseLie is Rough. No authored true fairway exists on 18.',
    'Review covers turf only. Trees, clothing and background appearance are outside this lane.',
    'Existing accepted nine moving routes were not rerun; candidate route flags remain bounded to the seven new routes.']
(OUT / 'ROOT_REVIEW_DETAILS.json').write_text(json.dumps(result, indent=2) + '\n')
concise = {k: v for k, v in result.items() if k != 'holes'}
concise['details'] = str(OUT / 'ROOT_REVIEW_DETAILS.json')
concise['holes'] = []
for h in result['holes']:
    p = h['runs']['pilot']; c = h['runs']['control']
    concise['holes'].append({'hole': h['hole'], 'portablePairsExact': sum(a['exact'] for a in h['portableComparisons']), 'staticAudit': h['staticAudit'],
        'pilotCellsInPoseOrder': [a['cells'] for a in p['poses']], 'coarseCrossRetainedCells': p['coarseCrossRetainedCells'], 'returnRegeneratedCells': p['returnRegeneratedCells'],
        'maximumRebuildMilliseconds': p['maximumRebuildMilliseconds'], 'pilotOwnedMaterials': p['ownedMaterialCounts'], 'controlOwnedMaterials': c['ownedMaterialCounts'],
        'middle': {k: p['poses'][3][k] for k in ('label','selectedCollider','selectedSurface','courseLie','ball')},
        'approach': {k: p['poses'][4][k] for k in ('label','selectedCollider','selectedSurface','courseLie','ball')}})
(OUT / 'ROOT_REVIEW_INPUT.json').write_text(json.dumps(concise, indent=2) + '\n')
print(json.dumps({'gate': result['gate'], 'numericalGate': result['numericalGate'], 'summary': result['summary'], 'failures': FAILURES}, indent=2))
raise SystemExit(1 if FAILURES else 0)
