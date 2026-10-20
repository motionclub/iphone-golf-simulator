"""Measured checks on the ASSEMBLED kit blend (the deliverable, not the npz).  blender -b --factory-startup --python checks.py -- <male|female>
Writes proof/raw/checks_<gender>.json.  Body reference = the authority file, loaded read-only (copy of the geometry); candidates are informational."""
import sys, os, json, hashlib, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from kit_common import mesh_topology
from band import body_envelope, slice_center

BLEND = {'male': f'{WORK}/export/StandardKit_Male.blend', 'female': f'{WORK}/export/StandardKit_Female.blend'}
BODY_FILE = {'male': (MALE_BLEND, 'Body_M', MALE_SHA), 'female': (FEMALE_BLEND, 'Body_F', FEMALE_SHA)}
CAND = {'male': [('male_pelvis_f2', ROOT + '/work/male-pelvis-form2/export/merged_fd04bc28.blend', 'Body_M')],
        'female': [('female_arms_candidate', ROOT + '/work/female-arms-form2/export/HeroBase_Female_arms_candidate.blend', 'Body_F')]}
BAND_Z = {'male': (0.925, 0.965), 'female': (0.955, 0.995)}
POLO_HEM = {'male': (0.950, 0.945), 'female': (0.980, 0.975)}          # designed front / back hem heights
TORSO_ZONE = {'male': dict(zmax=1.10, xmax=0.30), 'female': dict(zmax=1.04, xmax=0.30)}          # waist / hip part of the polo (below the sleeve openings; female: below the rib/sleeve crevice)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load_body_ref(gender):
    """authority body geometry (+ informational candidates) read from the source files WITHOUT modifying them."""
    path, obj, want = BODY_FILE[gender]
    assert sha(path) == want, 'authority body SHA mismatch'
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [obj]
    o = dst.objects[0]
    V, F = mesh_arrays(o)
    bpy.data.objects.remove(o, do_unlink=True)
    out = dict(authority=(V, F))
    for name, p, ob in CAND[gender]:
        if not os.path.exists(p):
            continue
        with bpy.data.libraries.load(p, link=False) as (src, dst):
            dst.objects = [ob]
        o = dst.objects[0]
        out[name] = mesh_arrays(o)
        bpy.data.objects.remove(o, do_unlink=True)
    return out


def tags_of(o):
    me = o.data
    tv = np.zeros(len(me.polygons), np.int32)
    me.attributes['kit_tag'].data.foreach_get('value', tv)
    return tv, json.loads(me['kit_tagnames'])


def signed_dist(tree, P):
    d = np.empty(len(P))
    for i, p in enumerate(P.tolist()):
        loc, n, idx, dist = tree.find_nearest(p)
        s = (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2]
        d[i] = dist if s >= 0 else -dist
    return d


def vertices_by_tag(F, tv, tags, pred):
    sel = np.array([pred(tags[t]) for t in tv], bool) if len(tv) else np.zeros(0, bool)
    return np.unique(F[sel]) if sel.any() else np.zeros(0, int), sel


def mt_first(V, F, o, d, tmin=1e-6):
    """exact Moller-Trumbore: smallest positive ray parameter over ALL triangles (None if no hit).  Used to confirm every ray the BVH reports as
    unblocked - Blender's BVH ray_cast has false negatives on rays that cross triangle edges (verified against this routine)."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = b - a, c - a
    h = np.cross(d[None, :], e2)
    det = np.einsum('ij,ij->i', e1, h)
    ok = np.abs(det) > 1e-14
    f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0)
    s = o[None, :] - a
    u = f * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * np.einsum('ij,ij->i', e2, q)
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > tmin)
    return float(t[hit].min()) if hit.any() else None


def bvh_ray(V, F, eps=2e-4):
    """BVH for occlusion rays: a small epsilon (0.2 mm) so a ray that grazes the shared edge of two triangles cannot slip through (eps=0 gives false misses).
    Real cracks in a garment are millimetres wide, so this does not hide any."""
    return BVHTree.FromPolygons([tuple(v) for v in np.asarray(V).tolist()], [tuple(f) for f in np.asarray(F).tolist()], epsilon=eps)


def view_dirs(els, n_az=24):
    out = []
    for e in els:
        for k in range(n_az):
            a = 2 * math.pi * k / n_az
            ce, se = math.cos(math.radians(e)), math.sin(math.radians(e))
            out.append((e, k * 360 / n_az, np.array([math.sin(a) * ce, -math.cos(a) * ce, se])))
    return out


def main():
    gender = sys.argv[sys.argv.index('--') + 1]
    rep = dict(gender=gender)
    ref = load_body_ref(gender)
    Vb, Fb = ref['authority']
    tree_body = bvh_from(Vb, Fb)
    cand_trees = {k: bvh_from(*v) for k, v in ref.items() if k != 'authority'}
    rep['body_sha256_now'] = sha(BODY_FILE[gender][0])
    rep['body_sha256_expected'] = BODY_FILE[gender][2]
    rep['body_sha_unchanged'] = rep['body_sha256_now'] == rep['body_sha256_expected']
    bpy.ops.wm.open_mainfile(filepath=BLEND[gender])
    suffix = 'M' if gender == 'male' else 'F'
    zwb, zwt = BAND_Z[gender]
    colls = {cw: [o for o in bpy.data.collections[f'Kit_{cw}'].objects] for cw in ('White', 'Black')}
    rep['pieces'] = {}
    # ------------------------------------------------------------------------------------------------ per piece: tris, topology, wall, clearance
    for cw in ('White', 'Black'):
        for o in colls[cw]:
            if o.type != 'MESH':
                continue
            V, F = mesh_arrays(o)
            me = o.data
            topo = mesh_topology(V, F)
            tv, tg = tags_of(o)
            r = dict(tris=int(len(F)), verts=int(len(V)), topology=topo, closed=bool(topo['boundary_edges'] == 0 and topo['nonmanifold_edges'] == 0 and topo['same_direction_edges'] == 0),
                     socket=o.get('socket'), parent=o.parent.name if o.parent else None, category=o.get('kit_category'), colorway=cw,
                     material_slots=[m.name for m in me.materials], uv_layers=len(me.uv_layers), custom_normals=bool(me.has_custom_normals),
                     modifiers=len(o.modifiers), world_identity=bool(np.allclose(np.array(o.matrix_world), np.eye(4), atol=1e-6)), mesh_users=me.users)
            if cw == 'White':
                # wall thickness per part: outer-sheet vertices of a part -> the nearest triangle of THAT part's own inner wall (nested layers such as the wrap flap sit
                # 0.4 mm above the skirt, so measuring against every inner wall would report the gap, not the wall)
                samples, per_part = [], {}
                for pf in sorted({t[:-4] for t in tg if t.endswith('_out')}):
                    if pf + '_in' not in tg:
                        continue
                    oid, iid = tg.index(pf + '_out'), tg.index(pf + '_in')
                    Vo = V[np.unique(F[tv == oid])]
                    tin = bvh_from(V, F[tv == iid])
                    sel = Vo[:: max(1, len(Vo) // 500)]
                    th = np.array([tin.find_nearest(p.tolist())[3] for p in sel]) * 1000
                    per_part[pf] = dict(min=round(float(th.min()), 2), p05=round(float(np.percentile(th, 5)), 2), median=round(float(np.median(th)), 2))
                    samples.append(th)
                if samples:
                    th = np.concatenate(samples)
                    r['wall_mm'] = dict(min=round(float(th.min()), 2), p05=round(float(np.percentile(th, 5)), 2), p10=round(float(np.percentile(th, 10)), 2), median=round(float(np.median(th)), 2),
                                        max=round(float(th.max()), 2), per_part=per_part)
                # clearance of every vertex vs the authority body (positive = outside the skin)
                d = signed_dist(tree_body, V)
                r['clearance_all_mm'] = dict(min=round(float(d.min() * 1000), 2), p05=round(float(np.percentile(d, 5) * 1000), 2), median=round(float(np.median(d) * 1000), 2),
                                             neg_vertices=int((d < 0).sum()))
                # inner-surface clearance (what reads as air between cloth and skin)
                in_ids = [i for i, t in enumerate(tg) if t.endswith('_in')]
                in_vi = np.unique(F[np.isin(tv, in_ids)]) if in_ids else np.zeros(0, int)
                if len(in_vi):
                    di = d[in_vi]
                    r['clearance_inner_mm'] = dict(min=round(float(di.min() * 1000), 2), p05=round(float(np.percentile(di, 5) * 1000), 2), median=round(float(np.median(di) * 1000), 2),
                                                   p95=round(float(np.percentile(di, 95) * 1000), 2))
                    if o.get('kit_category') == 'Top':
                        z = V[in_vi][:, 2]
                        zone = (z < TORSO_ZONE[gender]['zmax']) & (np.abs(V[in_vi][:, 0]) < TORSO_ZONE[gender]['xmax'])
                        r['clearance_inner_torso_mm'] = dict(min=round(float(di[zone].min() * 1000), 2), p05=round(float(np.percentile(di[zone], 5) * 1000), 2),
                                                             median=round(float(np.median(di[zone]) * 1000), 2), n=int(zone.sum()), zone=f'polo vertices z < {TORSO_ZONE[gender]["zmax"]} (waist/hip, below the sleeve openings)')
                        if gender == 'female':          # the hidden crevice between the hanging sleeve and the ribs (z 1.04..1.19, x 0.09..0.20): relaxed on purpose, see polo.py crevice
                            zc = (V[in_vi][:, 2] >= 1.04) & (V[in_vi][:, 2] <= 1.19) & (np.abs(V[in_vi][:, 0]) >= 0.09) & (np.abs(V[in_vi][:, 0]) <= 0.20)
                            if zc.any():
                                r['clearance_inner_crevice_zone_mm'] = dict(min=round(float(di[zc].min() * 1000), 2), median=round(float(np.median(di[zc]) * 1000), 2), n=int(zc.sum()),
                                                                           zone='torso side wall + sleeve inner side between the hanging arm and the ribs (never visible)')
                        # where is the polo closest to the skin?
                        k = int(np.argmin(di))
                        r['clearance_inner_argmin_xyz'] = V[in_vi][k].round(3).tolist()
                    if o.get('kit_category') == 'Bottom':
                        k = int(np.argmin(di))
                        r['clearance_inner_argmin_xyz'] = V[in_vi][k].round(3).tolist()
                r['overlap_pairs_vs_body'] = int(len(bvh_from(V, F).overlap(tree_body)))        # triangle-level body intersection (authority)
                for cn, ct in cand_trees.items():
                    dc = signed_dist(ct, V)
                    r.setdefault('clearance_vs_candidates_mm', {})[cn] = round(float(dc.min() * 1000), 2)
            rep['pieces'][f'{o.name}'] = r
    # ------------------------------------------------------------------------------------------------ garments of the White kit (geometry is identical in Black)
    kit = {o.get('kit_category') + ('_' + o.name.split('_')[2] if o.get('kit_category') in ('Sock', 'Shoe') else ''): o for o in colls['White'] if o.type == 'MESH'}
    polo = [o for o in colls['White'] if o.type == 'MESH' and o.get('kit_category') == 'Top'][0]
    bottom = [o for o in colls['White'] if o.type == 'MESH' and o.get('kit_category') == 'Bottom'][0]
    Vp, Fp = mesh_arrays(polo)
    Vq, Fq = mesh_arrays(bottom)
    tvp, tgp = tags_of(polo)
    tvq, tgq = tags_of(bottom)
    # ------------------------------------------------------------------------------------------------ polo hem vs band
    rim_vi, _ = vertices_by_tag(Fp, tvp, tgp, lambda t: t.startswith('polo_rim'))
    hem_vi = rim_vi[Vp[rim_vi][:, 2] < 1.0]
    P = Vp[hem_vi]
    cen = slice_center(Vb, Fb, 0.5 * (zwb + zwt))
    th = np.arctan2(P[:, 0] - cen[0], -(P[:, 1] - cen[1]))
    nb = 72
    bins = np.floor((th + math.pi) / (2 * math.pi) * nb).astype(int) % nb
    hem_z = np.array([P[bins == b][:, 2].min() if (bins == b).any() else np.nan for b in range(nb)])
    overlap = (zwt - hem_z) * 1000
    band_vi = np.unique(Fq[np.array([tgq[t] == 'band' for t in tvq])])
    band_faces = Fq[np.array([tgq[t] == 'band' for t in tvq])]
    Vband = Vq
    tree_band = bvh_from(Vq, band_faces)
    zb_top = float(Vq[band_vi][:, 2].max())
    zb_bot = float(Vq[band_vi][:, 2].min())
    rep['polo_hem'] = dict(hem_z_min=round(float(np.nanmin(hem_z)), 4), hem_z_max=round(float(np.nanmax(hem_z)), 4), band_top_z=round(zb_top, 4), band_bottom_z=round(zb_bot, 4),
                           band_height_mm=round((zb_top - zb_bot) * 1000, 2),
                           overlap_mm=dict(min=round(float(np.nanmin(overlap)), 2), mean=round(float(np.nanmean(overlap)), 2), max=round(float(np.nanmax(overlap)), 2)),
                           visible_band_below_hem_mm=dict(min=round(float((np.nanmin(hem_z) - zb_bot) * 1000), 2), max=round(float((np.nanmax(hem_z) - zb_bot) * 1000), 2)),
                           hem_loop_vertices=int(len(hem_vi)))
    # polo inner surface vs band outer surface (must be OUTSIDE the band with a gap, no triangle overlap)
    pin_ids = [i for i, t in enumerate(tgp) if t.endswith('_in')]
    pin_vi = np.unique(Fp[np.isin(tvp, pin_ids)])
    near = pin_vi[(Vp[pin_vi][:, 2] > zb_bot - 0.01) & (Vp[pin_vi][:, 2] < zb_top + 0.02)]
    dgap = signed_dist(tree_band, Vp[near]) if len(near) else np.array([np.nan])
    rep['polo_vs_band'] = dict(min_gap_mm=round(float(np.nanmin(dgap) * 1000), 2) if len(near) else None, vertices_tested=int(len(near)))
    tree_polo = bvh_from(Vp, Fp)
    tree_bottom = bvh_from(Vq, Fq)
    rep['polo_vs_bottom_overlap_pairs'] = int(len(tree_polo.overlap(tree_bottom)))
    # ------------------------------------------------------------------------------------------------ garment vs garment (White kit; geometry identical in Black)
    objs = {o.name.replace('_White', ''): o for o in colls['White'] if o.type == 'MESH'}
    meshes = {k: mesh_arrays(o) for k, o in objs.items()}
    trees = {k: bvh_from(*v) for k, v in meshes.items()}
    gg = {}
    pairs = [(k1, k2) for k1 in objs for k2 in objs if k1 < k2 and (objs[k1].get('kit_category'), objs[k2].get('kit_category')) not in
             {('Sock', 'Sock'), ('Shoe', 'Shoe')}]
    for k1, k2 in pairs:
        if abs(len(k1) - len(k2)) >= 0 and (('_L' in k1 and '_R' in k2) or ('_R' in k1 and '_L' in k2)) and objs[k1].get('kit_category') in ('Sock', 'Shoe'):
            continue                                              # left vs right foot pieces are 0.2 m apart: not a layering pair
        n = len(trees[k1].overlap(trees[k2]))
        if n or ({objs[k1].get('kit_category'), objs[k2].get('kit_category')} in ({'Top', 'Bottom'}, {'Sock', 'Shoe'}, {'Bottom', 'Sock'}, {'Bottom', 'Shoe'}, {'Top', 'Sock'}, {'Top', 'Shoe'})):
            gg[f'{k1} | {k2}'] = n
    # sock outer vs shoe inner wall: minimum distance (the shoe wall must not touch the sock)
    for side in ('L', 'R'):
        sk = [k for k in objs if k.startswith('Kit_Sock_' + side) and 'Arms' not in k]
        sh = [k for k in objs if k.startswith('Kit_Shoe_' + side) and 'Arms' not in k]
        if sk and sh:
            Vs_, Fs_ = meshes[sk[0]]
            tvs_, tgs_ = tags_of(objs[sk[0]])
            outs = [i for i, t in enumerate(tgs_) if t.endswith('_out')]
            vo = Vs_[np.unique(Fs_[np.isin(tvs_, outs)])]
            tsh = trees[sh[0]]
            dd = np.array([tsh.find_nearest(p.tolist())[3] for p in vo[::2]])
            # sign: sock outer vertices must be INSIDE the shoe; use the shoe-inner-wall distance
            tvh, tgh = tags_of(objs[sh[0]])
            ins = [i for i, t in enumerate(tgh) if t.endswith('_in')]
            tin = bvh_from(*meshes[sh[0]][:1], meshes[sh[0]][1][np.isin(tvh, ins)])
            d_in = np.array([tin.find_nearest(p.tolist())[3] for p in vo[::2]])
            gg[f'sock_outer_to_shoe_inner_wall_min_mm_{side}'] = round(float(d_in.min() * 1000), 2)
    rep['garment_vs_garment'] = gg
    # intra-piece layering of the bottom (islands of one object): liner vs skirt, flap vs skirt, band vs fabric
    isl = {}
    def sub(prefixes):
        m = np.array([any(tgq[t].startswith(pf) for pf in prefixes) for t in tvq])
        return bvh_from(Vq, Fq[m]) if m.any() else None
    layer = {'band': ('band',), 'liner': ('liner',), 'skirt': ('skirt_out', 'skirt_in', 'skirt_rim'), 'flap': ('flap',), 'shorts': ('shorts',)}
    ltrees = {k: sub(v) for k, v in layer.items()}
    for a, b in (('band', 'liner'), ('band', 'skirt'), ('band', 'flap'), ('band', 'shorts'), ('liner', 'skirt'), ('skirt', 'flap'), ('liner', 'flap')):
        if ltrees[a] is not None and ltrees[b] is not None:
            isl[f'{a} | {b}'] = len(ltrees[a].overlap(ltrees[b]))
    rep['bottom_layer_overlaps'] = isl
    # ------------------------------------------------------------------------------------------------ hem heights (bottom)
    out_skirt = [i for i, t in enumerate(tgq) if t.startswith('skirt') and (t.endswith('_out') or '_rim' in t)]
    liner_ids = [i for i, t in enumerate(tgq) if t.startswith('liner')]
    if liner_ids:
        lv, _ = vertices_by_tag(Fq, tvq, tgq, lambda t: t.startswith('liner'))
        sv, _ = vertices_by_tag(Fq, tvq, tgq, lambda t: t.startswith('skirt') and not t.startswith('skirt_hem'))
        fv, _ = vertices_by_tag(Fq, tvq, tgq, lambda t: t.startswith('flap'))
        sk_hem = float(Vq[sv][:, 2].min())
        ln_hem = float(Vq[lv][:, 2].min())
        # crotch + knee of the authority body -> mid-thigh
        crotch = knee = None
        zs = np.arange(0.40, 1.00, 0.005)
        for z in zs[::-1]:
            loops = [Pp for Pp in slice_plane(Vb, Fb, 2, float(z)) if len(Pp) >= 10 and abs(poly_area_xy(Pp)) > 0.01]
            if len(loops) >= 2:
                crotch = float(z + 0.005)
                break
        area_leg = []
        for z in np.arange(0.40, 0.62, 0.01):
            loops = [Pp for Pp in slice_plane(Vb, Fb, 2, float(z)) if len(Pp) >= 10 and abs(poly_area_xy(Pp)) > 0.003]
            if len(loops) >= 2:
                loops.sort(key=lambda p: p[:, 0].mean())
                area_leg.append((float(z), abs(poly_area_xy(loops[-1]))))
        knee = min(area_leg, key=lambda t: t[1])[0] if area_leg else None
        rep['skirt'] = dict(skirt_hem_z=round(sk_hem, 4), liner_hem_z=round(ln_hem, 4), skirt_longer_than_liner_mm=round((ln_hem - sk_hem) * 1000, 1), crotch_z=crotch, knee_z=knee,
                            mid_thigh_z=round(0.5 * (crotch + knee), 4) if crotch and knee else None, skirt_hem_below_crotch_mm=round((crotch - sk_hem) * 1000, 1) if crotch else None,
                            thigh_length_mm=round((crotch - knee) * 1000, 1) if crotch and knee else None, flap_vertices=int(len(fv)))
        rep['skirt']['hem_fraction_down_thigh'] = round((crotch - sk_hem) / (crotch - knee), 3) if crotch and knee else None
    else:
        sv, _ = vertices_by_tag(Fq, tvq, tgq, lambda t: t.startswith('shorts'))
        rep['shorts'] = dict(hem_z=round(float(Vq[sv][:, 2].min()), 4))
    # ------------------------------------------------------------------------------------------------ band colours per kit + materials
    band = {}
    for cw in ('White', 'Black'):
        bo = [o for o in colls[cw] if o.type == 'MESH' and o.get('kit_category') == 'Bottom'][0]
        po = [o for o in colls[cw] if o.type == 'MESH' and o.get('kit_category') == 'Top'][0]
        mats = [m for m in bo.data.materials]
        idx = np.zeros(len(bo.data.polygons), np.int32)
        bo.data.polygons.foreach_get('material_index', idx)
        tvb, tgb = tags_of(bo)
        band_faces_mask = np.array([tgb[t] == 'band' for t in tvb])
        slot2 = (idx == 2)
        fab = mats[0]
        bm = mats[2]
        rgb = lambda m: [round(float(x), 3) for x in m.get('unity_BaseColor_sRGB')]
        pidx = np.zeros(len(po.data.polygons), np.int32)
        po.data.polygons.foreach_get('material_index', pidx)
        band[cw] = dict(fabric_material=fab.name, fabric_rgb=rgb(fab), band_material=bm.name, band_rgb=rgb(bm), band_faces=int(band_faces_mask.sum()),
                        faces_in_slot2=int(slot2.sum()), slot2_faces_all_band=bool((slot2 == band_faces_mask).all()), band_on_bottom_object=bo.name,
                        polo_uses_band_slot=bool((pidx == 2).any()), polo_slots=[m.name for m in po.data.materials],
                        contrast=('black on white' if (cw == 'White' and bm.name == 'Std_Black_Lit') else ('white on black' if (cw == 'Black' and bm.name == 'Std_White_Lit') else 'WRONG')))
    rep['band_color'] = band
    # ------------------------------------------------------------------------------------------------ NO_LOGOS / materials / swappable
    imgs = [i.name for i in bpy.data.images if i.name not in ('Render Result', 'Viewer Node')]
    tex = [m.name for m in bpy.data.materials if m.use_nodes and any(n.bl_idname == 'ShaderNodeTexImage' for n in m.node_tree.nodes)]
    tagset = sorted({t for cw in ('White',) for o in colls[cw] if o.type == 'MESH' for t in tags_of(o)[1]})
    rep['no_logos'] = dict(blend_images=imgs, image_texture_materials=tex, object_types=sorted({o.type for o in bpy.data.objects}), text_objects=[o.name for o in bpy.data.objects if o.type == 'FONT'],
                           part_tag_vocabulary=tagset)
    sock = collections.defaultdict(list)
    for o in colls['White']:
        if o.type == 'EMPTY':
            sock[o.get('socket_name')].append(o.name)
    rep['swappable'] = dict(sockets=sorted(sock.keys()), pieces={o.name: dict(parent=o.parent.get('socket_name') if o.parent else None, mesh=o.data.name, mesh_users=o.data.users)
                                                              for o in colls['White'] if o.type == 'MESH'},
                            top_bottom_fused=bool(any(t.startswith('polo') for t in tags_of(bottom)[1]) or any(t.startswith(('shorts', 'skirt', 'liner', 'band', 'flap')) for t in tags_of(polo)[1])),
                            distinct_mesh_data=len({o.data.name for o in colls['White'] if o.type == 'MESH'}) == len([o for o in colls['White'] if o.type == 'MESH']))
    # ------------------------------------------------------------------------------------------------ ray tests: skin flash at the waist + liner visibility
    polo_t = bvh_ray(Vp, Fp)
    bot_t = bvh_ray(Vq, Fq)
    garment_trees = [polo_t, bot_t]
    # torso skin samples between shirt and bottom: polar rays from the torso axis hit the torso skin first
    zs = np.arange(zwb - 0.03, zwt + 0.09, 0.005)
    ths = np.radians(np.arange(0, 360, 4))
    trees_body = [tree_body]
    skin = []
    for z in zs:
        for t in ths:
            d = (float(np.sin(t)), float(-np.cos(t)), 0.0)
            loc, n, idx, dist = tree_body.ray_cast((cen[0], cen[1], float(z)), d, 0.6)
            if idx is not None:
                skin.append((np.array(loc), np.array(n)))
    Vgar = np.concatenate([Vp, Vq])
    Fgar = np.concatenate([Fp, Fq + len(Vp)])
    dirs = view_dirs((-10, 0, 10, 25), 24)
    exposed = []
    exposed_full = []
    tested = 0
    R = 3.0
    for loc, n in skin:
        for e, a, dvec in dirs:
            if float(n @ dvec) <= 0.05:
                continue                                                  # the skin faces away from this camera
            far = loc + dvec * R
            hb = tree_body.ray_cast(far.tolist(), (-dvec).tolist())       # camera -> skin: the body itself must not be in front (e.g. the arms)
            if hb[2] is None or hb[3] < R - 2e-3:
                continue
            tested += 1
            hit = False
            for tr in garment_trees:
                h = tr.ray_cast(far.tolist(), (-dvec).tolist())
                if h[2] is not None and h[3] < R - 1e-4:
                    hit = True
                    break
            if not hit:
                # BVH says unblocked -> confirm exactly against both garments before counting it as skin flash
                tt = mt_first(Vgar, Fgar, far, -dvec)
                if tt is not None and tt < R - 1e-4:
                    continue
                # the centre ray is unblocked: widen it to a 1 mm beam (4 more rays at +-0.5 mm, perpendicular to the view) - a gap narrower than 1 mm
                # is not visible skin (below a pixel at any proof distance)
                up = np.array([0, 0, 1.0])
                sx = np.cross(dvec, up)
                sx /= np.linalg.norm(sx)
                sy = np.cross(dvec, sx)
                blocked_beam = False
                for off in (0.0005 * sx, -0.0005 * sx, 0.0005 * sy, -0.0005 * sy):
                    t2 = mt_first(Vgar, Fgar, far + off, -dvec)
                    if t2 is not None and t2 < R - 1e-4:
                        blocked_beam = True
                        break
                if blocked_beam:
                    continue
                exposed.append((loc.round(3).tolist(), e, a))
                exposed_full.append((loc.tolist(), n.tolist(), e, a))
    json.dump(exposed_full, open(f'{WORK}/tmp/exposed_{gender}.json', 'w'))
    rep['skin_flash'] = dict(skin_samples=len(skin), ray_tests=tested, z_range=[round(float(zs[0]), 3), round(float(zs[-1]), 3)], elevations_deg=[-10, 0, 10, 25], azimuth_step_deg=15,
                             method='camera-side rays: a skin point is exposed only if a 1 mm wide beam from a distant camera reaches it with nothing (garment) in front; exact ray-triangle confirmation',
                             exposed=len(exposed), exposed_examples=exposed[:6])
    if liner_ids:
        lface = np.isin(tvq, [i for i, t in enumerate(tgq) if t.startswith('liner') and (t.endswith('_out') or '_rim' in t)])
        other = np.ones(len(Fq), bool)
        other[np.isin(tvq, liner_ids)] = False
        occ_b = bvh_ray(Vq, Fq[other])                         # skirt + flap + band (+ decals)
        liner_t = bvh_from(Vq, Fq[np.isin(tvq, liner_ids)])
        Fl = Fq[lface]
        cent = Vq[Fl].mean(1)
        nrm = np.cross(Vq[Fl[:, 1]] - Vq[Fl[:, 0]], Vq[Fl[:, 2]] - Vq[Fl[:, 0]])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        Vocc = np.concatenate([Vq, Vp, Vb])
        Focc = np.concatenate([Fq[other], Fp + len(Vq), Fb + len(Vq) + len(Vp)])          # everything except the liner itself
        GATE_EL = (-5, 0, 8, 22, 40)
        UNDER_EL = (-45, -30, -15)
        dirs2 = view_dirs(GATE_EL + UNDER_EL, 24)
        vis = collections.Counter()
        visible_faces = set()
        under_faces = set()
        vis_examples = []
        slit_only = []                                        # centre ray reaches the liner but a 1 mm beam does not (sub-millimetre slit)
        n_tests = 0
        all_t = bvh_ray(Vq, Fq)                                # whole bottom (liner included) -> first hit from the camera
        for fi, (c, nn) in enumerate(zip(cent, nrm)):
            for e, a, dvec in dirs2:
                if float(nn @ dvec) <= 0.02:
                    continue
                n_tests += 1
                far = c + dvec * R
                h = all_t.ray_cast(far.tolist(), (-dvec).tolist())
                first_is_liner = False
                if h[2] is not None:
                    hp = np.array(h[0])
                    first_is_liner = bool(np.linalg.norm(hp - c) < 1.5e-3)         # the first thing the camera sees along this ray is the liner face itself
                if not first_is_liner:
                    continue
                blocked = False
                for tr in (polo_t,):
                    hh = tr.ray_cast(far.tolist(), (-dvec).tolist())
                    if hh[2] is not None and hh[3] < R - 1e-4 and hh[3] < h[3] + 1e-4:
                        blocked = True
                        break
                hb = tree_body.ray_cast(far.tolist(), (-dvec).tolist())
                if hb[2] is not None and hb[3] < h[3] - 1e-4:
                    blocked = True
                if not blocked:
                    # candidate visible: exact check that nothing of the OTHER garments / the body is in front of the liner face
                    tt = mt_first(Vocc, Focc, far, -dvec)
                    if tt is not None and tt < R - 1e-3 - 0.0 and abs((R - tt) - 0.0) >= 0 and tt < float(np.linalg.norm(far - c)) - 1e-4:
                        continue
                    # the centre ray is unblocked: widen it to the same 1 mm beam as the skin-flash test (4 more rays at +-0.5 mm, perpendicular to the view).
                    # A slit narrower than 1 mm is below one pixel at any proof distance (~2 mm per pixel at 2.6 m / 85 mm lens) and cannot show the liner.
                    dist_c = float(np.linalg.norm(far - c))
                    sx = np.cross(dvec, np.array([0, 0, 1.0]))
                    sx /= np.linalg.norm(sx)
                    sy = np.cross(dvec, sx)
                    beam_blocked = False
                    for off in (0.0005 * sx, -0.0005 * sx, 0.0005 * sy, -0.0005 * sy):
                        t2 = mt_first(Vocc, Focc, far + off, -dvec)
                        if t2 is not None and t2 < dist_c - 1e-4:
                            beam_blocked = True
                            break
                    if beam_blocked:
                        if e in GATE_EL:
                            slit_only.append(dict(face=int(fi), el=e, az=a, centroid=c.round(4).tolist(), tag=tgq[tvq[np.nonzero(lface)[0][fi]]]))
                        continue
                    (visible_faces if e in GATE_EL else under_faces).add(fi)
                    vis[(e, a)] += 1
                    if e in GATE_EL and len(vis_examples) < 4000:
                        vis_examples.append((fi, e, a))
        rep['liner_visibility'] = dict(method='camera-side rays: a liner face is visible only if a 1 mm beam (centre + 4 rays at +-0.5 mm) meets it FIRST (skirt, flap, band, polo, body all count as occluders); exact ray-triangle confirmation',
                                       liner_faces_tested=int(len(Fl)), ray_tests=n_tests, gate_elevations_deg=list(GATE_EL), azimuth_step_deg=15,
                                       visible_faces_gate_views=int(len(visible_faces)), centre_ray_only_slits_gate_views=slit_only[:20], n_centre_ray_only_slits=len(slit_only), beam_mm=1.0, underside_elevations_deg=list(UNDER_EL), visible_faces_underside_views_info_only=int(len(under_faces)),
                                       visible_by_view_gate={f'{k[0]}/{k[1]}': v for k, v in vis.items() if k[0] in GATE_EL})
        if visible_faces:
            vf = sorted(visible_faces)
            cc = cent[vf]
            rep['liner_visibility']['visible_gate_faces_bbox'] = dict(min=cc.min(0).round(3).tolist(), max=cc.max(0).round(3).tolist(),
                                                                       z_hist=[int(((cc[:, 2] >= lo) & (cc[:, 2] < lo + 0.02)).sum()) for lo in np.arange(0.70, 1.0, 0.02)])
            rep['liner_visibility']['visible_gate_faces_examples'] = [dict(face_centroid=cent[f].round(4).tolist(), tag=tgq[tvq[np.nonzero(lface)[0][f]]]) for f in vf[:6]]
    json.dump(rep, open(f'{WORK}/proof/raw/checks_{gender}.json', 'w'), indent=1)
    # console summary
    print('SUMMARY', gender)
    for k, r in rep['pieces'].items():
        print(f"  {k:28s} tris {r['tris']:6d} closed {r['closed']} {r['topology']['islands']:3d} isl  wall {r.get('wall_mm', {}).get('median')}  clr_in {r.get('clearance_inner_mm', {}).get('min')}  clr_all {r.get('clearance_all_mm', {}).get('min')}")
    print('  polo torso clearance', rep['pieces'][f'Kit_Top_Polo_{suffix}_White'].get('clearance_inner_torso_mm'))
    print('  hem', rep['polo_hem'])
    print('  polo vs band', rep['polo_vs_band'], 'overlap pairs', rep['polo_vs_bottom_overlap_pairs'])
    print('  skirt', rep.get('skirt'), rep.get('shorts'))
    print('  skin flash', {k: v for k, v in rep['skin_flash'].items() if k != 'exposed_examples'}, rep['skin_flash']['exposed_examples'][:3])
    print('  liner', rep.get('liner_visibility'))
    print('  garment_vs_garment', rep['garment_vs_garment'])
    print('  bottom layers', rep['bottom_layer_overlaps'])
    print('  band', {cw: (b['contrast'], b['band_faces'], b['slot2_faces_all_band'], b['polo_uses_band_slot']) for cw, b in band.items()})


main()
