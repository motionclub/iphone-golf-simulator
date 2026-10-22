"""Female (ArtDir HeroBase_Female, SHA 200dc3b9) right hand: the hand is a set of separate shells (palm ball, thumb, four finger
sausages). Hand frame + finger model for the proof-only grip wrap on a COPY."""
import numpy as np
from collections import deque
from handpose import Chain, smoothstep


def components(n, tris, sel):
    s = set(int(i) for i in sel)
    adj = {}
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            if u in s and v in s:
                adj.setdefault(int(u), set()).add(int(v))
                adj.setdefault(int(v), set()).add(int(u))
    seen, comps = set(), []
    for st in sorted(s):
        if st in seen:
            continue
        q = deque([st]); seen.add(st); comp = [st]
        while q:
            u = q.popleft()
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v); q.append(v); comp.append(v)
        comps.append(np.array(comp))
    return comps


def hand_parts(co, tris):
    """Return dict: ball, thumb, fingers (list of 4 index arrays ordered lateral->medial), forearm (indices of the arm shell)."""
    sel = np.where((co[:, 0] < -0.20) & (co[:, 2] < 1.0))[0]
    comps = components(len(co), tris, sel)
    comps.sort(key=lambda c: -co[c, 2].max())
    forearm = comps[0]
    rest = comps[1:]
    ball = max(rest, key=len)
    others = [c for c in rest if c is not ball]
    # thumb = the piece with the most forward (most negative) y centroid; fingers = the four slim shells hanging lowest
    thumb = min(others, key=lambda c: co[c, 1].mean())
    fingers = [c for c in others if c is not thumb]
    fingers.sort(key=lambda c: co[c, 0].mean())                  # lateral (most negative x) -> medial
    assert len(fingers) == 4, [len(c) for c in others]
    return dict(forearm=forearm, ball=ball, thumb=thumb, fingers=fingers)


def frame_from_parts(co, parts):
    idx = np.concatenate([parts['ball'], parts['thumb']] + parts['fingers'])
    P = co[idx]
    c = P.mean(0)
    U_, S_, Vt = np.linalg.svd(P - c, full_matrices=False)
    u = Vt[0]
    if u[2] > 0:
        u = -u
    # thumb direction: from the finger row centroid towards the thumb centroid, made orthogonal to u
    fc = np.mean([co[f].mean(0) for f in parts['fingers']], axis=0)
    tc = co[parts['thumb']].mean(0)
    v = tc - fc
    v = v - np.dot(v, u) * u
    # the thumb piece sits at the medial end of the finger row: use +x (medial) projected as a more stable estimate
    vx = np.array([1.0, 0.0, 0.0]) - u[0] * u
    vx /= np.linalg.norm(vx)
    v = vx if np.dot(v, vx) > 0 or True else -vx
    v /= np.linalg.norm(v)
    p = np.cross(v, u)
    return idx, c, u, v, p


def to_hand(P, c, u, v, p):
    d = P - c
    return np.stack([d @ u, d @ v, d @ p], axis=1)


def from_hand(Q, c, u, v, p):
    return c + Q[:, 0:1] * u + Q[:, 1:2] * v + Q[:, 2:3] * p


def finger_models(co, parts, c, u, v, p):
    """Per finger sausage: base point M, axis d, length, membership indices (in hand coordinates)."""
    models = []
    for f in parts['fingers']:
        Pf = co[f]
        Qf = to_hand(Pf, c, u, v, p)
        # long axis of the sausage
        cc = Qf.mean(0)
        _, _, Vt = np.linalg.svd(Qf - cc, full_matrices=False)
        d = Vt[0]
        if d[0] < 0:
            d = -d                                            # pointing distally (+U)
        t = (Qf - cc) @ d
        t0, t1 = t.min(), t.max()
        base_off = 0.006                                      # base joint a little inside the proximal end
        M = cc + d * (t0 + base_off)
        models.append(dict(idx=f, M=M, d=d, length=float(t1 - t0 - base_off), centroid=cc))
    return models
