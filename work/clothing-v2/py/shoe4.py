"""SHOE v4 (2026-10-17, male reference pack sheets 13 tennis / 14 golf): the shoe is built from profiles TRACED off the reference sheet
(lateral view: outsole bottom, outsole top, midsole top, upper top line, collar line; top/sole view: outline) in reference units
(s = heel -> toe / shoe length, h = height above the sole bottom / shoe length), then fitted to the hero:
  - length Ls (design), heel 12 mm behind the foot heel, sole bottom at zb (the foot sole is z = 0, same convention as shoe2/shoe3)
  - the forefoot keeps the reference silhouette: the cartoon foot (taller than any real shoe) is NOT contained, its skin is hidden by
    the pipeline cover (gp/cover.foot_deep with GP_FOOT_ALL=1); only the worn SOCK at the collar decides the rear width (it is seen
    going into the mouth, so the mouth must hold it with room)
  - construction: outsole (rubber, herringbone / cleats), midsole (foam, flared sidewall), upper shell (leather, 2.6 mm, cut collar mouth +
    lacing throat), padded collar roll, tongue, eyelets + criss-cross laces, heel pull loop; panel colours (trim), perforations,
    stitching and tread are drawn per texel by maps.details_shoe4 from the same traced polygons (reference units) and the s/h fields.
Foot frame (shoe2.Frame): x lateral OUT, y heel -> toe, z up.
Blender -b --factory-startup --python shoe4.py -- <hero> <design> <side L|R> <out.blend>     (export: py/export2.py ... detail=shoe4)"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import bpy, bmesh
from polo2 import apply_modifier, smoothstep
from shoe2 import Frame, footprint, foot_top, make_mesh, tube_path, KIND, ROLE_SHOE, ROLE_SOLE, ROLE_HW, FABRIC

PIPE_DUMP = os.path.join(os.path.dirname(__file__), '..', 'pipeline', 'dump')


def px(points, x0=62., y0=590., L=670.):
    """reference sheet pixels (lateral view, heel left) -> (s, h)."""
    return [((x - x0) / L, (y0 - y) / L) for x, y in points]


def design_male_tennis():
    """sheet 13 (lateral view: heel back of the midsole x 62, toe tip x 732, ground y 590 -> L = 670 px)."""
    return dict(
        name='male_tennis', sport='tennis', Ls=.335, heel_off=.024, zb=-.030,
        bot=px([(62, 552), (70, 566), (100, 588), (200, 591), (500, 590), (600, 585), (650, 575), (700, 549), (722, 520), (732, 500)]),
        os_top=px([(62, 548), (90, 568), (150, 575), (300, 578), (500, 575), (600, 568), (650, 556), (680, 540), (710, 515), (726, 498)]),
        ms_top=px([(62, 486), (80, 478), (150, 482), (250, 488), (330, 498), (450, 530), (543, 542), (600, 535), (650, 525), (700, 500), (722, 482), (730, 476)]),
        # closed last top line (before the mouth / throat are cut); the throat is moved 0.08 s forward of the sheet so the mouth holds the sock
        top=[(0.0, .405), (.06, .415), (.14, .415), (.30, .43), (.42, .44), (.48, .41), (.56, .36), (.64, .31), (.72, .262), (.80, .228), (.88, .218), (.95, .205), (.985, .180), (1.0, .150)],
        collar=[(0.0, .392), (.05, .402), (.12, .404), (.20, .378), (.28, .350), (.36, .356), (.43, .382), (.50, .402)],
        throat=(.47, .76), throat_w=(.044, .026), collar_r=(.0115, .0098, .0045), tongue_top=(.42, .56), tongue_w=.090, tongue_w_top=.122,
        eyelets=7, lace_r=.0022, lace_flat=.42,
        flare=dict(heel=.016, side=.006, toe=.004), sole_bulge=.0035,
        upper_t=.0026, room=.006, fore_min=.066, subdiv=2,
        loop=dict(h0=.30, h1=.465, w=.0150),
        # panels in reference (s, h) units; one polygon set, both sides (the sheet's medial view mirrors the lateral one)
        panels=dict(
            trim=[px([(80, 392), (112, 392), (215, 470), (300, 372), (346, 362), (342, 420), (348, 498), (40, 498), (40, 392)]),       # heel counter + saddle
                  px([(530, 548), (548, 534), (580, 500), (620, 482), (660, 465), (700, 451), (722, 458), (760, 470), (760, 560), (530, 560)])],  # toe cap
            seams=[px([(560, 440), (452, 548)]), px([(300, 362), (560, 466)])],                        # vamp overlay, eyestay panel
            perf=dict(poly=px([(352, 420), (520, 470), (548, 444), (660, 452), (690, 458), (580, 500), (520, 530), (440, 540), (352, 520)]), pitch=.0072, r=.0011),
            counter_emboss=px([(80, 420), (110, 420), (170, 466), (80, 466)])),
        colours=dict(collar_trim=1, tongue_trim=0, outsole_tone=.60, midsole_tone=1.0, sole_trim=0),
        tread='herringbone', cleats=0,
        roles=('Kit_Shoe', 'Kit_Sole', 'Kit_Buckle'))


def design_male_golf():
    """sheet 14 (lateral view: heel back of the sole x 50, toe tip x 710, ground = lug bottom y 565 -> L = 660 px): classic saddle golf
    shoe; low navy sole (one unit, trim colour) with 6 star spikes + traction lugs, smooth leather, navy saddle + heel counter + padded
    collar, stitched cap toe, cream laces."""
    G = lambda pts: px(pts, x0=50., y0=565., L=660.)
    return dict(
        name='male_golf', sport='golf', Ls=.330, heel_off=.024, zb=-.026,
        bot=[(0, .038), (.015, .015), (.061, 0), (.379, 0), (.833, 0), (.924, .015), (.985, .05), (1.003, .091)],
        os_top=[(0, .060), (.015, .040), (.061, .028), (.379, .026), (.833, .026), (.924, .040), (.985, .075), (1.003, .10)],
        ms_top=[(0, .104), (.003, .106), (.076, .103), (.273, .091), (.40, .062), (.50, .042), (.803, .038), (.955, .068), (.992, .106), (1.0, .117)],
        top=[(0.0, .42), (.06, .435), (.14, .44), (.30, .44), (.42, .44), (.48, .40), (.56, .335), (.667, .258), (.803, .22), (.924, .182), (.977, .152), (.995, .118), (1.0, .10)],
        # the sheet's collar (h .31-.37) sits under the trouser break in sheet 03; on this hero the trouser hem is 11.8 cm up (the cartoon ankle),
        # so the collar rises to meet it and no ankle shows between hem and shoe (the golf kit has no socks)
        collar=[(0.0, .418), (.058, .432), (.121, .428), (.197, .405), (.288, .402), (.364, .410), (.43, .422), (.50, .430)],
        throat=(.47, .68), throat_w=(.040, .026), collar_r=(.0105, .0090, .0042), tongue_top=(.42, .53), tongue_w=.080, tongue_w_top=.112,
        eyelets=5, lace_r=.0024, lace_flat=.50,
        flare=dict(heel=.006, side=.0045, toe=.003), sole_bulge=.0012,
        upper_t=.0026, room=.006, fore_min=.064, subdiv=2,
        loop=None,
        panels=dict(
            trim=[[(.409, .417), (.424, .402), (.664, .258), (.636, .205), (.606, .152), (.561, .091), (.523, .045), (.50, -.02), (.288, -.02), (.288, .098), (.424, .356)],
                  [(-.06, .273), (.018, .273), (.076, .235), (.136, .174), (.174, .129), (.182, .098), (.19, -.02), (-.06, -.02)]],
            seams=[[(.859, .194), (.833, .144), (.803, .083), (.765, .030)]],
            perf=None, counter_emboss=None),
        colours=dict(collar_trim=1, tongue_trim=0, outsole_tone=1.0, midsole_tone=1.0, sole_trim=1),
        tread='lugs', cleats=6,
        roles=('Kit_Shoe', 'Kit_Sole', 'Kit_Buckle'))


# 10-18 silhouette pass: outline tables re-traced against sheets 13 / 14 with work/male-garments-refpack/tools/compare_lat.py (sheet units).
# instep=False keeps the sheet's throat line as the design; enclose=True then lifts / widens the upper wherever the cartoon foot needs it
# (+10 mm): hiding the foot under a sheet-thin upper (GP_FOOT_ALL=1) opened real see-through gaps in the pipeline suite (10-18, chat 5 split).
# The golf kit gets short socks (trouser colour) so the lower sheet collar shows no ankle.
# Round 7: shoes ~10 % longer than the foot needs (sheet proportions: the enclosing upper is tall + wide, length restores the side / top aspect);
# Room stays 10 mm (round 7 tried 7 mm with GP_SHOE_SKINW=1: skin spots came back on the medial forefoot); the pipeline skins the shoe with
# the foot's own weights (GP_SHOE_SKINW=1).
SILHOUETTE = {'male_tennis': {'instep': False, 'enclose': True, 'Ls': 0.365, 'encl_side': 0.0075, 'encl_room': 0.010, 'heel_off': 0.012, 'collar_drop': 0.018, 'collar': [[0.0, 0.392], [0.05, 0.402], [0.12, 0.404], [0.2, 0.372], [0.28, 0.345], [0.36, 0.356], [0.43, 0.39], [0.5, 0.402]], 'top': [[0.0, 0.405], [0.06, 0.415], [0.14, 0.415], [0.3, 0.43], [0.42, 0.44], [0.48, 0.4], [0.56, 0.352], [0.64, 0.305], [0.72, 0.258], [0.8, 0.226], [0.88, 0.214], [0.95, 0.202], [0.985, 0.178], [1.0, 0.15]], 'tongue_top': [0.42, 0.49], 'bow': 0.6},
              'male_golf': {'instep': False, 'enclose': True, 'Ls': 0.375, 'encl_side': 0.0075, 'encl_room': 0.010, 'collar': [[0.0, 0.345], [0.058, 0.362], [0.121, 0.345], [0.197, 0.272], [0.288, 0.282], [0.364, 0.33], [0.43, 0.385], [0.5, 0.4]], 'top': [[0.0, 0.37], [0.06, 0.385], [0.14, 0.39], [0.3, 0.4], [0.42, 0.4], [0.48, 0.37], [0.56, 0.315], [0.667, 0.238], [0.803, 0.198], [0.924, 0.165], [0.977, 0.148], [0.995, 0.118], [1.0, 0.1]], 'bot': [[0, 0.012], [0.015, 0.0], [0.061, 0], [0.379, 0], [0.833, 0], [0.924, 0.002], [0.98, 0.008], [1.0, 0.03], [1.02, 0.045]], 'os_top': [[0, 0.04], [0.015, 0.026], [0.061, 0.026], [0.833, 0.026], [0.924, 0.03], [0.98, 0.036], [1.0, 0.055], [1.02, 0.07]], 'collar_drop': 0.018, 'tongue_top': [0.45, 0.4], 'tongue_w_top': 0.07, 'bow': 0.3, 'heel_lean': [0.008, 0.22, 0.36], 'stations': [0.045, 0.065, 0.095, 0.14, 0.2, 0.27, 0.34, 0.42, 0.5, 0.58, 0.66, 0.74, 0.81, 0.87, 0.91, 0.945, 0.97, 0.99]}}


DESIGNS = {'male_tennis': design_male_tennis, 'male_golf': design_male_golf}


def prof(x, table):
    t = np.array(table, float); o = np.argsort(t[:, 0]); return np.interp(x, t[o, 0], t[o, 1])


def smooth1(a, n, w=(1, 2, 1)):
    a = np.array(a, float)
    for _ in range(n): a[1:-1] = (w[0] * a[:-2] + w[1] * a[1:-1] + w[2] * a[2:]) / sum(w)
    return a


def subsurf(ob, levels):
    m = ob.modifiers.new('ss', 'SUBSURF'); m.levels = levels; m.render_levels = levels; m.subdivision_type = 'CATMULL_CLARK'
    apply_modifier(ob, m)


def mesh_np(ob):
    me = ob.data; P = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', P); return P.reshape(-1, 3)


def boundary_loops(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    adj = {}
    for e in bm.edges:
        if not e.is_boundary: continue
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
    bm.free(); return loops


def sock_points(hero_id, side, fr):
    """the worn sock (pipeline dump = what the game draws today) in the foot frame; falls back to the leg skin + 3 mm."""
    f = os.path.join(PIPE_DUMP, hero_id, 'Kit_Sock_%s_pos.f32' % side)
    if not os.path.exists(f) and hero_id.endswith('_Male'):      # golf male: no sock in today's kit; the tennis male wears the same body
        f = os.path.join(PIPE_DUMP, 'MatchHero_Male', 'Kit_Sock_%s_pos.f32' % side)
    if os.path.exists(f):
        return fr.to(np.fromfile(f, np.float32).reshape(-1, 3).astype(np.float64)), 0.0
    body = fr.body
    return fr.to(body.pos[(fr.wf + fr.wl) > .3]), .003


def build(hero_id, design, side, outp):
    D = DESIGNS[design]()
    D.update(SILHOUETTE.get(design, {}))
    if os.environ.get('SHOE_DESIGN'): D.update(json.loads(os.environ['SHOE_DESIGN']))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import cv2io, glib as G
    hero = cv2io.Hero(hero_id); body = G.Body(hero)
    fr = Frame(body, side); L = fr.L
    Ls, y0, zb = D['Ls'], -D['heel_off'], D['zb']
    Y = lambda s: y0 + np.asarray(s) * Ls
    Z = lambda h: zb + np.asarray(h) * Ls
    # ---------------------------------------------------------------- stations (s) + per-station numbers
    S = np.array(D.get('stations', [.045, .065, .095, .14, .20, .27, .34, .42, .50, .58, .66, .74, .81, .87, .91, .945, .965, .978]))
    yS = Y(S)
    yfine = np.linspace(.004, L - .004, 120)
    xc_f, w_f = footprint(fr, yfine)
    xc = np.interp(yS, yfine, smooth1(xc_f, 8))
    D['collar'] = [(a_, b_ - D.get('collar_drop', 0.0)) for a_, b_ in D['collar']]
    z_ms = Z(prof(S, D['ms_top'])); z_top = Z(prof(S, D['top'])); z_col = Z(prof(S, D['collar']))
    # the lacing throat goes OVER the instep (laces never float above a hole): from the throat start to just past its end the top line
    # holds the foot top + room; the toe box keeps the sheet's low line (the toes under it are hidden)
    ft = foot_top(fr, yfine, xc_f)
    t0_, t1_ = D['throat']
    need = np.interp(np.clip(yS, .004, L - .004), yfine, ft) + D.get('instep_room', .010)
    wgt = smoothstep(t0_ - .06, t0_, S) * (1 - smoothstep(t1_, t1_ + .10, S))
    if D.get('instep', True): z_top = np.maximum(z_top, z_top + (need - z_top) * wgt * (need > z_top))   # instep=False: keep the sheet's throat line (the foot is hidden, GP_FOOT_ALL)
    if D.get('enclose'):
        # 10-18: the pipeline can only hide skin that the shoe is drawn over (hiding the cartoon forefoot under a low upper opened real
        # see-through gaps at low/side views), so the upper clears the foot top + room from just behind the throat to the toe tip
        need_e = np.interp(np.clip(yS, .004, L - .004), yfine, ft) + D.get('encl_room', .010)
        we = smoothstep(t0_ - .10, t0_ - .04, S)
        z_top = np.where(need_e > z_top, z_top + (need_e - z_top) * we, z_top)
    # designed half width of the upper base: the foot's own footprint (+ room) at the forefoot, rounded at heel and toe
    wfoot = np.interp(np.clip(yS, .004, L - .004), yfine, w_f)
    a = np.maximum(wfoot + D['room'], .030)
    a = np.maximum(a, D.get('fore_min', 0) * np.interp(S, [0, .30, .55, .80, .93, 1], [.75, .80, 1, 1, .92, .80]))
    a *= np.interp(S, [S[0], S[1], S[2], S[3], .87, .91, .945, .965, .978], [.42, .70, .88, .97, 1.0, .94, .80, .60, .34])
    # the sock at the collar: widen each rear section (lateral and medial side separately) until the sock fits inside the upper with
    # room (padding + shell); the closed section top in the mouth region is far above the collar (it is cut away), so the walls are
    # near-vertical where the sock passes the rim
    qs, extra = sock_points(hero_id, side, fr)
    room = .0040 + D['upper_t'] + extra
    n_ex = 2.4
    nS = np.interp(S, [0, D['throat'][0] - .02, D['throat'][0] + .10, 1], [D.get('n_rear', 3.2), D.get('n_rear', 3.2), 2.4, 2.4])
    z_top0 = z_top.copy()                                      # the designed top line (the tongue and laces follow it)
    z_top = np.where(S < D['throat'][0], np.maximum(z_top, z_col + .060), z_top)
    aL = a.copy(); aM = a.copy()
    for k in range(len(S)):
        if S[k] > D['throat'][0] + .04: break
        m = (np.abs(qs[:, 1] - yS[k]) < .012) & (qs[:, 2] < z_col[k] + .004) & (qs[:, 2] > z_col[k] - D.get('sock_band', .015))
        if m.sum() < 3: continue
        h = max(z_top[k] - z_ms[k], .02)
        for sg, arr in ((1, aL), (-1, aM)):
            mm = m & (np.sign(qs[:, 0] - xc[k]) == sg)
            if mm.sum() < 2: continue
            dx = np.abs(qs[mm, 0] - xc[k]) + room; dz = np.clip(qs[mm, 2] - z_ms[k] + room, 0, h * .999)
            sc = np.max((dx / arr[k]) ** nS[k] + (dz / h) ** nS[k]) ** (1 / nS[k])
            if sc > 1: arr[k] *= sc
    if D.get('enclose'):
        # 10-18: the cartoon foot is boxy and widest well above the sole (footprint() measures the sole only): widen each section until
        # every foot point at that station sits inside the upper with room (same superellipse test as the sock above)
        qf = fr.to(fr.body.pos[fr.wf > .5]); room_f = D.get('encl_side', .0075) + D['upper_t']   # 10 mm: the rigid shoe vs the blended foot skin drift apart a few mm off the bind pose
        for k in range(len(S)):
            m = (np.abs(qf[:, 1] - yS[k]) < .010) & (qf[:, 2] < z_top[k] - .002)
            if m.sum() < 3: continue
            h = max(z_top[k] - z_ms[k], .02)
            for sg, arr in ((1, aL), (-1, aM)):
                mm = m & (np.sign(qf[:, 0] - xc[k]) == sg)
                if mm.sum() < 2: continue
                dx = np.abs(qf[mm, 0] - xc[k]) + room_f; dz = np.clip(qf[mm, 2] - z_ms[k] + room_f, 0, h * .999)
                sc = np.max((dx / arr[k]) ** nS[k] + (dz / h) ** nS[k]) ** (1 / nS[k])
                if sc > 1: arr[k] *= sc
    k_th = int(np.searchsorted(S, D['throat'][0]))
    for arr in (aL, aM):
        arr[1:k_th] = np.maximum.accumulate(arr[1:k_th])
        arr[:] = smooth1(arr, 2)
    for k in range(len(S)): print('SEC s %.3f y %.3f xc %.4f aL %.4f aM %.4f z_ms %.3f z_top %.3f z_col %.3f wfoot %.4f foot_top %.3f' % (S[k], yS[k], xc[k], aL[k], aM[k], z_ms[k], z_top[k], z_col[k], wfoot[k], np.interp(np.clip(yS[k], .004, L - .004), yfine, ft)))
    # sock back: the heel back of the shell must sit behind the sock's back with room
    mb = (qs[:, 2] > z_ms[0] + .01) & (qs[:, 2] < z_col[0])
    if mb.sum():
        need = qs[mb, 1].min() - room - .002
        if yS[0] > need:
            d = yS[0] - need; yS = yS - d * np.clip(1 - S / .30, 0, 1)
    # ---------------------------------------------------------------- the upper cage (U sections open at the bottom)
    K = 13
    th = np.linspace(math.pi, 0, K)
    V = []
    for k in range(len(S)):
        h = max(z_top[k] - (z_ms[k] - .004), .012)
        for t_ in th:
            c, s_ = math.cos(t_), math.sin(t_)
            V.append((xc[k] + (aL[k] if c > 0 else aM[k]) * np.sign(c) * abs(c) ** (2 / nS[k]), yS[k], z_ms[k] - .004 + h * abs(s_) ** (2 / nS[k])))
    V = np.array(V); F = []
    idx = lambda k, i: k * K + i
    for k in range(len(S) - 1):
        for i in range(K - 1): F.append((idx(k, i), idx(k, i + 1), idx(k + 1, i + 1), idx(k + 1, i)))
    for k, dy in ((0, -1.0), (len(S) - 1, 1.0)):                     # zipped round ends
        mid = K // 2; spine = []
        for i in range(mid):
            p = (V[idx(k, i)] + V[idx(k, K - 1 - i)]) / 2; p[1] += dy * (.003 + .005 * math.sin(math.pi * i / max(1, mid - 1)))
            V = np.vstack([V, p]); spine.append(len(V) - 1)
        spine.append(idx(k, mid))
        for i in range(mid):
            q = [idx(k, i), idx(k, i + 1), spine[i + 1], spine[i]]; F.append(tuple(q if dy > 0 else q[::-1]))
            q = [spine[i], spine[i + 1], idx(k, K - 2 - i), idx(k, K - 1 - i)]; F.append(tuple(q if dy > 0 else q[::-1]))
    ob = make_mesh('Upper', V, F)
    subsurf(ob, D.get('subdiv', 3))
    P = mesh_np(ob)
    # heel counter: the heel back bulges out at mid height and tucks in toward the sole (sheet lateral view)
    sP = (P[:, 1] - y0) / Ls; hP = (P[:, 2] - zb) / Ls
    hb = D.get('heel_bulge', (.006, .21, .07))
    P[:, 1] -= smoothstep(.16, .05, sP) * hb[0] * np.exp(-((hP - hb[1]) / hb[2]) ** 2)
    hl = D.get('heel_lean', (0.0, .24, .38))                 # the heel's back edge leans forward toward the collar (sheet 14 lateral)
    P[:, 1] += smoothstep(.16, .05, sP) * hl[0] * smoothstep(hl[1], hl[2], hP)
    ob.data.vertices.foreach_set('co', P.astype(np.float32).ravel()); ob.data.update()
    sP = (P[:, 1] - y0) / Ls
    # ---------------------------------------------------------------- cut the collar mouth and the lacing throat
    t0, t1 = D['throat']
    zc = Z(prof(sP, D['collar']))
    xcP = np.interp(P[:, 1], yS, xc)
    tw = np.interp(sP, [t0, t0 + .05, t1], [D['throat_w'][0], D['throat_w'][0], D['throat_w'][1]])
    ztP = np.interp(P[:, 1], yS, z_top)
    cut_v = ((sP < t0) & (P[:, 2] > zc)) | ((sP >= t0 - .01) & (sP <= t1) & (np.abs(P[:, 0] - xcP) < tw / 2) & (P[:, 2] > ztP - .05))
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    kill = [f for f in bm.faces if sum(cut_v[v.index] for v in f.verts) >= 2]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    P = mesh_np(ob); loops = boundary_loops(ob)
    rim = max(loops, key=lambda lp: P[lp, 2].mean())
    R = P[rim].copy()
    for _ in range(14): R = (np.roll(R, 1, 0) + 2 * R + np.roll(R, -1, 0)) / 4
    P[rim] = R
    ob.data.vertices.foreach_set('co', P.astype(np.float32).ravel()); ob.data.update()
    base = [lp for lp in loops if lp is not rim]
    BP = P[np.concatenate(base)] if base else P[P[:, 2] < np.interp(P[:, 1], yS, z_ms)]
    # ---------------------------------------------------------------- per-vertex fields (reference units) for the maps
    def fields(P, kindname):
        s_ = (P[:, 1] - y0) / Ls; h_ = (P[:, 2] - zb) / Ls
        qx = P[:, 0] - np.interp(P[:, 1], yS, xc)
        d_rim = np.min(np.linalg.norm(P[:, None, :] - R[None, ::2, :], axis=2), axis=1) if len(P) < 60000 else np.full(len(P), .05)
        return dict(s4=s_, h4=h_, qx=qx, d_rim=d_rim, shoeL=np.full(len(P), Ls))
    me = ob.data
    UF = fields(P, 'upper')
    # soft raised overlays: trim panels sit 1.2 mm proud of the base leather (smooth step at the polygon edge)
    def in_polys(s_, h_, polys):
        ins = np.zeros(len(s_), bool)
        for poly in polys:
            poly = np.asarray(poly); c = np.zeros(len(s_), bool)
            for i in range(len(poly)):
                (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
                c ^= ((y1 > h_) != (y2 > h_)) & (s_ < (x2 - x1) * (h_ - y1) / (y2 - y1 + 1e-12) + x1)
            ins |= c
        return ins
    N = np.zeros(len(P) * 3); me.vertices.foreach_get('normal', N); N = N.reshape(-1, 3)
    ins = in_polys(UF['s4'], UF['h4'], D['panels']['trim']).astype(float)
    for _ in range(3):                                                  # soften the step over the subdivided mesh
        ins = smooth_vertex_field(me, ins)
    lift = .0012 * ins * smoothstep(.006, .014, UF['d_rim'])
    P = P + N * lift[:, None]
    me.vertices.foreach_set('co', P.astype(np.float32).ravel()); me.update()
    UF = fields(P, 'upper')
    for k_, v_ in UF.items():
        at = me.attributes.new(k_, 'FLOAT', 'POINT'); at.data.foreach_set('value', np.asarray(v_, np.float32))
    nf = len(me.polygons)
    for k_, v_ in (('role', ROLE_SHOE), ('face_kind', KIND['upper']), ('fabric', FABRIC['leather']), ('panel', 0)):
        at = me.attributes.new(k_, 'INT', 'FACE'); at.data.foreach_set('value', np.full(nf, v_, np.int32))
    objs = [ob]
    # ---------------------------------------------------------------- padded collar roll round the whole opening (mouth + eyestays)
    sr = (R[:, 1] - y0) / Ls
    cr = D['collar_r']
    rad = np.where(sr < t0 - .03, np.interp(sr, [-.1, .15, t0 - .03], [cr[0], cr[1], cr[1]]), np.interp(sr, [t0 - .03, t0 + .03, 1.0], [cr[1], cr[2], cr[2]]))
    cen = np.stack([np.interp(R[:, 1], yS, xc), R[:, 1], R[:, 2] - .03], 1)
    inward = cen - R; inward /= np.linalg.norm(inward, axis=1, keepdims=True) + 1e-12
    path = R + inward * rad[:, None] * .40
    path = np.vstack([path, path[:1]])
    TV, TF, tarc, tang = tube_path(path, np.append(rad, rad[0]), k=10, cap=False)
    f = fields(TV, 'collar'); f['d_rim'] = np.zeros(len(TV))
    is_mouth = (np.repeat(np.append(sr, sr[0]), 10) < t0 - .01).astype(float)
    f['mouth'] = is_mouth
    objs.append(make_mesh('Collar', TV, TF, roles=ROLE_SHOE, kinds=KIND['band'], fabric=FABRIC['mesh'], panel=2, uv=np.stack([tarc, tang * .004], 1), vattr=f))
    # ---------------------------------------------------------------- tongue (padded, rises above the collar front, leans back)
    s_t0, h_t = D['tongue_top']
    ty_s = np.linspace(s_t0, t1 + .03, 16)
    ty = Y(ty_s); tx = np.interp(ty, yS, xc)
    t_base = np.interp(ty, yS, z_top0) - .004
    rise = smoothstep(t0 + .07, s_t0, ty_s) * max(Z(h_t) - t_base[0], 0)
    tz = t_base + rise; ty = ty - rise * .40
    # the tongue lies ON the sock / shin: each row stays 4 mm in front of the sock's front surface at its height
    for j in range(len(ty)):
        m = (np.abs(qs[:, 2] - tz[j]) < .008) & (np.abs(qs[:, 0] - tx[j]) < D['tongue_w'] * .35) & (qs[:, 1] < Y(t0 + .04))      # the ankle front only, never the instep
        if m.sum(): ty[j] = max(ty[j], qs[m, 1].max() + .004 + extra)
    ty = np.maximum.accumulate(ty[::-1])[::-1] * 0 + ty
    tw2 = np.interp(ty_s, [s_t0, t0 + .02, t0 + .07, t1], [D.get('tongue_w_top', D['tongue_w'] * .92), D.get('tongue_w_top', D['tongue_w']), D['tongue_w'], D['tongue_w'] * .75])
    TV = []; nu = 9
    for j in range(len(ty)):
        for i in range(nu):
            u = (i / (nu - 1)) * 2 - 1
            TV.append((tx[j] + u * tw2[j] / 2, ty[j], tz[j] - .010 * u * u))
    TV = np.array(TV); TF = [(j * nu + i, j * nu + i + 1, (j + 1) * nu + i + 1, (j + 1) * nu + i) for j in range(len(ty) - 1) for i in range(nu - 1)]
    f = fields(TV, 'tongue'); f['tg_edge'] = np.abs(np.tile(np.linspace(-1, 1, nu), len(ty)))
    tob = make_mesh('Tongue', TV, TF, roles=ROLE_SHOE, kinds=KIND['tongue'], fabric=FABRIC['mesh'], panel=3, uv=TV[:, [0, 1]], vattr=f)
    subsurf(tob, 1); objs.append(tob)
    # ---------------------------------------------------------------- eyelets + criss-cross laces over the tongue
    ne = D['eyelets']; es = np.linspace(t0 + .03, t1 - .02, ne); ye = Y(es)
    xe = np.interp(ye, yS, xc)
    ze = np.interp(ye, yS, z_top) - .002
    half = np.interp(es, [t0, t1], [D['throat_w'][0], D['throat_w'][1]]) / 2 + .0075
    o_ = np.argsort(ty); zl = np.maximum(np.interp(ye, ty[o_], tz[o_]), ze) + .003           # laces ride on the tongue / eyestays
    LV, LF, LUV = [], [], []
    def tube(pts, r, flat, k=6):
        v_, f_, ar, ag = tube_path(np.asarray(pts), r, k=k, cap=True, flat=flat)
        o = len(LV); LV.extend(v_.tolist()); LF.extend([tuple(int(i) + o for i in f) for f in f_]); LUV.extend(np.stack([ar, ag * .002], 1).tolist())
    def lace(p0, p1, zmid):
        tt = np.linspace(0, 1, 11); pts = np.array([p0 + (p1 - p0) * t_ for t_ in tt])
        pts[:, 2] = np.maximum(pts[:, 2], zmid + .0015 * np.sin(tt * math.pi)) + .0025 * np.sin(tt * math.pi)
        tube(pts, D['lace_r'], D['lace_flat'])
    for i in range(ne - 1):
        pl0 = np.array([xe[i] - half[i], ye[i], ze[i]]); pr0 = np.array([xe[i] + half[i], ye[i], ze[i]])
        pl1 = np.array([xe[i + 1] - half[i + 1], ye[i + 1], ze[i + 1]]); pr1 = np.array([xe[i + 1] + half[i + 1], ye[i + 1], ze[i + 1]])
        zm = max(zl[i], zl[i + 1])
        lace(pl0, pr1, zm); lace(pr0, pl1, zm)
    # last (toe-most) bar straight across, bow at the top pair
    tube(np.array([[xe[-1] - half[-1], ye[-1], ze[-1]], [xe[-1], ye[-1], zl[-1] + .002], [xe[-1] + half[-1], ye[-1], ze[-1]]]), D['lace_r'], D['lace_flat'])
    bw_ = D.get('bow', 1.0); pb = np.array([xe[0], ye[0] - .003, ze[0] + .008 * bw_])
    for sg in (-1, 1):
        loop = np.array([pb + np.array([sg * .020 * bw_ * math.sin(t_), -.012 * bw_ * (1 - math.cos(t_)), .006 * bw_ * math.sin(t_)]) for t_ in np.linspace(0, 2 * math.pi, 16)])
        tube(loop, D['lace_r'], D['lace_flat'])
        tail = np.array([pb + np.array([sg * (.004 + .006 * t_), (.010 + .026 * t_) * bw_, -.012 * t_ * t_ * bw_]) for t_ in np.linspace(0, 1, 8)])
        tube(tail, D['lace_r'], D['lace_flat'])
    LV = np.array(LV)
    objs.append(make_mesh('Laces', LV, LF, roles=ROLE_SHOE, kinds=KIND['lace'], fabric=FABRIC['lace'], panel=4, uv=np.array(LUV), vattr=fields(LV, 'lace')))
    # eyelet grommets (hardware) round each lace hole on the eyestays
    EV, EF = [], []
    for i in range(ne):
        for sg in (-1, 1):
            c0 = np.array([xe[i] + sg * half[i], ye[i], ze[i] + .0006]); b0 = len(EV)
            for rr, dz in ((.0042, 0), (.0042, .0012), (.0024, .0012), (.0024, 0)):
                for q in range(10): ph = 2 * math.pi * q / 10; EV.append(c0 + [rr * math.cos(ph), rr * math.sin(ph), dz])
            for r_ in range(3):
                for q in range(10): q2 = (q + 1) % 10; EF.append((b0 + r_ * 10 + q, b0 + r_ * 10 + q2, b0 + (r_ + 1) * 10 + q2, b0 + (r_ + 1) * 10 + q))
    EV = np.array(EV)
    objs.append(make_mesh('Eyelets', EV, EF, roles=ROLE_HW, kinds=KIND['nub'], fabric=FABRIC['rubber'], panel=8, uv=EV[:, :2], vattr=fields(EV, 'eye')))
    # ---------------------------------------------------------------- heel pull loop (flat strap up the heel back, looping out over the collar)
    if D.get('loop'):
        lp = D['loop']; yb = float(np.min(P[:, 1]))
        # an open pull loop: sewn up the heel back to the collar, then a standing ring tilted back (sheet 13 lateral / back views)
        pts = [(lp['h0'], .0012), (lp['h0'] + .05, .0004), (lp['h1'] - .065, -.0002), (lp['h1'] - .035, -.003), (lp['h1'] - .010, -.008),
               (lp['h1'], -.0135), (lp['h1'] - .012, -.020), (lp['h1'] - .040, -.019), (lp['h1'] - .060, -.012)]
        zz = Z(np.array([q[0] for q in pts])); yy = yb + np.array([q[1] for q in pts]) * lp.get('scale', 1.0)
        path = np.stack([np.full(len(pts), xc[0]), yy, zz], 1)
        tt = np.linspace(0, 1, 30); path = np.stack([np.interp(tt * (len(pts) - 1), np.arange(len(pts)), path[:, j_]) for j_ in range(3)], 1)
        for _ in range(3): path[1:-1] = (path[:-2] + 2 * path[1:-1] + path[2:]) / 4
        v_, f_, ar, ag = ribbon(path, np.array([1.0, 0, 0]), lp['w'], .0024)
        objs.append(make_mesh('HeelLoop', v_, f_, roles=ROLE_SHOE, kinds=KIND['tab'], fabric=FABRIC['twill'], panel=6, uv=np.stack([ar, ag * .003], 1), vattr=fields(v_, 'tab')))
    # ---------------------------------------------------------------- sole unit: outline from the upper's base edge + flare
    ys2 = np.linspace(yS[0] - .004, yS[-1] + .004, 90)
    left = np.zeros(len(ys2)); right = np.zeros(len(ys2))
    for j, yv in enumerate(ys2):
        m = np.abs(BP[:, 1] - yv) < .006
        if m.sum() >= 2: left[j], right[j] = BP[m, 0].min(), BP[m, 0].max()
        else: left[j] = right[j] = np.nan
    g = ~np.isnan(left)
    left = np.interp(ys2, ys2[g], left[g]); right = np.interp(ys2, ys2[g], right[g])
    cxs = (left + right) / 2; hw = (right - left) / 2 + .0015
    e = np.sqrt(np.clip(1 - ((np.clip(ys2[0] + .030 - ys2, 0, None)) / .030) ** 2, 0, 1)) * np.sqrt(np.clip(1 - ((np.clip(ys2 - (ys2[-1] - .036), 0, None)) / .036) ** 2, 0, 1))
    hw = smooth1(hw, 6) * np.maximum(e, .14)
    outline = np.concatenate([np.stack([cxs + hw, ys2], 1), np.stack([cxs - hw, ys2], 1)[::-1]])
    for _ in range(4): outline = (np.roll(outline, 1, 0) + 2 * outline + np.roll(outline, -1, 0)) / 4
    NP = len(outline); c2 = outline.mean(0)
    tan = np.roll(outline, -1, 0) - np.roll(outline, 1, 0); tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    nrm2 = np.stack([tan[:, 1], -tan[:, 0]], 1)
    if np.mean(np.sum(nrm2 * (outline - c2), axis=1)) < 0: nrm2 = -nrm2
    so = (outline[:, 1] - y0) / Ls
    fl = D['flare']
    flare = fl['side'] + (fl['heel'] - fl['side']) * smoothstep(.16, .0, so) + (fl['toe'] - fl['side']) * smoothstep(.85, 1.0, so)
    z_bot = Z(prof(so, D['bot'])); z_os = Z(prof(so, D['os_top'])); z_lip = Z(prof(so, D['ms_top']))
    bul = D['sole_bulge']
    rows = [(z_lip + .0008, .0004 - .0010), (z_lip - .0015, flare * .55), (z_lip - (z_lip - z_os) * .30, flare + bul * .6),
            (z_lip - (z_lip - z_os) * .55, flare + bul), (z_os + .0030, flare * .96), (z_os + .0004, flare * .90),
            (z_os - .0004, flare * .92), (z_bot + .0030, flare * .90), (z_bot, flare * .62)]
    SR = np.stack([np.concatenate([outline + nrm2 * np.asarray(off)[:, None] if np.ndim(off) else outline + nrm2 * off, np.asarray(z_)[:, None]], 1) for z_, off in rows], 1)
    nrw = SR.shape[1]; SV = SR.reshape(-1, 3); SF = []
    for i in range(NP):
        i2 = (i + 1) % NP
        for r_ in range(nrw - 1): SF.append((i * nrw + r_, i2 * nrw + r_, i2 * nrw + r_ + 1, i * nrw + r_ + 1))
    SUV = np.stack([np.repeat(np.arange(NP) * .004, nrw), SR[:, :, 2].ravel()], 1)
    # caps: nested rings (outline scaled toward the centre line) that follow the bottom / lip profile (a single fan bulged at the toe spring)
    def cap(ring, zf, flip, uoff):
        nonlocal SV, SF, SUV
        cx_ = np.interp(ring[:, 1], ys2, cxs)
        rings = [ring]
        for r in (.80, .58, .36, .16):
            q = ring.copy(); q[:, 0] = cx_ + (ring[:, 0] - cx_) * r; q[:, 2] = zf((q[:, 1] - y0) / Ls); rings.append(q)
        o = len(SV); SV = np.vstack([SV] + rings)
        for r in range(len(rings) - 1):
            for i in range(NP):
                i2 = (i + 1) % NP; q = (o + r * NP + i, o + r * NP + i2, o + (r + 1) * NP + i2, o + (r + 1) * NP + i)
                SF.append(q[::-1] if flip else q)
        last = o + (len(rings) - 1) * NP                     # close the innermost ring across the centre line (strip of quads)
        for i in range(NP // 2 - 1):
            a0, a1, b1, b0 = last + i, last + i + 1, last + NP - 2 - i, last + NP - 1 - i
            q = (a0, a1, b1, b0); SF.append(q[::-1] if flip else q)
        SUV = np.vstack([SUV] + [rg[:, :2] + [uoff, 0] for rg in rings])
    cap(SR[:, -1, :], lambda s_: Z(prof(s_, D['bot'])), False, 1.0)
    cap(SR[:, 0, :], lambda s_: Z(prof(s_, D['ms_top'])) - .004, True, 2.0)
    f = fields(SV, 'sole')
    f.update(sole_os=np.interp(SV[:, 1], outline[:NP // 2, 1], z_os[:NP // 2]) if False else Z(prof((SV[:, 1] - y0) / Ls, D['os_top'])),
             sole_ms=Z(prof((SV[:, 1] - y0) / Ls, D['ms_top'])), sole_bot=Z(prof((SV[:, 1] - y0) / Ls, D['bot'])), sole_cx=np.interp(SV[:, 1], ys2, cxs), sole_hw=np.interp(SV[:, 1], ys2, hw))
    sob = make_mesh('Sole', SV, SF, roles=ROLE_SHOE if D['colours']['sole_trim'] else ROLE_SOLE, kinds=KIND['sole'], fabric=FABRIC['foam'], panel=5, uv=SUV, vattr=f)
    objs.append(sob)
    # golf: replaceable spikes (star cleats, hardware) + the traction lugs come from the maps on the low outsole
    if D.get('cleats'):
        lay = [(.10, -.42), (.12, .42), (.66, -.50), (.70, .50), (.84, -.38), (.86, .36)]
        NV, NF = [], []
        for (rs, rx) in lay:
            cy_ = Y(rs); j = int(np.argmin(np.abs(ys2 - cy_))); cx_ = cxs[j] + rx * hw[j] * 1.02
            zt_ = float(Z(prof(np.array([rs]), D['bot']))[0]) + .0006
            b0 = len(NV)
            # hub + 6 arms (a soft star) as one ring profile with an angular bump
            for zz, r_, arm in ((zt_ + .0015, .0135, 0), (zt_ - .0025, .0135, .30), (zt_ - .0060, .0125, .65), (zt_ - .0090, .0075, .45), (zt_ - .0102, .0035, 0)):
                for q in range(24):
                    ph = 2 * math.pi * q / 24; rr = r_ * (1 + arm * .5 * max(0, math.cos(6 * ph)) ** 3)
                    NV.append((cx_ + rr * math.cos(ph), cy_ + rr * math.sin(ph), zz))
            for r_ in range(4):
                for q in range(24): q2 = (q + 1) % 24; NF.append((b0 + r_ * 24 + q, b0 + r_ * 24 + q2, b0 + (r_ + 1) * 24 + q2, b0 + (r_ + 1) * 24 + q))
            NF.append(tuple(b0 + 96 + q for q in range(24))[::-1])
        NV = np.array(NV)
        objs.append(make_mesh('Cleats', NV, NF, roles=ROLE_HW, kinds=KIND['nub'], fabric=FABRIC['rubber'], panel=7, uv=NV[:, :2], vattr=fields(NV, 'cleat')))
    # ---------------------------------------------------------------- world space, orientation, thickness, join
    det = float(np.linalg.det(np.stack([fr.lat, fr.fwd, [0, 0, 1.]])))
    for o in objs:
        me = o.data; p = mesh_np(o)
        me.vertices.foreach_set('co', fr.back(p).astype(np.float32).ravel()); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        if o.name in ('Sole', 'Cleats', 'Laces', 'Collar', 'HeelLoop', 'Eyelets'): bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        elif det < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free(); me.update()
    thick = {'Upper': D['upper_t'], 'Tongue': .0050}
    for o in objs:
        o.data.shade_smooth()
        for nm in ('outer', 'inner', 'rim'): o.data.materials.append(bpy.data.materials.get(nm) or bpy.data.materials.new(nm))
        if o.name in thick:
            sm = o.modifiers.new('solid', 'SOLIDIFY'); sm.thickness = thick[o.name]; sm.offset = -1; sm.use_even_offset = False
            sm.use_quality_normals = True; sm.use_rim = True; sm.material_offset = 1; sm.material_offset_rim = 2
            apply_modifier(o, sm)
            if o.name == 'Upper':                       # the lining (inner wall) is baked like the outside (kind 21), so the sheet's navy lining shows in the mouth
                me = o.data; mi = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
                kk = np.zeros(len(me.polygons), np.int32); me.attributes['face_kind'].data.foreach_get('value', kk)
                kk[mi == 1] = 21; me.attributes['face_kind'].data.foreach_set('value', kk)
                mi[mi == 1] = 0; me.polygons.foreach_set('material_index', mi); me.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.join()
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=.003, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.name = 'Kit_Shoe_' + side; ob['roles'] = list(D['roles'])
    # design data for maps.details_shoe4 (reference units)
    pn = D['panels']; flat = lambda polys: [float(v) for poly in polys for p in poly for v in p]
    ob['mapdata_s4_trim'] = flat(pn['trim']); ob['mapdata_s4_trim_n'] = [len(p) for p in pn['trim']]
    ob['mapdata_s4_seams'] = flat(pn['seams']); ob['mapdata_s4_seams_n'] = [len(p) for p in pn['seams']]
    pf = pn.get('perf') or {}
    ob['mapdata_s4_perf'] = flat([pf['poly']]) if pf else [0.0]; ob['mapdata_s4_perf_n'] = [len(pf['poly'])] if pf else [0]
    ob['mapdata_s4_perfp'] = [float(pf.get('pitch', 0)), float(pf.get('r', 0))] if pf else [0.0, 0.0]
    ob['mapdata_s4_emboss'] = flat([pn['counter_emboss']]) if pn.get('counter_emboss') else [0.0]
    ob['mapdata_s4_emboss_n'] = [len(pn['counter_emboss'])] if pn.get('counter_emboss') else [0]
    c = D['colours']
    ob['mapdata_s4_col'] = [float(c['collar_trim']), float(c['tongue_trim']), float(c['outsole_tone']), float(c['midsole_tone']), float(c['sole_trim']),
                            1.0 if D['tread'] == 'herringbone' else 2.0, float(t0), float(t1)]
    bpy.ops.wm.save_as_mainfile(filepath=outp)
    print('SHOE4 %s %s Ls %.3f faces %d' % (design, side, Ls, len(ob.data.polygons)))


def ribbon(path, wdir, w, th):
    """flat strap along a path: width along wdir, thickness across; rounded edges (8 points per ring)."""
    path = np.asarray(path, float); n = len(path)
    t = np.gradient(path, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
    prof = [(-.5, -.3), (-.5, .3), (-.38, .5), (.38, .5), (.5, .3), (.5, -.3), (.38, -.5), (-.38, -.5)]
    V = []
    for i in range(n):
        a = wdir - t[i] * (wdir @ t[i]); a /= np.linalg.norm(a); b = np.cross(t[i], a)
        for u, v in prof: V.append(path[i] + a * u * w + b * v * th)
    k = len(prof); F = []
    for i in range(n - 1):
        for q in range(k): q2 = (q + 1) % k; F.append((i * k + q, i * k + q2, (i + 1) * k + q2, (i + 1) * k + q))
    F.append(tuple(range(k))[::-1]); F.append(tuple(range((n - 1) * k, n * k)))
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    return np.array(V), F, np.repeat(arc, k), np.tile(np.arange(k), n)


def smooth_vertex_field(me, f):
    """one umbrella pass of a per-vertex scalar over the mesh edges."""
    n = len(me.vertices); E = np.zeros(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
    acc = np.zeros(n); cnt = np.zeros(n)
    np.add.at(acc, E[:, 0], f[E[:, 1]]); np.add.at(acc, E[:, 1], f[E[:, 0]]); np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    return np.where(cnt > 0, (f + acc) / (1 + cnt), f)


if __name__ == '__main__' and '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    build(a[0], a[1], a[2], a[3])
