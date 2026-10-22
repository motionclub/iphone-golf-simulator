"""HERO_DETAIL: UV-space "seams / collar / placket / hems" maps for the worn kit (Blender, headless).

    Blender -b --factory-startup --python bake_kit.py -- <Male|Female> <out_dir>

Reads Unity/Assets/Characters/MatchHeroKit/<Sex>_Kit.fbx (the UVs the Unity mesh really has) and writes, per piece, a float32 .npy of the
darkening multiplier (1 = untouched white, lower = darker) rasterised in that piece's own UV layout, plus a preview json.
The multiplier comes from the GEOMETRY of the shell, not from hand painting:
  * cavity   : a vertex that sits below its smoothed neighbourhood (folds, the collar's under-fold, the placket gutter, the armhole crease)
  * edge     : the rim of the shell where the surface turns round (hems, cuffs, collar edge, button rims)
  * border   : vertices where two kit materials meet (shirt / piping, shorts / waistband, upper / sole)
  * seam     : garment seams the shells do not model: side seams and inseams, laid out in 3D (see `seam_lines`)
Everything is evaluated per vertex and then interpolated across triangles in UV space, so the darkening is continuous over UV island
cuts (the cuts are an unwrap artefact, not garment seams).
"""
import sys, os, math, json
import numpy as np
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SEX, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# texture size per piece (px): the shirt carries the collar / placket detail, the rest are low-frequency
SIZE = {"Kit_Top": 2048, "Kit_Bottom": 1024, "Kit_Shoe_L": 1024, "Kit_Shoe_R": 1024, "Kit_Sock_L": 512, "Kit_Sock_R": 512}
PAD = 6   # gutter (px) so mip levels never pull in the empty background


def smooth(P, ea, eb, iters, lam=0.5):
    n = len(P)
    deg = np.bincount(np.concatenate([ea, eb]), minlength=n).astype(np.float64)
    deg[deg == 0] = 1
    S = P.copy()
    for _ in range(iters):
        acc = np.zeros_like(S)
        np.add.at(acc, ea, S[eb]); np.add.at(acc, eb, S[ea])
        S = S + lam * (acc / deg[:, None] - S)
    return S


def ambient_occlusion(m, P, N, rays=48, reach=0.028, seed=7):
    """Per-vertex occlusion 0..1 by ray casting the shell against itself (cosine-weighted hemisphere, hits weighted by 1 - d / reach).
    Folds that really are deep (under the collar, the gap beside the placket, inside a sleeve) darken; mesh facet noise does not."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    bm = bmesh.new(); bm.from_mesh(m); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    tree = BVHTree.FromBMesh(bm)
    rng = np.random.default_rng(seed)
    occ = np.zeros(len(P)); expo = np.zeros(len(P))
    # one fixed set of cosine-weighted directions in the local frame, rotated per vertex
    u1, u2 = rng.random(rays), rng.random(rays)
    r = np.sqrt(u1); th = 2 * np.pi * u2
    local = np.stack([r * np.cos(th), r * np.sin(th), np.sqrt(1 - u1)], 1)
    for i in range(len(P)):
        n = N[i]
        a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
        t = np.cross(n, a); t /= np.linalg.norm(t); b = np.cross(n, t)
        dirs = local[:, 0:1] * t + local[:, 1:2] * b + local[:, 2:3] * n
        o = Vector(P[i] + n * 0.0006); tot = 0.0
        for d in dirs:
            hit = tree.ray_cast(o, Vector(d), reach)
            if hit[0] is not None:
                tot += 1.0 - hit[3] / reach
        occ[i] = tot / rays
        # exposure: how much of the hemisphere is open to the outside (rays that leave the shell for 0.8 m); internal layers score ~0
        esc = 0
        for d in dirs[:16]:
            if tree.ray_cast(o, Vector(d), 0.8)[0] is None:
                esc += 1
        expo[i] = esc / 16.0
    bm.free()
    return occ, expo


def seam_lines(name, P, N, ea, eb):
    """Side seams / inseams, 0..1 per vertex (1 on the seam line, a ~1.6 mm Gaussian across it). Laid out per piece:
    shirt / shorts / skirt: the line where each z-slice of the shell reaches its lateral extreme (|x| max) on the body part (not the arm)."""
    seam = np.zeros(len(P))
    if name not in ("Kit_Top", "Kit_Bottom"):
        return seam
    z = P[:, 2]; x = P[:, 0]
    zmin, zmax = float(z.min()), float(z.max())
    for sgn in (-1.0, 1.0):
        side = (x * sgn) > 0
        # the body part only: the shirt torso is the narrow column between the armpits and the hem, so ignore anything past 0.24 m off the centre (the sleeves)
        body = side & (np.abs(x) < (0.24 if name == "Kit_Top" else 0.30))
        if name == "Kit_Top":
            body &= (z < (zmax - 0.24))   # below the armpit / sleeve root
        nb = 70
        edges = np.linspace(zmin, zmax, nb + 1)
        for k in range(nb):
            sel = body & (z >= edges[k]) & (z < edges[k + 1])
            if sel.sum() < 6:
                continue
            idx = np.nonzero(sel)[0]
            ext = np.abs(x[idx]).max()
            if ext < (0.12 if name == "Kit_Top" else 0.10):
                continue
            d = ext - np.abs(x[idx])               # distance (in x) from the lateral extreme of this slice
            seam[idx] = np.maximum(seam[idx], np.exp(-0.5 * (d / 0.0016) ** 2))
    return seam


def outer_triangles(m, body_tree):
    """The kit shells are closed and double walled and the inner wall reuses the outer wall's UVs, so only the OUTER wall may be painted:
    a triangle is outer when its normal points away from the nearest point of the body it is worn on."""
    from mathutils import Vector
    out = np.zeros(len(m.loop_triangles), dtype=bool); hidden = np.zeros(len(m.loop_triangles), dtype=bool)
    for i, t in enumerate(m.loop_triangles):
        c = (m.vertices[t.vertices[0]].co + m.vertices[t.vertices[1]].co + m.vertices[t.vertices[2]].co) / 3
        loc, nrm, idx, dist = body_tree.find_nearest(c)
        out[i] = t.normal.dot(loc - c) < 0
        # a face whose normal runs straight into the body (inner wall, layers under a flap) is never seen
        hit = body_tree.ray_cast(c + t.normal * 0.0003, t.normal, 0.10)
        hidden[i] = hit[0] is not None
    return out, hidden


def bake(obj, name, body_tree):
    m = obj.data
    m.calc_loop_triangles()
    nv = len(m.vertices)
    P = np.zeros(nv * 3); m.vertices.foreach_get("co", P); P = P.reshape(-1, 3).astype(np.float64)
    # shading normals = the corner normals the FBX carries (the geometric vertex normals of these welded shells are noisy; the render never uses them)
    cn = np.zeros(len(m.loops) * 3); m.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3).astype(np.float64)
    lv = np.zeros(len(m.loops), dtype=np.int64); m.loops.foreach_get("vertex_index", lv)
    N = np.zeros((nv, 3)); np.add.at(N, lv, cn)
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
    E = np.zeros(len(m.edges) * 2, dtype=np.int64); m.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
    ea, eb = E[:, 0], E[:, 1]

    # --- cavity: how far a vertex sits below its smoothed neighbourhood along the outward normal
    def cav(it):
        S = smooth(P, ea, eb, it)
        return np.einsum("ij,ij->i", S - P, N)
    c1 = cav(1)
    groove = np.clip((c1 - 0.00035) / 0.0010, 0, 1)             # a narrow, clean groove (raglan seam line, placket edge), not facet noise
    ao, expo = ambient_occlusion(m, P, N)
    aod = np.clip((ao - 0.06) / 0.5, 0, 1)
    cavity = np.clip(0.5 * aod + 0.5 * groove, 0, 1)
    # --- edge: the largest normal turn across any edge at the vertex (rim of the shell, hems, collar edge)
    dots = np.clip(np.einsum("ij,ij->i", N[ea], N[eb]), -1, 1)
    ang = np.arccos(dots)
    nvar = np.zeros(nv); np.maximum.at(nvar, ea, ang); np.maximum.at(nvar, eb, ang)
    edge = np.clip((nvar - 0.50) / 0.8, 0, 1)
    # --- border: a vertex that belongs to faces of more than one material
    mats = np.zeros(len(m.polygons), dtype=np.int64); m.polygons.foreach_get("material_index", mats)
    pv = np.zeros(len(m.polygons) * 0, dtype=np.int64)
    first = np.full(nv, -1, dtype=np.int64); border = np.zeros(nv)
    loops_v = np.zeros(len(m.loops), dtype=np.int64); m.loops.foreach_get("vertex_index", loops_v)
    poly_start = np.zeros(len(m.polygons), dtype=np.int64); poly_tot = np.zeros(len(m.polygons), dtype=np.int64)
    m.polygons.foreach_get("loop_start", poly_start); m.polygons.foreach_get("loop_total", poly_tot)
    lp_mat = np.repeat(mats, poly_tot)
    for v, mi in zip(loops_v, lp_mat):
        if first[v] < 0:
            first[v] = mi
        elif first[v] != mi:
            border[v] = 1.0
    seam = seam_lines(name, P, N, ea, eb)

    dark = 0.80 * aod + 0.60 * groove + 0.55 * edge + 0.45 * border + 0.30 * seam
    dark = np.clip(dark, 0, 1)
    if os.environ.get("BAKE_DEBUG"):
        np.savez(os.path.join(OUT, f"_dbg_{SEX}_{name}.npz"), P=P, N=N, expo=expo, nvar=nvar, aod=aod, ao=ao, groove=groove, edge=edge, border=border, seam=seam, dark=dark)
    mult = 1.0 - float(os.environ.get('BAKE_DEPTH', '0.50')) * dark               # linear multiplier: never darker than 0.54 (a seam is a line, not a hole)

    # --- rasterise per-vertex multiplier into the piece's UV layout
    size = SIZE[name]
    uvd = np.zeros(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uvd); UV = uvd.reshape(-1, 2).astype(np.float64)
    img = np.zeros((size, size)); wgt = np.zeros((size, size), dtype=bool)
    outer, hidden = outer_triangles(m, body_tree)
    print("WALLS", name, "outer", int(outer.sum()), "inner", int((~outer).sum()))
    # Where UV layers still overlap (flap over chest, collar under-side) the most exposed triangle is painted last and wins.
    tri_ao = np.array([ao[list(t.vertices)].mean() for t in m.loop_triangles])
    tri_expo = np.array([expo[list(t.vertices)].mean() for t in m.loop_triangles])
    visible = outer & ~hidden
    print("VISIBLE", name, "painted", int(visible.sum()), "of outer", int(outer.sum()))
    order = [i for i in np.argsort(-tri_ao, kind="stable") if visible[i]]
    for ti in order:
        t = m.loop_triangles[ti]
        li = t.loops; vi = t.vertices
        uv = UV[list(li)] * size
        minx = max(int(math.floor(uv[:, 0].min())) - 1, 0); maxx = min(int(math.ceil(uv[:, 0].max())) + 1, size - 1)
        miny = max(int(math.floor(uv[:, 1].min())) - 1, 0); maxy = min(int(math.ceil(uv[:, 1].max())) + 1, size - 1)
        if maxx < minx or maxy < miny:
            continue
        xs, ys = np.meshgrid(np.arange(minx, maxx + 1) + 0.5, np.arange(miny, maxy + 1) + 0.5)
        (x0, y0), (x1, y1), (x2, y2) = uv
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-12:
            continue
        w0 = ((y1 - y2) * (xs - x2) + (x2 - x1) * (ys - y2)) / den
        w1 = ((y2 - y0) * (xs - x2) + (x0 - x2) * (ys - y2)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        val = w0 * mult[vi[0]] + w1 * mult[vi[1]] + w2 * mult[vi[2]]
        sub = img[miny:maxy + 1, minx:maxx + 1]; sw = wgt[miny:maxy + 1, minx:maxx + 1]
        sub[inside] = val[inside]; sw[inside] = True
    cover = wgt.mean()
    # --- gutter: grow the painted texels outwards PAD px (nearest painted neighbour), background = 1 (white)
    for _ in range(PAD):
        grow = ~wgt
        acc = np.zeros_like(img); cnt = np.zeros_like(img)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(img, (dy, dx), (0, 1)); sw = np.roll(wgt, (dy, dx), (0, 1))
            acc += np.where(sw, sh, 0); cnt += sw
        take = grow & (cnt > 0)
        img[take] = acc[take] / cnt[take]; wgt = wgt | take
    img[~wgt] = 1.0
    # image row 0 is the TOP in a PNG, UV v=0 is the BOTTOM: flip so v maps straight onto the file
    img = img[::-1]
    np.save(os.path.join(OUT, f"{SEX}_{name}.npy"), img.astype(np.float32))
    st = dict(piece=name, verts=nv, tris=len(m.loop_triangles), uv_cover=round(float(cover), 3),
              ao_mean=round(float(aod.mean()), 4), groove_mean=round(float(groove.mean()), 4), edge_mean=round(float(edge.mean()), 4), border_verts=int(border.sum()),
              seam_verts=int((seam > 0.3).sum()), mult_min=round(float(mult.min()), 3), mult_mean=round(float(mult.mean()), 4))
    print("BAKE", json.dumps(st))
    return st


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT, f"Unity/Assets/Characters/MatchHeroKit/{SEX}_Kit.fbx"))
kit_objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name in SIZE]
bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT, f"Unity/Assets/Characters/MatchHeroes/{SEX}/{SEX}_ReadyIdle.fbx"))
import bmesh
from mathutils.bvhtree import BVHTree
body = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("Body_")][0]
bmb = bmesh.new(); bmb.from_mesh(body.data); bmb.transform(body.matrix_world); bmesh.ops.triangulate(bmb, faces=bmb.faces[:])
body_tree = BVHTree.FromBMesh(bmb)
stats = []
for o in kit_objs:
    stats.append(bake(o, o.name, body_tree))
json.dump(stats, open(os.path.join(OUT, f"{SEX}_bake_stats.json"), "w"), indent=1)
