"""blender -b --python fbx_normals.py -- <fbx> <S1.fbx> : compare corner normals of the re-imported FBX with Blender's vertex normals; also zone diff vs the S1 FBX"""
import bpy, sys, numpy as np
a=sys.argv[sys.argv.index('--')+1:]
def imp(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=p)
    o=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]; me=o.data
    n=len(me.vertices); V=np.zeros(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
    nl=len(me.loops); CN=np.zeros(nl*3); me.corner_normals.foreach_get('vector',CN); CN=CN.reshape(-1,3)
    VN=np.zeros(n*3); me.vertex_normals.foreach_get('vector',VN); VN=VN.reshape(-1,3)
    li=np.zeros(nl,dtype=np.int64); me.loops.foreach_get('vertex_index',li)
    return V,CN,VN,li,o
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms/'
zone=np.load(W+'data/zone.npy')
V,CN,VN,li,o=imp(a[0])
d=(CN*VN[li]).sum(1)
zl=zone[li]
print('FBX_NORMALS corner-vs-vertex normal dot: zone min %.5f mean %.6f ; outside min %.5f'%(d[zl].min(),d[zl].mean(),d[~zl].min()))
V1,CN1,VN1,li1,o1=imp(a[1])
# vertex order identical? compare coords outside zone
print('FBX_NORMALS same vertex count',len(V)==len(V1))
if len(V)==len(V1):
    mv=(np.abs(V-V1).max(1)>1e-6)
    print('FBX_NORMALS verts differing vs S1 FBX (>1e-6 m):',int(mv.sum()),'outside zone:',int((mv&~zone).sum()))
    # corner normal change per corner (angle) inside zone vs outside
    dn=(CN*CN1).sum(1); ang=np.degrees(np.arccos(np.clip(dn,-1,1)))
    print('FBX_NORMALS corner normal change deg: zone mean %.3f max %.2f ; outside max %.3f'%(ang[zl].mean(),ang[zl].max(),ang[~zl].max()))
