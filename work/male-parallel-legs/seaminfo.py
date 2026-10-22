import sys, numpy as np, bpy
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
from leglib import ZONE
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
b=bpy.data.objects['Body_M']; me=b.data
print('modifiers',[m.type for m in b.modifiers],'shape keys',me.shape_keys,'custom normals',me.has_custom_normals)
sm=np.array([p.use_smooth for p in me.polygons]); print('polys',len(sm),'flat shaded',(~sm).sum())
print('sharp edges',sum(1 for e in me.edges if e.use_edge_sharp),'seams',sum(1 for e in me.edges if e.use_seam))
print('uv layers',[u.name for u in me.uv_layers],'attributes',[a.name for a in me.attributes])
zi=np.array([all(ZONE[v] for v in p.vertices) for p in me.polygons])
print('flat shaded in zone',((~sm)&zi).sum())
