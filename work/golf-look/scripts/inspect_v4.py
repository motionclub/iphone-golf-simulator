import bpy,json,sys
from pathlib import Path
r=Path.cwd();w=r/'work/golf-look';p=r/'Unity/Assets/Resources/StandardCharacters/standard_male_golf.fbx'
bpy.ops.import_scene.fbx(filepath=str(p),use_anim=True)
rows=[]
for o in bpy.data.objects:
 if o.type=='ARMATURE':rows.append(dict(name=o.name,bones=[dict(name=b.name,parent=b.parent.name if b.parent else None,head=list(b.head_local),tail=list(b.tail_local)) for b in o.data.bones],world=[list(v) for v in o.matrix_world]))
actions=[dict(name=a.name,frames=list(a.frame_range)) for a in bpy.data.actions]
(w/'data/v4_swing_inventory.json').write_text(json.dumps(dict(source=str(p),rigs=rows,actions=actions),indent=2)+'\n')
print(json.dumps(dict(rigs=[dict(name=r['name'],bones=[b['name'] for b in r['bones']]) for r in rows],actions=actions)))
