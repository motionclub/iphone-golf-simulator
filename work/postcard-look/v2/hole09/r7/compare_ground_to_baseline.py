import bpy, sys, json, numpy as np
A = sys.argv[sys.argv.index("--") + 1:]
out = {}
def grab(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    d = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")):
            mw = np.array(o.matrix_world); co = np.array([v.co[:] for v in o.data.vertices]) @ mw[:3, :3].T + mw[:3, 3]
            d[o.name] = (co, len(o.data.polygons), [tuple(p.vertices) for p in o.data.polygons])
    mk = {}
    for n in ("MARKER_TEE", "MARKER_PIN", "MARKER_UP", "BALL_START", "HOLE_CUP"):
        o = bpy.data.objects.get(n)
        if o: mk[n] = tuple(round(c, 6) for c in o.matrix_world.translation)
    return d, mk
b, mb = grab(A[0]); s, ms = grab(A[1])
ok = True
rows = []
for n in sorted(set(b) | set(s)):
    if n not in b or n not in s:
        rows.append((n, "MISSING in " + ("baseline" if n not in b else "stage"))); ok = False; continue
    cb, nb, fb = b[n]; cs, ns, fs = s[n]
    same_topo = (len(cb) == len(cs) and nb == ns and fb == fs)
    dmax = float(np.abs(cb - cs).max()) if len(cb) == len(cs) else 99.0
    rows.append((n, f"verts {len(cb)}/{len(cs)} polys {nb}/{ns} topology {'same' if same_topo else 'DIFFERENT'} max |dxyz| {dmax:.3e} m"))
    ok &= same_topo and dmax < 1e-6
print("COMPARE", "PASS" if ok and mb == ms else "FAIL", "markers", mb == ms)
for r in rows: print("  ", r[0], r[1])
