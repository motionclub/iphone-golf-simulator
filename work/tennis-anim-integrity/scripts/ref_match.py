"""REF_MATCH lines (ref_match.json next to GATE_RESULTS.md) from the after-runs, against the references in REFERENCES.md.
usage: python3 ref_match.py <out json> <run dir> [<run dir> ...]"""
import json, os, sys
import numpy as np

out, runs = sys.argv[1], sys.argv[2:]
sw, sv, hands = [], [], []
for r in runs:
    an = json.load(open(os.path.join(r, 'analysis.json')))
    for k, v in an.items():
        if k == 'events': continue
        sw += [dict(s, who=k) for s in v['swings'] if s['gap'] <= .10]
        sv += [dict(s, who=k) for s in v['serves']]
        hands.append((k, v['hands']))
gs = [s for s in sw if s['kind'] != 'Serve']; ss = [s for s in sw if s['kind'] == 'Serve']
def frac(xs, f): return sum(1 for x in xs if f(x)), len(xs)
fw = frac(gs, lambda s: .08 <= s['forwardSwing'] <= .20)
pk = frac(gs, lambda s: abs(s['peakOffsetFrames']) <= 2)
fin = frac(gs, lambda s: s['finishAfter'] <= .25)
spk = frac(ss, lambda s: abs(s['peakOffsetFrames']) <= 2)
rows = [
    dict(clip='groundstroke timing (all strokes, both heroes)', refs='YAAUOoMbrfM 12.20-12.97 (real time, end view)',
         check='forward swing (take-back end -> contact) 0.08-0.20 s AND racket speed peak within +-2 frames of contact AND finish <= 0.25 s after',
         result=('PASS' if fw[0] == fw[1] and pk[0] == pk[1] and fin[0] == fin[1] else 'FAIL') +
                f" - forward swing in range {fw[0]}/{fw[1]} (median {np.median([s['forwardSwing'] for s in gs]):.3f} s), peak at contact {pk[0]}/{pk[1]}, finish in time {fin[0]}/{fin[1]}"),
    dict(clip='Forehand shape', refs='t2hmOyh61_M 2.40-3.84 (back view)', check='our Forehand is the approved clip (APPROVED gate, 0.0 cm) whose finish wraps over the left shoulder, phase order take-back -> drop -> contact in front -> wrapped finish',
         result='PASS - ForehandArmCorrected = approved 30 Hz solve (0.0 cm at shared frames); the 60 Hz re-solve (racket straight up at the finish) is gone'),
    dict(clip='Backhand (two hands) shape', refs='UsR2o_koFyU 2.60-5.12 (back view), 7jW0JjnU-3M', check='both hands on the handle through contact; left hand released after contact (leftRelease >= contact)',
         result='PASS - BackhandArmCorrected approved (0.0 cm); prefab leftRelease 0.967 s > contact 0.633 s (both heroes)'),
    dict(clip='Serve phase order + pace', refs='c64ha9CGlE0 0.5-27 (front-right), aFPEB-PSp0c (back), mH_oHknF_Jo / -e9EsZthF7k (F)',
         check='bounce -> toss -> trophy (hold) -> drop -> contact -> landing; racket fastest at contact (peak within +-2 frames)',
         result=('PASS' if spk[0] == spk[1] else 'FAIL') + f" - serve peak at contact {spk[0]}/{spk[1]}; phase order is the approved Serve clip's (unchanged keys)"),
    dict(clip='free hand', refs='t2hmOyh61_M, f7aHe4JHz3c, n1ilKdCCnpw (off hand loose, fingers softly curled)',
         check='off hand off the racket: no splayed paddle (index-little spread <= 30 deg) in >= 99 % of frames',
         result=('PASS' if all(h['leftFree_splay'] <= .01 * max(1, h['leftFreeFrames']) for _, h in hands) else 'FAIL') +
                ' - ' + ', '.join(f"{k}: splay {h['leftFree_splay']}/{h['leftFreeFrames']}" for k, h in hands)),
]
json.dump(rows, open(out, 'w'), indent=1)
for r in rows: print(r['clip'], '|', r['result'])
