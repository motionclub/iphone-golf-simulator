import bpy,json,bmesh
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Tennis/Island/TennisIsland.fbx'))
report=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 me=ob.data; bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001); bm.to_mesh(me); bm.free(); parent=list(range(len(me.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in me.edges:
  a,b=e.vertices;parent[find(a)]=find(b)
 groups={}
 for v in me.vertices:groups.setdefault(find(v.index),[]).append(v.index)
 components=[]
 for inds in groups.values():
  if len(inds)<4:continue
  coords=[ob.matrix_world@me.vertices[i].co for i in inds]
  lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
  components.append({'verts':len(inds),'lo':lo,'hi':hi})
 report.append({'name':ob.name,'vertices':len(me.vertices),'faces':len(me.polygons),
  'materials':[m.name for m in me.materials],'components':sorted(components,key=lambda c:-c['verts'])})
(root/'work/full-visual-overhaul/tennis/island-welded-topology.json').write_text(json.dumps(report,indent=2))
print([(o['name'],o['vertices'],o['faces'],len(o['components'])) for o in report])
