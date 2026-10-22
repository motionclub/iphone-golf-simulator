import bpy,pathlib,math,json
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';out={}
def s(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def g(x,a):return math.exp(-(x/a)**2)
for sex in ('male','female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_reference_expression2.blend'));h=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('GEO-') and not any(t in o.name for t in ('.iris.','.sclera.','.eye.')));prior=h.data.shape_keys.key_blocks['Reference_Expression2'];k=h.shape_key_add(name='Reference_Expression3',from_mix=True);k.relative_key=prior;k.value=1
 for v in k.data:
  x,y,z=v.co
  if sex=='female':
   # Actual modeled lower vermilion lies at z=-.074..-.086, not the earlier chin mask.
   lip=s(-.070,-.075,z)*(1-s(-.083,-.090,z))*g(x,.032)*s(-.042,-.060,y)
   v.co.z+=(-.073+(z+.073)*.68-z)*lip;v.co.y+=.0022*lip
   corner=g(abs(x)-.030,.012)*g(z+.074,.012)*s(-.025,-.050,y);v.co.z+=.0040*corner
   cheek=g(abs(x)-.055,.028)*g(z+.048,.028)*s(.01,-.04,y);v.co.z+=.0012*cheek;v.co.y-=.0006*cheek
  else:
   corner=g(abs(x)-.027,.012)*g(z+.068,.013)*s(.005,-.020,y);v.co.z+=.0036*corner
   # Rest upper modeled lids on the enlarged spherical eyes for an almond aperture.
   for c in (-.03228,.03228):
    lid=g(x-c,.020)*g(z,.016)*s(.01,-.010,y)
    if z>0:v.co.z-=.0014*lid
    else:v.co.z+=.00045*lid
 # Restrained pigment on modeled vermilion faces only; no overlay or added seam mesh.
 if len(h.data.materials)>1:
  n=h.data.materials[1].node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(.49,.245,.19,1) if sex=='male' else (.66,.325,.265,1)
  seam=-.067 if sex=='male' else -.073
  count=0
  for p in h.data.polygons:
   co=sum((k.data[i].co for i in p.vertices),Vector())/len(p.vertices)
   if abs(co.x)<.029 and abs(co.z-seam)<(.0045 if sex=='male' else .0055) and co.y<(-.024 if sex=='male' else -.055):p.material_index=1;count+=1
  out[sex]={'lipFaces':count,'maxExpressionDelta':max((v.co-prior.data[i].co).length for i,v in enumerate(k.data))}
 sc=bpy.context.scene;target=Vector((0,0,.006))
 for angle,loc in [('front',(0,-1.1,.010)),('threequarter',(.58,-1.1,.025))]:
  sc.camera.location=loc;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex}_expression3_{angle}.png');bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_reference_expression3.blend'))
(O/'expression3-manifest.json').write_text(json.dumps(out,indent=2));print('EXPRESSION3',out)
