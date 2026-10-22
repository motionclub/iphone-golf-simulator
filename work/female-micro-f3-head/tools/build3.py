"""build + carve + Face_F + preview blend.  blender -b --factory-startup --python build3.py -- [tag]"""
import sys, time, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
import fl, geo, build, feats, feat_f, carve, loftf, facef, fair, looptidy
from fl import MM


def lid_walls(H, sk, P, F, loops, side_of, poly):
    """lid thickness: quads from the margin loop down to a loop lid_t deeper (and pulled toward the aperture centre)"""
    I = feat_f.IRIS; newP = []; newF = []
    for nm, lp in loops.items():
        if not nm.startswith('eye'): continue
        side = side_of[nm]
        x = P[lp, 0]; z = P[lp, 2]
        Pp, N = sk.pt(x, z)
        c = np.array([side * I['cx'], 0, I['cz']])
        inw = np.stack([c[0] - P[lp, 0], np.zeros(len(lp)), c[2] - P[lp, 2]], 1); inw /= np.linalg.norm(inw, axis=1, keepdims=True)
        M2 = P[lp] - facef.EYE['lid_t'] * N + 0.0004 * inw
        base = len(P) + len(newP); newP += [m for m in M2]
        n = len(lp)
        for i in range(n):
            a, b = lp[i], lp[(i + 1) % n]; a2, b2 = base + i, base + (i + 1) % n
            newF.append([a, b, b2, a2])
    return newP, newF


def orient_to(P, F, centers):
    out = []
    for f in F:
        p = P[f]; cc = p.mean(0); nrm = np.cross(p[1] - p[0], p[2] - p[0])
        out.append(f)
    return out


def project_layer(P, F, L):
    """project the flagged Face_F vertices onto the final skin mesh (BVH) and lift them along the mesh normal.
    lift float: nearest point; lift ('ray', l): front-projection ray (exactly the requested x, z), first hit, lifted by l along the face normal"""
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    tris = []
    for f in F:
        for i in range(1, len(f) - 1): tris.append((int(f[0]), int(f[i]), int(f[i + 1])))
    bvh = BVHTree.FromPolygons([tuple(v) for v in P], tris)
    V = np.array(L.V); n = 0; nray = 0; nmiss = 0
    for i, lf in enumerate(L.lift):
        if lf is None: continue
        if isinstance(lf, tuple):
            loc, nrm, idx, dist = bvh.ray_cast(Vector((V[i][0], -0.30, V[i][2])), Vector((0.0, 1.0, 0.0)))
            if loc is None: nmiss += 1; continue
            nn = np.array(nrm)
            if nn[1] > 0: nn = -nn                      # outward = facing the ray origin
            V[i] = np.array(loc) + lf[1] * nn; nray += 1
            continue
        loc, nrm, idx, dist = bvh.find_nearest(tuple(V[i]))
        if loc is None: continue
        V[i] = np.array(loc) + lf * np.array(nrm); n += 1
    L.V = [tuple(v) for v in V]
    print('project_layer: nearest', n, 'ray', nray, 'ray misses', nmiss)
    return n + nray


def make_blend(path, P, F, L, body_mats=('Skin_F',)):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    ob = fl.make_mesh_object('Body_F', P, F); ob.data.materials.append(bpy.data.materials.new('Skin_F'))
    fo = fl.make_mesh_object('Face_F', np.array(L.V), L.F)
    for nm in facef.MATS: fo.data.materials.append(bpy.data.materials.new('Face_' + nm))
    fo.data.polygons.foreach_set('material_index', np.array(L.M, np.int32))
    bpy.ops.wm.save_as_mainfile(filepath=str(path))


def run(tag='b3', prm=None):
    t0 = time.time()
    H, U, F, P, info = build.build(prm, tag=tag, verbose=False)
    sk = facef.Skin(H)
    loops = {}; side_of = {}
    eye = feat_f.eye_poly(6)
    for side, nm in ((-1, 'L'), (+1, 'R')):
        F, lp, nrem, rms = feats.carve_hole(H, U, P, F, eye, side, 'eye' + nm)
        loops['eye' + nm] = lp; side_of['eye' + nm] = side
        feats.relax_chart(H, U, P, carve.edge_adj(F, len(P)), lp, rings=2, iters=3)
    # ---- mouth chains (seam + vermilion borders), snapped in the front chart
    mo = feat_f.MOUTH; hw = mo['hw']
    def seam_xz(n=61):
        xs = np.linspace(-hw, hw, n); return np.column_stack([xs, H.seam_z(xs)])
    def up_xz(n=61):
        xs = np.linspace(-0.95 * hw, 0.95 * hw, n); return np.column_stack([xs, mo['ztop'] + (mo['ztop_k'] - mo['ztop']) * (np.abs(xs) / hw) ** 3.0])
    def lo_xz(n=45):
        hl = 0.0262 * 0.97; xs = np.linspace(-hl, hl, n); zsl = H.seam_z(xs)
        return np.column_stack([xs, zsl - (zsl - 1.4634) * np.sqrt(np.clip(1 - (xs / 0.0262) ** 2, 0, 1))])
    cand_mouth = (np.abs(P[:, 0]) < 0.047) & (P[:, 1] < -0.10) & (np.abs(P[:, 2] - 1.475) < 0.018)
    # nostril rings (closed chains around the nostril dimples) in the front chart
    nos = feat_f.NOSTRIL
    for side, sn in ((-1, 'L'), (+1, 'R')):
        t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
        ring = np.column_stack([nos['cx'] + 1.9 * nos['rx'] * np.cos(t), nos['cz'] + 1.9 * nos['rz'] * np.sin(t)])
        c3, _ = H.surf_xz(side * ring[:, 0], ring[:, 1])
        cand_n = (np.sign(P[:, 0]) == side) & (np.abs(P[:, 0]) < 0.05) & (P[:, 1] < -0.10) & (np.abs(P[:, 2] - nos['cz']) < 0.015)
        adj = carve.edge_adj(F, len(P)); chain = carve.curve_chain(P, adj, c3, tol=0.0035, closed=True, cand=np.where(cand_n)[0])
        if len(chain) > 1 and chain[0] == chain[-1]: chain = chain[:-1]
        loops['nostril_' + sn] = chain; print('nostril ring', sn, len(chain), '(edge loop around the nostril, not snapped)')
    for nm, fn in (('seam', seam_xz), ('lip_up', up_xz), ('lip_lo', lo_xz)):
        c2 = fn(); c3, _ = H.surf_xz(c2[:, 0], c2[:, 1])
        chain, adj = feats.make_chain(H, U, P, F, c3, 0.0035, cand_mouth)
        rms = feats.assign_chain(H, U, P, chain, c2, False, 'xzs')
        loops[nm] = chain; print('chain', nm, len(chain), 'rms mm %.2f' % (rms * 1000))
    # ---- ear loops (per side): attach outline, helix crest, concha rim; snapped in the (y, z) ear chart
    ef = H.ear; poly = ef.poly
    cen = poly.mean(0)
    def inward(poly, dist):
        t = np.gradient(poly, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
        nrm = np.stack([-t[:, 1], t[:, 0]], 1); sg = np.sign(np.sum(nrm * (cen[None, :] - poly), axis=1)); sg[sg == 0] = 1
        dist = np.asarray(dist, float)
        return poly + nrm * sg[:, None] * (dist[:, None] if dist.ndim else dist)
    s_pts = np.clip((poly[:, 0] - np.interp(poly[:, 1], ef.zz, ef.ya_z)) / np.maximum(np.interp(poly[:, 1], ef.zz, ef.yp_z) - np.interp(poly[:, 1], ef.zz, ef.ya_z), 1e-4), 0, 1)
    root = inward(poly, -ef.delta_s(s_pts))                      # root contour: plate outline (front half) / dilated outline (back half)
    helix = inward(poly, feat_f.EAR['rim_d'])                    # crest = plate outline offset by the rim distance
    ccy, ccz = feat_f.EAR['conch_c']; th = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    concha = np.column_stack([ccy + 0.0062 * np.cos(th), ccz + 0.0085 * np.sin(th)])
    for side, sn in ((-1, 'L'), (+1, 'R')):
        for nm, curve in (('ear_attach', root), ('helix', helix), ('concha', concha)):
            c3 = []
            for (yy, zz) in curve:
                pt, uu = None, None
            ys = curve[:, 0]; zs = curve[:, 1]
            # 3D polyline on the final ear surface (via the chart)
            tmpU = np.zeros((len(curve), 3)); tmpP = np.zeros((len(curve), 3)); idx = list(range(len(curve)))
            feats.snap_chart_yz(H, tmpU, tmpP, idx, [(a, b) for a, b in curve], side)
            cand_ear = (np.sign(P[:, 0]) == side) & (np.abs(P[:, 0]) > 0.07) & (P[:, 1] > -0.02) & (P[:, 1] < 0.055) & (P[:, 2] > 1.485) & (P[:, 2] < 1.600)
            adj = carve.edge_adj(F, len(P)); cand = np.where(cand_ear)[0]
            chain = carve.curve_chain(P, adj, curve, tol=0.0035, closed=True, cand=cand, cols=(1, 2))
            # drop the duplicated closing vertex
            if len(chain) > 1 and chain[0] == chain[-1]: chain = chain[:-1]
            rms = feats.assign_chain(H, U, P, chain, curve, True, 'yz', side)
            loops[f'{nm}_{sn}'] = chain; print('ear', nm, sn, len(chain), 'rms mm %.2f' % (rms * 1000))
    for nm_ in ('eyeL', 'eyeR'):
        lp_ = loops[nm_]; zc_ = feat_f.IRIS['cz']
        loops['lid_up_' + nm_[-1]] = [v for v in lp_ if P[v, 2] >= zc_ + 0.0035]; loops['lid_low_' + nm_[-1]] = [v for v in lp_ if P[v, 2] < zc_ + 0.0035]
    # smooth the ear relief (removes the stair-stepping of the steep rim)
    adj_s = carve.edge_adj(F, len(P))
    ear_idx = np.where((np.abs(P[:, 0]) > 0.075) & (P[:, 1] > -0.016) & (P[:, 1] < 0.050) & (P[:, 2] > 1.490) & (P[:, 2] < 1.592))[0]
    carve.taubin(P, adj_s, ear_idx, iters=6)

    # ---- implicit fairing: chin underside (graded-mesh stair-steps at the chin/neck crease) + ear transition band (spikes where the ear relief meets the coarse head)
    adj_f = fair.vertex_adj(F, len(P))
    chin = np.where((np.abs(P[:, 0]) < 0.050) & (P[:, 1] > -0.140) & (P[:, 1] < -0.050) & (P[:, 2] > 1.412) & (P[:, 2] < 1.455))[0]
    print('fair chin', len(chin), 'max move mm %.2f' % (fair.fair(P, adj_f, chin, lam=0.03) * 1000))
    dE = feat_f.poly_signed_dist(P[:, 1], P[:, 2], ef.poly)
    for side, sn in ((-1, 'L'), (+1, 'R')):
        reg = np.where((np.sign(P[:, 0]) == side) & (np.abs(P[:, 0]) > 0.060) & (dE > -0.016) & (P[:, 1] > -0.03) & (P[:, 1] < 0.07) & (P[:, 2] > 1.45) & (P[:, 2] < 1.62))[0]
        print('fair ear', sn, len(reg), 'max move mm %.2f' % (fair.fair(P, adj_f, reg, lam=0.15) * 1000))

    ear_zone = (np.abs(P[:, 0]) > 0.065) & (P[:, 1] > -0.03) & (P[:, 1] < 0.07) & (P[:, 2] > 1.455)
    jaw = np.where((P[:, 2] > 1.4125) & (P[:, 2] < 1.52) & (P[:, 1] > -0.075) & (~ear_zone))[0]
    print('fair jaw angle / behind ear / neck top', len(jaw), 'max move mm %.2f' % (fair.fair(P, adj_f, jaw, lam=0.02, rings=2) * 1000))

    # ---- jaw -> ear loops (per side): from the ear-lobe attach point along the jaw line to the chin centre; alar crease chains
    for side, sn in ((-1, 'L'), (+1, 'R')):
        tt = np.linspace(0, 1, 60)
        zj = 1.5020 - 0.0725 * tt ** 0.9
        thj = np.radians(-14.0 - 76.0 * tt ** 1.25)
        Pj = H.L.point(thj, zj); Pj[:, 0] *= side
        d = Pj - geo.C[None, :]; uj = d / np.linalg.norm(d, axis=1, keepdims=True); Cj = H.phi(uj)
        cand_j = (np.sign(P[:, 0]) == side) & (P[:, 2] > 1.425) & (P[:, 2] < 1.506) & (np.abs(P[:, 0]) < 0.105) & (P[:, 1] < 0.045)
        adj = carve.edge_adj(F, len(P)); chain = carve.curve_chain(P, adj, Cj, tol=0.006, closed=False, cand=np.where(cand_j)[0])
        loops['jaw_ear_' + sn] = chain; print('jaw_ear', sn, len(chain), '(edge path along the jaw line, not snapped: snapping scarred the cheek)')
        # alar crease: lateral + lower outline of the ala (front chart), edge path only
        ala = np.array([(0.0215, 1.5130), (0.0240, 1.5050), (0.0232, 1.4975), (0.0195, 1.4930), (0.0140, 1.4912)])
        a2 = feat_f.catmull_open(ala, 6)
        c3, _ = H.surf_xz(side * a2[:, 0], a2[:, 1])
        cand_a = (np.sign(P[:, 0]) == side) & (np.abs(P[:, 0]) < 0.04) & (P[:, 1] < -0.09) & (P[:, 2] > 1.48) & (P[:, 2] < 1.52)
        adj = carve.edge_adj(F, len(P)); chain = carve.curve_chain(P, adj, c3, tol=0.0045, closed=False, cand=np.where(cand_a)[0])
        loops['ala_' + sn] = chain; print('ala', sn, len(chain))
    # tidy the ordered loop lists: closed rings become simple cycles, the lid chains become contiguous upper/lower chains of the eye ring
    for k in [k for k in loops if k.startswith(('nostril_', 'ear_attach_', 'helix_', 'concha_'))]: loops[k] = looptidy.simple_cycle(loops[k])
    for sn in ('L', 'R'):
        loops['lid_up_' + sn], loops['lid_low_' + sn] = looptidy.split_lids(loops['eye' + sn], P, feat_f.IRIS['cz'] + 0.0035)
    # faint philtrum (post-process on the carved mesh: a displacement inside Phi destabilises the exact (x, z) solve on the overhanging lip bump):
    # shallow central groove flanked by two soft ridges between the upper-lip bow and the nose base, along the vertex normals
    z0p, z1p = float(fl.zrow(213.8)) + 0.0015, float(fl.zrow(205.0))
    nrm = np.zeros_like(P)
    for f in F:
        pp = P[f]
        for i in range(1, len(f) - 1):
            c_ = np.cross(pp[i] - pp[0], pp[i + 1] - pp[0]); nrm[f[0]] += c_; nrm[f[i]] += c_; nrm[f[i + 1]] += c_
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    zone_p = np.where((np.abs(P[:, 0]) < 0.014) & (P[:, 2] > z0p - 0.002) & (P[:, 2] < z1p + 0.002) & (P[:, 1] < -0.10))[0]
    xa = np.abs(P[zone_p, 0]); za = P[zone_p, 2]
    winp = fl.sstep(z0p, z0p + 0.003, za) * (1.0 - fl.sstep(z1p - 0.003, z1p + 0.0005, za))
    dph = winp * 0.0009 * (-np.exp(-(xa / 0.0028) ** 2) + 0.55 * np.exp(-((xa - 0.0058) / 0.0020) ** 2))
    flip = nrm[zone_p, 1] > 0; nz = nrm[zone_p].copy(); nz[flip] *= -1                       # outward = toward -y
    P[zone_p] += dph[:, None] * nz
    print('philtrum: %d verts, max |d| %.2f mm' % (len(zone_p), np.abs(dph).max() * 1000))
    F_skin = list(F)
    newP, newF = lid_walls(H, sk, P, F, loops, side_of, eye)
    P = np.vstack([P, np.array(newP)]); F = F + newF
    L = facef.Layer()
    facef.brows(H, L, sk)
    for side in (-1, +1):
        facef.eye_shell(H, L, sk, side); facef.eye_lines(H, L, sk, side)
    facef.mouth(H, L, sk)
    facef.nostrils(H, L, sk)
    nproj = project_layer(P, F_skin, L)
    print('body verts', len(P), 'tris', sum(len(f) - 2 for f in F), '| face layer verts', len(L.V), 'faces', len(L.F), 'proj', nproj, 'time %.1f' % (time.time() - t0))
    return H, U, F, P, L, loops, info


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    tag = argv[0] if argv else 'b3'
    H, U, F, P, L, loops, info = run(tag)
    make_blend(fl.W / f'data/{tag}.blend', P, F, L)
    np.savez(fl.W / f'data/{tag}_state.npz', P=P, U=U)
    # patch for assemble.py
    ringd = np.load(fl.W / 'data/ring.npz'); ring_ids = ringd['ring']
    collar_map = {int(c): int(ring_ids[o]) for c, o in zip(info['collar'], info['collar_order'])}
    off = np.concatenate([[0], np.cumsum([len(f) for f in F])]); flat = np.concatenate([np.asarray(f, np.int64) for f in F])
    foff = np.concatenate([[0], np.cumsum([len(f) for f in L.F])]); fflat = np.concatenate([np.asarray(f, np.int64) for f in L.F])
    np.savez(fl.W / f'data/{tag}_patch.npz', P=P, F=flat, Foff=off, LV=np.array(L.V), LF=fflat, LFoff=foff, LM=np.array(L.M, np.int32), Lname=np.array(L.name))
    json.dump(dict(collar_map=collar_map, loops={k: [int(v) for v in vv] for k, vv in loops.items()}, mats=facef.MATS), open(fl.W / f'data/{tag}_patch.json', 'w'))
    print('patch saved', tag)
