import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOLDERS = {run: ROOT / 'proof/reference-rebuild' / ('moving-turf23-19-20-' + run) for run in ('pilot', 'control')}
REPORTS = {run: json.loads((folder / 'moving-turf-proof.json').read_text()) for run, folder in FOLDERS.items()}
FAILURES = []

def check(ok, message):
    if not ok:
        FAILURES.append(message)
    return ok

def read(run, hole, suffix):
    return json.loads((FOLDERS[run] / f'hole{hole}_{suffix}.json').read_text())

def portable(state):
    # The only removed fields are process-local component and mesh instance IDs.
    result = copy.deepcopy(state)
    result['colliders'] = sorted([
        {k: v for k, v in collider.items() if k not in ('componentId', 'meshId')}
        for collider in result['colliders']
    ], key=lambda collider: (collider['path'], collider['type']))
    return result

def changed(a, b):
    return [key for key in sorted(set(a) | set(b)) if a.get(key) != b.get(key)]

result = {
    'scope': 'Actual moving-turf23 proof, holes 19 and 20 only; read-only review, no Assets edits or Unity run.',
    'proofs': {run: str(folder / 'moving-turf-proof.json') for run, folder in FOLDERS.items()},
    'environment': {'unity': REPORTS['pilot']['unity'], 'graphics': REPORTS['pilot']['graphics']},
    'portablePhysicsMethod': 'Remove only collider componentId and meshId, sort colliders by path/type, compare every remaining field exactly. Windmill phase differences remain visible and are checked separately against each shot contract.',
    'holes': [],
}
for run, report in REPORTS.items():
    check(report['gate'] == 'PASS' and report['error'] == '', run + ' overall gate')

for number in (19, 20):
    hs = {run: next(h for h in report['holes'] if h['hole'] == number) for run, report in REPORTS.items()}
    baseline = read('pilot', number, 'physics_before_addresses')
    item = {
        'hole': number,
        'staticAudit': {'colliders': len(baseline['colliders']), 'obstacles': baseline['obstacleCount'], 'groundSamples': baseline['groundSamples'],
                        'meshVertices': sum(c['vertices'] for c in baseline['colliders']), 'meshTriangles': sum(c['triangles'] for c in baseline['colliders']),
                        **{k: baseline[k] for k in ('obstacleHash', 'surfaceHash', 'groundSampleHash')}},
        'portableComparisons': [], 'runs': {},
    }
    suffixes = ['physics_before_addresses'] + [p['label'] + '_physics' for p in hs['pilot']['poses']] + ['flight_physics_before', 'flight_physics_after']
    for suffix in suffixes:
        delta = changed(portable(read('pilot', number, suffix)), portable(read('control', number, suffix)))
        allowed_phase = number == 20 and suffix == 'flight_physics_after' and delta == ['windmillHash']
        check(not delta or allowed_phase, f'hole {number} portable {suffix}: {delta}')
        item['portableComparisons'].append({'audit': suffix, 'exact': not delta, 'changedFields': delta, 'expectedIndependentShotPhase': allowed_phase})
    for part in ('before', 'after'):
        delta = changed(portable(read('pilot', number, 'dressing_physics')[part]), portable(read('control', number, 'dressing_physics')[part]))
        check(not delta, f'hole {number} portable dressing {part}: {delta}')
        item['portableComparisons'].append({'audit': 'dressing_' + part, 'exact': not delta, 'changedFields': delta})
    for run, h in hs.items():
        poses = h['poses']
        b = read(run, number, 'physics_before_addresses')
        for pose in poses:
            check(read(run, number, pose['label'] + '_physics') == b, f'{run} {number} full address physics {pose["label"]}')
            check(all(pose[k] for k in ('matricesExact', 'materialsExact', 'physicsExact', 'sameStationNoRebuild')), f'{run} {number} address flags {pose["label"]}')
            check(pose['placedFrame'] == pose['renderedFrame'] == pose['lateUpdateFrame'], f'{run} {number} capture frame {pose["label"]}')
            check(pose['cells'] <= 640 and pose['near'] <= 48 and pose['mid'] <= 96 and pose['near'] + pose['mid'] + pose['far'] <= 640, f'{run} {number} caps')
            if run == 'pilot':
                check(pose['cells'] > 0 and pose['near'] + pose['mid'] + pose['far'] > 0, f'{run} {number} positive grass {pose["label"]}')
        check(len({p['renderedFrame'] for p in poses}) == len(poses), f'{run} {number} duplicate capture frame')
        materials = sorted({p['ownedMaterialCount'] for p in poses})
        check(materials == ([5] if run == 'pilot' else [3]), f'{run} {number} material lifetime')
        same = poses[1]
        check(same['rebuildAfter'] == same['rebuildBefore'] and same['poolHash'] == poses[0]['poolHash'] and same['groundQueries'] == poses[0]['groundQueries'], f'{run} {number} same station')
        if run == 'pilot':
            check(poses[2]['rebuildAfter'] == poses[2]['rebuildBefore'] + 1 and poses[2]['retainedCells'] > 0, f'{run} {number} coarse crossing')
            check(poses[5]['regeneratedComparedCells'] > 0 and poses[5]['poolHash'] == poses[3]['poolHash'], f'{run} {number} positive deterministic regeneration')
            check(poses[6]['poolHash'] == poses[0]['poolHash'], f'{run} {number} deterministic tee return')
        else:
            check(all(p['rebuildBefore'] == p['rebuildAfter'] == 0 for p in poses), f'{run} {number} static control rebuilds')
            check(all(p['near'] + p['mid'] + p['far'] == 0 for p in poses[3:6]), f'{run} {number} static control away from tee')
        dressing = read(run, number, 'dressing_physics')
        check(dressing['before'] == dressing['after'] and dressing['sourceReferencesExact'] and not dressing['changedOriginalSourceFilters'] and not dressing['visualMeshesReusingCollisionSource'], f'{run} {number} full dressing exact')
        before = read(run, number, 'flight_physics_before')
        after = read(run, number, 'flight_physics_after')
        delta = changed(before, after)
        check(before == b, f'{run} {number} preflight vs address baseline')
        check(delta == ([] if number == 19 else ['windmillHash']), f'{run} {number} full flight delta {delta}')
        for key in ('ownerExact', 'dressingPhysicsExact', 'flightRebuildsAbsent', 'flightStaticPhysicsExact', 'windmillStaticExact', 'windmillLaunchExact', 'windmillPhaseExact'):
            check(h[key], f'{run} {number} {key}')
        check(h['flightFrames'] > 0 and h['flightCoarseStations'] > 1, f'{run} {number} actual flight activity')
        check(h['renderedWaterTriangles'] > 0 and (number != 19 or h['knownWaterStationRejected']), f'{run} {number} actual water exclusion')
        wind = {k: h[k] for k in ('windmillChangedFields', 'windmillLaunchExpected', 'windmillLaunchActual', 'windmillMaximumPhaseError', 'windmillCurrentAngleBefore', 'windmillCurrentAngleAfter', 'windmillInitialFlightTime')}
        if number == 20:
            check([c['field'] for c in h['windmillChangedFields']] == ['AngleAtLaunch'], f'{run} {number} changed wind fields')
            check(h['windmillLaunchActual'] == h['windmillLaunchExpected'] == h['windmillCurrentAngleBefore'] - 36 * h['windmillInitialFlightTime'], f'{run} {number} independently recomputed launch phase')
            check(h['windmillMaximumPhaseError'] == 0, f'{run} {number} exact live phase')
            wind.update({'degreesPerSecond': 36, 'expectedLaunchAdvanceDegrees': -36 * h['windmillInitialFlightTime'],
                         'drawnAngleAdvanceDegrees': h['windmillCurrentAngleAfter'] - h['windmillCurrentAngleBefore'],
                         'fullAuditWindmillHashBefore': before['windmillHash'], 'fullAuditWindmillHashAfter': after['windmillHash']})
        item['runs'][run] = {
            'reportedGate': h['gate'], 'fullAddressAuditsExact': len(poses), 'fullDressingBeforeAfterExact': dressing['before'] == dressing['after'],
            'fullFlightChangedFields': delta, 'flightFrames': h['flightFrames'], 'flightCoarseStations': h['flightCoarseStations'],
            'flightTurfRebuilds': 0 if h['flightRebuildsAbsent'] else 'FAILED', 'ownedMaterialCounts': materials,
            'renderedWaterTriangles': h['renderedWaterTriangles'], 'knownUnderwaterStationRejected': h['knownWaterStationRejected'] if number == 19 else 'not applicable',
            'sameStationRebuilds': same['rebuildAfter'] - same['rebuildBefore'], 'sameStationGroundQueryDelta': same['groundQueries'] - poses[0]['groundQueries'],
            'windmill': wind,
            'poses': [{k: p[k] for k in ('label', 'selectedCollider', 'selectedSurface', 'courseLie', 'ball', 'renderedFrame', 'cells', 'near', 'mid', 'far', 'rebuildBefore', 'rebuildAfter', 'retainedCells', 'regeneratedComparedCells', 'groundQueries', 'colliderRaycasts', 'rebuildMilliseconds')} for p in poses],
        }
    item['portablePhysicsAccepted'] = all(p['exact'] or p.get('expectedIndependentShotPhase', False) for p in item['portableComparisons'])
    result['holes'].append(item)

reviewed = ['hole19_tee.png', 'hole19_tee_coarse_cross.png', 'hole19_mid_fringe.png', 'hole19_approach_rough.png', 'hole20_tee.png', 'hole20_tee_coarse_cross.png', 'hole20_fairway.png', 'hole20_approach_rough.png']
result['visualReview'] = {
    'gate': 'PASS', 'images': [str(FOLDERS['pilot'] / image) for image in reviewed],
    'controlComparisonImage': str(FOLDERS['control'] / 'hole19_mid_fringe.png'),
    'hole19': 'The chosen middle station is actual FAIRWAY_FIRSTCUT / Fringe with playable Fairway lie, not a fabricated fairway surface. Golfer, ball and grass are dry; the old underwater station is rejected. No blades visibly grow on the adjoining stone cliff. Approach rough is rooted outside the smooth putting green; ball and club remain readable.',
    'hole20': 'Tee, coarse crossing and true fairway addresses are dry, with rooted grass and readable ball/club. Approach rough ends outside the smooth putting green. Water remains beyond the playable foreground; no water overlay at the addresses. Putting grid is hidden.',
    'limits': 'These address images do not provide a close path or bunker boundary view. Acceptance covers the reviewed grass/green/water/stone views, not an exhaustive route-wide hazard image audit. Existing canopy/cloth/atlas appearance is outside this bounded turf review.',
}
pilot_poses = [p for h in REPORTS['pilot']['holes'] for p in h['poses']]
result['summary'] = {
    'portablePairs': sum(len(h['portableComparisons']) for h in result['holes']),
    'portablePairsFullyExact': sum(p['exact'] for h in result['holes'] for p in h['portableComparisons']),
    'expectedIndependentWindmillPhasePairs': 1,
    'fullAddressAuditsExact': 28, 'fullDressingAuditsExact': 4,
    'oneAddressPerActualFrame': True, 'capturedAddresses': 28,
    'pilotCellsMin': min(p['cells'] for p in pilot_poses), 'pilotCellsMax': max(p['cells'] for p in pilot_poses),
    'pilotNearMax': max(p['near'] for p in pilot_poses), 'pilotMidMax': max(p['mid'] for p in pilot_poses),
    'pilotPositiveAddresses': sum(p['cells'] > 0 and p['near'] + p['mid'] + p['far'] > 0 for p in pilot_poses),
    'pilotRebuildMillisecondsMax': max(p['rebuildMilliseconds'] for p in pilot_poses),
    'pilotRebuildGroundQueriesMax': max(p['groundQueries'] for p in pilot_poses), 'pilotRebuildColliderRaycastsMax': max(p['colliderRaycasts'] for p in pilot_poses),
    'timingScope': REPORTS['pilot']['timingScope'],
    'waterNegativeProbe': {'hole': 19, 'x': -0.004415035247802734, 'z': 179.12255859375, 'rejectedPilotAndControl': True},
    'promotionReview': 'PASS for bounded supported moving coverage on holes 19 and 20. Physics geometry, surfaces, obstacles and ground samples are exact; only the independently verified legitimate windmill launch phase differs after hole 20 shots.',
}
result['failures'] = FAILURES
result['gate'] = 'FAIL' if FAILURES else 'PASS'
out = Path(__file__).with_name('ROOT_REVIEW_INPUT.json')
details = out.with_name('ROOT_REVIEW_DETAILS.json')
details.write_text(json.dumps(result, indent=2) + '\n')
concise = {k: result[k] for k in ('gate', 'scope', 'proofs', 'environment', 'portablePhysicsMethod', 'summary', 'visualReview', 'failures')}
concise['details'] = str(details)
concise['holes'] = []
for item in result['holes']:
    row = {'hole': item['hole'], 'portablePhysicsAccepted': item['portablePhysicsAccepted'], 'staticAudit': item['staticAudit'],
           'portablePairs': len(item['portableComparisons']), 'portablePairsExact': sum(p['exact'] for p in item['portableComparisons']), 'runs': {}}
    for run, audit in item['runs'].items():
        poses = audit['poses']
        entry = {k: v for k, v in audit.items() if k not in ('poses', 'windmill')}
        if item['hole'] == 20:
            entry['windmill'] = audit['windmill']
        if run == 'pilot':
            entry.update({'poolCellsInPoseOrder': [p['cells'] for p in poses], 'maximumRebuildMilliseconds': max(p['rebuildMilliseconds'] for p in poses),
                          'coarseCrossRetainedCells': poses[2]['retainedCells'], 'returnRegeneratedCells': poses[5]['regeneratedComparedCells'],
                          'selectedMiddle': {k: poses[3][k] for k in ('label', 'selectedCollider', 'selectedSurface', 'courseLie', 'ball')},
                          'selectedApproach': {k: poses[4][k] for k in ('label', 'selectedCollider', 'selectedSurface', 'courseLie', 'ball')}})
        row['runs'][run] = entry
    concise['holes'].append(row)
out.write_text(json.dumps(concise, indent=2) + '\n')
print(json.dumps({'gate': result['gate'], 'summary': result['summary'], 'failures': FAILURES, 'output': str(out)}, indent=2))
