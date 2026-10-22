"""candidate gate metrics on old vs new spires. usage: Blender -b --factory-startup --python spire_metrics.py -- [old]"""
import sys, os, math, importlib.util
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
if a and a[0] == "old":
    spec = importlib.util.spec_from_file_location("postcard_props_lib", REPO + "/work/postcard-look/v2/libs_r1/backup/postcard_props_lib.py")
    PL = importlib.util.module_from_spec(spec); sys.modules["postcard_props_lib"] = PL; spec.loader.exec_module(PL)
else:
    import postcard_props_lib as PL
def metrics(me):
    co, tris, tp = PL._np_mesh(me)
    nrm, area, lt = PL._poly_arrays(me)
    zmax = co[:, 2].max()
    # smooth edge share
    me.calc_loop_triangles()
    ne = len(me.edges)
    sharp = np.zeros(ne, bool)
    try:
        sh = me.attributes.get("sharp_edge")
        if sh is not None:
            arr = np.empty(ne, bool); sh.data.foreach_get("value", arr); sharp = arr
    except Exception:
        pass
    # edges between two faces
    ef = {}
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            k = tuple(sorted((vs[i], vs[(i+1) % len(vs)]))); ef.setdefault(k, []).append(p.index)
    interior = [k for k, v in ef.items() if len(v) == 2]
    ed = np.empty(ne*2, np.int32); me.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    idx = {tuple(sorted(e)): i for i, e in enumerate(ed.tolist())}
    smooth = sum(1 for k in interior if not sharp[idx[k]])
    smooth_share = smooth / max(len(interior), 1)
    # up-facing ledge faces above 12 % of the height, nz > 0.55 (non roof): count connected groups
    vis = co[:, 2].max() - 0.0
    pc = np.array([p.center.z for p in me.polygons])
    ledge = (nrm[:, 2] > 0.55) & (pc > 0.12 * zmax) & (pc < 0.85 * zmax)
    n_ledge = int(ledge.sum())
    # silhouette asymmetry from 4 azimuths: area left vs right of the base centre axis, above the water
    asym = []
    keep = co[:, 2] > 0.0
    for az in (0, 45, 90, 135):
        a_ = math.radians(az); u = co[:, 0]*math.cos(a_) + co[:, 1]*math.sin(a_)
        sel = co[:, 2] >= 0
        base = co[(co[:, 2] > -0.1) & (co[:, 2] < 0.6)]
        uc = float((base[:, 0]*math.cos(a_) + base[:, 1]*math.sin(a_)).mean())
        # sample the silhouette by z slices: left extent vs right extent around uc
        zs = np.linspace(0.5, 0.92 * zmax, 14)
        ext = []
        for z in zs:
            pts = PL.mesh_section(co, tris, z)
            if len(pts) < 2: continue
            uu = pts[:, 0]*math.cos(a_) + pts[:, 1]*math.sin(a_) - uc
            ext.append((uu.min(), uu.max()))
        ext = np.array(ext)
        width = (ext[:, 1] - ext[:, 0]).sum()
        asym.append(abs((ext[:, 1] + ext[:, 0]).sum()) / max(width, 1e-6))
    return dict(faces=len(me.polygons), tri_area_mean=float(area.mean()), smooth_share=smooth_share, ledge_faces=n_ledge, asym=[round(x, 3) for x in asym])
kinds = list(PL.SEASTACK_KINDS) + ["ROCK_SPIRE_A"]
PL.ensure_library(kinds)
for k in kinds:
    m = metrics(PL.library_object(k).data)
    print("MET", k, m)
