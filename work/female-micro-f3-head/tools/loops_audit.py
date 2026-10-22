"""Audit the LOOP_* vertex groups of the assembled Body_F: membership, edge connectivity (closed ring / open chain), edge spacing.
blender -b --factory-startup --python loops_audit.py -- <assembled.blend> <out.json>"""
import sys, json, collections
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
blend, out = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
body = bpy.data.objects['Body_F']; me = body.data
V, F = fl.mesh_arrays(me)
adj = collections.defaultdict(set)
for f in F:
    n = len(f)
    for i in range(n):
        a, b = int(f[i]), int(f[(i + 1) % n]); adj[a].add(b); adj[b].add(a)
groups = {g.index: g.name for g in body.vertex_groups}
members = collections.defaultdict(list)
for v in me.vertices:
    for g in v.groups:
        if g.weight > 0.5 and g.group in groups: members[groups[g.group]].append(v.index)
EXPECT = {  # name -> kind ('ring' closed edge loop | 'chain' open edge path | 'band' region of verts around a feature)
    'LOOP_eyeL': 'band', 'LOOP_eyeR': 'band', 'LOOP_nostril_L': 'ring', 'LOOP_nostril_R': 'ring', 'LOOP_seam': 'chain', 'LOOP_lip_up': 'chain', 'LOOP_lip_lo': 'chain',
    'LOOP_ear_attach_L': 'band', 'LOOP_ear_attach_R': 'band', 'LOOP_helix_L': 'band', 'LOOP_helix_R': 'band', 'LOOP_concha_L': 'ring', 'LOOP_concha_R': 'ring',
    'LOOP_lid_up_L': 'chain', 'LOOP_lid_low_L': 'chain', 'LOOP_lid_up_R': 'chain', 'LOOP_lid_low_R': 'chain',
    'LOOP_jaw_ear_L': 'chain', 'LOOP_jaw_ear_R': 'chain', 'LOOP_ala_L': 'chain', 'LOOP_ala_R': 'chain'}
res = {}
for name in sorted(members):
    m = sorted(members[name]); S = set(m)
    deg = {v: len([w for w in adj[v] if w in S]) for v in m}
    # connected components inside the group
    seen = set(); comps = []
    for s in m:
        if s in seen: continue
        st = [s]; seen.add(s); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for w in adj[x]:
                if w in S and w not in seen: seen.add(w); st.append(w)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    edges = sorted({(min(a, b), max(a, b)) for a in m for b in adj[a] if b in S})
    el = np.array([np.linalg.norm(V[a] - V[b]) for a, b in edges]) * 1000 if edges else np.zeros(1)
    dc = collections.Counter(deg.values())
    kind = EXPECT.get(name, '?')
    # ring: every vertex has deg>=2 and the largest component contains a cycle through >= 90 % of the group
    big = comps[0]; bs = set(big)
    nb_edges = sum(1 for a, b in edges if a in bs and b in bs)
    cyc = nb_edges - len(big) + 1          # cyclomatic number of the largest component
    ends = sum(1 for v in big if deg[v] == 1)
    if kind == 'ring': ok = (len(comps) == 1) and cyc >= 1 and ends == 0
    elif kind == 'chain': ok = (len(big) >= 0.9 * len(m)) and cyc == 0 and ends >= 1 or (cyc >= 1 and len(big) >= 0.9 * len(m))
    else: ok = (len(big) >= 0.9 * len(m)) and cyc >= 1
    res[name] = dict(kind=kind, verts=len(m), components=len(comps), largest=len(big), edges=len(edges), cyclomatic=int(cyc), ends=int(ends),
                     deg_hist=dict(sorted(dc.items())), edge_mm_mean=float(el.mean()), edge_mm_max=float(el.max()), edge_mm_min=float(el.min()), connected_ok=bool(ok))
    print(f'{name:18s} {kind:5s} verts {len(m):4d} comps {len(comps):2d} largest {len(big):4d} cyc {cyc:3d} ends {ends:2d} deg {dict(sorted(dc.items()))} edge mm mean {el.mean():.2f} max {el.max():.2f} min {el.min():.2f}  {"OK" if ok else "CHECK"}')
json.dump(res, open(out, 'w'), indent=1)
