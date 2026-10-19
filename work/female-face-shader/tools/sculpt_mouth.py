"""Female jaw + lips sculpt (2026-10-17), toward reference sheet 07 (ArtDir/style/alive/neutral-reference-pack-2026-10-15).
Runs in Blender. Works on the CURRENT production head (work/jaw-sculpt-2026-10-12/Female_JawSculpt.blend = the installed
OriginalSeamBlinkFinish/Female.fbx), snapshotted once to ../source_female_1017.npz (basis + shape keys + authored normals).
All targets are in the game's face frame (HeroFaceReferenceFit warp frame, mm: x right, y up from the sclera centroid, z forward);
the game warp is applied (ft.game_warp) before measuring, so the result is what Unity draws.
  profile : the midline profile (subnasale .. menton) is pulled to the reference profile (stomion deeper, lower lip behind the
            upper lip, a real mentolabial groove, chin pad 3.5 mm back); lateral falloff follows the lip outline / chin width.
  width   : the lower-face side wall (jaw angle region, above the jaw border) moves out up to `wide` mm.
  corners : small tuck at the mouth corners (modiolus).
Vertex count/order, UVs, weights unchanged; shape keys get the same delta; authored custom normals rotated with the surface.
"""
import bpy, numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft
W = ft.WORK
SRC = W + '/source_female_1017.npz'
TRI = None

def snapshot():
    me = bpy.data.objects['Body'].data
    if not os.path.exists(SRC):
        keys = {k.name: ft.coords(me, k.name) for k in me.shape_keys.key_blocks}
        nrm = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', nrm)
        np.savez(SRC, basis=ft.coords(me), normals=nrm.reshape(-1, 3), **{'key_' + k: v for k, v in keys.items()})
    d = np.load(SRC)
    assert len(d['basis']) == len(me.vertices)
    return d['basis'], {k[4:]: d[k] for k in d.files if k.startswith('key_')}, d['normals']

def ctx():
    body = bpy.data.objects['Body']; feat = bpy.data.objects['ReferenceFeatures']; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    return ft.frame(body, feat, rig)

def to_face(co, F):
    eye, right, up, fwd = F; d = co - eye
    return np.stack([d @ right, d @ up, d @ fwd], 1) * 1000.0

def smooth(a, b, x): return ft.smooth(a, b, x)

def mid_profile(G, ys, tri=None, xw=4.0):
    """Midline front profile z(y) of game-frame points G (mm): the mesh cut by the plane x = 0 (exact polyline), front-most per y."""
    tri = TRI if tri is None else tri
    a, b, c = G[tri[:, 0]], G[tri[:, 1]], G[tri[:, 2]]
    pts = []
    for p, q in ((a, b), (b, c), (c, a)):
        m = (p[:, 0] * q[:, 0] < 0)
        t = p[m, 0] / (p[m, 0] - q[m, 0])
        pts.append(p[m] + (q[m] - p[m]) * t[:, None])
    P = np.vstack(pts); P = P[(P[:, 2] > -25) & (P[:, 1] < -40) & (P[:, 1] > -160)]
    out = np.full(len(ys), np.nan)
    for k, y in enumerate(ys):
        m = np.abs(P[:, 1] - y) < .35
        if m.any(): out[k] = P[m, 2].max()
    ok = ~np.isnan(out)
    return np.interp(ys, ys[ok], out[ok])

def target_profile(p):
    """Reference midline profile in our frame: knots (y, z) mm."""
    k = np.array(sorted(p['profile']))
    return lambda y: np.interp(y, k[:, 0], k[:, 1])

def border_y(ax, p):
    t = np.array(p['border']);  return np.interp(ax, t[:, 0], t[:, 1])

def field(G, p, cur_mid, tgt):
    """Forward-axis displacement (mm, game frame) for every point."""
    x, y, z = G[:, 0], G[:, 1], G[:, 2]; ax = np.abs(x)
    k = np.array(sorted(p['profile']))   # ascending y: k[0] = lowest (menton), k[-1] = subnasale
    inside = smooth(k[0, 0] - 2.0, k[0, 0] - .01, y) * (1 - smooth(k[-1, 0] + .01, k[-1, 0] + 2.0, y))
    dmid = (tgt(y) - cur_mid(y)) * inside
    # vertical extent of the profile pull: from just under the nose to the chin underside, fading over a few mm
    vy = smooth(p['pull_top'][0], p['pull_top'][1], -y) * (1 - smooth(p['pull_bot'][0], p['pull_bot'][1], -y))
    hw = p['mouth_hw']
    lipband = 1 - smooth(p['lip_to_chin'][0], p['lip_to_chin'][1], -y)        # 1 in the lip rows, 0 on the chin
    lip_lat = 1 - smooth(p['lip_lat'][0] * hw, p['lip_lat'][1] * hw, ax)
    chin_lat = 1 - smooth(p['chin_lat'][0], p['chin_lat'][1], ax)
    lat = lipband * lip_lat + (1 - lipband) * chin_lat
    front = smooth(p['front_z'][0], p['front_z'][1], z)                       # only the face's front surface
    Dz = dmid * vy * lat * front
    # mouth-corner tuck (modiolus)
    cy = p['seam_y']; cr = p['corner_r']
    Dz -= p['corner_tuck'] * np.exp(-((ax - hw) ** 2 + (y - cy) ** 2) / (2 * cr * cr)) * front
    # lower-face side wall out (jaw angle), above the jaw border, below the cheekbone, behind the face front
    by = border_y(ax, p)
    wv = smooth(by - 1.0, by + p['wide_ramp'], y) * (1 - smooth(p['wide_top'][0], p['wide_top'][1], y))
    wl = smooth(p['wide_x'][0], p['wide_x'][1], ax) * (1 - smooth(p['wide_z'][0], p['wide_z'][1], z))
    e = p['ear']; reach = np.sqrt(((y - e[0]) / e[2]) ** 2 + ((z - e[1]) / e[3]) ** 2)
    wl = wl * smooth(1.25, 1.6, reach)
    Dx = np.sign(x) * p['wide'] * wv * wl
    if 'jawfill' in p:      # the jaw edge itself out (front silhouette y -77..-108), not the neck below it
        q = p['jawfill']
        v = np.interp(y, *np.array(q['y_profile']).T)
        lat = smooth(q['x'][0], q['x'][1], ax)
        below = smooth(by - q['below'][0], by - q['below'][1], y)
        back = 1 - smooth(q['z'][0], q['z'][1], z)
        e2 = smooth(1.25, 1.6, reach)
        Dx += np.sign(x) * q['amount'] * v * lat * below * back * e2
    return Dx, Dz

def slide_field(G, p):
    """Upward-axis displacement (mm): the upper vermilion border loop slides down (tent between subnasale and seam)."""
    if 'slide' not in p: return np.zeros(len(G))
    x, y, z = G[:, 0], G[:, 1], G[:, 2]; ax = np.abs(x); q = p['slide']
    yc = np.interp(ax, *np.array(q['border']).T)
    A = q['centre'] * np.exp(-(ax / q['centre_r']) ** 2) + q['base'] * (1 - smooth(q['fade'][0], q['fade'][1], ax))
    top, bot = q['top'], q['bot']
    up = np.clip((y - top) / (yc - top), 0, 1); dn = np.clip((y - bot) / (yc - bot), 0, 1)
    tent = np.where(y > yc, up, dn)
    front = smooth(p['front_z'][0], p['front_z'][1], z)
    return -A * tent * front

def compute(p, iters=3):
    base, keys, nrm = snapshot()
    me = bpy.data.objects['Body'].data
    F = ctx(); eye, right, up, fwd = F
    idx, tri, edges, nu = ft.topology_at(base, me)
    global TRI
    me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', t); TRI = t.reshape(-1, 3)
    female = True
    co = base.copy()
    ys = np.arange(-140, -50, .5)
    tgt = target_profile(p)
    Dtot = np.zeros((nu, 3))
    P0 = np.zeros((nu, 3)); P0[idx] = base
    # fixed: far from the zone
    G0 = to_face(ft.game_warp(base, female, True, F), F)
    U0 = np.zeros((nu, 3)); U0[idx] = G0
    zone = (U0[:, 1] < -40) & (U0[:, 1] > -150) & (np.abs(U0[:, 0]) < 100)
    fixed = ~ft.dilate(edges, nu, zone, 2)
    hist = []
    G = to_face(ft.game_warp(co, female, True, F), F)
    Dy = slide_field(G, p)
    if np.abs(Dy).max() > 0:
        Du = np.zeros((nu, 3)); Du[idx] = np.outer(Dy, up) / 1000.0
        Du[fixed] = 0; Dtot += Du; co = base + Dtot[idx]
    for it in range(iters):
        G = to_face(ft.game_warp(co, female, True, F), F)
        cm = mid_profile(G, ys)
        cur = lambda y, cm=cm: np.interp(y, ys, cm)
        Dx, Dz = field(G, p, cur, tgt)
        if it > 0: Dx = Dx * 0           # width is applied once (not a target-tracking term)
        D = np.zeros((len(co), 3))
        D += (np.outer(Dx, right) + np.outer(Dz, fwd)) / 1000.0
        Du = np.zeros((nu, 3)); Du[idx] = D
        Du = smooth_field(Du, edges, nu, p['smooth_iters'], .5, fixed)
        Dtot += Du
        co = base + Dtot[idx]
        hist.append(float(np.abs(Dz).max()))
    lipzone = (np.abs(U0[:, 0]) < 29) & (U0[:, 1] < -64) & (U0[:, 1] > -96) & (U0[:, 2] > -12)
    Dtot, nfix0 = sliver_fix(P0, Dtot, tri, nu)
    Dtot, rounds = crease_guard(P0, Dtot, tri, edges, nu, fixed, 58.0, rounds=p.get("crease_rounds", 16), soft=lipzone, soft_limit=p.get("lip_crease", 85.0))
    Dtot, nfix = sliver_fix(P0, Dtot, tri, nu)
    Dtot, sh = sharpen_lost(P0, Dtot, tri, nu)
    Dtot, sg = split_guard(P0, Dtot, tri, passes=p.get("split_passes", 20))
    sg = dict(sharpened=sh, guard=sg)
    co = base + Dtot[idx]
    G = to_face(ft.game_warp(co, female, True, F), F)
    print('SLIVERS fixed', nfix, 'SPLIT GUARD', sg)
    return base, keys, nrm, idx, tri, edges, nu, Dtot, dict(iter_max_dz=hist, crease_rounds=rounds), G

def sliver_fix(P, D, tri, nu, area_mm2=0.25, passes=3):
    """Near-degenerate triangles: their odd vertex (the one closest to the opposite edge) takes the displacement interpolated along
    that edge, so the sliver stays flat instead of folding (Unity splits vertices at folds past 60 degrees)."""
    n = 0
    e0, a0 = dihedral(P, tri); sharp = {tuple(e) for e in e0[a0 > 55]}     # slivers already folded in the source stay as they are
    def keep(t): return any(tuple(sorted((int(t[i]), int(t[(i + 1) % 3])))) in sharp for i in range(3))
    for _ in range(passes):
        a = P[tri[:, 0]]; b = P[tri[:, 1]]; c = P[tri[:, 2]]
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2 * 1e6
        for t in tri[area < area_mm2]:
            if keep(t): continue
            best = None
            for k in range(3):
                v, e0, e1 = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
                ev = P[e1] - P[e0]; L2 = ev @ ev
                if L2 < 1e-14: continue
                u = np.clip((P[v] - P[e0]) @ ev / L2, 0, 1); dist = np.linalg.norm(P[e0] + u * ev - P[v])
                if best is None or dist < best[0]: best = (dist, v, e0, e1, u)
            if best is None: continue
            _, v, e0, e1, u = best
            D[v] = D[e0] * (1 - u) + D[e1] * u; n += 1
    return D, n

def sharpen_lost(P, D, tri, nu, limit=60.0, target=61.0, step=1e-4, cap=15):
    """Edges past 60 degrees in the source that the sculpt softened below it: push their two vertices outward along the vertex
    normal in 0.1 mm steps (at most 1.5 mm) until the crease is back past 60 degrees (a crisp vermilion border, not a new split)."""
    e0, a0 = dihedral(P, tri); moved = 0
    for _ in range(cap):
        Q = P + D; e1, a1 = dihedral(Q, tri)
        lost = (a0 > limit) & (a1 <= target)
        if not lost.any(): break
        N = ft.vertex_normals(Q, tri)
        vs = np.unique(e1[lost].ravel()); D[vs] += N[vs] * step; moved = len(vs)
    return D, int(moved)

def split_guard(P, D, tri, limit=60.0, margin=1.0, passes=20):
    """Unity splits vertices at edges sharper than its 60-degree smoothing angle: every edge must stay on the same side of 60 degrees
    as in the source, or the imported vertex count (and every vertex-indexed bank: shoulder fit, cover masks, correctives) changes.
    An edge that changed side gets its 4-vertex hinge moved rigidly (the mean displacement), which restores its source angle."""
    e0, a0 = dihedral(P, tri)
    # opposite vertices of each edge
    from collections import defaultdict
    opp = defaultdict(list)
    for t in tri:
        for k in range(3):
            a, b, c = int(t[k]), int(t[(k + 1) % 3]), int(t[(k + 2) % 3])
            opp[(min(a, b), max(a, b))].append(c)
    hist = []
    for r in range(passes):
        e1, a1 = dihedral(P + D, tri)
        bad = ((a0 > limit) & (a1 <= limit + margin)) | ((a0 <= limit) & (a1 > limit - margin))
        bad &= np.abs(a1 - a0) > .05
        hist.append(int(bad.sum()))
        if not bad.any(): return D, hist
        for e in e1[bad]:
            hv = [int(e[0]), int(e[1])] + opp[(int(e[0]), int(e[1]))]
            D[hv] = D[hv[int(np.argmin(np.linalg.norm(D[hv], axis=1)))]]   # rigid: the least-moved hinge vertex leads (keeps the nose/locked side still)
    return D, hist

def smooth_field(D, edges, n, iters, lam, fixed):
    i, j = edges[:, 0], edges[:, 1]
    deg = np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
    D = D.copy(); D[fixed] = 0
    for it in range(iters):
        acc = np.zeros_like(D); np.add.at(acc, i, D[j]); np.add.at(acc, j, D[i])
        step = lam if it % 2 == 0 else -(lam + .03)
        D = D + step * (acc / np.maximum(deg, 1)[:, None] - D); D[fixed] = 0
    return D

def dihedral(P, tri):
    fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1), 1e-15)[:, None]
    e = np.vstack([np.sort(tri[:, [0, 1]], 1), np.sort(tri[:, [1, 2]], 1), np.sort(tri[:, [2, 0]], 1)]); f = np.tile(np.arange(len(tri)), 3)
    o = np.lexsort((e[:, 1], e[:, 0])); e = e[o]; f = f[o]
    same = (e[1:] == e[:-1]).all(1)
    return e[:-1][same], np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', fn[f[:-1][same]], fn[f[1:][same]]), -1, 1)))

def crease_guard(P, D, tri, edges, nu, fixed, limit, rounds=16, soft=None, soft_limit=85.0):
    e0, a0 = dihedral(P, tri)
    lim = np.full(len(e0), limit)
    if soft is not None: lim[soft[e0[:, 0]] & soft[e0[:, 1]]] = soft_limit
    for r in range(rounds):
        e1, a1 = dihedral(P + D, tri)
        bm = (a1 > lim) & (a1 > a0 + .25); bad = e1[bm]
        if not len(bad): return D, r
        if r in (0, rounds - 1): print('CREASE round', r, 'bad', len(bad), 'pos mm', np.round((P[bad[:, 0]] * 1000)[:8], 0).tolist(), 'angles', np.round(a1[bm][:8], 0).tolist(), np.round(a0[bm][:8], 0).tolist())
        m = np.zeros(nu, bool); m[bad.ravel()] = True
        m = ft.dilate(edges, nu, m, 3) & ~fixed
        i, j = edges[:, 0], edges[:, 1]; deg = np.bincount(i, minlength=nu) + np.bincount(j, minlength=nu)
        for _ in range(4):
            acc = np.zeros_like(D); np.add.at(acc, i, D[j]); np.add.at(acc, j, D[i])
            D[m] += .5 * (acc / np.maximum(deg, 1)[:, None] - D)[m]
    return D, rounds

def transfer_normals(base, nrm, idx, tri, edges, nu, smooth_iters=4):
    me = bpy.data.objects['Body'].data
    i, j = edges[:, 0], edges[:, 1]
    def sn(co):
        P = np.zeros((nu, 3)); P[idx] = co; N = ft.vertex_normals(P, tri)
        for _ in range(smooth_iters):
            acc = N.copy(); np.add.at(acc, i, N[j]); np.add.at(acc, j, N[i]); N = acc / np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None]
        return N
    n0 = sn(base); n1 = sn(ft.coords(me))
    lv = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', lv)
    a = n0[idx[lv]]; b = n1[idx[lv]]
    k = np.cross(a, b); s = np.linalg.norm(k, axis=1); c = np.einsum('ij,ij->i', a, b); kk = k / np.maximum(s, 1e-12)[:, None]
    v = nrm
    rot = v * c[:, None] + np.cross(kk, v) * s[:, None] + kk * (np.einsum('ij,ij->i', kk, v) * (1 - c))[:, None]
    out = np.where((s > 1e-7)[:, None], rot, v); out /= np.linalg.norm(out, axis=1)[:, None]
    me.normals_split_custom_set(out.tolist()); me.update()
    return dict(max_turn_deg=round(float(np.degrees(np.arcsin(np.clip(s.max(), 0, 1)))), 2), turned=int((s > 1e-4).sum()))

def apply(p):
    base, keys, nrm, idx, tri, edges, nu, D, info, G = compute(p)
    me = bpy.data.objects['Body'].data
    Dv = D[idx]
    for name, k in keys.items(): ft.set_coords(me, k + Dv, name)
    ft.set_coords(me, base + Dv); me.update()
    info['normals'] = transfer_normals(base, nrm, idx, tri, edges, nu)
    m = np.linalg.norm(Dv, axis=1) * 1000
    G0 = to_face(ft.game_warp(base, True, True, ctx()), ctx())
    info.update(moved=int((m > .001).sum()), max_mm=round(float(m.max()), 2),
                ymin_moved=round(float(G0[m > .001][:, 1].min()), 1), ymax_moved=round(float(G0[m > .001][:, 1].max()), 1))
    ys = np.arange(-135, -55, 1.0)
    info['mid_before'] = [round(float(v), 2) for v in mid_profile(G0, ys)]
    info['mid_after'] = [round(float(v), 2) for v in mid_profile(G, ys)]
    info['mid_target'] = [round(float(v), 2) for v in target_profile(p)(ys)]
    info['ys'] = ys.tolist()
    return info, Dv

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    prm_path, tag = argv[0], argv[1]
    p = json.load(open(prm_path))
    bpy.ops.wm.open_mainfile(filepath=ft.JAW + '/Female_JawSculpt.blend')
    info, Dv = apply(p)
    np.save(f'{W}/eval/{tag}_delta.npy', Dv)
    json.dump(info, open(f'{W}/eval/{tag}_sculpt.json', 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=f'{W}/scratch/{tag}.blend')
    print('SCULPT DONE', {k: v for k, v in info.items() if not k.startswith('mid') and k != 'ys'})
