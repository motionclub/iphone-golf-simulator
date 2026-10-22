def _seg_weights():
    """selection weights of the brick interiors: darker bricks (the render of Masonry_C is far paler than split.jpg's ruin, mean 190 against 95) and bricks without a moss patch are preferred.
    z-scores over the 8-row table; w = exp(-0.9 z_lum) * exp(-0.8 max(0, z_moss))."""
    brick_segments()
    t = np.array(_SEG_TONE, float)
    zl = (t[:, 0] - t[:, 0].mean()) / max(float(t[:, 0].std()), 1e-6)
    zm = (t[:, 1] - t[:, 1].mean()) / max(float(t[:, 1].std()), 1e-6)
    return list(np.exp(-0.9 * zl) * np.exp(-0.8 * np.maximum(zm, 0.0)))


_W_SEG = None


def pick_seg(rng):
    """index of a brick interior of Masonry_C.png, drawn with the dark / no-moss weights."""
    global _W_SEG
    if _W_SEG is None:
        _W_SEG = _seg_weights()
    return rng.choices(range(len(_W_SEG)), weights=_W_SEG, k=1)[0]


def uv_window(rng, w, h, kmin, kmax, widest=False, pref=None):
    """(u0, v0, k): a window of size (k*w, k*h) uv inside one brick interior, kmin <= k <= kmax (uv per metre). pref = index of the brick the stone prefers (every face of a stone takes
    a window of the SAME brick when it fits, so a stone keeps one tone and neighbouring stones differ); widest: the lintel's long faces take the widest interior at kmin."""
    segs = brick_segments()
    if widest:
        s = max(segs, key=lambda q: (q[1] - q[0]))
        k = kmin
        return rng.uniform(s[0], max(s[0], s[1] - k * w)), rng.uniform(s[2], max(s[2], s[3] - k * h)), k
    order = ([pref] if pref is not None else []) + [pick_seg(rng) for _ in range(60)]
    for idx in order:
        s = segs[idx]
        k = min((s[1] - s[0]) / max(w, 1e-3), (s[3] - s[2]) / max(h, 1e-3), kmax)
        if k < kmin:
            continue
        k = rng.uniform(max(kmin, 0.75 * k), k)
        return rng.uniform(s[0], s[1] - k * w), rng.uniform(s[2], s[3] - k * h), k
    s = max(segs, key=lambda q: (q[1] - q[0]) * (q[3] - q[2]))
    return s[0], s[2], kmin


def _face_uv(rng, pts, widest=False, pref=None):
    """UV of one polygon (list of Vector / xyz): a brick-interior window in the polygon's own plane axes (a standing face: u along the face, v up; a top / bottom face: a random 90-degree turn).
    The polygon is planar (hole09_stone), so this single affine map is the UV of the whole face: no triangle of it can differ from its neighbour."""
    p = np.array([tuple(q) for q in pts], float)
    n = np.zeros(3)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
    ln = float(np.linalg.norm(n))
    n = n / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0])
    kd = 1.0 / L.LOOK["LK_MASONRY"][2]
    if abs(n[2]) < 0.75:
        up = np.array([0.0, 0.0, 1.0])
        vax = up - n * float(up @ n)
        vax /= max(float(np.linalg.norm(vax)), 1e-9)
        uax = np.cross(vax, n)
        a, b = p @ uax, p @ vax
        flip = rng.random() < 0.5
    else:
        ang = rng.choice((0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi)) + rng.uniform(-0.25, 0.25)
        c, s = math.cos(ang), math.sin(ang)
        a, b = c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1]
        flip = rng.random() < 0.5
    w, h = float(a.max() - a.min()), float(b.max() - b.min())
    kmin = (UV_K[0] if abs(n[2]) < 0.75 else UV_K_TOP) * kd                 # a top face may be up to 1.7 m across: it gets a slightly lower density (UV_DENSITY: per-edge floor is 1/4)
    u0, v0, k = uv_window(rng, max(w, 0.04), max(h, 0.04), kmin, UV_K[1] * kd, widest=widest, pref=pref)
    if flip:
        return [(u0 + k * float(a.max() - a[i]), v0 + k * float(b[i] - b.min())) for i in range(len(p))]
    return [(u0 + k * float(a[i] - a.min()), v0 + k * float(b[i] - b.min())) for i in range(len(p))]


# --------------------------------------------------------------------------------------------- Rock_C.png (the LK_ROCK faces: tops and some stones)
_ROCK = None


def _rock_tex():
    """Rock_C.png as (integral image of the luminance over a 2 x 2 tiling, integral image of the moss excess, size)."""
    global _ROCK
    if _ROCK is not None:
        return _ROCK
    import os
    path = os.path.join(L.LOOK_DIR, "Rock_C.png")
    had = bpy.data.images.get("Rock_C.png")
    img = bpy.data.images.load(path, check_existing=True)
    W, H = img.size
    a = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(a)
    rgb_ = a.reshape(H, W, 4)[..., :3].astype(np.float64)
    if had is None:
        bpy.data.images.remove(img)
    lum = rgb_.mean(-1)
    moss = rgb_[..., 1] - 0.5 * (rgb_[..., 0] + rgb_[..., 2])
    out = []
    for arr in (lum, moss):
        t = np.tile(arr, (2, 2))
        ii = np.zeros((t.shape[0] + 1, t.shape[1] + 1))
        ii[1:, 1:] = t.cumsum(0).cumsum(1)
        out.append(ii)
    _ROCK = (out[0], out[1], W, H)
    return _ROCK


def _rock_window_mean(u0, v0, wu, hv):
    """(mean luminance, mean moss excess) of the Rock_C window [u0, u0 + wu] x [v0, v0 + hv] (uv units, tiling; a window of a tile or more is the whole texture)."""
    il, im, W, H = _rock_tex()
    if wu >= 0.98 or hv >= 0.98:
        x0, x1, y0, y1 = 0, W, 0, H
    else:
        x0, y0 = int((u0 % 1.0) * W), int((v0 % 1.0) * H)
        x1, y1 = x0 + max(1, int(wu * W)), y0 + max(1, int(hv * H))
    area = float((x1 - x0) * (y1 - y0))
    res = []
    for ii in (il, im):
        res.append((ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]) / area)
    return res[0], res[1]


def rock_offset(rng, w_m, h_m, tile, dark=1.0, moss_ok=False, n=7):
    """(u0, v0) of a Rock_C window of w_m x h_m metres (density 1 / tile): the darkest-leaning of n random candidates (luminance z-score weights, moss penalised unless moss_ok)."""
    cands = []
    for _ in range(n):
        u0, v0 = rng.random(), rng.random()
        cands.append((u0, v0) + _rock_window_mean(u0, v0, w_m / tile, h_m / tile))
    lum = np.array([c[2] for c in cands])
    mo = np.array([c[3] for c in cands])
    zl = (lum - lum.mean()) / max(float(lum.std()), 1e-6)
    zm = (mo - mo.mean()) / max(float(mo.std()), 1e-6)
    w = np.exp(-0.9 * dark * zl) * (1.0 if moss_ok else np.exp(-0.8 * np.maximum(zm, 0.0)))
    i = rng.choices(range(n), weights=list(w), k=1)[0]
    return cands[i][0], cands[i][1]


def _rock_face_uv(pts, n, st):
    """UV of one LK_ROCK polygon: a continuous box projection in WORLD axes (the dominant axis of the face normal n), one density k, one 90-degree turn and one offset per stone `st`, so all faces of
    a stone that lean the same way share ONE continuous mapping (no seam, no triangle split) and a neighbouring stone differs."""
    ax = int(np.argmax(np.abs(n)))
    cols = {2: (0, 1), 0: (1, 2), 1: (0, 2)}[ax]
    tile = L.LOOK["LK_ROCK"][2]
    out = []
    for q in pts:
        a, b = float(q[cols[0]]) * st["k"] / tile, float(q[cols[1]]) * st["k"] / tile
        if st["turn"]:
            a, b = b, a
        out.append((a + st["u0"], b + st["v0"]))
    return out


# --------------------------------------------------------------------------------------------- stone shapes
def _box_corners(rng, sx, sy, sz, top_rag=0.0):
    """8 corners (ix, iy, iz in {0, 1}) of a hand-hewn block: origin = centre of the bottom face, x along the wall, y thickness, z up. A box pushed through a random taper + shear (no two faces
    parallel) with a tilted top plane; top_rag lowers and slopes the top steeply (a broken top: up to ~40 % of the height at one corner)."""
    tx, ty = rng.uniform(-0.04, 0.05), rng.uniform(-0.05, 0.05)
    shx, shy = rng.uniform(-0.05, 0.05) * sz, rng.uniform(-0.05, 0.05) * sz
    twist = rng.uniform(-0.03, 0.03)
    sl_x, sl_y = rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06)
    drop = rng.uniform(0.0, 0.04) + top_rag * rng.uniform(0.15, 0.45)
    rag_x, rag_y = top_rag * rng.uniform(-1.1, 1.1), top_rag * rng.uniform(-0.8, 0.8)
    C = {}
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                u, v = (ix - 0.5), (iy - 0.5)
                x, y = u * sx * (1.0 + tx * (iz * 2 - 1)), v * sy * (1.0 + ty * (iz * 2 - 1))
                if iz:
                    c, sn = math.cos(twist), math.sin(twist)
                    x, y = c * x - sn * y, sn * x + c * y
                    x, y = x + shx, y + shy
                    z = sz * (1.0 - drop - (sl_x + rag_x) * u - (sl_y + rag_y) * v)
                    z = max(z, 0.18 * sz)
                else:
                    z = sz * 0.012 * (u + v)                       # the bed is almost flat
                C[(ix, iy, iz)] = np.array([x, y, z])
    return C


def _fracture_planes(rng, C, sx, sy, sz, rag):
    """1-2 fracture planes across the top of a broken stone (a ragged, steeply cut top: 14-37 deg, up to 30 % of the height removed on one side). [(n, d)]"""
    tops = [C[(i, j, 1)] for i in (0, 1) for j in (0, 1)]
    t0 = np.mean(tops, axis=0)
    out = []
    for _ in range(1 + (1 if rng.random() < 0.55 else 0)):
        al = rng.uniform(0.25, 0.65)
        ph = rng.uniform(0.0, math.tau)
        n = np.array([math.sin(al) * math.cos(ph), math.sin(al) * math.sin(ph), math.cos(al)])
        q = t0 + np.array([math.cos(ph) * rng.uniform(0.0, 0.30) * sx, math.sin(ph) * rng.uniform(0.0, 0.30) * sy, -rng.uniform(0.03, 0.28) * sz])
        out.append((n, float(n @ q)))
    return out


def _split_planes(rng, C, sx, sy, sz):
    """a shallow quarry-split on the front or the back face: a plane through a point of the face tilted 5-10 deg (up to ~4 cm deep at the far end) - the face shows two planes at an obtuse angle."""
    out = []
    side = 1 if rng.random() < 0.5 else -1
    be = rng.uniform(0.09, 0.18)
    ps = rng.uniform(0.0, math.tau)
    n = np.array([math.sin(be) * math.cos(ps), side * math.cos(be), math.sin(be) * math.sin(ps)])
    q = np.array([rng.uniform(-0.25, 0.25) * sx, side * 0.5 * sy, rng.uniform(0.3, 0.7) * sz])
    out.append((n / np.linalg.norm(n), float(n / np.linalg.norm(n) @ q)))
    return out


class StoneSet:
    """Collects stones into DRESS_<kind>_<nn>_<pp> meshes of <= max_faces faces: LK_MASONRY (per-face brick-interior UV window of the face's own plane) with LK_ROCK on the tops and on some stones
    (one continuous box projection per stone, darker-leaning window), FLAT shading. Every face is an exactly planar n-gon (hole09_stone)."""

    def __init__(self, D, prefix, seed, clip=None, max_faces=300, rock_share=0.26, rock_tops=True):
        self.D, self.prefix = D, prefix
        self.rng = random.Random(seed)
        self.clip = clip                       # clip(X, Y) -> bool array: every vertex of a stone must pass
        self.base = L._next_name(D, prefix)
        self.mat = L.look_material("LK_MASONRY", D)
        self.mat_rock = L.look_material("LK_ROCK", D)
        self.max_faces = max_faces
        self.rock_share = rock_share
        self.rock_tops = rock_tops
        self.part = 0
        self.objs = []
        self.n_blocks = 0
        self.n_refused = 0
        self.refused = []                      # (x, y) of every refused stone
        self.records = []                      # (kind, bottom z, centre x, y) of every stone (for the report)
        self.tris = 0
        self.n_faces = 0
        self._reset()

    def _reset(self):
        self.V, self.F, self.UV, self.MI = [], [], [], []

    def flush(self):
        if not self.F:
            return
        name = f"{self.base}_{self.part:02d}"
        mats = [self.mat, self.mat_rock] if 1 in self.MI else [self.mat]
        ob = L._new_piece(self.D, name, self.V, self.F, self.UV, list(self.MI), mats, col="STRUCTURES", sharp_deg=32.0)
        ob.data.shade_flat()                   # loop normal == face normal: no diagonal shading steps inside a face
        ob.data.update()
        ob["h9_class"] = "masonry"
        self.objs.append(ob)
        self.part += 1
        self._reset()

    def add_poly(self, P_loc, faces, normals, origin, R, kind="block", widest_uv=False, force_masonry=False, rock_sides=None):
        """Add one stone given as a planar-faced polyhedron (local vertices P_loc (n, 3), faces = vertex id lists ccw seen from outside, their outward normals), placed at origin (world, m) with the 3x3
        rotation R. Returns True when it was kept (every vertex passes the clip)."""
        W = [Vector(origin) + R @ Vector(tuple(v)) for v in P_loc]
        if self.clip is not None:
            xy = np.array([(w.x, w.y) for w in W])
            if not bool(np.all(self.clip(xy[:, 0], xy[:, 1]))):
                self.n_refused += 1
                self.refused.append((float(origin[0]), float(origin[1])))
                return False
        if len(self.F) + len(faces) > self.max_faces:
            self.flush()
        rng = self.rng
        base = len(self.V)
        self.V.extend((float(w.x), float(w.y), float(w.z)) for w in W)
        pref = pick_seg(rng)
        if rock_sides is None:
            rock_sides = (not force_masonry) and (rng.random() < self.rock_share)
        wp = np.array([tuple(w) for w in W])
        ext = wp.max(axis=0) - wp.min(axis=0)
        tile = L.LOOK["LK_ROCK"][2]
        st = dict(k=rng.uniform(0.85, 1.45), turn=rng.random() < 0.5)
        st["u0"], st["v0"] = rock_offset(rng, float(max(ext[0], ext[1])), float(max(ext[1], ext[2])), tile, moss_ok=False)
        for f, nl in zip(faces, normals):
            nw = np.array(tuple(R @ Vector(tuple(nl))))
            pts = [W[i] for i in f]
            top = nw[2] > 0.70
            use_rock = (top and self.rock_tops and not force_masonry) or (rock_sides and nw[2] > -0.6)
            self.F.append(tuple(base + i for i in f))
            if use_rock:
                self.UV.append(_rock_face_uv([tuple(p_) for p_ in pts], nw, st))
                self.MI.append(1)
            else:
                self.UV.append(_face_uv(rng, pts, widest=widest_uv, pref=pref))
                self.MI.append(0)
            self.tris += max(1, len(f) - 2)
        self.n_faces += len(faces)
        self.n_blocks += 1
        self.records.append((kind, float(min(w.z for w in W)), float(origin[0]), float(origin[1])))
        return True

    def stone(self, origin, yaw, sx, sy, sz, top_rag=0.0, chamfer=0.35, tilt=0.015, kind="block", bulge_faces=(), widest_uv=False, top_chip=None, chip_scale=1.0, split_p=0.30):
        """One hand-hewn stone (hole09_stone.build_stone): `chamfer` = the old chip probability knob (mapped to 0.35 + 0.7 x chamfer per corner), `chip_scale` scales the corner chips, `top_chip` caps the chips of
        the top corners (a stone that carries another one), `split_p` = chance of a quarry-split on the front or back face (not on stones that carry another)."""
        rng = self.rng
        R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'X') @ Matrix.Rotation(rng.uniform(-tilt, tilt), 3, 'Y')
        C = _box_corners(rng, sx, sy, sz, top_rag)
        extra = []
        if top_rag > 0.0:
            extra += _fracture_planes(rng, C, sx, sy, sz, top_rag)
        if top_chip is None and rng.random() < split_p and min(sx, sz) > 0.3:
            extra += _split_planes(rng, C, sx, sy, sz)
        res = ST.build_stone(rng, C, chip_p=min(0.95, 0.35 + 0.7 * chamfer), chip_leg=(0.05 * chip_scale, 0.17 * chip_scale), top_chip=top_chip, bevel_p=0.35, extra_planes=extra, top_axis=2)
        if res is None:
            return False
        P_loc, faces, normals = res
        return self.add_poly(P_loc, faces, normals, origin, R, kind, widest_uv, force_masonry=(kind in ("lintel", "voussoir")))


