import bpy,json,sys
from pathlib import Path
sex=sys.argv[-1];W=Path(__file__).resolve().parents[1]
rig=bpy.data.objects['Rig_'+sex]
objects=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  o.data.calc_loop_triangles()
  objects.append(dict(name=o.name,verts=len(o.data.vertices),triangles=len(o.data.loop_triangles),matrix=list(map(list,o.matrix_world)),parent=o.parent.name if o.parent else None,materials=[m.name if m else '' for m in o.data.materials],modifiers=[(m.type,m.object.name if m.type=='ARMATURE' and m.object else '') for m in o.modifiers],bounds=[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box]))
data=dict(sex=sex,fps=bpy.context.scene.render.fps,objects=objects,bones=[dict(name=b.name,parent=b.parent.name if b.parent else None,head=list(b.head_local),tail=list(b.tail_local),matrix_local=list(map(list,b.matrix_local)),length=b.length) for b in rig.data.bones],actions=[dict(name=a.name,range=list(a.frame_range)) for a in bpy.data.actions])
(W/f'data/source_{sex}.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(sex=sex,objects=[(o['name'],o['triangles']) for o in objects],bones=len(data['bones']),actions=len(data['actions']))))
