import bpy, numpy as np, json
me=bpy.data.objects['Body_F'].data
v=np.array([tuple(x.co) for x in me.vertices]); h=v[v[:,2]>1.45]
json.dump({'yc':float((h[:,1].min()+h[:,1].max())/2)},open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-parallel-limbs/data/headcentre.json','w'))
