import bpy,pathlib,sys,json
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
face=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Face_'))
eyeidx={i for p in face.data.polygons if face.data.materials[p.material_index].name=='Face_Sclera' for i in p.vertices}
eyes=[]
for sign in (-1,1):
 ps=[face.data.vertices[i].co for i in eyeidx if face.data.vertices[i].co.x*sign>0]
 lo=Vector((min(p[d] for p in ps) for d in range(3)));hi=Vector((max(p[d] for p in ps) for d in range(3)));eyes.append(((lo+hi)*.5,hi-lo))
result={}
for material in face.data.materials:
 ids={i for p in face.data.polygons if face.data.materials[p.material_index]==material for i in p.vertices}
 coords=[]
 for i in ids:
  p=face.data.vertices[i].co;centre,size=min(eyes,key=lambda e:abs(p.x-e[0].x));coords.append([(p.x-centre.x)/(size.x*.5),(p.z-centre.z)/(size.z*.5)])
 result[material.name]={'vertices':len(ids),'eyeCoordMin':[min(p[d] for p in coords) for d in (0,1)],'eyeCoordMax':[max(p[d] for p in coords) for d in (0,1)],'coords':coords if material.name in ('Face_Seam','Face_LidLine','Face_LidLower','Face_BrowSoft') else []}
(R/f'proof/full-visual-overhaul/characters/face-paint-audit-{sex}.json').write_text(json.dumps(result,indent=2));print('FACE_PAINT_AUDIT',sex,{k:{i:v for i,v in val.items() if i!='coords'} for k,val in result.items()})
