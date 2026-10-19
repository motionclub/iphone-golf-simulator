"""Chat 4: per-clip checks on a TennisAnimClipDump folder.
usage: python3 clipcheck.py <dump dir> [--json out]
RATE (key spacing), APPROVED (hands / strings / racket tip vs the approved 30 Hz clip at shared 1/30 s frames), racket speed profile
(speed at the contact vs the swing's peak, peak offset), grip curl (raw / after HeroGripPolish), free-hand curl, sole height."""
import json, sys, os
import numpy as np
import analyze as A

NB = 55
ROW = 1 + 3 + 7 + NB * 7 * 2 + 2
RATE = 120.0
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))
TABLE30 = {(c['sex'], c['name']): c for c in json.load(open(REPO + '/work/frame-rate-60/clip_table_30_original.json'))['clips']}


def load(d, sex):
    clips = json.load(open(os.path.join(d, sex + '_clips.json')))
    names = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bones.json')))
    A.setup(names)
    out = {}
    for c in clips:
        if c['dup']:
            continue
        raw = np.fromfile(os.path.join(d, c['file']), dtype=np.float32).reshape(-1, ROW).astype(np.float64)
        r = dict(meta=c, t=raw[:, 0], strings=raw[:, 1:4], grip=raw[:, 4:7], gripq=raw[:, 7:11])
        b = raw[:, 11:11 + NB * 7].reshape(-1, NB, 7); p = raw[:, 11 + NB * 7:11 + 2 * NB * 7].reshape(-1, NB, 7)
        r['pos'], r['rot'] = b[:, :, :3], b[:, :, 3:]
        r['ppos'], r['prot'] = p[:, :, :3], p[:, :, 3:]
        r['sole'] = raw[:, -2:]
        out[(c['tag'], c['clip'])] = r
    return out


def tip(r):
    return r['strings'] + (r['strings'] - r['grip']) * .45


def speed(r):
    s = np.zeros(len(r['t'])); s[1:] = np.linalg.norm(np.diff(r['strings'], axis=0), axis=1) * RATE
    return s


def curl(pos, side):
    h = {'pos': pos}
    return np.mean([v for k, v in A.flex(h, side).items() if k != 'Thumb'], 0), A.flex(h, side)['Thumb']


def check(d, sex):
    C = load(d, sex); B = A.B; res = {}
    approved = {k[1]: v for k, v in C.items() if k[0] == 'approved30'}
    for (tag, name), r in C.items():
        m = r['meta']; e = dict(tag=tag, slot=m['slot'], length=m['length'], contact=None, frameRate=m['frameRate'], minKeyDt=m['minKeyDt'], maxKeyDt=m['maxKeyDt'])
        s = speed(r)
        if (not m['contact'] or m['contact'] <= 0) and tag in ('approved30', 'resampled60'):
            base0 = name.split('_', 1)[1].replace('ArmCorrected', '')
            row = TABLE30.get((sex, base0))
            if row: m = dict(m, contact=row['contact'], leftRelease=row['leftRelease'])
        if m['contact'] and m['contact'] > 0:
            ci = int(round(m['contact'] * RATE)); w0 = max(0, ci - int(.35 * RATE)); w1 = min(len(s), ci + int(.15 * RATE))
            pk = w0 + int(np.argmax(s[w0:w1]))
            e['contact'] = m['contact']
            e.update(speedAtContact=round(float(s[ci]), 2), peak=round(float(s[pk]), 2), peakOffset60=round((pk - ci) / 2.0, 1), ratio=round(float(s[ci] / max(s[pk], 1e-6)), 2))
        # approved comparison (shared 1/30 s frames)
        base = name.replace('Male_', '').replace('Female_', '')
        ap = approved.get(sex + '_' + base)
        if ap is not None and tag != 'approved30':
            n = min(int(round(min(r['t'][-1], ap['t'][-1]) * 30)) + 1, 10000)
            ia = [int(round(k / 30 * RATE)) for k in range(n)]
            ia = [i for i in ia if i < len(r['t']) and i < len(ap['t'])]
            def dmax(fa, fb): return float(np.max(np.linalg.norm(fa[ia] - fb[ia], axis=1)))
            e['approvedMax'] = dict(RightHand=round(dmax(r['pos'][:, B['RightHand']], ap['pos'][:, B['RightHand']]), 4), LeftHand=round(dmax(r['pos'][:, B['LeftHand']], ap['pos'][:, B['LeftHand']]), 4),
                                    strings=round(dmax(r['strings'], ap['strings']), 4), tip=round(dmax(tip(r), tip(ap)), 4))
            e['approvedLength'] = round(float(ap['t'][-1]), 4)
        rc, rt = curl(r['pos'], 'Right'); pc, pt = curl(r['ppos'], 'Right'); lc, lt = curl(r['pos'], 'Left')
        e['rightCurl'] = [round(float(np.min(rc)), 1), round(float(np.median(rc)), 1)]; e['rightCurlPolished'] = [round(float(np.min(pc)), 1), round(float(np.median(pc)), 1)]
        e['leftCurl'] = [round(float(np.min(lc)), 1), round(float(np.median(lc)), 1), round(float(np.max(lc)), 1)]
        e['handToGripMax'] = round(float(np.max(np.linalg.norm(r['pos'][:, B['RightHand']] - r['grip'], axis=1))), 3)
        e['soleMin'] = [round(float(np.min(r['sole'][:, 0])), 4), round(float(np.min(r['sole'][:, 1])), 4)]
        res[tag + ':' + name] = e
    return res


if __name__ == '__main__':
    d = sys.argv[1]
    allr = {s: check(d, s) for s in ('Male', 'Female') if os.path.exists(os.path.join(d, s + '_clips.json'))}
    json.dump(allr, open(sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else os.path.join(d, 'clipcheck.json'), 'w'), indent=1)
    for s, r in allr.items():
        for k, e in sorted(r.items()):
            print(s, k, {x: e.get(x) for x in ('frameRate', 'minKeyDt', 'contact', 'speedAtContact', 'peak', 'peakOffset60', 'ratio', 'approvedMax', 'rightCurl', 'rightCurlPolished', 'leftCurl', 'soleMin') if e.get(x) is not None})
