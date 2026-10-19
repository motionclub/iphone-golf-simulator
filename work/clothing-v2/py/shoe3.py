"""SHOE v3 (2026-10-17, reference 05_shoes_ref.jpg): a performance sneaker on a DESIGNED last, built like the product.
  upper   : a subdivision cage of rounded cross-sections (heel counter, ankle, instep, toe box) per station along the foot, each section scaled
            just enough to hold the leg / sock at the collar (the hidden foot below does not dictate the shape), ends zipped closed
            (rounded toe box and heel), Catmull-Clark, then the collar mouth and the lacing throat are cut along designed curves
  collar  : padded collar roll (thick at the heel, slim along the eyestays) + heel pull tab
  tongue  : padded tongue in the throat, rising above the collar front
  laces   : 6 eyelet pairs, criss-cross laces arched over the tongue, a bow
  sole    : chunky midsole (sidewall wraps up the heel and the toe), outsole band (trim colour on tennis), tennis tread / golf cleats via shoe2
  trims   : Z-wing overlays on both sides, heel counter + toe bumper wrap, heel chevron: smooth fields for maps.details_shoe3 (trim colour follows
            the player's shoe colour pick)
Foot frame (shoe2.Frame): x lateral OUT, y heel -> toe, z up (ground z = 0; the sole sits under the ground plane like shoe2, so contact is unchanged).
Blender -b --factory-startup --python shoe3.py -- <hero> <design> <side L|R> <out.blend>     (export: py/export2.py ... detail=shoe3)"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy, bmesh
from polo2 import apply_modifier, smoothstep
from shoe2 import Frame, footprint, foot_top, make_mesh, tube_path, KIND, ROLE_SHOE, ROLE_SOLE, ROLE_HW, FABRIC


def design_male_tennis_05():
    return dict(
        name='male_tennis_05', heel_room=.010, toe_room=.022, side_room=.008,
        sole_t=(.030, .021), toe_spring=.012, lip=[(-.05, .026), (.08, .020), (.25, .012), (.60, .011), (.88, .014), (1.06, .022)],
        flare=.0055, band_h=.0140,
        # closed-last top line (z above the ground, frame units = metres) BEFORE the opening is cut; the foot top + room is a floor
        top=[(-.05, .104), (.10, .114), (.30, .122), (.45, .120), (.55, .106), (.65, .090), (.75, .075), (.85, .061), (.92, .051), (1.0, .041), (1.07, .032)],
        top_room=.009, shoulder=2.4,
        collar=[(-.05, .100), (.04, .097), (.14, .084), (.24, .079), (.32, .085), (.37, .094), (.40, .104)],   # collar mouth (y/L, z)
        throat=(.40, .80), throat_w=(.048, .030), collar_r=(.0105, .0090, .0042), tongue_rise=.022, tongue_w=.066,
        eyelets=6, lace_r=.0021,
        wings=[[(0.04, 0.0727), (0.091, 0.0762), (0.409, 0.015), (0.307, 0.0103)], [(0.085, 0.0758), (0.568, 0.0727), (0.614, 0.0602), (0.182, 0.0556)], [(0.42, 0.0532), (0.58, 0.0587), (0.511, 0.0384), (0.443, 0.0314)]],   # reference 05 side view: heel sweep, top bar to the laces, arrow
        heel_counter=.20, toe_bumper=.88, chev=True, trim_sole=True, perf=False, nubs=False, tread=True,
        roles=('Kit_Shoe', 'Kit_Sole', 'Kit_Buckle'), upper_t=.0026)


def design_male_tennis():
    """male reference pack 13-tennis-shoe-detail (2026-10-17): white perforated upper, ONE diagonal saddle band from the eyestay down to
    the midsole, toe cap + heel counter + padded collar + pull tab in the trim colour, white midsole over a darker outsole. Polygons are
    (y/L heel->toe, z m) traced from the lateral view (L = 455 px, z = .012 + (340 - y_px) * .00067)."""
    D = design_male_tennis_05()
    D.update(name='male_tennis',
             wings=[[(0.330, 0.0844), (0.451, 0.0870), (0.374, 0.004), (0.209, 0.004)]],
             heel_counter=.14, counter_slope=.35, toe_bumper=.82, toe_slope=-1.2, chev=False, trim_sole=False, perf=True, perf_y=(.47, .80),
             shoe_trim=dict(counter=1, toe=1, collar=.012, outsole_tone=.70))
    return D


def design_female_tennis():
    D = design_male_tennis_05()
    D.update(name='female_tennis', sole_t=(.027, .019), top_room=.008, collar_r=(.0085, .0072, .0036), tongue_rise=.016, lace_r=.0018,
             top=[(-.05, .090), (.10, .100), (.30, .108), (.45, .110), (.60, .100), (.72, .087), (.82, .072), (.91, .058), (1.0, .046), (1.07, .036)],
             collar=[(-.05, .084), (.04, .082), (.14, .073), (.24, .069), (.32, .074), (.40, .087), (.44, .099)])
    return D


def _golf05():
    D = design_male_tennis_05()
    D.update(name='male_golf_05', sole_t=(.031, .024), lip=[(-.05, .015), (.08, .012), (.25, .010), (.60, .010), (.88, .011), (1.06, .014)],
             flare=.0040, band_h=.0060, wings=[], trim_sole=False, perf=True, nubs=True,
             nub_h=.0085, tread=False, tongue_rise=.016)
    return D


def design_male_golf_05():
    return _golf05()


def design_male_golf_14():
    """male reference pack 14-golf-shoe-detail: classic saddle shoe. Wide trim-colour saddle from the eyestay to the sole, heel counter +
    padded collar in the trim colour, stitched toe-cap seam (no colour), smooth leather (no perforation), sole in the trim colour.
    Lateral view traced: L = 447 px, z = .010 + (335 - y_px) * .00067."""
    D = _golf05()
    D.update(name='male_golf', wings=[[(0.441, 0.0837), (0.664, 0.067), (0.530, 0.004), (0.329, 0.004)]],
             heel_counter=.18, counter_slope=.45, toe_bumper=.86, toe_slope=-1.0, perf=False, trim_sole=True,
             shoe_trim=dict(counter=1, toe=0, collar=.012, outsole_tone=1.0))
    return D


def design_female_golf():
    D = design_female_tennis()
    D['name'] = 'female_golf'
    D.update(name='female_golf', sole_t=(.029, .022), lip=[(-.05, .014), (.08, .011), (.25, .009), (.60, .009), (.88, .010), (1.06, .013)],
             flare=.0036, band_h=.0055, wings=[], trim_sole=False, perf=True, nubs=True,
             nub_h=.0075, tread=False)
    return D


DESIGNS = {'male_tennis': design_male_tennis, 'male_tennis_05': design_male_tennis_05, 'female_tennis': design_female_tennis, 'male_golf': design_male_golf_14, 'male_golf_05': design_male_golf_05, 'female_golf': design_female_golf}


def prof(x, table):
    t = np.array(table, float); return np.interp(x, t[:, 0], t[:, 1])


def smooth1(a, n, w=(1, 2, 1)):
    a = np.array(a, float)
    for _ in range(n): a[1:-1] = (w[0] * a[:-2] + w[1] * a[1:-1] + w[2] * a[2:]) / sum(w)
    return a


def subsurf(ob, levels):
    m = ob.modifiers.new('ss', 'SUBSURF'); m.levels = levels; m.render_levels = levels; m.subdivision_type = 'CATMULL_CLARK'
    apply_modifier(ob, m)


def mesh_np(ob):
    me = ob.data; n = len(me.vertices)
    P = np.zeros(n * 3); me.vertices.foreach_get('co', P)
    return P.reshape(-1, 3)


def build(hero_id, design, side, outp):
    D = DESIGNS[design]()
    if os.environ.get('SHOE_DESIGN'): D.update(json.loads(os.environ['SHOE_DESIGN']))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import cv2io, glib as G, builtins
    cache = getattr(builtins, '_HCACHE', None)
    if cache is not None and hero_id in cache: hero, body = cache[hero_id]
    else:
        hero = cv2io.Hero(hero_id); body = G.Body(hero)
        if cache is not None: cache[hero_id] = (hero, body)
    fr = Frame(body, side); L = fr.L
    # ---------------------------------------------------------------- stations, footprint, leg hull
    Y = np.array([-.035, .01, .07, .15, .25, .36, .47, .58, .69, .79, .88, .955, 1.0]) * L
    Y[0] = -D['heel_room'] + .012; Y[-1] = L + D['toe_room'] - .010
    yfine = np.linspace(-.02 * L, L, 120)
    xc_f, w_f = footprint(fr, np.clip(yfine, .004, L - .004))
    ztop_f = foot_top(fr, np.clip(yfine, .004, L - .004), xc_f)
    xc = np.interp(Y, yfine, smooth1(xc_f, 8)); wfoot = np.interp(np.clip(Y, 0, L), yfine, w_f)
    yf = Y / L
    zc_collar = prof(yf, D['collar'])
    lip = prof(yf, D['lip'])
    # cross-section half width a (at the base) and top height per station: designed, never smaller than foot + room
    a = np.maximum(wfoot + D['side_room'], .030)
    a[0] *= .70; a[1] *= .95; a[-1] *= .80; a[-2] *= .97
    zt = prof(yf, D['top'])
    ftop = np.interp(np.clip(Y, 0, L), yfine, ztop_f)
    zt = np.maximum(zt, ftop + np.where(yf < D.get('foot_floor_to', .50), D['top_room'], .0035))   # the vamp follows its designed line but always holds the (cartoon) foot: skin poking out of a shoe could not be hidden
    z0 = lip - .004
    n_ex = D['shoulder']
    # the leg (and sock) at the collar: scale each rear section until the leg hull fits inside with room
    qa = fr.to(body.pos[(fr.wf + fr.wl) > .3])
    room = .0045 + .0030
    for k in range(len(Y)):
        if yf[k] > D['throat'][0] + .06: break
        m = (np.abs(qa[:, 1] - Y[k]) < .010) & (qa[:, 2] < zc_collar[k] + .004) & (qa[:, 2] > z0[k] + .004)
        if m.sum() < 3: continue
        dx = np.abs(qa[m, 0] - xc[k]) + room; dz = np.maximum(qa[m, 2] - z0[k] + room, 0)
        h = zt[k] - z0[k]
        s = np.max((dx / a[k]) ** n_ex + (dz / h) ** n_ex) ** (1 / n_ex)
        if s > 1: a[k] *= s
    a = smooth1(np.maximum.accumulate(a[:7]).tolist() + a[7:].tolist(), 2)          # the heel never pinches in before the ankle
    # ---------------------------------------------------------------- the cage: U sections (open at the bottom, the sole closes it)
    K = 11                                                     # points per section, base-left over the top to base-right
    th = np.linspace(math.pi, 0, K)                            # pi = inner side (-x), 0 = outer side (+x); the frame x points OUT
    V = []
    for k in range(len(Y)):
        h = zt[k] - z0[k]
        for t_ in th:
            c, s_ = math.cos(t_), math.sin(t_)
            x = xc[k] + a[k] * np.sign(c) * abs(c) ** (2 / n_ex)
            z = z0[k] + h * abs(s_) ** (2 / n_ex)
            V.append((x, Y[k], z))
    V = np.array(V); F = []
    idx = lambda k, i: k * K + i
    for k in range(len(Y) - 1):
        for i in range(K - 1): F.append((idx(k, i), idx(k, i + 1), idx(k + 1, i + 1), idx(k + 1, i)))
    # zipped ends: a centre spine between mirrored points closes the heel and the toe with quads (round after subdivision)
    for k, dy in ((0, -1.0), (len(Y) - 1, 1.0)):
        mid = K // 2; spine = []
        for i in range(mid):
            p = (V[idx(k, i)] + V[idx(k, K - 1 - i)]) / 2; p[1] += dy * (.006 + .004 * math.sin(math.pi * i / max(1, mid - 1)))
            V = np.vstack([V, p]); spine.append(len(V) - 1)
        spine.append(idx(k, mid))
        for i in range(mid):
            q = [idx(k, i), idx(k, i + 1), spine[i + 1], spine[i]]; F.append(tuple(q if dy > 0 else q[::-1]))
            q = [spine[i], spine[i + 1], idx(k, K - 2 - i), idx(k, K - 1 - i)]; F.append(tuple(q if dy > 0 else q[::-1]))
    ob = make_mesh('Upper', V, F)
    subsurf(ob, 3)
    P = mesh_np(ob)
    # ---------------------------------------------------------------- cut the collar mouth and the lacing throat
    yP = P[:, 1] / L
    t0, t1 = D['throat']
    zc = prof(yP, D['collar'])
    xcP = np.interp(P[:, 1], Y, xc)
    tw = np.interp(yP, [t0, t0 + .05, t1], [D['throat_w'][0], D['throat_w'][0], D['throat_w'][1]])
    cut_v = ((yP < t0) & (P[:, 2] > zc)) | ((yP >= t0 - .01) & (yP <= t1) & (np.abs(P[:, 0] - xcP) < tw / 2) & (P[:, 2] > np.interp(P[:, 1], Y, zt) - .045))
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    kill = [f for f in bm.faces if sum(cut_v[v.index] for v in f.verts) >= 2]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    P = mesh_np(ob)
    # the opening rim: ordered boundary loop, relaxed so the roll follows a clean line
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    bedges = [e for e in bm.edges if e.is_boundary]
    adj = {}
    for e in bedges:
        a_, b_ = e.verts[0].index, e.verts[1].index; adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
    loops = []; seen = set()
    for s0 in adj:
        if s0 in seen: continue
        lp = [s0]; seen.add(s0); prev = None; cur = s0
        while True:
            nx = [v for v in adj[cur] if v != prev and v not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; lp.append(cur); seen.add(cur)
        loops.append(lp)
    bm.free()
    # the mouth loop is the one that reaches highest; the base edge (bottom, open) is the other
    rim = max(loops, key=lambda lp: P[lp, 2].mean())
    R = P[rim].copy()
    for _ in range(12): R = (np.roll(R, 1, 0) + 2 * R + np.roll(R, -1, 0)) / 4
    P[rim] = R
    me = ob.data; me.vertices.foreach_set('co', P.astype(np.float32).ravel()); me.update()
    # ---------------------------------------------------------------- fields for the maps (upper)
    def dist_to_poly(Q, poly):
        d = np.full(len(Q), np.inf)
        for i in range(len(poly)):
            a0, a1 = poly[i], poly[(i + 1) % len(poly)]
            dd = a1 - a0; t_ = np.clip(((Q - a0) @ dd) / (dd @ dd), 0, 1); d = np.minimum(d, np.linalg.norm(Q - (a0 + t_[:, None] * dd), axis=1))
        # inside test (even-odd)
        x, y = Q[:, 0], Q[:, 1]; ins = np.zeros(len(Q), bool)
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1); ins ^= c
        return np.where(ins, -d, d)
    def upper_fields(P):
        yv, zv = P[:, 1], P[:, 2]; qx = P[:, 0] - np.interp(P[:, 1], Y, xc)
        d_rim = np.min(np.linalg.norm(P[:, None, :] - R[None, ::2, :], axis=2), axis=1)
        YZ = np.stack([yv / L, zv], 1)
        f_w = np.min([dist_to_poly(YZ, np.array(w)) for w in D['wings']], axis=0) if D['wings'] else np.full(len(P), .05)
        onside = smoothstep(.022, .034, np.abs(qx))
        f_wing = np.where(onside > .5, f_w * L * .35, .05)               # metres-ish, negative inside a wing
        f_counter = (D['heel_counter'] * L - (zv - .01) * D.get('counter_slope', .6)) - yv
        f_toe = yv - (D['toe_bumper'] * L - (zv - .01) * D.get('toe_slope', .5))
        zh = float(prof(np.array([0.0]), D['collar'])[0]); XZ = np.stack([qx, zv], 1)
        def seg(Q, a0, a1):
            dd = a1 - a0; t_ = np.clip(((Q - a0) @ dd) / (dd @ dd), 0, 1); return np.linalg.norm(Q - (a0 + t_[:, None] * dd), axis=1)
        f_chev = np.minimum(seg(XZ, np.array([-.026, zh - .010]), np.array([0, zh - .040])), seg(XZ, np.array([.026, zh - .010]), np.array([0, zh - .040])))
        f_chev = np.where(yv / L < .10, f_chev, .05)
        return dict(d_rim=d_rim, qy=yv / L, qz=zv, qx=qx, f_wing=f_wing, f_counter=f_counter, f_toe=f_toe, f_chev=f_chev,
                    f_eye=np.full(len(P), .05), f_stripe=np.where(onside > .5, f_wing + .007, .05) if os.environ.get('SHOE_FAST') else np.full(len(P), .05), f_bump=np.full(len(P), .05),
                    tr_stripe=np.full(len(P), 1.0 if D['wings'] else 0.0), tr_chev=np.full(len(P), 1.0 if D.get('chev') else 0.0),
                    tr_sole=np.full(len(P), 1.0 if D.get('trim_sole') else 0.0), perf=np.full(len(P), 1.0 if D.get('perf') else 0.0), shoeL=np.full(len(P), L))
    UF = upper_fields(P)
    # soft raised overlays (wings, heel counter, toe cap) as a smooth lift along the normal
    me = ob.data; me.update()
    N = np.zeros(len(P) * 3); me.vertices.foreach_get('normal', N); N = N.reshape(-1, 3)
    lift = (.0016 * (1 - smoothstep(-.0015, .0015, UF['f_wing'])) + .0014 * smoothstep(-.0015, .0015, UF['f_counter']) + .0012 * smoothstep(-.0015, .0015, UF['f_toe']))
    lift *= smoothstep(.006, .014, UF['d_rim'])
    P = P + N * lift[:, None]
    me.vertices.foreach_set('co', P.astype(np.float32).ravel()); me.update()
    for k_, v_ in upper_fields(P).items():
        at = me.attributes.new(k_, 'FLOAT', 'POINT'); at.data.foreach_set('value', np.asarray(v_, np.float32))
    nf = len(me.polygons)
    for k_, v_ in (('role', ROLE_SHOE), ('face_kind', KIND['upper']), ('fabric', FABRIC['leather']), ('panel', 0)):
        at = me.attributes.new(k_, 'INT', 'FACE'); at.data.foreach_set('value', np.full(nf, v_, np.int32))
    # UVs: u = arc around the section, v = y (subdivided from the cage would need a cage UV; project instead: cylindrical around the last)
    uvl = me.uv_layers.new(name='UVMap'); li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li)
    ang = np.arctan2(P[:, 2] - np.interp(P[:, 1], Y, z0), P[:, 0] - np.interp(P[:, 1], Y, xc))
    rr = np.interp(P[:, 1], Y, a)
    uv = np.stack([ang * rr, P[:, 1]], 1)
    uvl.data.foreach_set('uv', uv[li].astype(np.float32).ravel())
    objs = [ob]
    # ---------------------------------------------------------------- collar roll + eyestays (one padded tube round the opening)
    yr = R[:, 1] / L
    cr = D['collar_r']
    rad = np.where(yr < t0 - .03, np.interp(yr, [-.1, .12, t0 - .03], [cr[0], cr[1], cr[1]]), np.interp(yr, [t0 - .03, t0 + .03, 1.0], [cr[1], cr[2], cr[2]]))
    # inset the tube centre a little into the opening so it sits ON the rim
    cen = np.stack([np.interp(R[:, 1], Y, xc), R[:, 1], R[:, 2] - .02], 1)
    inward = cen - R; inward /= np.linalg.norm(inward, axis=1, keepdims=True) + 1e-12
    path = R + inward * rad[:, None] * .45
    path = np.vstack([path, path[:1]])
    TV, TF, tarc, tang = tube_path(path, np.append(rad, rad[0]), k=10, cap=False)
    objs.append(make_mesh('Collar', TV, TF, roles=ROLE_SHOE, kinds=KIND['band'], fabric=FABRIC['mesh'], panel=2, uv=np.stack([tarc, tang * .004], 1),
                          vattr=dict(d_rim=np.zeros(len(TV)), tg_edge=np.ones(len(TV)), qy=TV[:, 1] / L, qz=TV[:, 2], qx=TV[:, 0])))
    # ---------------------------------------------------------------- tongue
    ty = np.linspace(t0 - .015, min(t1 + .02, .86), 14) * L
    tx = np.interp(ty, Y, xc)
    t_top = np.maximum(np.interp(ty, Y, zt) - .006, np.interp(np.clip(ty, 0, L), yfine, ztop_f) + .004)   # inside the throat under the eyestays, but always over the instep
    rise = smoothstep(t0 + .08, t0 - .02, ty / L) * D['tongue_rise']
    tz = t_top + rise
    ty = ty - rise * .55                                                    # the tongue leans back above the collar
    tw2 = np.interp(ty / L, [t0, t1], [D['tongue_w'], D['tongue_w'] * .8])
    TV = []; nu = 7
    for j in range(len(ty)):
        for i in range(nu):
            u = (i / (nu - 1)) * 2 - 1
            TV.append((tx[j] + u * tw2[j] / 2, ty[j], tz[j] - .007 * u * u))
    TV = np.array(TV); TF = [(j * nu + i, j * nu + i + 1, (j + 1) * nu + i + 1, (j + 1) * nu + i) for j in range(len(ty) - 1) for i in range(nu - 1)]
    tob = make_mesh('Tongue', TV, TF, roles=ROLE_SHOE, kinds=KIND['tongue'], fabric=FABRIC['mesh'], panel=3, uv=TV[:, [0, 1]],
                    vattr=dict(tg_edge=np.abs(np.tile(np.linspace(-1, 1, nu), len(ty))), qy=TV[:, 1] / L, qz=TV[:, 2], qx=TV[:, 0]))
    subsurf(tob, 1); objs.append(tob)
    # ---------------------------------------------------------------- laces over the tongue
    ne = D['eyelets']; ye = np.linspace(t0 + .035, t1 - .015, ne) * L
    xe = np.interp(ye, Y, xc); ze = np.maximum(np.interp(ye, Y, zt) + .0005, np.interp(np.clip(ye, 0, L), yfine, ztop_f) + .0085)
    half = np.interp(ye / L, [t0, t1], [D['throat_w'][0], D['throat_w'][1]]) / 2 + .006
    LV, LF, LUV = [], [], []
    def lace(p0, p1):
        pts = np.array([p0 + (p1 - p0) * t_ for t_ in np.linspace(0, 1, 9)])
        pts[:, 2] += .0035 * np.sin(np.linspace(0, math.pi, 9))
        v_, f_, ar, ag = tube_path(pts, D['lace_r'], k=6, cap=True, flat=.55)
        o = len(LV); LV.extend(v_.tolist()); LF.extend([tuple(int(i) + o for i in f) for f in f_]); LUV.extend(np.stack([ar, ag * .002], 1).tolist())
    for i in range(ne - 1):
        pl0 = np.array([xe[i] - half[i], ye[i], ze[i]]); pr0 = np.array([xe[i] + half[i], ye[i], ze[i]])
        pl1 = np.array([xe[i + 1] - half[i + 1], ye[i + 1], ze[i + 1]]); pr1 = np.array([xe[i + 1] + half[i + 1], ye[i + 1], ze[i + 1]])
        lace(pl0, pr1); lace(pr0, pl1)
    # bow at the top eyelet pair
    pb = np.array([xe[0], ye[0] - .004, ze[0] + .008])
    for sg in (-1, 1):
        loop = np.array([pb + np.array([sg * .022 * math.sin(t_), -.010 * (1 - math.cos(t_)), .004 * math.sin(t_)]) for t_ in np.linspace(0, 2 * math.pi, 14)])
        v_, f_, ar, ag = tube_path(loop, D['lace_r'], k=6, cap=True, flat=.55); o = len(LV)
        LV.extend(v_.tolist()); LF.extend([tuple(int(i) + o for i in f) for f in f_]); LUV.extend(np.stack([ar, ag * .002], 1).tolist())
    objs.append(make_mesh('Laces', np.array(LV), LF, roles=ROLE_SHOE, kinds=KIND['lace'], fabric=FABRIC['lace'], panel=4, uv=np.array(LUV)))
    # ---------------------------------------------------------------- heel tab
    hz = float(prof(np.array([Y[0] / L]), D['collar'])[0])
    yb = float(np.min(P[:, 1]))                                               # the heel's back surface
    hp = np.array([[xc[0], yb + .004, hz - .022], [xc[0], yb - .006, hz - .012], [xc[0], yb - .009, hz + .004], [xc[0], yb - .006, hz + .016], [xc[0], yb + .004, hz + .020]])
    v_, f_, ar, ag = tube_path(hp, .0060, k=8, cap=True, flat=.30)
    objs.append(make_mesh('HeelTab', v_, f_, roles=ROLE_SHOE, kinds=KIND['tab'], fabric=FABRIC['twill'], panel=6, uv=np.stack([ar, ag * .003], 1)))
    # ---------------------------------------------------------------- sole unit: outline from the upper's base edge
    base = [lp for lp in loops if lp is not rim]
    BP = P[np.concatenate(base)] if base else P[P[:, 2] < np.interp(P[:, 1], Y, z0) + .002]
    ys2 = np.linspace(Y[0] - .012, Y[-1] + .010, 70)
    left = np.zeros(len(ys2)); right = np.zeros(len(ys2))
    for j, yv in enumerate(ys2):
        m = np.abs(BP[:, 1] - yv) < .006
        if m.sum() >= 2: left[j], right[j] = BP[m, 0].min(), BP[m, 0].max()
        else: left[j] = right[j] = np.nan
    g = ~np.isnan(left)
    left = np.interp(ys2, ys2[g], left[g]); right = np.interp(ys2, ys2[g], right[g])
    cxs = (left + right) / 2; hw = (right - left) / 2 + .002
    e = np.sqrt(np.clip(1 - ((np.clip(ys2[0] + .030 - ys2, 0, None)) / .030) ** 2, 0, 1)) * np.sqrt(np.clip(1 - ((np.clip(ys2 - (ys2[-1] - .036), 0, None)) / .036) ** 2, 0, 1))
    hw = smooth1(hw, 6) * np.maximum(e, .12)
    outline = np.concatenate([np.stack([cxs + hw, ys2], 1), np.stack([cxs - hw, ys2], 1)[::-1]])
    for _ in range(4): outline = (np.roll(outline, 1, 0) + 2 * outline + np.roll(outline, -1, 0)) / 4
    NP = len(outline); c2 = outline.mean(0)
    tan = np.roll(outline, -1, 0) - np.roll(outline, 1, 0); tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    nrm2 = np.stack([tan[:, 1], -tan[:, 0]], 1)
    if np.mean(np.sum(nrm2 * (outline - c2), axis=1)) < 0: nrm2 = -nrm2
    yo = outline[:, 1] / L
    T = np.interp(yo, [-.1, .62, 1.1], [D['sole_t'][0], D['sole_t'][1], D['sole_t'][1]])
    spring = D['toe_spring'] * np.clip((yo - .66) / .40, 0, 1) ** 2
    prot = float(D.get('nub_h', 0.0) if D.get('nubs') else (.0016 if D.get('tread') else 0.0))
    zb = -T + spring + prot; zos = zb + D['band_h']; lipo = prof(yo, D['lip']); fl = D['flare']
    bulge = fl * (1 + .5 * np.exp(-((yo - .08) / .14) ** 2))
    rows = [(lipo, .0006, 0), (lipo - .002, .0030, 0), ((lipo + zos) / 2 + .003, bulge, 0), ((lipo + zos) / 2 - .003, bulge * .96, 0), (zos + .0025, bulge * .80, 0),
            (zos, bulge * .86, 1), (zos - .0012, bulge * .95, 1), (zb + .0022, bulge * .92, 1), (zb, bulge * .60, 1)]
    SR = np.stack([np.concatenate([outline + nrm2 * (np.asarray(off)[:, None] if np.ndim(off) else off), np.broadcast_to(z_, (NP,))[:, None]], 1) for z_, off, _ in rows], 1)
    roles_r = [r for _, _, r in rows]
    nrw = SR.shape[1]; SV = SR.reshape(-1, 3); SF = []; srole = []
    for i in range(NP):
        i2 = (i + 1) % NP
        for r_ in range(nrw - 1): SF.append((i * nrw + r_, i2 * nrw + r_, i2 * nrw + r_ + 1, i * nrw + r_ + 1)); srole.append(roles_r[r_ + 1])
    SUV = np.stack([np.repeat(np.arange(NP) * .004, nrw), SR[:, :, 2].ravel()], 1)
    # caps on their own duplicated rings with planar UVs (fans sharing the wall's vertices stretched the UV packing 4x)
    nside = len(SV)
    bot = SR[:, -1, :]; top = SR[:, 0, :]
    SV = np.vstack([SV, bot, [[c2[0], c2[1], float(zb.mean())]], top, [[c2[0], c2[1], float(lipo.mean()) - .004]]])
    ob0 = nside; cb = nside + NP; ot0 = cb + 1; ct = ot0 + NP
    for i in range(NP): SF.append((ob0 + i, ob0 + (i + 1) % NP, cb)); srole.append(1)
    for i in range(NP): SF.append((ot0 + (i + 1) % NP, ot0 + i, ct)); srole.append(0)
    SUV = np.vstack([SUV, bot[:, :2] + [1.0, 0], [[c2[0] + 1.0, c2[1]]], top[:, :2] + [2.0, 0], [[c2[0] + 2.0, c2[1]]]])
    sole_trim = np.array(srole) == 1
    zos_v = np.concatenate([np.repeat(zos, nrw), zos, [zos.mean()], zos, [zos.mean()]])
    objs.append(make_mesh('Sole', SV, SF, roles=ROLE_SHOE,      # the sole follows the shoe colour pick; the outsole band is the trim channel (shoe2 rule) kinds=KIND['sole'],
                          fabric=np.where(sole_trim, FABRIC['rubber'], FABRIC['foam']), panel=5, uv=SUV,
                          vattr=dict(sole_y=SV[:, 1] / L, sole_z=SV[:, 2], sole_zos=zos_v, tr_sole=np.full(len(SV), 1.0 if D.get('trim_sole') else 0.0),
                                     perf=np.zeros(len(SV)), shoeL=np.full(len(SV), L))))
    # golf cleats: reuse shoe2's layout on this outline
    if D.get('nubs'):
        lay = [(.60, -.52), (.60, .52), (.72, -.58), (.72, 0.0), (.72, .58), (.85, -.42), (.85, .42), (.10, -.40), (.10, .40), (.21, -.56), (.21, .56)]
        NV, NF = [], []
        for (ry, rx) in lay:
            cy_ = ry * L; j = int(np.argmin(np.abs(ys2 - cy_))); cx_ = cxs[j] + rx * (hw[j] - .016)
            zt_ = float(np.interp(ry, yo[np.argsort(yo)], zb[np.argsort(yo)])) + .0008; b0 = len(NV)
            for zz, r_ in ((zt_, .0092), (zt_ - .0022, .0086), (zt_ - .0034, .0054), (zt_ - D['nub_h'] * .75, .0046), (zt_ - D['nub_h'], .0036)):
                for q in range(10): ph = 2 * math.pi * q / 10; NV.append((cx_ + r_ * math.cos(ph), cy_ + r_ * math.sin(ph), zz))
            for r_ in range(4):
                for q in range(10): q2 = (q + 1) % 10; NF.append((b0 + r_ * 10 + q, b0 + r_ * 10 + q2, b0 + (r_ + 1) * 10 + q2, b0 + (r_ + 1) * 10 + q))
            NF.append(tuple(b0 + 40 + q for q in range(10))[::-1])
        objs.append(make_mesh('Cleats', np.array(NV), NF, roles=ROLE_HW, kinds=KIND['nub'], fabric=FABRIC['rubber'], panel=7, uv=np.array(NV)[:, :2]))
    # ---------------------------------------------------------------- world space, orientation, thickness, join
    det = float(np.linalg.det(np.stack([fr.lat, fr.fwd, [0, 0, 1.]])))
    for o in objs:
        me = o.data; p = mesh_np(o)
        me.vertices.foreach_set('co', fr.back(p).astype(np.float32).ravel()); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        if o.name in ('Sole', 'Cleats', 'Laces', 'Collar', 'HeelTab'): bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        elif det < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free(); me.update()
    thick = {'Upper': D['upper_t'], 'Tongue': .0055}
    for o in objs:
        o.data.shade_smooth()
        for nm in ('outer', 'inner', 'rim'): o.data.materials.append(bpy.data.materials.get(nm) or bpy.data.materials.new(nm))
        if o.name in thick:
            sm = o.modifiers.new('solid', 'SOLIDIFY'); sm.thickness = thick[o.name]; sm.offset = -1; sm.use_even_offset = False
            sm.use_quality_normals = True; sm.use_rim = True; sm.material_offset = 1; sm.material_offset_rim = 2
            apply_modifier(o, sm)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.join()
    # one clean unwrap of the whole shoe (the fields drive the maps per texel, so any good layout works; the quick per-part UVs
    # above degenerate at the heel / toe and halved the texel density)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=.003, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.name = 'Kit_Shoe_' + side; ob['roles'] = list(D['roles'])
    # the wing overlays as polygons (y/L, z) for the maps: drawn per texel, crisp at any mesh density
    T_ = D.get('shoe_trim') or {}; py_ = D.get('perf_y', (.20, .66))
    ob['mapdata_shoetrim'] = [float(T_.get('counter', 0)), float(T_.get('toe', 0)), float(T_.get('collar', 0)), float(T_.get('outsole_tone', 1)), float(py_[0]), float(py_[1])]
    ob['mapdata_wings'] = [float(v) for w in D['wings'] for p in w for v in p]; ob['mapdata_wing_n'] = [len(w) for w in D['wings']] or [0]; ob['collar_prof'] = [float(v) for p in D['collar'] for v in p]
    bpy.ops.wm.save_as_mainfile(filepath=outp)
    print('SHOE3 %s %s L %.3f faces %d' % (design, side, L, len(ob.data.polygons)))


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    build(a[0], a[1], a[2], a[3])
