"""Chat 4 tennis animation integrity: measure a filmed match (TaiRecorder output).
usage: python3 analyze.py <film dir> [--json out.json]
Reads frames.csv + bones.f32 + events.csv; reports pops, foot slide/dip, grip curl, contact gap/speed, serve pace per hero."""
import csv, json, sys, math, os
import numpy as np

FPS = 60.0
NB = 55
HEAD = 25
B = None
PARENT = {}

def setup(names):
    global B, PARENT
    B = {n: i for i, n in enumerate(names)}
    p = {'LeftUpperLeg': 'Hips', 'RightUpperLeg': 'Hips', 'LeftLowerLeg': 'LeftUpperLeg', 'RightLowerLeg': 'RightUpperLeg',
         'LeftFoot': 'LeftLowerLeg', 'RightFoot': 'RightLowerLeg', 'LeftToes': 'LeftFoot', 'RightToes': 'RightFoot',
         'Spine': 'Hips', 'Chest': 'Spine', 'UpperChest': 'Chest', 'Neck': 'UpperChest', 'Head': 'Neck',
         'LeftShoulder': 'UpperChest', 'RightShoulder': 'UpperChest', 'LeftUpperArm': 'LeftShoulder', 'RightUpperArm': 'RightShoulder',
         'LeftLowerArm': 'LeftUpperArm', 'RightLowerArm': 'RightUpperArm', 'LeftHand': 'LeftLowerArm', 'RightHand': 'RightLowerArm'}
    for s in ('Left', 'Right'):
        for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Little'):
            p[s + f + 'Proximal'] = s + 'Hand'; p[s + f + 'Intermediate'] = s + f + 'Proximal'; p[s + f + 'Distal'] = s + f + 'Intermediate'
    PARENT = {B[c]: B[q] for c, q in p.items() if c in B and q in B}

def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(a, -1, 0); bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack([aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz], -1)
def qinv(a): return a * np.array([-1, -1, -1, 1.0])
def qangle(a, b):  # degrees between rotations (sign safe)
    d = np.abs(np.sum(a * b, -1)).clip(0, 1); return np.degrees(2 * np.arccos(d))
def qrot(q, v):
    u = q[..., :3]; w = q[..., 3:4]
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)

def load(d):
    meta = json.load(open(d + '/meta.json')); setup(meta['bones'])
    rows = list(csv.DictReader(open(d + '/frames.csv')))
    head = meta.get('head', HEAD)
    raw = np.fromfile(d + '/bones.f32', dtype=np.float32).reshape(-1, head + NB * 7).astype(np.float64)
    heroes = {}
    for k in (0, 1):
        sel = raw[:, 1] == k
        r = raw[sel]
        fr = [x for x in rows if x['role'] == ('player' if k == 0 else 'rival')]
        n = min(len(fr), len(r)); r = r[:n]; fr = fr[:n]
        h = dict(rows=fr, tick=r[:, 0].astype(int), root=r[:, 2:5], rootq=r[:, 5:9], actor=r[:, 9:12], ball=r[:, 12:15], strings=r[:, 15:18],
                 grip=r[:, 18:21], gripq=r[:, 21:25], pos=r[:, head:].reshape(n, NB, 7)[:, :, :3], rot=r[:, head:].reshape(n, NB, 7)[:, :, 3:])
        if head >= 116: h['gripScale'] = r[:, 25]; h['prePolish'] = r[:, 26:116].reshape(n, 30, 3)
        h['sex'] = fr[0]['hero'] if fr else '?'
        h['clip'] = [x['clip'] for x in fr]; h['clipTime'] = np.array([float(x['clipTime']) for x in fr])
        h['swinging'] = np.array([x['swinging'] == 'True' for x in fr]); h['ttc'] = np.array([float(x['ttc']) for x in fr])
        h['state'] = [x['state'] for x in fr]; h['flow'] = [x['flow'] for x in fr]
        h['sink'] = np.array([float(x['finalSink']) for x in fr]); h['pace'] = np.array([float(x['swingPace']) for x in fr])
        h['kind'] = [x['kind'] for x in fr]; h['weights'] = [x['weights'] for x in fr]
        if fr and 'soleAfter' in fr[0] and fr[0]['soleAfter'] not in ('', '-1'): h['soleAfter'] = np.array([float(x['soleAfter']) for x in fr]); h['soleBefore'] = np.array([float(x['soleBefore']) for x in fr])
        heroes[k] = h
    events = list(csv.DictReader(open(d + '/events.csv')))
    return heroes, events

def local_rot(h):
    rot = h['rot']; loc = rot.copy()
    for c, p in PARENT.items(): loc[:, c] = qmul(qinv(rot[:, p]), rot[:, c])
    loc[:, B['Hips']] = qmul(qinv(h['rootq']), rot[:, B['Hips']])
    return loc

MAJOR = ['Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'Head', 'LeftShoulder', 'RightShoulder', 'LeftUpperArm', 'RightUpperArm', 'LeftLowerArm', 'RightLowerArm',
         'LeftHand', 'RightHand', 'LeftUpperLeg', 'RightUpperLeg', 'LeftLowerLeg', 'RightLowerLeg', 'LeftFoot', 'RightFoot', 'LeftToes', 'RightToes']

def angvel(h):
    loc = local_rot(h)
    av = np.zeros(loc.shape[:2]); av[1:] = qangle(loc[1:], loc[:-1]) * FPS
    gap = np.diff(h['tick'], prepend=h['tick'][0]) != 1; av[gap] = 0
    return av

def pops(h, av, factor=2.0, floor=500.0):
    """Frames where a major joint's angular speed exceeds factor x the joint's steady-state peak for the clip(s) on screen around it."""
    clips = h['clip']; n = len(clips)
    steady = np.array([i > 3 and i < n - 3 and len(set(clips[i - 3:i + 4])) == 1 and h['weights'][i].count('=') <= 2 for i in range(n)])
    ref = {}
    for c in set(clips):
        idx = [i for i in range(n) if clips[i] == c and steady[i]]
        ref[c] = np.percentile(av[idx], 99.5, axis=0) if len(idx) > 20 else None
    out = []
    for j in [B[x] for x in MAJOR]:
        for i in range(1, n):
            v = av[i, j]
            if v < floor: continue
            near = set(clips[max(0, i - 6):i + 7])
            refs = [ref[c][j] for c in near if ref.get(c) is not None]
            peak = max(refs) if refs else 0
            if v > factor * max(peak, floor / factor):
                out.append(dict(tick=int(h['tick'][i]), bone=MAJOR[[B[x] for x in MAJOR].index(j)], degps=round(float(v)), ref=round(float(peak)),
                                clip=clips[i], prev=clips[i - 1], state=h['state'][i], transition=len(near) > 1))
    # merge: one entry per tick (worst bone)
    best = {}
    for p in out:
        k = p['tick']
        if k not in best or p['degps'] / max(p['ref'], 1) > best[k]['degps'] / max(best[k]['ref'], 1): best[k] = p
    return sorted(best.values(), key=lambda p: p['tick'])

def feet(h):
    """Planted-foot slide per plant interval (min of heel/toe drift) and sole dip from the driver's FinalSink."""
    res = []
    up = qrot(h['rootq'], np.array([0, 1.0, 0]))
    for side in ('Left', 'Right'):
        fo, to = h['pos'][:, B[side + 'Foot']], h['pos'][:, B[side + 'Toes']]
        hf = np.sum((fo - h['root']) * up, 1); ht = np.sum((to - h['root']) * up, 1)
        ready = np.array(['ReadyIdle' in c for c in h['clip']])
        rf = np.percentile(hf[ready], 10) if ready.sum() > 10 else np.percentile(hf, 2)
        rt = np.percentile(ht[ready], 10) if ready.sum() > 10 else np.percentile(ht, 2)
        planted = (np.minimum(hf - rf, ht - rt) < .012)
        i = 0; n = len(planted)
        while i < n:
            if not planted[i]: i += 1; continue
            j = i
            while j + 1 < n and planted[j + 1] and h['tick'][j + 1] == h['tick'][j] + 1: j += 1
            if j - i >= 5:
                seg = slice(i, j + 1)
                heelDown = (hf[seg] - rf) < .012; toeDown = (ht[seg] - rt) < .012
                def drift(p, m):
                    if m.sum() < 3: return 9.9
                    q = p[seg][m]; q = q[:, [0, 2]]; return float(np.max(np.linalg.norm(q - q[0], axis=1)))
                slide = min(drift(fo, heelDown), drift(to, toeDown))
                cl = h['clip'][i:j + 1]
                res.append(dict(foot=side, t0=int(h['tick'][i]), t1=int(h['tick'][j]), slide=round(slide, 4), clip=max(set(cl), key=cl.count), clips=sorted(set(cl)),
                                moving=round(float(np.linalg.norm(np.diff(h['actor'][seg][:, [0, 2]], axis=0), axis=1).sum()), 3)))
            i = j + 1
    return res

FING = ['Index', 'Middle', 'Ring', 'Little']
def flex(h, side):
    """MCP+PIP flexion (deg) per finger, from joint positions; thumb tip spread from index."""
    P = h['pos']; hand = P[:, B[side + 'Hand']]; out = {}
    for f in FING + ['Thumb']:
        a, b, c = P[:, B[side + f + 'Proximal']], P[:, B[side + f + 'Intermediate']], P[:, B[side + f + 'Distal']]
        def ang(u, v): return np.degrees(np.arccos(np.clip(np.sum(u * v, 1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1) + 1e-9), -1, 1)))
        out[f] = ang(a - hand, b - a) + ang(b - a, c - b)
    return out

def hand_shape(h, side):
    """Per frame: claw (knuckles straight < 15 deg while the middle joints bend > 45), paddle (knuckles + middle joints < 25 total), splay
    (index and little fingers > 30 deg apart), from the finger joint positions."""
    P = h['pos']; hand = P[:, B[side + 'Hand']]
    def ang(u, v): return np.degrees(np.arccos(np.clip(np.sum(u * v, 1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1) + 1e-9), -1, 1)))
    mcp, pip = [], []
    for f in FING:
        a, b, c = P[:, B[side + f + 'Proximal']], P[:, B[side + f + 'Intermediate']], P[:, B[side + f + 'Distal']]
        mcp.append(ang(a - hand, b - a)); pip.append(ang(b - a, c - b))
    mcp, pip = np.mean(mcp, 0), np.mean(pip, 0)
    ix = P[:, B[side + 'IndexIntermediate']] - P[:, B[side + 'IndexProximal']]; lt = P[:, B[side + 'LittleIntermediate']] - P[:, B[side + 'LittleProximal']]
    return dict(claw=(mcp < 15) & (pip > 45), paddle=(mcp + pip) < 25, splay=ang(ix, lt) > 30)


def handle_dist(h):
    """Distance of each right-hand finger distal joint to the racket handle axis (grip position, grip up)."""
    up = qrot(h['gripq'], np.array([0, 1.0, 0])); g = h['grip']; out = {}
    for f in FING:
        d = h['pos'][:, B['Right' + f + 'Distal']] - g
        out[f] = np.linalg.norm(d - np.sum(d * up, 1)[:, None] * up, axis=1)
    out['hand'] = np.linalg.norm(h['pos'][:, B['RightHand']] - g, axis=1)
    return out

def swings(h):
    """One record per contact: strings vs ball at ttc = 0 (rendered frames), racket speed at contact vs swing peak."""
    sw = h['swinging']; ttc = h['ttc']; S = h['strings']; ball = h['ball']; n = len(sw)
    spd = np.zeros(n); spd[1:] = np.linalg.norm(np.diff(S, axis=0), axis=1) * FPS
    out = []
    for i in range(1, n):
        if not (sw[i] and sw[i - 1] and ttc[i - 1] > 0 >= ttc[i]): continue
        u = ttc[i - 1] / (ttc[i - 1] - ttc[i])
        s0 = S[i - 1] + (S[i] - S[i - 1]) * u
        if abs(ttc[i]) < 1e-4: s0 = S[i]          # the game draws the contact step itself (it stops simulating there)
        # honest contact: how far the strings at the strike are from the ball's incoming flight (the ray through its last two frames)
        if i >= 2:
            p, v = ball[i - 1], ball[i - 1] - ball[i - 2]
            tt = max(0.0, float(np.dot(s0 - p, v) / max(np.dot(v, v), 1e-9)))
            b0 = p + v * min(tt, 3.0)
        else: b0 = ball[i - 1]
        w0, w1 = max(0, i - 24), min(n, i + 14)
        pk = w0 + int(np.argmax(spd[w0:w1]))
        sc = spd[i - 1]   # the last full frame into the ball (the contact frame is a partial game step: the game stops simulating at the hit)
        # forward swing start: the last frame before the contact where the racket was still nearly at rest (< 15 % of its speed into the ball)
        kb = next((k for k in range(i - 2, max(0, i - 40), -1) if spd[k] < .15 * max(spd[i - 1], 1e-3)), max(0, i - 40))
        fin = next((k for k in range(i, min(n, i + 30)) if spd[k] < .3 * max(spd[pk], 1e-6)), min(n - 1, i + 30))
        out.append(dict(tick=int(h['tick'][i]), clip=h['clip'][i], kind=h['kind'][i], gap=round(float(np.linalg.norm(s0 - b0)), 3),
                        forwardSwing=round((i - kb) / FPS, 3), finishAfter=round((fin - i) / FPS, 3),
                        speedAtContact=round(float(sc), 2), peak=round(float(spd[pk]), 2), peakOffsetFrames=int(h['tick'][pk] - h['tick'][i]),
                        followSpeed=round(float(spd[min(n - 1, i + 4)]), 2)))
    return out

def serves(h):
    """Visible Serve clip rate (clip s per real s) from the swing start to contact, and the actor's swingPace."""
    out = []; n = len(h['clip']); i = 0
    while i < n:
        if h['swinging'][i] and 'Serve' in h['clip'][i] and h['ttc'][i] > 0:
            j = i
            while j + 1 < n and h['swinging'][j + 1] and h['ttc'][j + 1] > 0: j += 1
            ct = h['clipTime'][i:j + 1]; dur = (j - i + 1) / FPS
            # the active swing: from the last held frame (clip still, the trophy hold) to the contact
            rate = np.diff(ct) * FPS; held = [q for q in range(len(rate)) if rate[q] < .1]
            a0 = (held[-1] + 1) if held else 0
            act = ct[a0:]; adur = (len(act) - 1) / FPS
            out.append(dict(tick=int(h['tick'][i]), frames=j - i + 1, clipFrom=round(float(ct[0]), 3), clipTo=round(float(ct[-1]), 3),
                            visibleRate=round(float((ct[-1] - ct[0]) / max(dur - 1 / FPS, 1e-3)), 3), actorPace=round(float(np.median(h['pace'][i:j + 1])), 3),
                            activeFrom=round(float(act[0]), 3), activeSeconds=round(adur, 3), activeRate=round(float((act[-1] - act[0]) / max(adur, 1e-3)), 3) if len(act) > 1 else None))
            i = j + 1
        else: i += 1
    return out

def summary(d):
    heroes, events = load(d)
    rep = {}
    for k, h in heroes.items():
        av = angvel(h)
        rf = flex(h, 'Right'); lf = flex(h, 'Left'); hd = handle_dist(h)
        onRacket = hd['hand'] < .145
        rcurl = np.mean([rf[f] for f in FING], 0)
        lcurl = np.mean([lf[f] for f in FING], 0)
        lh = h['pos'][:, B['LeftHand']]; up = qrot(h['gripq'], np.array([0, 1.0, 0])); dv = lh - h['grip']
        loff = np.linalg.norm(dv - np.sum(dv * up, 1)[:, None] * up, axis=1) > .17
        rep[h['sex'] + '_' + ('player' if k == 0 else 'rival')] = dict(
            frames=len(h['clip']),
            clips={c: h['clip'].count(c) for c in sorted(set(h['clip']))},
            pops=pops_vs_clips(h, av, PEAKS) if PEAKS else pops(h, av), feet=feet(h), swings=swings(h), serves=serves(h),
            soleMax=round(float(np.max(h['soleAfter'])), 4) if 'soleAfter' in h else None,
            hands=dict(rightOnRacketCurl=[round(float(np.percentile(rcurl[onRacket], q)), 1) for q in (0, 5, 50)] if onRacket.any() else None,
                       leftFreeCurl=[round(float(np.percentile(lcurl[loff], q)), 1) for q in (0, 5, 50, 95, 100)] if loff.any() else None,
                       leftFreeOutside=int(((lcurl < 35) | (lcurl > 140))[loff].sum()), leftFreeFrames=int(loff.sum()),
                       **{'leftFree_' + k: int(v[loff].sum()) for k, v in hand_shape(h, 'Left').items()}),
            sinkMax=round(float(h['sink'].max()), 4), sinkFrames5mm=int((h['sink'] > .005).sum()),
            grip=dict(rightCurlByClip={c: [round(float(np.percentile(rcurl[[i for i in range(len(rcurl)) if h['clip'][i] == c]], q)), 1) for q in (5, 50)] for c in sorted(set(h['clip']))},
                      handOffRacketFrames=int((~onRacket).sum()),
                      distalFarFrames=int((np.max([hd[f] for f in FING], 0) > .045).sum()),
                      leftCurlByClip={c: [round(float(np.percentile(np.mean([lf[f] for f in FING], 0)[[i for i in range(len(rcurl)) if h['clip'][i] == c]], q)), 1) for q in (5, 50, 95)] for c in sorted(set(h['clip']))}))
    rep['events'] = events
    return rep



# ---- authored per-bone peak angular speed of every clip (from a TennisAnimClipDump folder), keyed by slot id and clip name
def clip_peaks(dump_dir):
    import clipcheck as C
    setup(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bones.json'))))   # clipcheck sets up its own import of this module
    peaks = {}
    for sex in ('Male', 'Female'):
        if not os.path.exists(os.path.join(dump_dir, sex + '_clips.json')): continue
        for (tag, name), r in C.load(dump_dir, sex).items():
            if tag != 'live': continue
            h = dict(rot=r['rot'], rootq=np.tile([0, 0, 0, 1.0], (len(r['t']), 1)), tick=np.arange(len(r['t'])))
            loc = local_rot(h)
            av = np.zeros(loc.shape[:2]); av[1:] = qangle(loc[1:], loc[:-1]) * C.RATE
            pk = np.nanmax(av, axis=0)
            peaks[(sex, name)] = pk
            if r['meta']['slot']: peaks[(sex, r['meta']['slot'])] = pk
    return peaks


def pops_vs_clips(h, av, peaks, factor=2.0, floor=360.0):
    """Frames where a major joint turns faster than factor x the fastest that joint turns in any clip on screen (weights within +-6
    frames), scaled by that clip's live play rate. Floor: slow-turning joints never count below 360 deg/s."""
    sex = h['sex'].capitalize(); n = len(h['clip'])
    rate = np.ones(n); rate[1:] = np.abs(np.diff(h['clipTime'])) * FPS
    names = []
    for i in range(n):
        w = h['weights'][i]; ids = [x.split('=')[0] for x in w.replace('upper=', 'upper:').split() if '=' in x]
        up = w.split('upper=')[-1].split(':')[-1] if 'upper=' in w else '-'
        names.append(set(ids + ([up] if up != '-' else []) + [h['clip'][i]]))
    out = []; MJ = [B[x] for x in MAJOR]
    for i in range(1, n):
        near = set().union(*names[max(0, i - 6):i + 7])
        r = max(1.0, float(np.median(rate[max(1, i - 3):i + 4])))
        for jj, j in enumerate(MJ):
            v = av[i, j]
            if v < floor: continue
            ref = max([peaks[(sex, c)][j] for c in near if (sex, c) in peaks] + [0.0]) * r
            if v > factor * max(ref, floor / factor):
                out.append(dict(tick=int(h['tick'][i]), bone=MAJOR[jj], degps=round(float(v)), ref=round(float(ref)), clip=h['clip'][i], state=h['state'][i], transition=len(near) > 1))
    best = {}
    for p in out:
        if p['tick'] not in best or p['degps'] / max(p['ref'], 1) > best[p['tick']]['degps'] / max(best[p['tick']]['ref'], 1): best[p['tick']] = p
    return sorted(best.values(), key=lambda p: p['tick'])


PEAKS = None
if __name__ == '__main__':
    d = sys.argv[1]
    if '--peaks' in sys.argv: PEAKS = clip_peaks(sys.argv[sys.argv.index('--peaks') + 1])
    r = summary(d)
    out = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else d + '/analysis.json'
    json.dump(r, open(out, 'w'), indent=1)
    for k, v in r.items():
        if k == 'events': continue
        print(k, 'frames', v['frames'], 'pops', len(v['pops']), 'plants', len(v['feet']), 'slides>1.5cm', sum(1 for f in v['feet'] if f['slide'] > .015),
              'sinkMax', v['sinkMax'], 'swings', len(v['swings']), 'serves', v['serves'])

