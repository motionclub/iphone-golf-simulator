# ----------------------------------------------------------------------------- round 6: what the address camera SEES at the tee step (the gates for the reviewer's finding)
SEEN_COLS_GRASS = tuple(range(8, 892, 12))
SEEN_NEAR, SEEN_FAR = 3, 24
SEEN_MAX_GRASS_JUMP = 0.004        # tile units of the 10 m fairway tile = 4 cm of ground: the texture phase jump across the plate edge, extrapolated from both sides (round 5: 0.035 = 35 cm)
SEEN_MAX_PATH_JUMP = 0.008         # tile units of the 5 m path tile = 4 cm


def _tee_seen_bvh():
    """BVH (world) of the surfaces the tee camera sees at the step (TEE_BOX, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN_APRON, DRESS_PATH_*) with per-triangle UVs and object names."""
    bpy.context.view_layer.update()
    Vs, Fs, tags, base = [], [], [], 0
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and (o.name in ("TEE_BOX", "FAIRWAY", "FAIRWAY_FIRSTCUT", "GREEN_APRON") or o.name.startswith("DRESS_PATH"))]:
        me = ob.data
        me.calc_loop_triangles()
        mw = np.array(ob.matrix_world)
        V = np.array([v.co[:] for v in me.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        uv = np.array([l.uv[:] for l in me.uv_layers.active.data]).reshape(-1, 2) if me.uv_layers.active else None
        for lt in me.loop_triangles:
            Fs.append(tuple(base + int(i) for i in lt.vertices))
            tags.append((ob.name, None if uv is None else uv[list(lt.loops)]))
        Vs += [tuple(p) for p in V.tolist()]
        base += len(V)
    return BVHTree.FromPolygons(Vs, Fs), tags, np.array(Vs), Fs


def tee_seen_seam(cam=None, cols=SEEN_COLS_GRASS, near=SEEN_NEAR, far=SEEN_FAR, W=900, H=1600):
    """Ray casts through the 900 x 1600 tee frame (the address camera). Per pixel column the plate's edge row r0 is where the first hit drops from the plate's height to the fairway's (z < plate - 5 cm).
    GRASS columns (hits TEE_BOX above the seam, FAIRWAY below on both sides): the (u, v) of the hit at rows r0 + near .. r0 + far (plate side) and r0 - near .. r0 - far (fairway side) are fitted by lines
    in the row number; their values at the seam row differ by the texture JUMP the viewer sees (tile units, wrapped to -0.5..0.5). PATH columns (DRESS_PATH on both sides): the same jump of the path
    UV, and the count of rows between r0 - far and r0 + far where the first hit is NOT the path (a grass strip across the stones). Returns dict."""
    cam_, look_, _b = tee_cam() if cam is None else cam
    bvh, tags, Vs, Fs = _tee_seen_bvh()
    tb = bpy.data.objects["TEE_BOX"]
    zt = float(max(v.co.z for v in tb.data.vertices))
    hide_z = zt - 0.05

    def hit(px, py):
        d = _cam_ray(cam_, look_, px, py, W, H)
        h = bvh.ray_cast(cam_, d, 900.0)
        if h[0] is None:
            return None
        nm, uvs = tags[h[2]]
        a, b, c = (Vector(Vs[i].tolist()) for i in Fs[h[2]])
        wt = G.barycentric_transform(h[0], a, b, c, Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)))
        w1, w2 = wt.x, wt.y
        uv = (1 - w1 - w2) * uvs[0] + w1 * uvs[1] + w2 * uvs[2] if uvs is not None else np.zeros(2)
        return nm, float(h[0].z), uv

    def fit(rows, vals):
        r = np.array(rows, float)
        v = np.array(vals, float)
        k, c = np.polyfit(r, v, 1)
        return k, c, float(np.abs(v - (k * r + c)).max())

    wrap = lambda d: (d + 0.5) % 1.0 - 0.5
    grass, path = [], []
    for x in cols:
        r0 = None
        prev = None
        for py in range(900, 500, -1):
            h = hit(x, py)
            if h is None:
                prev = None
                continue
            if prev is not None and prev[1] >= hide_z and h[1] < hide_z:
                r0 = py
                break
            prev = h
        if r0 is None:
            continue
        rows_t = list(range(r0 + near, r0 + far + 1, 3))
        rows_f = list(range(r0 - far, r0 - near + 1, 3))
        ht = [hit(x, r) for r in rows_t]
        hf = [hit(x, r) for r in rows_f]
        if any(q is None for q in ht + hf):
            continue
        names_t = {q[0] for q in ht}
        names_f = {q[0] for q in hf}
        if names_t == {"TEE_BOX"} and names_f <= {"FAIRWAY", "FAIRWAY_FIRSTCUT", "GREEN_APRON"} and len(names_f) == 1:
            ju, jv = [], []
            for dim in (0, 1):
                kt, ct, rt_ = fit(rows_t, [q[2][dim] for q in ht])
                kf, cf, rf_ = fit(rows_f, [q[2][dim] for q in hf])
                # unwrap each side on its own (fits on values that may cross an integer): shift the values by their first element's nearest integer
                (ju if dim == 0 else jv).append((cf + kf * (r0 + 0.5)) - (ct + kt * (r0 + 0.5)))
            du, dv = wrap(ju[0]), wrap(jv[0])
            grass.append((x, r0, du, dv))
        elif all(n_.startswith("DRESS_PATH") for n_ in names_t | names_f):
            gap = 0
            for r in range(r0 - far, r0 + far + 1):
                q = hit(x, r)
                if q is None or not q[0].startswith("DRESS_PATH"):
                    gap += 1
            jv = []
            for dim in (0, 1):
                kt, ct, _ = fit(rows_t, [q[2][dim] for q in ht])
                kf, cf, _ = fit(rows_f, [q[2][dim] for q in hf])
                jv.append(wrap((cf + kf * (r0 + 0.5)) - (ct + kt * (r0 + 0.5))))
            path.append((x, r0, jv[0], jv[1], gap))
    return dict(grass=grass, path=path)


def _seen_summary(sc):
    g, p = sc["grass"], sc["path"]
    gu = max((abs(q[2]) for q in g), default=float("nan"))
    gv = max((abs(q[3]) for q in g), default=float("nan"))
    pu = max((abs(q[2]) for q in p), default=float("nan"))
    pv = max((abs(q[3]) for q in p), default=float("nan"))
    gaps = sum(q[4] for q in p)
    return dict(n_grass=len(g), grass_du=gu, grass_dv=gv, n_path=len(p), path_du=pu, path_dv=pv, gap_rows=gaps,
                mean_row=float(np.mean([q[1] for q in g])) if g else None)
