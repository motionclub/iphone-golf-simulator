"""COURT_UNCHANGED, frame evidence: the painted court lines are where the geometry says, before and after.

Each court line is a known world-space segment (the kit dump gives their positions). For every shot the capture tool takes, the segment is
projected with the capture camera, sampled at many points, and at each point we ask one question: is there a thin bright line here, i.e. is
the pixel clearly brighter than the court surface 5 px to either side of it? The share of "yes" samples is the line score. Players and shadows
hide a few samples in both frames, so the score is compared old against new, not against 100%.

If the court, the lines or the camera had moved by even a few pixels the score would collapse (--selftest proves it by shifting a frame).

    check_court_frames.py <old_dir> <new_dir>
    check_court_frames.py --selftest <dir>
"""
import sys
import numpy as np
from PIL import Image

SHOTS = {   # name: (camera position, look-at, vertical fov)
    '1_gameplay': ((0, 3.5, -15.6), (0, 1.15, -3.2), 56),
    '2_postcard': ((0, 9, -30), (0, 1, 6), 46),
    '3_drone5': ((-14, 7.5, -22), (0, .5, 0), 50),     # TennisVenue.Drone(1): the landing pose every venue shares
}
Y = .06
SEGMENTS = {   # world-space line segments of the painted court (metres)
    'near baseline': ((-5.485, Y, -11.885), (5.485, Y, -11.885)), 'far baseline': ((-5.485, Y, 11.885), (5.485, Y, 11.885)),
    'doubles sideline L': ((-5.485, Y, -11.885), (-5.485, Y, 11.885)), 'doubles sideline R': ((5.485, Y, -11.885), (5.485, Y, 11.885)),
    'singles sideline L': ((-4.115, Y, -11.885), (-4.115, Y, 11.885)), 'singles sideline R': ((4.115, Y, -11.885), (4.115, Y, 11.885)),
    'near service line': ((-4.115, Y, -6.4), (4.115, Y, -6.4)), 'far service line': ((-4.115, Y, 6.4), (4.115, Y, 6.4)),
    'centre service line': ((0, Y, -6.4), (0, Y, 6.4)),
}

def project(P, cam, look, fov, W=1920, H=1080):
    P, C, L = np.array(P, float), np.array(cam, float), np.array(look, float)
    f = L - C; f /= np.linalg.norm(f)
    right = np.cross([0, 1, 0], f); right /= np.linalg.norm(right)
    up = np.cross(f, right)
    v = P - C; zc = v @ f
    t = np.tan(np.radians(fov) / 2)
    return np.array([(v @ right / (zc * t * W / H) + 1) / 2 * W, (1 - (v @ up) / (zc * t)) / 2 * H])

def lum(a): return a @ np.array([.2126, .7152, .0722], dtype=np.float32)

def sample(l, p):
    x, y = int(round(p[0])), int(round(p[1]))
    return l[y, x] if 6 <= x < l.shape[1] - 6 and 6 <= y < l.shape[0] - 6 else None

def scores(path, shot, dx=0, dy=0, n=60):
    cam, look, fov = SHOTS[shot]
    l = lum(np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255)
    if dx or dy: l = np.roll(np.roll(l, dy, 0), dx, 1)
    out = {}
    for name, (a, b) in SEGMENTS.items():
        pa, pb = project(a, cam, look, fov), project(b, cam, look, fov)
        d = pb - pa; length = np.linalg.norm(d)
        if length < 40: continue
        normal = np.array([-d[1], d[0]]) / length
        hit = tot = 0
        for t in np.linspace(.04, .96, n):
            p = pa + d * t
            centre = [sample(l, p + normal * s) for s in (-1, 0, 1)]
            side = [sample(l, p + normal * s) for s in (-6, 6)]
            if None in centre or None in side: continue
            tot += 1; hit += (max(centre) - np.mean(side)) > .10
        if tot >= 20: out[name] = hit / tot
    return out

if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        d = sys.argv[2].rstrip('/'); ok = True
        for venue in ('skyscraper', 'volcano'):
            s0 = scores(f'{d}/{venue}_1_gameplay.png', '1_gameplay'); s1 = scores(f'{d}/{venue}_1_gameplay.png', '1_gameplay', 4, 3)
            a, b = np.mean(list(s0.values())), np.mean(list(s1.values()))
            print(f'{venue:10s} aligned {a*100:5.1f}%   shifted by (4,3) px {b*100:5.1f}%  -> {"detects a shift" if a - b > .25 else "TOO INSENSITIVE"}')
            ok &= (a - b > .25)
        sys.exit(0 if ok else 1)
    old, new = sys.argv[1].rstrip('/'), sys.argv[2].rstrip('/'); ok = True
    for venue in ('skyscraper', 'volcano'):
        for shot in SHOTS:
            try: so = scores(f'{old}/{venue}_{shot}.png', shot); sn = scores(f'{new}/{venue}_{shot}.png', shot)
            except FileNotFoundError: continue
            common = [k for k in so if k in sn]
            mo, mn = np.mean([so[k] for k in common]), np.mean([sn[k] for k in common])
            worst = min(common, key=lambda k: sn[k] - so[k]); dw = sn[worst] - so[worst]
            status = 'same' if mn >= mo - .08 and mn >= .6 and dw > -.35 else 'CHECK'
            ok &= status == 'same'
            print(f'{venue:10s} {shot:11s} {len(common)} segments  line score old {mo*100:5.1f}%  new {mn*100:5.1f}%   worst segment "{worst}" {so[worst]*100:3.0f}% -> {sn[worst]*100:3.0f}%  {status}')
    print('court-frame check:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)
