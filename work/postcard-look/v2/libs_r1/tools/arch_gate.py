"""ARCH_NO_SEE_THROUGH + coplanar piers + chamfer-only joints, measured on the real arch mesh. usage: Blender -b --factory-startup --python arch_gate.py
GATE lines. Builds the hole 8 arch (span 7.5, h 11), the hole 9 broken arch (span 6, h 9) and an intact span 6 / 9."""
import sys, math, os, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_props_lib as PL

def check(span, height, broken, seed, tag):
    r = PL.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=span, height_m=height, seed=seed, base_rock=False, vines=False, broken=broken)
    ob = r["arch"]; d = r["dims"]
    me = ob.data
    nf = len(me.polygons)
    nrm_x = np.array([p.normal.x for p in me.polygons]); cx = np.array([p.center.x for p in me.polygons]); cz = np.array([p.center.z for p in me.polygons])
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    r_in, r_out, zs, pw = d["r_in"], d["r_out"], d["zs"], d["pw"]
    depth = max(1.0, 0.17 * span)
    # solid region predicate (shrunk by m)
    m = 0.03
    def solid(x, z):
        ax = abs(x)
        if 0.36 + m < z < zs - m and r_in + m < ax < r_in + pw - m:
            if broken and x < 0 and z > zs - 1.9:
                return False
            return True
        # ring
        rr = math.hypot(x, z - zs)
        if z > zs + m and r_in + m < rr < r_out - 0.06:
            ang = math.atan2(z - zs, x)
            n_ = int(round(math.pi * (r_in + (r_out - r_in) / 2) / max(0.7, 0.12 * span))); n_ += 1 - n_ % 2
            if broken and ang > math.pi * (n_ // 2 - 1) / n_ - 0.03:
                return False
            return True
        return False
    bad = 0; n = 0
    xs = np.arange(-(r_in + pw), r_in + pw, 0.02)
    zs_ = np.arange(0.40, height, 0.02)
    ex = []
    for z in zs_:
        for x in xs:
            if not solid(x, z):
                continue
            n += 1
            h = bvh.ray_cast(Vector((x, -depth, z)), Vector((0, 1, 0)), 2 * depth)
            if h[0] is None:
                bad += 1
                if len(ex) < 5: ex.append((round(x, 2), round(z, 2)))
    # coplanar pier faces: every vertex of the pier outer face lies at x = +-(r_in + pw) (up to the plinth) -> measure the spread of outer-face x
    sel = (np.abs(nrm_x) > 0.999) & (cz > 0.5) & (cz < zs - 0.2) & (np.abs(cx) > r_in + pw - 0.01)
    spread = float(np.abs(np.abs(cx[sel]) - (r_in + pw)).max()) if sel.any() else 0.0
    n_outer = int(sel.sum())
    # thin quads: triangle aspect / area
    print(f"GATE: ARCH_NO_SEE_THROUGH_{tag} {'PASS' if bad == 0 else 'FAIL'} - {n} sample rays at 2 cm through the solid region (3 cm inside every edge), see-through {bad} {ex}")
    print(f"GATE: ARCH_PIER_COPLANAR_{tag} {'PASS' if spread < 1e-4 else 'FAIL'} - {n_outer} outer pier faces (normal +-X, pier courses) lie within {spread*1000:.3f} mm of x = +-(r_in + pw)")
    print(f"GATE: ARCH_FACES_{tag} {'PASS' if nf <= 500 else 'FAIL'} - {nf} polygons (<= 500), {r['dims']['parts']}")
    return bad == 0 and spread < 1e-4 and nf <= 500

ok = True
for (sp, h, br, sd, tag) in ((7.5, 11.0, False, 8, "08"), (6.0, 9.0, True, 12, "09_broken"), (6.0, 9.0, False, 3, "06_intact")):
    ok &= check(sp, h, br, sd, tag)
print("GATE: ARCH_ALL", "PASS" if ok else "FAIL")

# ---- SLITS: depth-map relief (the review's "dark slivers" = narrow, deep joint gaps that read black under a shadowing sun)
import importlib.util
def slit_metric(mod, span, height, broken, seed, tag, label):
    r = mod.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=span, height_m=height, seed=seed, base_rock=False, vines=False, broken=broken)
    ob = r["arch"]; d = r["dims"]
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    depth = max(1.0, 0.17 * span)
    r_in, r_out, zs, pw = d["r_in"], d["r_out"], d["zs"], d["pw"]
    step = 0.02
    xs = np.arange(-(r_in + pw) + 0.1, r_in + pw - 0.1, step)
    zz = np.arange(0.45, height - 0.2, step)
    Dm = np.full((len(zz), len(xs)), np.nan)
    y_start = -depth / 2 - 0.5
    for i, z in enumerate(zz):
        for j, x in enumerate(xs):
            h = bvh.ray_cast(Vector((x, y_start, z)), Vector((0, 1, 0)), depth + 1.0)
            if h[0] is not None:
                Dm[i, j] = h[0].y - y_start
    k = 2                                           # +-4 cm
    def relief(A, axis):
        a = np.roll(A, k, axis); b = np.roll(A, -k, axis)
        return A - np.maximum(a, b)
    rl = np.fmax(relief(Dm, 0), relief(Dm, 1))
    rl[:k] = 0; rl[-k:] = 0; rl[:, :k] = 0; rl[:, -k:] = 0
    n_hit = int(np.isfinite(Dm).sum())
    where = [(round(float(xs[j]),2), round(float(zz[i]),2), round(float(rl[i,j])*100,1)) for i, j in np.argwhere(np.nan_to_num(rl, nan=0.0) > 0.03)[:6]]
    print('SLITWHERE', label, tag, where)
    slit = np.nan_to_num(rl, nan=0.0) > 0.03
    # opening edge false positives: where neighbours are misses (nan) the max() ignores them -> fine
    print(f"SLITS {label} {tag}: {n_hit} hit cells, relief max {np.nanmax(rl)*100:.1f} cm, cells deeper than 3 cm than both +-4 cm neighbours: {int(slit.sum())} ({slit.sum()/max(n_hit,1)*100:.3f} % of the face); >1.5 cm: {int((np.nan_to_num(rl,nan=0)>0.015).sum())}")
    return int(slit.sum()), float(np.nanmax(rl)), n_hit

spec = importlib.util.spec_from_file_location("postcard_props_lib_old", REPO + "/work/postcard-look/v2/libs_r1/backup/postcard_props_lib.py")
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
for (sp, h, br, sd, tag) in ((7.5, 11.0, False, 8, "08"), (6.0, 9.0, True, 12, "09_broken")):
    n_old, m_old, h_old = slit_metric(old, sp, h, br, sd, tag, "OLD")
    n_new, m_new, h_new = slit_metric(PL, sp, h, br, sd, tag, "NEW")
    print(f"GATE: ARCH_NO_DEEP_SLITS_{tag} {'PASS' if n_new <= max(4, 0.0002 * h_new) and n_old > 50 * max(n_new, 1) else 'FAIL'} - new arch: <= 0.02 % of the face expected, {n_new} cells ({100*n_new/max(h_new,1):.4f} %) deeper than 3 cm than both neighbours at +-4 cm (max relief {m_new*100:.1f} cm); negative control (the old arch) {n_old} cells, max relief {m_old*100:.1f} cm {'(control detects slits)' if n_old > 0 else '(CONTROL BLIND)'}")
