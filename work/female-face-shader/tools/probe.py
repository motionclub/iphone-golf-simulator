import bpy, sys, numpy as np, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader/tools')
import ft
bpy.ops.wm.open_mainfile(filepath=ft.JAW + '/Female_JawSculpt.blend')
print([ (o.name,o.type, len(o.data.vertices) if o.type=='MESH' else '') for o in bpy.data.objects])
body=bpy.data.objects['Body']; feat=bpy.data.objects['ReferenceFeatures']; rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
print('shape keys', [k.name for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else None)
print('feat keys', [k.name for k in feat.data.shape_keys.key_blocks] if feat.data.shape_keys else None)
print('attrs', [a.name for a in body.data.attributes], 'uv', [u.name for u in body.data.uv_layers])
F=ft.frame(body,feat,rig); print('frame', [list(np.round(v,4)) for v in F])
co=ft.coords(body.data); eye,right,up,fwd=F; d=co-eye; x=d@right; y=d@up; z=d@fwd
m=(np.abs(x)<.045)&(y>-.115)&(y<-.06)&(z>-.03)
print('mouth zone verts', m.sum())
idx,tri,e,nu=ft.topology(body.data)
P=np.zeros((nu,3)); P[idx]=co
um=np.zeros(nu,bool); um[idx[m]]=True
em=um[e[:,0]]&um[e[:,1]]; L=np.linalg.norm(P[e[em,0]]-P[e[em,1]],axis=1)
print('mouth edge len mm median/p10/p90', np.median(L)*1000, np.percentile(L,10)*1000, np.percentile(L,90)*1000)
# midline profile: vertices with |x|<1.5mm, sorted by y
mm=(np.abs(x)<.0015)&(z>-.06)&(y<-.02)&(y>-.16)
o=np.argsort(y[mm])
for yy,zz in zip(y[mm][o],z[mm][o]): print('mid y %.1f z %.1f'%(yy*1000,zz*1000))
