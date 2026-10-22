import sys, numpy as np, bpy
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
from leglib import ZONE
def info(path,tag):
    bpy.ops.wm.open_mainfile(filepath=path)
    b=bpy.data.objects['Body_M']; me=b.data
    n=len(me.vertices)
    cn=np.empty(len(me.corner_normals)*3); me.corner_normals.foreach_get('vector',cn); cn=cn.reshape(-1,3)
    cv=np.empty(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',cv)
    # geometric vertex normals (area weighted face normals averaged)
    V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
    vn=np.zeros((n,3))
    for p in me.polygons:
        fnv=np.array(p.normal)
        for v in p.vertices: vn[v]+=fnv*p.area
    vn/=np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-12)
    ang=np.degrees(np.arccos(np.clip((cn*vn[cv]).sum(1),-1,1)))
    zl=ZONE[cv]
    print(tag,'loops',len(cv),'| zone loops',zl.sum(),'angle custom vs geometric: zone mean %.2f p95 %.2f max %.2f deg | non-zone mean %.2f p95 %.2f max %.2f'%(ang[zl].mean(),np.percentile(ang[zl],95),ang[zl].max(),ang[~zl].mean(),np.percentile(ang[~zl],95),ang[~zl].max()))
    # is the custom normal field the stored attribute or auto?
    print('   has_custom_normals',me.has_custom_normals,'attrs',[a.name for a in me.attributes if 'normal' in a.name or 'sharp' in a.name])
for p,t in ((sys.argv[sys.argv.index('--')+1],'base(artdir_after_torso)'),(sys.argv[sys.argv.index('--')+2],'new(merged legs)')):
    info(p,t)
