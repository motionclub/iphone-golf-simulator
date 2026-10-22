"""Authored distant ridge spine/spurs in the existing resort island envelopes.
Uses the same single-shell coast/Delaunay/vertex-colour workflow as existing
TennisCoast, with controlled terrain ridges instead of Gaussian mound peaks.
All output is work-only; Blender Z-up / Unity Y-up, metres.
"""
import bpy, bmesh, math, json, random, hashlib
from pathlib import Path
from mathutils import Vector, noise
from mathutils.geometry import delaunay_2d_cdt
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W=R/'work/reference-rebuild/tennis-horizon2';W.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

def clamp(x,a=0,b=1):return max(a,min(b,x))
def smooth(a,b,x):t=clamp((x-a)/(b-a));return t*t*(3-2*t)
def mix(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def field(x,y,seed,scale=.028):return noise.noise(Vector((x*scale,y*scale,seed*.231)))
# Purposeful irregular skyline, connected mountain saddles and descending spurs.
SPINE=[(-220,20,2),(-192,24,11),(-172,19,24),(-150,18,33),(-134,28,31),
 (-114,30,40),(-95,27,48),(-76,16,57),(-55,21,63),(-40,28,53),(-17,22,37),
 (2,26,43),(23,31,49),(42,29,56),(60,34,49),(80,36,55),(99,30,44),
 (120,22,38),(143,25,41),(167,23,28),(190,20,16),(219,18,2)]
FORE_SPINE=[(-211,-28,3),(-176,-37,11),(-147,-34,16),(-122,-42,19),
 (-92,-33,22),(-64,-46,20),(-39,-38,16),(-9,-44,13),(20,-38,19),
 (48,-31,26),(74,-43,20),(94,-40,16),(120,-34,18),(142,-43,15),
 (172,-37,11),(205,-24,3)]
SPURS=[ [(-150,18,33),(-158,-3,29),(-142,-25,22),(-148,-53,12),(-167,-71,3)],
 [(-95,27,48),(-108,4,37),(-98,-17,31),(-113,-39,22),(-101,-70,4)],
 [(-55,21,63),(-50,-2,48),(-62,-24,35),(-54,-43,23),(-39,-72,3)],
 [(23,31,49),(13,8,41),(26,-12,31),(9,-40,19),(-2,-73,3)],
 [(80,36,55),(66,12,45),(79,-13,33),(66,-35,23),(83,-68,4)],
 [(143,25,41),(133,3,34),(141,-24,24),(124,-51,12),(143,-68,3)] ]

vertices=[];faces=[];colours=[];islands=[]
def crest(x,spine=SPINE):
 for a,b in zip(spine,spine[1:]):
  if a[0]<=x<=b[0]:
   t=(x-a[0])/(b[0]-a[0]);return a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t
 return (20,0)
def spur_height(x,y):
 best=0
 for chain in SPURS:
  for a,b in zip(chain,chain[1:]):
   dx=b[0]-a[0];dy=b[1]-a[1];t=clamp(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy))
   distance=math.hypot(x-a[0]-dx*t,y-a[1]-dy*t)
   h=a[2]+(b[2]-a[2])*t;width=8.5+2.5*(1-t)
   best=max(best,h*clamp(1-distance/(width*2.0))**1.18)
 return best

def island(name,centre,extent,seed,step,height_scale,detail):
 rng=random.Random(seed*1719);ex,ey=extent
 def outline(a):return 1+.065*math.sin(a*3+seed)+.035*math.cos(a*5+seed*.31)
 def radius(x,y):
  angle=math.atan2(y/ey,x/ex);return math.hypot(x/ex,y/ey)/outline(angle)
 def elevation(x,y):
  # The same central landform is re-proportioned on recessed side islands.
  xx=x/ex*228;yy=y/ey*95;r=radius(x,y)
  cy,h=crest(xx);span=87 if yy<cy else 74
  backbone=h*clamp(1-abs(yy-cy)/span)**1.15
  fore=spur_height(xx,yy)
  fy,fh=crest(xx,FORE_SPINE)
  foreground=fh*clamp(1-abs(yy-fy)/35)**1.30
  geology=max(backbone,fore,foreground)
  # Broad directional erosion subdivides shoulder planes, not noisy turf detail.
  erosion=(field(xx,yy,seed,.031)*2.2+field(xx,yy,seed+29,.080)*1.3+field(xx,yy,seed+19,.145)*.42)
  shore=smooth(0,.19,1-r)
  shelf=3.4*shore
  h=-4.1+(shelf+max(0,geology+erosion)*height_scale)*shore
  return h
 # Smooth organic boundary and irregular constrained interior points reuse the
 # established coast source workflow. Crest constraints guarantee authored peaks.
 n=132 if detail else 84;points=[];edges=[]
 for i in range(n):
  a=i*math.tau/n;s=outline(a);points.append(Vector((math.cos(a)*ex*s,math.sin(a)*ey*s)))
 for i in range(n):edges.append((i,(i+1)%n))
 for row in range(int(2*ey/step)+1):
  y=-ey+row*step
  for col in range(int(2*ex/step)+1):
   x=-ex+col*step
   x+=rng.uniform(-step*.19,step*.19);z=y+rng.uniform(-step*.19,step*.19)
   if radius(x,z)<.972:points.append(Vector((x,z)))
 chain=[]
 for k,(a,b) in enumerate(zip(SPINE,SPINE[1:])):
  count=max(1,math.ceil((b[0]-a[0])/6))
  for j in range(count):
   t=j/count;x=(a[0]+(b[0]-a[0])*t)*ex/228;y=(a[1]+(b[1]-a[1])*t)*ey/95
   if radius(x,y)<.965:
    chain.append(len(points));points.append(Vector((x,y)))
 chain.append(len(points));points.append(Vector((SPINE[-1][0]*ex/228,SPINE[-1][1]*ey/95)))
 edges.extend(zip(chain,chain[1:]))
 if detail:
  foreground_chain=[]
  for a,b in zip(FORE_SPINE,FORE_SPINE[1:]):
   count=max(1,math.ceil((b[0]-a[0])/6))
   for j in range(count):
    t=j/count;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
    if radius(x,y)<.965:foreground_chain.append(len(points));points.append(Vector((x,y)))
  edges.extend(zip(foreground_chain,foreground_chain[1:]))
  for spur in SPURS:
   for a,b in zip(spur,spur[1:]):
    for t in (.16,.44,.72,1):
     x=(a[0]+(b[0]-a[0])*t)*ex/228;y=(a[1]+(b[1]-a[1])*t)*ey/95
     if radius(x,y)<.945:points.append(Vector((x,y)))
 vs,es,fs,_,_,_=delaunay_2d_cdt(points,edges,[list(range(n))],1,.002,False)
 local=[(v.x,v.y,elevation(v.x,v.y)) for v in vs];localfaces=[]
 for f in fs:
  if len(f)!=3:raise RuntimeError('Expected constrained triangulation')
  a,b,c=(local[i] for i in f)
  if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:f=tuple(reversed(f))
  localfaces.append(tuple(f))
 # A short sealed skirt and flat submerged underside keep every island manifold.
 topedges={}
 for f in localfaces:
  for a,b in zip(f,f[1:]+f[:1]):
   key=tuple(sorted((a,b)));topedges[key]=topedges.get(key,0)+1
 boundary=[k for k,count in topedges.items() if count==1]
 foot={}
 for a,b in boundary:
  for i in (a,b):
   if i not in foot:foot[i]=len(local);local.append((local[i][0],local[i][1],-5.1))
 bottom=len(local);local.append((0,0,-5.1))
 for a,b in boundary:
  # Choose the outward ring order from the top oriented boundary.
  for f in localfaces:
   if any(u==a and v==b for u,v in zip(f,f[1:]+f[:1])):break
  else:a,b=b,a
  localfaces.extend([(b,a,foot[a]),(b,foot[a],foot[b]),(foot[b],foot[a],bottom)])
 # Build local mesh first so analytic broad slope tint sees shared smooth normals.
 me=bpy.data.meshes.new(name);me.from_pydata(local,[],localfaces);me.update()
 for f in me.polygons:f.use_smooth=True
 obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);bpy.context.view_layer.update()
 tint=[]
 for i,v in enumerate(me.vertices):
  x,y,h=v.co
  normal=Vector((-(elevation(x+1,y)-elevation(x-1,y))*.5,-(elevation(x,y+1)-elevation(x,y-1))*.5,1)).normalized()
  xx=x/ex*228;yy=y/ey*95
  canopy=clamp(.5+field(xx,yy,seed+61,.032)*1.20+field(xx,yy,seed+37,.082)*.35)
  colour=mix((.075,.23,.13),(.28,.43,.15),canopy)
  colour=mix(colour,(.075,.245,.15),(1-smooth(-44,-20,yy))*.24)
  # Forest light/shade carries wide patches and clear ridge/gully depth. Avoid
  # individual trees or repeated pinprick highlights at six hundred metres.
  valley=clamp((spur_height(xx,yy)-max(0,h/height_scale))/22+.35)
  colour=mix(colour,(.08,.21,.145),valley*.17)
  steep=1-smooth(.55,.83,max(0,normal.z))
  stoneMask=clamp(.5+field(xx,yy,seed+73,.052)*1.5)
  mineral=steep*(.20+.40*stoneMask)
  colour=mix(colour,(.47,.475,.345),mineral)
  shoreShare=1-smooth(0,9,h)
  colour=mix(colour,(.62,.58,.435),shoreShare*.75)
  # Recessed islands carry a cooler grade before the shared atmosphere. Main
  # forest colours remain legible; dedicated horizon fog adds only bounded haze.
  haze=.07 if detail else .22
  colour=mix(colour,(.33,.46,.48),haze)
  tint.append((*colour,1))
 colour=me.color_attributes.new(name='HorizonAlbedo',type='FLOAT_COLOR',domain='POINT')
 for item,c in zip(colour.data,tint):item.color=c
 uv=me.uv_layers.new(name='UVMap')
 for f in me.polygons:
  for li in f.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x*.018,v.y*.018)
 obj.location=(centre[0],centre[1],0)
 bm=bmesh.new();bm.from_mesh(me);boundaryCount=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free();me.calc_loop_triangles()
 islands.append({'name':name,'centreUnityXZ':centre,'originalExtentXZ':extent,'triangles':len(me.loop_triangles),'vertices':len(me.vertices),'boundaryEdges':boundaryCount,'nonmanifoldEdges':nonmanifold,'minHeight':min(v.co.z for v in me.vertices),'maxHeight':max(v.co.z for v in me.vertices)})
 return obj
objects=[island('Central forest ridge island',(-15,600),(228,95),1,6.0,1.0,True),
 island('Recessed east island',(285,690),(130,72),3,7.5,.52,False),
 island('Recessed west island',(-340,720),(144,64),6,7.5,.42,False)]
# Merge the three disconnected but sealed shells to one shared-material render mesh.
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='HORIZON_FOREST_LIMESTONE';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
mat=bpy.data.materials.new('HORIZON_FOREST_LIMESTONE');mat.use_nodes=True;mat.diffuse_color=(.20,.34,.17,1)
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.90
vertex=mat.node_tree.nodes.new('ShaderNodeVertexColor');vertex.layer_name='HorizonAlbedo';mat.node_tree.links.new(vertex.outputs['Color'],bs.inputs['Base Color']);obj.data.materials.append(mat)
obj.data.calc_loop_triangles()
bpy.ops.export_scene.fbx(filepath=str(W/'TennisHorizon2.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',mesh_smooth_type='FACE',colors_type='LINEAR',bake_anim=False,add_leaf_bones=False)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'TennisHorizon2.blend'))
report={'status':'work-only source; actual Unity capture pending','styleSource':'Existing TennisCoast constrained Delaunay / sealed island / blended vertex-colour workflow','schema':'One HORIZON_FOREST_LIMESTONE mesh; one material; imported smooth normals; linear HorizonAlbedo vertex colours','triangles':len(obj.data.loop_triangles),'vertices':len(obj.data.vertices),'islands':islands,'boundsUnity':{'min':[min(v.co[i] for v in obj.data.vertices) for i in (0,2,1)],'max':[max(v.co[i] for v in obj.data.vertices) for i in (0,2,1)]},'sha256':hashlib.sha256((W/'TennisHorizon2.fbx').read_bytes()).hexdigest(),'notes':['Original distant island centre/outline extents retained','authored jagged main crest and descending forest spurs','no trees/textures/alpha/details in play corridor','submerged skirts/bottoms sealed; no colliders']}
(W/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
