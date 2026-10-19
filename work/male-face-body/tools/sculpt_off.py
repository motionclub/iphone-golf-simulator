"""Male face sculpt, offline (numpy), 2026-10-17 chat 11.  python3 tools/sculpt_off.py <params.json> <tag>
Targets live in the game face frame (mm, after the runtime warp with the NEW male constants `warp`): the midline profile is pulled to
reference sheet 07 (eval/ref07_tables.npz) with lateral falloffs per zone (nose / lips / chin), plus optional width terms. The source
displacement is found by inverting the warp per vertex (finite-difference Jacobian, fixed-point), then smoothed (Taubin) and passed
through the female pass's topology guards (sliver_fix, crease_guard, sharpen_lost, split_guard: no edge may cross Unity's 60-degree
split angle, the imported vertex count must stay 44,168).  Output: eval/<tag>_delta.npy (per source vertex, metres) + <tag>_sculpt.json."""
import sys, os, json, types
sys.modules.setdefault('bpy', types.ModuleType('bpy'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, off, ft, sculpt_mouth as SM
W = off.W

def gauss1d(v, s):
    k = np.exp(-.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum()
    pad = np.pad(v, len(k) // 2, mode='edge'); return np.convolve(pad, k, 'valid')

def desired(G, h, p, Rt, cur_front):
    """Game-frame displacement (mm) per welded vertex."""
    x, y, z = G[:, 0], G[:, 1], G[:, 2]; ax = np.abs(x)
    ys = np.arange(5, -140, -.5)
    ref = np.interp(ys, Rt['y'][::-1], Rt['front'][::-1])
    dz = np.nan_to_num(ref - cur_front(ys))
    dz = gauss1d(dz, p.get('profile_sigma', 4))
    yk = np.array(p['profile_y'])                                  # [top fade start, top full, bottom full, bottom fade end]
    env = off.smooth(yk[0], yk[1], -ys) * (1 - off.smooth(yk[2], yk[3], -ys))
    dz = np.clip(dz * env, -p['max_dz'], p['max_dz'])
    Dz = np.interp(y, ys[::-1], dz[::-1])
    # lateral reach per height: nose / lips / chin
    zw = p['zones']                                                 # list of [y_top, y_bot, full_x, fade_x]
    fg = np.full(len(ys), float(zw[-1][2])); dg = np.full(len(ys), float(zw[-1][3]))
    for yt, yb, fx, fd in zw:
        m = (ys <= yt) & (ys > yb); fg[m] = fx; dg[m] = fd
    fg = gauss1d(fg, 6); dg = gauss1d(dg, 6)
    full = np.interp(y, ys[::-1], fg[::-1]); fade = np.interp(y, ys[::-1], dg[::-1])
    lat = 1 - off.smooth(full, fade, ax)
    fr = cur_front(np.clip(y, -139, 4))
    front = off.smooth(fr - p['depth'][1], fr - p['depth'][0], z)   # only the front skin, not the back of the head
    D = np.zeros_like(G); D[:, 2] = Dz * lat * front * p.get('profile_gain', 1.0)
    for t in p.get('bumps', []):                                    # local adjustments: [cx, cy, sx, sy, dx, dy, dz, mirror]
        cx, cy, sx, sy, dx, dy, dzz, mir = t[:8]
        xx = ax if mir else x
        w = np.exp(-.5 * (((xx - cx) / sx) ** 2 + ((y - cy) / sy) ** 2)) * (front if len(t) < 9 or t[8] else off.smooth(-70, -40, z))
        if len(t) > 9: w = w * (1 - off.smooth(t[9] - 3, t[9], y))
        D[:, 0] += (np.sign(x) if mir else 1) * dx * w; D[:, 1] += dy * w; D[:, 2] += dzz * w
    for t in p.get('smooth_brush', []):                            # fill grooves: [cx, cy, sx, sy, strength, iterations] (mirrored in x)
        cx, cy, sx, sy, st, it = t
        w = np.exp(-.5 * (((ax - cx) / sx) ** 2 + ((y - cy) / sy) ** 2)) * front
        i_, j_ = h.edges[:, 0], h.edges[:, 1]; deg = np.bincount(i_, minlength=len(G)) + np.bincount(j_, minlength=len(G))
        Ls = G.copy()
        for _ in range(int(it)):
            acc = np.zeros_like(Ls); np.add.at(acc, i_, Ls[j_]); np.add.at(acc, j_, Ls[i_]); Ls = .5 * Ls + .5 * acc / np.maximum(deg, 1)[:, None]
        D += (Ls - G) * (st * w)[:, None]
    # keep the eyelids out of it (closed-lid blink triangles are near-degenerate: any delta flips Unity's 60-degree splits)
    er = np.sqrt(((ax - 38) / p.get('eye_rx', 24)) ** 2 + ((y + 4) / p.get('eye_ry', 17)) ** 2)
    D *= off.smooth(1.0, 1.35, er)[:, None]
    return D

def invert(h, S0, Gt, P, iters=5):
    """Source positions (welded, metres, object space) whose warp lands on Gt (face frame, metres)."""
    S = S0.copy(); eps = 1e-4
    rep = lambda s: s   # welded already
    def W_(s):
        f = h.to_face(s); x, y, z, live = off.warp_face(f[:, 0], f[:, 1], f[:, 2], P); o = np.stack([x, y, z], 1); o[~live] = f[~live]; return o
    for it in range(iters):
        g = W_(S); r = Gt - g
        if np.abs(r).max() < 2e-6: break
        f = h.to_face(S); J = np.zeros((len(S), 3, 3))
        for k in range(3):
            fe = f.copy(); fe[:, k] += eps; x, y, z, live = off.warp_face(fe[:, 0], fe[:, 1], fe[:, 2], P)
            ge = np.stack([x, y, z], 1); ge[~live] = fe[~live]; J[:, :, k] = (ge - g) / eps
        step = np.linalg.solve(J + np.eye(3) * 1e-6, r[:, :, None])[:, :, 0]
        S = h.from_face(f + step)
    return S

def split_guard_mean(P, D, tri, limit=60.0, margin=1.0, passes=60, keys=(), hold=None):
    """As sculpt_mouth.split_guard, but the hinge (edge + its two opposite vertices) takes its MEAN displacement: a rigid move keeps
    the source dihedral exactly while keeping the push (min-norm froze whole lips). Iterated: neighbours of a frozen hinge can flip."""
    from collections import defaultdict
    shapes = [P] + list(keys); base = [SM.dihedral(S, tri) for S in shapes]; opp = defaultdict(list)
    for t in tri:
        for k in range(3):
            a, b, c = int(t[k]), int(t[(k + 1) % 3]), int(t[(k + 2) % 3]); opp[(min(a, b), max(a, b))].append(c)
    hist = []
    for r in range(passes):
        if hold is not None: D[hold] = 0
        badl = []
        for S, (e0, a0) in zip(shapes, base):
            e1, a1 = SM.dihedral(S + D, tri)
            bad = ((a0 > limit) & (a1 <= limit + margin)) | ((a0 <= limit) & (a1 > limit - margin)); bad &= np.abs(a1 - a0) > .05
            badl.append(e1[bad])
        allbad = np.vstack(badl); hist.append(int(len(allbad)))
        if not len(allbad): return D, hist
        for e in allbad:
            hv = [int(e[0]), int(e[1])] + opp[(int(e[0]), int(e[1]))]
            D[hv] = D[hv].mean(0) if r < passes // 2 else D[hv[int(np.argmin(np.linalg.norm(D[hv], axis=1)))]]
    return D, hist

def split_guard_scale(P, D, tri, edges, nu, limit=60.0, margin=1.0, passes=80, keys=(), hold=None, spread=6):
    """Monotone 60-degree guard: a per-vertex gain lam (1 = full displacement) is cut by 0.6 on every hinge (edge + 2 opposite
    vertices) that would cross 60 degrees in the basis or any shape key, then eased with a min-only neighbour average so the cut
    fades smoothly. lam -> 0 always satisfies the guard, so it converges; only the problem hinges lose amplitude."""
    from collections import defaultdict
    shapes = [P] + list(keys); base = [SM.dihedral(S, tri) for S in shapes]; opp = defaultdict(list)
    for t in tri:
        for k in range(3):
            a, b, c = int(t[k]), int(t[(k + 1) % 3]), int(t[(k + 2) % 3]); opp[(min(a, b), max(a, b))].append(c)
    lam = np.ones(len(D)); i, j = edges[:, 0], edges[:, 1]; deg = np.bincount(i, minlength=nu) + np.bincount(j, minlength=nu)
    if hold is not None: lam[hold] = 0
    hist = []
    for r in range(passes):
        Dl = D * lam[:, None]; badl = []
        for S, (e0, a0) in zip(shapes, base):
            e1, a1 = SM.dihedral(S + Dl, tri)
            bad = ((a0 > limit) & (a1 <= limit + margin)) | ((a0 <= limit) & (a1 > limit - margin)); bad &= np.abs(a1 - a0) > .05
            badl.append(e1[bad])
        allbad = np.vstack(badl); hist.append(int(len(allbad)))
        if not len(allbad): return Dl, hist, lam
        hit = np.zeros(nu, bool)
        for e in allbad:
            hv = [int(e[0]), int(e[1])] + opp[(int(e[0]), int(e[1]))]; lam[hv] *= .75; hit[hv] = True
        if r >= spread: continue
        ring = ft.dilate(edges, nu, hit, 1) & ~hit
        acc = np.zeros(nu); np.add.at(acc, i, lam[j]); np.add.at(acc, j, lam[i]); avg = acc / np.maximum(deg, 1)
        lam[ring] = np.minimum(lam[ring], .5 * lam[ring] + .5 * avg[ring])
    return D * lam[:, None], hist, lam

def run(p, tag):
    h = off.Head(); P = dict(off.DEFAULT); P.update(p['warp'])
    Rt = off.ref_tables()
    S0 = h.U(h.base)                                                # welded source, metres
    G = h.U(h.warp(h.base, P)) * 1000
    fixedzone = (G[:, 1] < -150) | (G[:, 1] > 15) | (np.abs(G[:, 0]) > 75)
    ys = np.arange(5, -140, -.5)
    D_total = np.zeros_like(S0); hist = []
    for it in range(p.get('iters', 2)):
        Gc = h.U(h.warp(h.base + D_total[h.idx], P)) * 1000
        _, fr = off.slices(Gc, h.tri, ys); fr = np.nan_to_num(fr, nan=0)
        cur = lambda yy, fr=fr: np.interp(yy, ys[::-1], fr[::-1])
        Dg = desired(Gc, h, p, Rt, cur) * (1.0 if it == 0 else p.get('relax_gain', 1.0))
        Dg[fixedzone] = 0
        St = invert(h, S0 + D_total, (Gc + Dg) / 1000.0, P)
        Ds = St - (S0 + D_total)
        fixed = ~ft.dilate(h.edges, h.nu, ~fixedzone & (np.linalg.norm(Ds, axis=1) > 1e-6), 2)
        Ds = SM.smooth_field(Ds, h.edges, h.nu, p.get('smooth_iters', 6), .5, fixed)
        er = np.sqrt(((np.abs(Gc[:, 0]) - 38) / p.get('eye_rx', 24)) ** 2 + ((Gc[:, 1] + 4) / p.get('eye_ry', 17)) ** 2)
        Ds *= off.smooth(1.0, 1.35, er)[:, None]
        D_total += Ds; hist.append(float(np.abs(Dg).max()))
    P0 = S0
    keys = {k[4:]: h.U(h.d[k]) for k in h.d.files if k.startswith('key_') and k != 'key_Basis'}
    lid = np.zeros(h.nu, bool)
    for K in keys.values(): lid |= np.linalg.norm(K - S0, axis=1) > p.get('lid_eps', 1e-3)
    hold = ft.dilate(h.edges, h.nu, lid, p.get("lid_hold", 1)); taper = ft.dilate(h.edges, h.nu, hold, p.get("lid_taper", 2)) & ~hold
    D_total[hold] = 0; D_total[taper] *= .5
    soft = (np.abs(G[:, 0]) < 30) & (G[:, 1] < -60) & (G[:, 1] > -98) & (G[:, 2] > 20)
    fixed = ~ft.dilate(h.edges, h.nu, np.linalg.norm(D_total, axis=1) > 1e-7, 3)
    D, n0 = SM.sliver_fix(P0, D_total.copy(), h.tri, h.nu)
    D, rounds = SM.crease_guard(P0, D, h.tri, h.edges, h.nu, fixed, 58.0, rounds=p.get('crease_rounds', 16), soft=soft, soft_limit=p.get('lip_crease', 85.0))
    D, n1 = SM.sliver_fix(P0, D, h.tri, h.nu)
    sh = 0   # SM.sharpen_lost also pushes untouched 60-61 degree edges body-wide (hands, feet); the split guard covers crossings
    if p.get('debug'):
        for K in keys.values():
            ek0, ak0 = SM.dihedral(K, h.tri); ek1, ak1 = SM.dihedral(K + D, h.tri); b = ((ak0 > 60) & (ak1 <= 61)) | ((ak0 <= 60) & (ak1 > 59)); b &= np.abs(ak1 - ak0) > .05
            Gb = G[ek1[b][:, 0]]; print('DEBUG key bad before split', int(b.sum()), np.round(Gb[:6], 0).tolist(), 'D mm', np.round(np.linalg.norm(D[ek1[b][:, 0]], axis=1)[:6] * 1000, 2).tolist())
    D, sg, lam = split_guard_scale(P0, D, h.tri, h.edges, h.nu, passes=p.get('split_passes', 200), keys=list(keys.values()), hold=hold)
    np.save(f'{W}/eval/{tag}_lam.npy', lam)
    e0, a0 = SM.dihedral(P0, h.tri); e1, a1 = SM.dihedral(P0 + D, h.tri)
    new = int(((a1 > 60) & (a0 <= 60)).sum()); lost = int(((a1 <= 60) & (a0 > 60)).sum())
    for K in keys.values():
        ek0, ak0 = SM.dihedral(K, h.tri); ek1, ak1 = SM.dihedral(K + D, h.tri)
        new += int(((ak1 > 60) & (ak0 <= 60)).sum()); lost += int(((ak1 <= 60) & (ak0 > 60)).sum())
    Dv = D[h.idx]
    np.save(f'{W}/eval/{tag}_delta.npy', Dv)
    Gn = h.U(h.warp(h.base + Dv, P)) * 1000
    m = np.linalg.norm(D, axis=1) * 1000
    info = dict(iter_max_dg=hist, crease_rounds=rounds, slivers=[n0, n1], sharpened=sh, split_guard=sg, edges_new_gt60=new, edges_lost_gt60=lost,
                moved=int((m > .001).sum()), max_mm=round(float(m.max()), 2), warp=P)
    _, fn = off.slices(Gn, h.tri, ys); _, fo = off.slices(G, h.tri, ys)
    ref = np.interp(ys, Rt['y'][::-1], Rt['front'][::-1])
    info['profile'] = [(float(a), round(float(b), 1), round(float(c), 1), round(float(d), 1)) for a, b, c, d in zip(ys[::4], fo[::4], fn[::4], ref[::4])]
    json.dump(info, open(f'{W}/eval/{tag}_sculpt.json', 'w'), indent=1)
    np.save(f'{W}/eval/{tag}_G.npy', Gn)
    print('SCULPT', tag, {k: v for k, v in info.items() if k not in ('profile', 'warp')})
    return info

if __name__ == '__main__':
    p = json.load(open(sys.argv[1])); run(p, sys.argv[2])
