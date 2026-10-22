# ----------------------------------------------------------------------------- round 6: the outcrop's near flank (reviewer, medium, arch shot)
OUTCROP_DRESS = True
OUTCROP_CUTS_M = (0.8, 1.7, 2.8)        # horizontal cuts this far under the outcrop's grass top (world z): the library facets span most of the wall, so a face-by-face re-material cannot dress only its upper band
OUTCROP_TURF_M = 0.8                    # the band under the grass top that wears turf
OUTCROP_MIX_M = 1.7                     # ... and the band under it that is patchy turf / rock
OUTCROP_AMP_M = (-0.10, 0.26)           # displacement of the cut vertices, outward (+) / inward (-), a smooth noise field: no flat polygon with straight edges


def dress_outcrop(D, outcrop, top, seed=3):
    """Reviewer (medium, arch shot): "a flat grey stone slab with hard straight edges ... a bare stone plate, the reference shows a grassy island top with shrubs and rubble". The slab is the outcrop's
    camera-side wall: the library mesh ROCK_OUTCROP_A is a hull of 163 big planar facets (one facet spans 2 m x 3 m, normal (0.68, -0.68, 0.27)), seen from the pad rim at 30 degrees. This cuts the
    mesh horizontally at OUTCROP_CUTS_M under the grass top, pushes the cut vertices in / out by a smooth noise field (the wall is no longer one plane, its silhouette is irregular), puts turf
    on the upper band (LK_ROUGH, a grassy bank hanging over the rock), patchy turf / rock on the next one and rock below, and re-writes the box UVs with the props library's own rule (object
    space / the slot's contract tile). Plan positions of the top ring (the grass rim every plant and vine is placed on) do not change. Returns a report dict."""
    me = outcrop.data
    bpy.context.view_layer.update()
    mw = np.array(outcrop.matrix_world)
    sz = float(np.linalg.svd(mw[:3, :3], compute_uv=False).min())
    sxy = float(np.linalg.svd(mw[:3, :3], compute_uv=False).max())
    z0 = float(mw[2, 3])
    names = [m.name.split(".")[0] if m else "" for m in me.materials]
    if "LK_ROUGH" not in names or "LK_ROCK" not in names:
        raise RuntimeError(f"outcrop materials {names}")
    i_rock, i_rough = names.index("LK_ROCK"), names.index("LK_ROUGH")
    n_before = len(me.polygons)
    bm = bmesh.new()
    bm.from_mesh(me)
    cut_z_obj = [((top - c) - z0) / sz for c in OUTCROP_CUTS_M]
    new_verts = set()
    for zo in cut_z_obj:
        r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0.0, 0.0, zo), plane_no=(0.0, 0.0, 1.0))
        for g in r["geom_cut"]:
            if isinstance(g, bmesh.types.BMVert):
                new_verts.add(g)
    bm.verts.ensure_lookup_table()
    # displacement of the cut vertices: radial from the outcrop axis (object space x, y), world-metre amplitude
    amp_lo, amp_hi = OUTCROP_AMP_M
    n_moved = 0
    for v in new_verts:
        if not v.is_valid:
            continue
        w = mw @ np.append(np.array(v.co[:]), 1.0)
        if w[2] > top - 0.05:
            continue
        nz_ = float(fbm_pt(w[0] * 0.9 + w[2] * 0.35, w[1] * 0.9 - w[2] * 0.2, seed))
        amp = amp_lo + (amp_hi - amp_lo) * nz_
        rad = np.array([v.co.x, v.co.y])
        ln = float(np.hypot(*rad))
        if ln < 1e-6:
            continue
        d = rad / ln
        v.co.x += float(d[0]) * amp / sxy
        v.co.y += float(d[1]) * amp / sxy
        n_moved += 1
    # materials: band + patchy mix
    bm.faces.ensure_lookup_table()
    n_turf = n_mix = 0
    rg = random.Random(D.number * 311 + seed)
    for f in bm.faces:
        c = f.calc_center_median()
        w = mw @ np.array([c.x, c.y, c.z, 1.0])
        nn = f.normal
        nw = mw[:3, :3] @ np.array([nn.x, nn.y, nn.z])
        nw /= max(float(np.linalg.norm(nw)), 1e-9)
        patch = rg.random()
        if f.material_index != i_rock and f.material_index != i_rough:
            continue
        if w[2] > top - 0.05:
            continue
        if nw[2] < -0.05:
            f.material_index = i_rock
            continue
        if w[2] > top - OUTCROP_TURF_M:
            f.material_index = i_rough
            n_turf += 1
        elif w[2] > top - OUTCROP_MIX_M:
            f.material_index = i_rough if patch < 0.5 else i_rock
            n_mix += f.material_index == i_rough
        else:
            f.material_index = i_rock
    bm.to_mesh(me)
    bm.free()
    me.update()
    L._finish_mesh(outcrop, 13.0)
    tiles = [(PL.TILE.get(m.name.split(".")[0]) or 4.0) if m is not None else 4.0 for m in me.materials]
    uv = PL.box_uv_expected(me, tiles)
    me.uv_layers.active.data.foreach_set("uv", uv.ravel())
    me.update()
    return dict(faces_before=n_before, faces_after=len(me.polygons), cut_vertices=len(new_verts), moved=n_moved, turf_faces=n_turf, mix_turf_faces=int(n_mix), cuts_obj_z=[round(z, 3) for z in cut_z_obj])


def fbm_pt(x, y, seed):
    return float(L.fbm(np.array([x]), np.array([y]), 3.2, seed)[0])
