import bpy, numpy as np, sys
name = sys.argv[sys.argv.index("--")+1]
o = bpy.data.objects[name]; me = o.data
me.calc_loop_triangles()
V = np.array([v.co[:] for v in me.vertices]); uv = me.uv_layers[0]
u = np.empty(len(me.loops)*2); uv.data.foreach_get("uv", u); u = u.reshape(-1,2)
bad=[]
for t in me.loop_triangles:
    p = V[list(t.vertices)]; a = 0.5*np.linalg.norm(np.cross(p[1]-p[0], p[2]-p[0]))
    q = u[list(t.loops)]; ua = 0.5*abs((q[1,0]-q[0,0])*(q[2,1]-q[0,1])-(q[1,1]-q[0,1])*(q[2,0]-q[0,0]))
    if a<1e-10: continue
    per = (ua/a)**0.5; r = per*8
    n = np.array(me.polygons[t.polygon_index].normal)
    if r < 0.25: bad.append((round(r,3), round(a,3), np.round(n,2).tolist(), t.polygon_index))
print(name, "tris", len(me.loop_triangles), "bad (<0.25x):", len(bad))
for b in bad[:12]: print(b)
