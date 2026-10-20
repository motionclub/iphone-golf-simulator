"""blender -b <blend> --python dump_mesh.py -- out.npz : dump Body_M raw arrays"""
import bpy, sys, numpy as np
out = sys.argv[sys.argv.index('--')+1]
o = bpy.data.objects['Body_M']; me = o.data
n = len(me.vertices); V = np.zeros(n*3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1,3)
npoly = len(me.polygons); nl = len(me.loops)
cv = np.zeros(nl, np.int32); me.loops.foreach_get('vertex_index', cv)
ls = np.zeros(npoly, np.int32); me.polygons.foreach_get('loop_start', ls)
lt = np.zeros(npoly, np.int32); me.polygons.foreach_get('loop_total', lt)
res = dict(V=V, corner_verts=cv, loop_start=ls, loop_total=lt)
for name in ('sharp_face','sharp_edge','custom_normal'):
    a = me.attributes.get(name)
    if a is None: print('no attr', name); continue
    print(name, a.domain, a.data_type, len(a.data))
    if name=='custom_normal':
        # stored as float vector? try vector
        try:
            arr = np.zeros(len(a.data)*3, np.float32); a.data.foreach_get('vector', arr); res['custom_normal']=arr.reshape(-1,3)
        except Exception as e:
            print('custom_normal read err', e)
            try:
                arr = np.zeros(len(a.data)*2, np.int16); a.data.foreach_get('value', arr); res['custom_normal_i16']=arr.reshape(-1,2)
            except Exception as e2: print('err2', e2)
    else:
        arr = np.zeros(len(a.data), bool); a.data.foreach_get('value', arr); res[name]=arr
        print(name, 'true count', int(arr.sum()))
# vertex groups
dv = [[(g.group, g.weight) for g in v.groups] for v in me.vertices]
vg_idx=[]; vg_gr=[]; vg_w=[]
for i,l in enumerate(dv):
    for (g,w) in l: vg_idx.append(i); vg_gr.append(g); vg_w.append(w)
res['vg_idx']=np.array(vg_idx,np.int32); res['vg_gr']=np.array(vg_gr,np.int32); res['vg_w']=np.array(vg_w,np.float32)
print('has_custom_normals', me.has_custom_normals)
np.savez(out, **res)
print('verts', n, 'polys', npoly, 'loops', nl, 'sizes', {int(k): int(v) for k,v in zip(*np.unique(lt, return_counts=True))})
