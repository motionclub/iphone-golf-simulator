"""Probe: per-component topology/shape numbers of every ROCK_ library mesh (lib_smoke_now hole 8/10 blend) and of ico-bundle attack meshes."""
import sys, os, importlib.util, collections
import numpy as np, bpy, bmesh
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
argv = sys.argv[sys.argv.index("--")+1:]
blend = argv[0]
if blend.endswith(".fbx"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=blend)
else:
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False)
seen = set()
def comp_report(name, me):
    nv = len(me.vertices)
    co = np.empty(nv*3); me.vertices.foreach_get("co", co); V = co.reshape(-1,3)
    wid = m.weld_ids(V); nw = int(wid.max())+1
    P = np.zeros((nw,3)); np.add.at(P, wid, V); P /= np.maximum(np.bincount(wid, minlength=nw),1)[:,None]
    # polygons
    polys = []
    for p in me.polygons:
        ids = [int(wid[i]) for i in p.vertices]
        ids2 = []
        for i in ids:
            if not ids2 or ids2[-1] != i: ids2.append(i)
        if len(ids2) > 1 and ids2[0] == ids2[-1]: ids2.pop()
        if len(set(ids2)) >= 3: polys.append(ids2)
    # components by polygon vertex sharing
    parent = list(range(nw))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for pl in polys:
        for a in pl[1:]:
            ra, rb = find(pl[0]), find(a)
            if ra != rb: parent[ra] = rb
    comps = collections.defaultdict(list)
    for pl in polys: comps[find(pl[0])].append(pl)
    out = []
    for r, pls in comps.items():
        edges = collections.Counter()
        for pl in pls:
            for i in range(len(pl)):
                a, b = pl[i], pl[(i+1)%len(pl)]
                edges[(min(a,b), max(a,b))] += 1
        verts = {v for pl in pls for v in pl}
        val = collections.Counter()
        for (a,b) in edges: val[a]+=1; val[b]+=1
        closed = all(c==2 for c in edges.values())
        hist = collections.Counter(val.values())
        out.append((len(verts), len(edges), len(pls), closed, dict(sorted(hist.items()))))
    return out
cnt = 0
for o in bpy.data.objects:
    if o.type != "MESH": continue
    n = o.name.split(".")[0]
    if not (n.startswith("ROCK_") or n.startswith("CLIFF_ROCK")): continue
    if o.data.name in seen: continue
    seen.add(o.data.name)
    cr = comp_report(o.name, o.data)
    big = sorted(cr, key=lambda c: -c[0])
    print(f"{o.name:28s} mesh {o.data.name:24s} ncomp {len(cr):3d} | first comps (V,E,F,closed,valhist): {big[:4]}")

# ---- component sphericity / facets for real vs attack
def comp_numbers(me):
    nv = len(me.vertices)
    co = np.empty(nv*3); me.vertices.foreach_get("co", co); V = co.reshape(-1,3)
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tv = np.empty(nt*3, np.int64); me.loop_triangles.foreach_get("vertices", tv); T = tv.reshape(-1,3)
    wid = m.weld_ids(V); nw = int(wid.max())+1
    P = np.zeros((nw,3)); np.add.at(P, wid, V); P /= np.maximum(np.bincount(wid, minlength=nw),1)[:,None]
    Tw = wid[T]
    N, A = m.tri_geom(P, Tw)
    lab = m.tri_components(Tw)
    res = []
    for c in np.unique(lab):
        sel = lab == c
        rcv, ecv, acv, ext = m.tess_numbers(P, Tw[sel], A[sel])
        cl = m.facet_clusters(N[sel], A[sel], 16.0, 0.02)
        nvc = len(np.unique(Tw[sel]))
        vert_share = float((np.abs(N[sel][:,2]) < 0.15).astype(float) @ A[sel] / A[sel].sum())
        res.append(dict(nv=nvc, nt=int(sel.sum()), rcv=round(rcv,3), ecv=round(ecv,2), acv=round(acv,2), nfac=len(cl), vert=round(vert_share,2), ext=[round(float(e),2) for e in ext]))
    return res
seen2 = set()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    n = o.name.split(".")[0]
    if not (n.startswith("ROCK_") or n.startswith("CLIFF_ROCK")) or o.data.name in seen2 or n.startswith("ROCK_SKIN"): continue
    seen2.add(o.data.name)
    r = comp_numbers(o.data)
    print("COMP", f"{o.name:26s}", "ncomp", len(r), "| rcv:", [x["rcv"] for x in r][:8], "| nv:", [x["nv"] for x in r][:8], "| vertshare", [x["vert"] for x in r][:6], "| nfac", [x["nfac"] for x in r][:6])
