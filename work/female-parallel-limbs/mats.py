import bpy, numpy as np
b=bpy.data.objects['Body_F']; me=b.data
for m in me.materials:
    print('MAT',m.name,'nodes' if m.use_nodes else 'nonodes',[ (n.type,n.name, getattr(n,'image',None) and n.image.name) for n in (m.node_tree.nodes if m.use_nodes else [])][:8], tuple(round(x,3) for x in m.diffuse_color))
uv=me.uv_layers.active; print('uv layers',[l.name for l in me.uv_layers])
uvs=np.array([tuple(d.uv) for d in uv.data]); print('uv range',uvs.min(0),uvs.max(0))
# uv of hand/foot loops
import collections
mi=np.array([p.material_index for p in me.polygons])
v=np.array([tuple(x.co) for x in me.vertices])
for name,sel in(('foot',lambda p:max(v[i][2] for i in p.vertices)<0.1575),('hand',lambda p:all(abs(v[i][0])>0.195 and 0.65<v[i][2]<0.85 for i in p.vertices))):
    ps=[p for p in me.polygons if sel(p)]
    tris=sum(len(p.vertices)-2 for p in ps)
    loops=[l for p in ps for l in p.loop_indices]
    u=uvs[loops]
    print(name,'faces',len(ps),'tris',tris,'uv min/max',u.min(0).round(3),u.max(0).round(3),'mats',collections.Counter(mi[p.index] for p in ps))
print('all tris',sum(len(p.vertices)-2 for p in me.polygons))
print('custom normals', me.has_custom_normals, 'smooth faces', sum(p.use_smooth for p in me.polygons),'of',len(me.polygons))
