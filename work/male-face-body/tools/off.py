"""Offline (numpy only, no Blender) male head toolkit, 2026-10-17 chat 11.
warp_m(co, F, P, kind): the MALE path of Unity's HeroFaceReferenceFit.Warp (port of ft.game_warp), with the male constants exposed in a
dict so the proportions pass (head width, ears, eyes) can be tuned and then written back to the C# with the same numbers.
kind = 'body' | 'features' (features: brow / iris index sets).
Silhouettes are taken from the welded triangle mesh in the face frame (mm): front half-width and profile front edge per height."""
import numpy as np, json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = dict(head_scale=.085, mouth_scale=.06, eye_stretch=.32, iris_spread=.20, ear_angle=20.0, ear_shrink1=.14, ear_shrink2=.14,
               eye_grow=1.08, eye_tall=1.55, iris_scale=1.16, nose_blend=.55, nose_narrow=.24, nose_back=.0045,
               ear_drop=0.0, ear_scale=1.0, head_low=None, low_y=(-.115, -.095))

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def warp_face(x, y, z, P, is_body=True, isbrow=None, isiris=None):
    """Face-frame coordinates in, face-frame out (metres). Male path only."""
    n = len(x); isbrow = np.zeros(n, bool) if isbrow is None else isbrow; isiris = np.zeros(n, bool) if isiris is None else isiris
    Settle = -.010
    head = smooth(-.17, -.12, y) * (1 - smooth(.16, .20, np.abs(x)))
    front = smooth(-.075, -.045, z)
    eyeCenter = .0367
    orbit = smooth(-.085, -.022, y) * (1 - smooth(.060, .110, y)) * front
    eyeRegion = np.exp(-((np.abs(x) - eyeCenter) / .027) ** 4 - (y / .018) ** 4) * front
    side = x / np.sqrt(x * x + .0001)
    m = ~isbrow
    y2 = y + y * P['eye_stretch'] * eyeRegion
    irisRegion = np.exp(-((np.abs(x) - eyeCenter) / .030) ** 4) * eyeRegion
    x2 = x + (x - side * eyeCenter) * P['iris_spread'] * irisRegion
    y = np.where(m, y2, y); x = np.where(m, x2, x)
    orbitalSides = smooth(.012, .030, np.abs(x)) * np.exp(-(y / .050) ** 4)
    x = x - side * .0035 * orbit * orbitalSides
    y = y - P.get('orbit_drop', .010) * orbit
    mouth = np.exp(-((y + .079) / .022) ** 4) * (1 - smooth(.045, .075, np.abs(x))) * front
    x = x * (1 + P['mouth_scale'] * mouth)
    if is_body:
        ear = smooth(.072, .100, np.abs(x)) * (1 - smooth(-.085, -.025, z)) * smooth(-.100, -.060, y) * (1 - smooth(.010, .055, y))
        ang = np.radians(P['ear_angle']) * ear
        dx = np.abs(x) - .078; dz = z + .090
        x = np.sign(x) * (.078 + dx * np.cos(ang) - dz * np.sin(ang))
        z = -.090 + dx * np.sin(ang) + dz * np.cos(ang)
        yc = -.017 + Settle; zc = -.092; root = .0906 / 1.085
        ry, rz, shrink = .040, .026, P['ear_shrink1']
        reach = np.sqrt(((y - yc) / ry) ** 2 + ((z - zc) / rz) ** 2)
        es = shrink * (1 - smooth(1, 1.6, reach)) * smooth(root - .030, root - .015, np.abs(x))
        on = es != 0
        y = np.where(on, yc + (y - yc) * (1 - es), y); z = np.where(on, zc + (z - zc) * (1 - es), z)
        lat = np.abs(x) - root
        x = np.where(on, x - np.sign(x) * es * smooth(0, .006, lat) * np.maximum(lat, 0), x)
        cheek = np.exp(-2 * ((np.abs(x) - .052) / .030) ** 2 - 2 * ((y + .049) / .032) ** 2) * smooth(-.055, -.010, z)
        z = z + .0035 * cheek
        x = x + side * .0012 * cheek
        tip = np.exp(-2 * (x / .023) ** 2 - 2 * ((y + .049) / .019) ** 2)
        bridge = np.exp(-2 * (x / .010) ** 2 - 2 * ((y + .019) / .035) ** 2)
        alar = np.exp(-2 * ((np.abs(x) - P.get('alar_x', .020)) / .009) ** 2 - 2 * ((y + .053) / .011) ** 2)
        targetNose = .035 + P.get('tip_amp', .019) * tip + .014 * bridge + P.get('alar_amp', .006) * alar
        if P.get('dorsum', 0):
            targetNose = targetNose + P['dorsum'] * np.exp(-2 * (x / P['dorsum_sx']) ** 2 - ((y - P['dorsum_y']) / P['dorsum_sy']) ** 2)
        noseBlend = np.exp(-(x / .032) ** 4 - ((y + .047) / .032) ** 4) * smooth(.020, .052, z)
        nf = P.get('nose_floor', (-.074, -.060)); noseBlend = noseBlend * smooth(nf[0], nf[1], y)
        z = z + (targetNose - z) * noseBlend * P['nose_blend']
        lipWidth = .041
        lipShape = np.clip(1 - x * x / (lipWidth * lipWidth), 0, 1) ** 2 * front
        lower = np.exp(-((y + .084) / .0070) ** 2)
        z = z + .0018 * lower * lipShape
    hs = P['head_scale'] if P.get('head_low') is None else P['head_low'] + (P['head_scale'] - P['head_low']) * smooth(P['low_y'][0], P['low_y'][1], y)
    x = x * (1 + hs * head)
    sx = np.sign(x); ax = np.abs(x)
    ec = .0385; ey = -.0015 - P.get('orbit_drop', .010); hw = .020; hh = .0075
    grow = P['eye_grow']; tall = P['eye_tall']
    dx = ax - ec; dy = y - ey; reach = np.sqrt(dx * dx / (hw * hw) + dy * dy / (hh * hh))
    eyeFront = smooth(-.060, -.035, z)
    eyeWeight = (1 - smooth(1.0, 2.6, reach)) * eyeFront
    ic = .0366; iy = .0014 - P.get('orbit_drop', .010); irs = P['iris_scale']
    ax_i = ic + (ax - ic) * irs; y_i = iy + (y - iy) * irs
    other = (~isbrow) & (eyeWeight > 0) & (~isiris)
    ax_o = ec + dx * (1 + (grow - 1) * eyeWeight); y_o = ey + dy * (1 + (tall - 1) * eyeWeight)
    ax = np.where(isiris, ax_i, np.where(other, ax_o, ax)); y = np.where(isiris, y_i, np.where(other, y_o, y))
    x = sx * ax
    if is_body:
        noseFront = smooth(.031, .045, z)
        nose = np.exp(-(x / .028) ** 4 - ((y - Settle + .048) / .030) ** 4) * noseFront
        x = x * (1 - P['nose_narrow'] * nose)
        z = z - P['nose_back'] * nose * smooth(0, 1, nose)
        yc = -.0152 + Settle; zc = -.0932; root = .0909
        ry, rz, shrink = .036, .022, P['ear_shrink2']
        er = np.sqrt(((y - yc) / ry) ** 2 + ((z - zc) / rz) ** 2)
        es = shrink * (1 - smooth(1, 1.6, er)) * smooth(root - .030, root - .015, np.abs(x))
        on = es != 0
        y = np.where(on, yc + (y - yc) * (1 - es), y); z = np.where(on, zc + (z - zc) * (1 - es), z)
        lat = np.abs(x) - root
        x = np.where(on, x - np.sign(x) * es * smooth(0, .006, lat) * np.maximum(lat, 0), x)
        if P.get('ear_tall', 1.0) != 1.0 or P.get('ear_drop', 0.0):
            w = (1 - smooth(1, 1.6, er)) * smooth(root - .030, root - .015, np.abs(x))
            y = yc + (y - yc) * (1 + (P.get('ear_tall', 1.0) - 1) * w) - P.get('ear_drop', 0.0) * w
    return x, y, z, head >= .00001

class Head:
    def __init__(self, snap=W + '/source_male_1017.npz'):
        d = np.load(snap); self.d = d
        self.base = d['basis']; self.eye, self.right, self.up, self.fwd = d['eye'], d['right'], d['up'], d['fwd']
        key = np.round(self.base, 6); u, idx = np.unique(key, axis=0, return_inverse=True); self.idx = idx.ravel(); self.nu = len(u)
        tri = self.idx[d['tri']]; self.tri = tri[(tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])]
        e = np.vstack([self.tri[:, [0, 1]], self.tri[:, [1, 2]], self.tri[:, [2, 0]]]); e.sort(1); self.edges = np.unique(e, axis=0)
        self.rep = np.zeros(self.nu, int); self.rep[self.idx] = np.arange(len(self.idx))
    def to_face(self, co):
        dd = co - self.eye; return np.stack([dd @ self.right, dd @ self.up, dd @ self.fwd], 1)
    def from_face(self, f):
        return self.eye + np.outer(f[:, 0], self.right) + np.outer(f[:, 1], self.up) + np.outer(f[:, 2], self.fwd)
    def warp(self, co, P=DEFAULT):
        f = self.to_face(co); x, y, z, live = warp_face(f[:, 0], f[:, 1], f[:, 2], P)
        out = np.stack([x, y, z], 1); out[~live] = f[~live]; return out   # face frame, metres
    def U(self, co):
        """welded (unique) coordinates"""
        return co[self.rep]

def slices(G, tri, ys, xlim=None, zmin=None):
    """Per height y (mm): front half-width (max |x|) and profile front (max z) of the mesh cut by the plane, G in mm."""
    a, b, c = G[tri[:, 0]], G[tri[:, 1]], G[tri[:, 2]]
    half = np.full(len(ys), np.nan); front = np.full(len(ys), np.nan)
    for k, y in enumerate(ys):
        pts = []
        for p, q in ((a, b), (b, c), (c, a)):
            m = (p[:, 1] - y) * (q[:, 1] - y) < 0
            t = (y - p[m, 1]) / (q[m, 1] - p[m, 1]); pts.append(p[m] + (q[m] - p[m]) * t[:, None])
        P = np.vstack(pts)
        if xlim is not None: P = P[np.abs(P[:, 0]) <= xlim]
        if zmin is not None: P = P[P[:, 2] >= zmin]
        if len(P): half[k] = np.abs(P[:, 0]).max(); front[k] = P[:, 2].max()
    return half, front

def ref_tables():
    d = np.load(W + '/eval/ref07_tables.npz'); return d
