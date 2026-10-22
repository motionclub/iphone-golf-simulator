import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from onhand import *
bpy.ops.wm.open_mainfile(filepath=str(WORK / 'tmp' / 'oh' / 'RacketOnHero_Female_APose.blend'))
body = bpy.data.objects['Body_F']
dg = bpy.context.evaluated_depsgraph_get()
tree = BVHTree.FromObject(body, dg)
def inside_parity(p):
    # cast rays in +x, +y, -z ... majority vote of parity
    votes = 0
    for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        o = Vector(p); n = 0
        for _ in range(40):
            hit = tree.ray_cast(o, Vector(d))
            if hit[0] is None: break
            n += 1
            o = hit[0] + Vector(d) * 1e-4
        votes += (n % 2)
    return votes >= 2
for name in ('Racket_Classic', 'Grip', 'StringBed'):
    o = bpy.data.objects[name]
    mw = np.array(o.matrix_world)
    V = mesh_co(o)
    idx = np.random.RandomState(0).choice(len(V), min(400, len(V)), replace=False)
    pts = V[idx] @ mw[:3, :3].T + mw[:3, 3]
    ins = [inside_parity(q) for q in pts]
    print(name, 'inside body (ray parity):', sum(ins), '/', len(ins))
    # also report the signed nearest test
    d = signed_clearance(tree, pts)
    print('   nearest-normal test: min', round(d.min()*1000, 1), 'mm, n<0:', int((d < 0).sum()))
