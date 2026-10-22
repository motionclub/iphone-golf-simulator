# ----------------------------------------------------------------------------- round 6: the tee step (see TEE_STEP above)
def tee_hidden_k(cam=None):
    """(k, cam_xy, z_plate, z_fairway): the hidden-band factor of the plate's front edge as seen from the address camera. A ray from the camera over the plate's edge (z_plate) meets the
    fairway plate (z_fairway) beyond the edge at C + k (E - C) in plan, k = (cam z - z_fairway) / (cam z - z_plate) (1.0445 for the tee shot: the 10 cm step hides ~0.35 m)."""
    cam_, _look, _ball = tee_cam() if cam is None else cam
    tb, fw = bpy.data.objects["TEE_BOX"], bpy.data.objects["FAIRWAY"]
    zt = float(max(v.co.z for v in tb.data.vertices))
    zf = float(max(v.co.z for v in fw.data.vertices))
    k = (cam_.z - zf) / (cam_.z - zt)
    return k, (float(cam_.x), float(cam_.y)), zt, zf


def _plate_poly(name="TEE_BOX"):
    ob = bpy.data.objects[name]
    zt = float(max(v.co.z for v in ob.data.vertices))
    return _outcrop_rim(ob, zt), zt


def _poly_sd(poly, X, Y):
    """Signed distance (m) of points to a convex counter-clockwise polygon: negative inside (max over the edge half-planes)."""
    A = poly
    B = np.roll(poly, -1, axis=0)
    e = B - A
    ln = np.maximum(np.hypot(e[:, 0], e[:, 1]), 1e-12)
    nx, ny = e[:, 1] / ln, -e[:, 0] / ln
    X = np.atleast_1d(np.asarray(X, float))
    Y = np.atleast_1d(np.asarray(Y, float))
    return ((X[:, None] - A[None, :, 0]) * nx[None] + (Y[:, None] - A[None, :, 1]) * ny[None]).max(axis=1)


def _poly_boundary_dist(poly, X, Y):
    A = poly
    B = np.roll(poly, -1, axis=0)
    e = B - A
    l2 = np.maximum((e ** 2).sum(1), 1e-12)
    X = np.atleast_1d(np.asarray(X, float))
    Y = np.atleast_1d(np.asarray(Y, float))
    t = np.clip(((X[:, None] - A[None, :, 0]) * e[None, :, 0] + (Y[:, None] - A[None, :, 1]) * e[None, :, 1]) / l2[None], 0.0, 1.0)
    return np.hypot(X[:, None] - (A[None, :, 0] + e[None, :, 0] * t), Y[:, None] - (A[None, :, 1] + e[None, :, 1] * t)).min(axis=1)


def _path_lattice(me):
    """(rows n, columns nl) of a DRESS_PATH ribbon made by L.build_path: n rows of (nl top vertices + 2 skirt feet) then 2 x (nl + 1) end-skirt pairs; faces (n + 1) x (nl + 1)."""
    V, F = len(me.vertices), len(me.polygons)
    for nl in range(7, 80):
        if F % (nl + 1):
            continue
        n = F // (nl + 1) - 1
        if n > 1 and n * (nl + 2) + 4 * (nl + 1) == V:
            return n, nl
    raise RuntimeError(f"DRESS_PATH lattice not recognised: {V} vertices {F} faces")


def step_path_over_plate(D, ob, plate="TEE_BOX", cam=None):
    """Cut the flagstone ribbon `ob` along the outline of the raised `plate`, lift the part over the plate onto it, keep the rest on the fairway, join the two with a vertical
    riser, and shift the UVs of the plate part by the hidden band (see TEE_STEP). Plan positions of every original vertex are untouched. Returns a report dict."""
    poly, zt = _plate_poly(plate)
    k_h, cxy, zt2, zf = tee_hidden_k(cam)
    off = L.Z_PATH
    skirt = 0.04
    me = ob.data
    n, nl = _path_lattice(me)
    tile = L.LOOK["LK_PATH"][2]
    # per-row tangent / right vector of the original lattice (for the UV shift): centre column positions
    co0 = np.array([v.co[:] for v in me.vertices])
    stride = nl + 2
    cen = co0[np.arange(n) * stride + nl // 2][:, :2]
    tg = np.gradient(cen, axis=0)
    tg /= np.maximum(np.hypot(tg[:, 0], tg[:, 1]), 1e-9)[:, None]
    from mathutils.kdtree import KDTree
    kd = KDTree(n)
    for i, (x, y) in enumerate(cen.tolist()):
        kd.insert((x, y, 0.0), i)
    kd.balance()
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    ptop = bm.faces.layers.int.new("ptop")
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        i = f.index
        f[ptop] = 1 if (i < (n - 1) * (nl + 1) and 1 <= i % (nl + 1) <= nl - 1) else 0
    n_cuts = 0
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        e_ = b - a
        ln = float(np.hypot(*e_))
        if ln < 1e-6:
            continue
        nx_, ny_ = e_[1] / ln, -e_[0] / ln
        lo, hi = np.minimum(a, b) - 0.3, np.maximum(a, b) + 0.3
        sel = []
        for f in bm.faces:
            xs = [v.co.x for v in f.verts]
            ys = [v.co.y for v in f.verts]
            if max(xs) < lo[0] or min(xs) > hi[0] or max(ys) < lo[1] or min(ys) > hi[1]:
                continue
            ds = [(v.co.x - a[0]) * nx_ + (v.co.y - a[1]) * ny_ for v in f.verts]
            if max(ds) > 1e-7 and min(ds) < -1e-7:
                sel.append(f)
        if not sel:
            continue
        geom = list(sel) + list({e2 for f in sel for e2 in f.edges}) + list({v2 for f in sel for v2 in f.verts})
        r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=(float(a[0]), float(a[1]), 0.0), plane_no=(float(nx_), float(ny_), 0.0),
                                   use_snap_center=False, clear_outer=False, clear_inner=False)
        n_cuts += len(r["geom_cut"])
    bm.faces.ensure_lookup_table()
    # classify faces: inside the plate outline or outside (no face may straddle the outline any more)
    eps = 2e-5
    cls = {}
    mixed = 0
    for f in bm.faces:
        sd = _poly_sd(poly, [v.co.x for v in f.verts], [v.co.y for v in f.verts])
        if (sd > eps).any() and (sd < -eps).any():
            mixed += 1
        c = f.calc_center_median()
        cls[f] = 1 if _poly_sd(poly, [c.x], [c.y])[0] < 0 else 0
    if mixed:
        raise RuntimeError(f"{ob.name}: {mixed} faces straddle the {plate} outline after the cuts")
    seam = [e for e in bm.edges if len(e.link_faces) == 2 and cls[e.link_faces[0]] != cls[e.link_faces[1]]]
    bd = _poly_boundary_dist(poly, [v.co.x for e in seam for v in e.verts], [v.co.y for e in seam for v in e.verts])
    if len(seam) == 0 or float(bd.max()) > 1e-4:
        raise RuntimeError(f"{ob.name}: {len(seam)} seam edges, farthest {float(bd.max()) if len(bd) else None} m from the {plate} outline")
    # the seam edges before the split, keyed by their end points, so the risers can be built afterwards
    seam_keys = {}
    for e in seam:
        pa = tuple(np.round([e.verts[0].co.x, e.verts[0].co.y, e.verts[0].co.z], 6))
        pb = tuple(np.round([e.verts[1].co.x, e.verts[1].co.y, e.verts[1].co.z], 6))
        seam_keys[e.index] = (pa, pb)
    r = bmesh.ops.split_edges(bm, edges=seam)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    cls = {f: (1 if _poly_sd(poly, [f.calc_center_median().x], [f.calc_center_median().y])[0] < 0 else 0) for f in bm.faces}
    n_in = n_out = n_seam_out = 0
    vside = {}
    for v in bm.verts:
        cs = {cls[f] for f in v.link_faces}
        if len(cs) != 1:
            raise RuntimeError(f"{ob.name}: vertex {v.index} touches faces of both sides after the split")
        vside[v] = cs.pop()
    top_v = {v for v in bm.verts if any(f[ptop] == 1 for f in v.link_faces)}
    zf_top = zf + off
    for v in bm.verts:
        on_seam = float(_poly_boundary_dist(poly, [v.co.x], [v.co.y])[0]) < 1e-4
        if vside[v] == 1:
            v.co.z = (zt + off) if v in top_v else (zt - skirt)
            n_in += 1
        elif on_seam:
            v.co.z = zf_top if v in top_v else (zf - skirt)
            n_seam_out += 1
        else:
            n_out += 1
    # UV shift of the plate part: p' = C + k (p - C), delta in plan = (k - 1) (p - C), expressed in the ribbon's own (lateral, arc) frame
    shift_u = shift_v = 0.0
    cnt_sh = 0
    for f in bm.faces:
        if cls[f] != 1:
            continue
        for lp in f.loops:
            p = lp.vert.co
            i = kd.find((p.x, p.y, 0.0))[1]
            t = tg[i]
            rt = np.array([t[1], -t[0]])
            d = np.array([(k_h - 1.0) * (p.x - cxy[0]), (k_h - 1.0) * (p.y - cxy[1])])
            du, dv = float(d @ rt) / tile, float(d @ t) / tile
            lp[uvl].uv = (lp[uvl].uv[0] + du, lp[uvl].uv[1] + dv)
            shift_u, shift_v, cnt_sh = max(shift_u, abs(du)), max(shift_v, abs(dv)), cnt_sh + 1
    # risers: pair each in-side seam edge with the out-side edge at the same place
    by_key = {}
    for e in bm.edges:
        if len(e.link_faces) != 1:
            continue
        pa, pb = ((round(e.verts[0].co.x, 6), round(e.verts[0].co.y, 6)), (round(e.verts[1].co.x, 6), round(e.verts[1].co.y, 6)))
        if float(_poly_boundary_dist(poly, [e.verts[0].co.x, e.verts[1].co.x], [e.verts[0].co.y, e.verts[1].co.y]).max()) > 1e-4:
            continue
        by_key.setdefault(frozenset((pa, pb)), []).append(e)
    n_riser = 0
    for key, es in by_key.items():
        if len(es) != 2:
            continue
        e_in = next((e for e in es if cls[e.link_faces[0]] == 1), None)
        e_out = next((e for e in es if cls[e.link_faces[0]] == 0), None)
        if e_in is None or e_out is None:
            continue
        a_in, b_in = e_in.verts
        a_out = next(v for v in e_out.verts if (round(v.co.x, 6), round(v.co.y, 6)) == (round(a_in.co.x, 6), round(a_in.co.y, 6)))
        b_out = next(v for v in e_out.verts if (round(v.co.x, 6), round(v.co.y, 6)) == (round(b_in.co.x, 6), round(b_in.co.y, 6)))
        f_in = e_in.link_faces[0]
        f_out = e_out.link_faces[0]
        out_dir = f_out.calc_center_median() - f_in.calc_center_median()
        try:
            fr = bm.faces.new((a_in, b_in, b_out, a_out))
        except ValueError:
            continue
        nrm = fr.normal
        if nrm.x * out_dir.x + nrm.y * out_dir.y < 0:
            fr.normal_flip()
        fr.material_index = f_in.material_index
        fr[ptop] = 0
        fr.smooth = False
        uv_a = next(lp[uvl].uv.copy() for lp in f_in.loops if lp.vert == a_in)
        uv_b = next(lp[uvl].uv.copy() for lp in f_in.loops if lp.vert == b_in)
        for lp in fr.loops:
            lp[uvl].uv = uv_a if lp.vert in (a_in, a_out) else uv_b
        n_riser += 1
    bm.faces.layers.int.remove(ptop)
    bm.to_mesh(me)
    bm.free()
    me.update()
    L._finish_mesh(ob, 50.0)
    return dict(path=ob.name, nl=nl, rows=n, cuts=n_cuts, seam_edges=len(seam), in_verts=n_in, out_seam_verts=n_seam_out, risers=n_riser, k=round(k_h, 4), zt=zt, zf=zf,
                uv_shift_max=(round(shift_u, 4), round(shift_v, 4)), faces=len(me.polygons))


def tee_step(D, info):
    """Round 6: the whole tee-step treatment (path cut + lift + riser, UV shifts of the plate part). Returns a report."""
    if not TEE_STEP:
        return dict(enabled=False)
    rep = dict(enabled=True, paths=[])
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("DRESS_PATH")]:
        poly, _zt = _plate_poly("TEE_BOX")
        co = np.array([v.co[:] for v in ob.data.vertices])
        if (_poly_sd(poly, co[:, 0], co[:, 1]) < 0).any():
            rep["paths"].append(step_path_over_plate(D, ob))
    return rep
