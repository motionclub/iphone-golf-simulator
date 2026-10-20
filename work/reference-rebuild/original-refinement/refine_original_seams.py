"""One work-only original-head seam pilot; no canonical or Assets writes.

Keep every original Body coordinate/weight and the eye feature coordinates.
Append a welded, skin-coloured bevel to each actual Body eye-hole boundary.
Replace floating lip/nostril/crease paint with a feathered colour attribute on
the original skin. Retain one original brow, fitted only in depth to skin.
"""
import bpy, bmesh, pathlib, json, math, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=pathlib.Path.cwd(); O=R/'work/reference-rebuild/original-refinement';O.mkdir(parents=True,exist_ok=True)
REPORT={}

def mat(name,c,rough=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.3;return m

def smoothstep(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

def group_points(body,name):
 g=body.vertex_groups.get(name)
 return [v.co.copy() for v in body.data.vertices if g and any(w.group==g.index and w.weight>.25 for w in v.groups)]

def z_at(points,x):
 # Existing labelled contour points define the lip edge, without new paint meshes.
 if not points:return None
 order=sorted(points,key=lambda p:p.x)
 near=sorted(order,key=lambda p:abs(p.x-x))[:3]
 weights=[1/max(.00025,abs(p.x-x))**2 for p in near]
 return sum(p.z*w for p,w in zip(near,weights))/sum(weights)

def colour_skin(body,sex,base):
 up=group_points(body,'LOOP_mouth_lip_upper' if sex=='Male' else 'LOOP_lip_up')
 lo=group_points(body,'LOOP_mouth_lip_lower' if sex=='Male' else 'LOOP_lip_lo')
 seam=group_points(body,'LOOP_mouth_seam' if sex=='Male' else 'LOOP_seam')
 nostrils=[group_points(body,'LOOP_nostril_'+s) for s in ('L','R')]
 centres=[sum(ps,Vector())/len(ps) for ps in nostrils if ps]
 ca=body.data.color_attributes.new(name='SkinPigment',type='FLOAT_COLOR',domain='POINT')
 lip=(base[0]*.93,base[1]*.66,base[2]*.68);line=(base[0]*.64,base[1]*.49,base[2]*.48)
 width=max(abs(p.x) for p in up+lo) if up+lo else .025
 counts=collections.Counter();lookup=[]
 for i,v in enumerate(body.data.vertices):
  p=v.co;c=list(base);lipWeight=0;darkWeight=0
  if p.y<-.08 and abs(p.x)<width+.0015 and up and lo:
   u=z_at(up,p.x);l=z_at(lo,p.x);u,l=max(u,l),min(u,l)
   a=smoothstep(l-.0012,l+.0005,p.z)*(1-smoothstep(u-.0005,u+.0012,p.z))*(1-smoothstep(width-.002,width+.0008,abs(p.x)))
   if a>.01:counts['lipVertices']+=1
   lipWeight=.70*a;c=[q*(1-lipWeight)+t*lipWeight for q,t in zip(c,lip)]
   s=z_at(seam,p.x)
   if s is not None:
    a2=math.exp(-((p.z-s)/.0006)**2)*(1-smoothstep(width-.003,width,abs(p.x)))*.46
    darkWeight=a2;c=[q*(1-a2)+t*a2 for q,t in zip(c,line)]
  for n in centres:
   d=((p.x-n.x)/.0028)**2+((p.z-n.z)/.00135)**2+((p.y-n.y)/.004)**2
   a=math.exp(-d)*.35
   if a>.01:counts['nostrilVertices']+=1
   darkWeight=1-(1-darkWeight)*(1-a);c=[q*(1-a)+t*a for q,t in zip(c,line)]
  ca.data[i].color=(*c,1)
  lookup.append(((.5+63*lipWeight)/64,(.5+63*darkWeight)/64))
 # A continuous two-scalar tint lookup uses the existing untextured Body UV0.
 # Runtime BaseMap is a tiny *relative* multiplier LUT, so no selected skin hue
 # is replaced and no shared shader is needed. Triangle interpolation is valid
 # across this analytic colour field (unlike a random per-vertex texel atlas).
 for layer in list(body.data.uv_layers):body.data.uv_layers.remove(layer)
 uv=body.data.uv_layers.new(name='SkinPigmentLookup')
 for p in body.data.polygons:
  for li in p.loop_indices:uv.data[li].uv=lookup[body.data.loops[li].vertex_index]
 m=mat('Skin_OriginalSurfacePigment',base,.47);nodes=m.node_tree.nodes;vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='SkinPigment';m.node_tree.links.new(vc.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
 body.data.materials.clear();body.data.materials.append(m)
 for p in body.data.polygons:p.material_index=0;p.use_smooth=True
 return dict(counts), {'upper':[[*p] for p in up],'lower':[[*p] for p in lo],'seam':[[*p] for p in seam],'nostrilCentres':[[*p] for p in centres]}

def eye_bevel(body,face,eye_z):
 eyeids={v for p in face.data.polygons if 'Sclera' in face.data.materials[p.material_index].name for v in p.vertices};eyeindex={v:i for i,v in enumerate(sorted(eyeids))}
 eyeBVH=BVHTree.FromPolygons([face.matrix_world@face.data.vertices[v].co for v in sorted(eyeids)],[tuple(eyeindex[v] for v in p.vertices) for p in face.data.polygons if 'Sclera' in face.data.materials[p.material_index].name])
 bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();deform=bm.verts.layers.deform.verify()
 boundary=[e for e in bm.edges if e.is_boundary and min(v.co.z for v in e.verts)>eye_z-.05 and max(v.co.z for v in e.verts)<eye_z+.05 and all(v.co.y<-.05 for v in e.verts)]
 adj=collections.defaultdict(list)
 for e in boundary:
  a,b=e.verts;adj[a].append(b);adj[b].append(a)
 seen=set();rings=[]
 for start in adj:
  if start in seen:continue
  ring=[];prev=None;current=start
  while current not in seen:
   seen.add(current);ring.append(current);nxt=[v for v in adj[current] if v!=prev]
   if not nxt:break
   prev,current=current,nxt[0]
  if len(ring)>20:rings.append(ring)
 report=[]
 for ring in rings:
  c=sum((v.co for v in ring),Vector())/len(ring);rows=[ring]
  # A small continuous roll, welded to the original skin edge. Eye scale and
  # original rim coordinates stay exact; two rows lie inside the true aperture.
  maxDepth=0
  for radial,amount in ((.00035,.35),(.00070,.75),(.0010,1.0)):
   row=[]
   for v in ring:
    p=v.co.copy();d=Vector((c.x-p.x,0,c.z-p.z));d.normalize();p+=d*radial
    hit,n,_,_=eyeBVH.ray_cast(Vector((p.x,-1,p.z)),Vector((0,1,0)))
    front=hit.y-.00035 if hit is not None else v.co.y-.0007
    p.y=v.co.y+(front-v.co.y)*amount-.00025*math.sin(math.pi*amount)
    maxDepth=max(maxDepth,abs(p.y-v.co.y))
    nv=bm.verts.new(p)
    for gi,w in v[deform].items():nv[deform][gi]=w
    row.append(nv)
   rows.append(row)
  for a,b in zip(rows,rows[1:]):
   for j in range(len(ring)):
    q=(j+1)%len(ring);f=bm.faces.new((a[j],a[q],b[q],b[j]));f.smooth=True;f.material_index=0
  report.append({'boundaryVertices':len(ring),'centre':list(c),'radialInsetMetres':.0010,'maxAppendedDepthMetres':maxDepth,'fit':'Actual unchanged Sclera surface; original Body boundary retained'})
 bm.normal_update();bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
 # Deliberately discard original split-normal discontinuities on the work pilot.
 body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
 return report

def features(body,face,rig,sex):
 vs=[];fs=[];mis=[];materials=[];kept=[];maxfit=0;browRepairs=[];skinBVH=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[p.vertices[:] for p in body.data.polygons])
 for mi,old in enumerate(face.data.materials):
  name=old.name
  keep=any(s in name for s in ('Sclera','Iris','Pupil','Limbal')) or name=='Face_Brow'
  if not keep:continue
  polys=[p for p in face.data.polygons if p.material_index==mi];ids={i for p in polys for i in p.vertices};mapping={}
  for i in sorted(ids):
   p=face.matrix_world@face.data.vertices[i].co
   if name=='Face_Brow':
    hit,n,_,_=skinBVH.ray_cast(Vector((p.x,-1,p.z)),Vector((0,1,0)))
    if hit is not None:
     # Preserve eyebrow x/z and rounded source profile; bring only floating
     # depth onto skin, keeping its original front/back cross-section thickness.
     p.y-=.0012;y=hit.y-.0013
     if p.y>y:p.y=y
     maxfit=max(maxfit,abs(p.y-(face.matrix_world@face.data.vertices[i].co).y))
   mapping[i]=len(vs);vs.append(p)
  index=len(materials)
  if 'Sclera' in name:c=(.82,.84,.78);rough=.3
  elif 'Pupil' in name:c=(.004,.003,.002);rough=.2
  elif 'Iris' in name:c=(.135,.053,.018);rough=.28
  elif 'Limbal' in name:c=(.035,.018,.008);rough=.32
  elif 'Catch' in name:c=(.92,.94,.9);rough=.2
  else:c=(.035,.018,.008);rough=.7
  materials.append(mat('Reference_'+name,c,rough))
  start=len(fs)
  for p in polys:fs.append(tuple(mapping[i] for i in p.vertices));mis.append(index)
  if name=='Face_Brow':
   # The original brow has open/incorrectly oriented sheet boundaries which
   # Cycles displays from both sides. Close those boundaries and orient the
   # volume for the actual game's back-face culling; retain its exact x/z shape.
   keys=sorted(ids);local={mapping[i]:j for j,i in enumerate(keys)};temp=bpy.data.meshes.new('BrowClosureWork');temp.from_pydata([vs[mapping[i]] for i in keys],[],[tuple(local[i] for i in p) for p in fs[start:]])
   bm=bmesh.new();bm.from_mesh(temp);edges=[e for e in bm.edges if e.is_boundary];filled=bmesh.ops.holes_fill(bm,edges=edges,sides=0).get('faces',[]) if edges else []
   bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(temp);bm.free();temp.update()
   fs[start:]=[tuple(mapping[keys[i]] for i in p.vertices) for p in temp.polygons];mis[start:]=[index]*len(temp.polygons)
   browRepairs.append({'sourceOpenBoundaryEdges':len(edges),'closedFaces':len(filled),'frontClearanceMetres':.0013})
   bpy.data.meshes.remove(temp)
  kept.append(name)
 # A tiny curved corneal highlight is seated on the real unchanged iris, never
 # outside the aperture or above the lid. Eye diameter/iris geometry stay exact.
 eyeids={v for p in face.data.polygons if any(n in face.data.materials[p.material_index].name for n in ('Sclera','Iris','Pupil')) for v in p.vertices};ei={i:j for j,i in enumerate(sorted(eyeids))};eyeBVH=BVHTree.FromPolygons([face.matrix_world@face.data.vertices[i].co for i in sorted(eyeids)],[tuple(ei[i] for i in p.vertices) for p in face.data.polygons if any(n in face.data.materials[p.material_index].name for n in ('Sclera','Iris','Pupil'))])
 iris=[face.matrix_world@face.data.vertices[v].co for p in face.data.polygons if face.data.materials[p.material_index].name=='Face_Iris' for v in p.vertices];catchIndex=len(materials);materials.append(mat('Reference_Face_Catch',(.98,.98,.96),.2));catchReport=[]
 for sign in (-1,1):
  ips=[p for p in iris if p.x*sign>0];c=sum(ips,Vector())/len(ips);radius=(max(p.z for p in ips)-min(p.z for p in ips))*.5;cx=c.x-radius*.28;cz=c.z+radius*.32;rx=radius*.145;rz=radius*.18;baseIndex=len(vs)
  # A shallow curved disc, fitted point-by-point to the actual anterior surface.
  for ring in (0,.5,1):
   for k in range(16):
    a=2*math.pi*k/16;x=cx+rx*ring*math.cos(a);z=cz+rz*ring*math.sin(a);hit,n,_,_=eyeBVH.ray_cast(Vector((x,-1,z)),Vector((0,1,0)));y=hit.y-.00010-.00006*(1-ring*ring) if hit is not None else c.y-.0002;vs.append(Vector((x,y,z)))
  for row in range(2):
   for k in range(16):a=baseIndex+row*16+k;b=baseIndex+row*16+(k+1)%16;fs.append((a,a+16,b+16,b));mis.append(catchIndex)
  catchReport.append({'centreXZ':[cx,cz],'radiusXZ':[rx,rz],'maxSurfaceSeparationMetres':.00016})
 kept.append('Reference_Face_Catch (surface-seated)')
 me=bpy.data.meshes.new('OriginalReferenceFeatures');me.from_pydata(vs,[],fs);me.update()
 for m in materials:me.materials.append(m)
 for p,mi in zip(me.polygons,mis):p.material_index=mi;p.use_smooth=True
 ob=bpy.data.objects.new('ReferenceFeatures',me);bpy.context.scene.collection.objects.link(ob);ob.parent=rig;ob.vertex_groups.new(name='Head').add(list(range(len(vs))),1,'REPLACE');mod=ob.modifiers.new('OriginalRig','ARMATURE');mod.object=rig
 return ob,{'keptOriginalMaterialRegions':kept,'maxBrowDepthFitMetres':maxfit,'browBoundaryRepairs':browRepairs,'cornealCatchlights':catchReport,'eyeCoordinateChangeMetres':0}

def studio(sc,eye):
 sc.use_nodes=False;sc.render.film_transparent=False;sc.world=bpy.data.worlds.new('SeamPilotStudio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.42,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.30
 target=eye+Vector((0,0,-.018))
 for name,delta,power,size,color in [('Key',(-.55,-.7,.75),25,1,(1,.91,.80)),('Fill',(.55,-.7,.20),12,1,(.85,.91,1)),('Rim',(.3,.35,.55),32,.75,(1,.89,.75))]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;d.color=color;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=eye+Vector(delta);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('OriginalSeamPortrait');cam=bpy.data.objects.new('OriginalSeamPortrait',d);sc.collection.objects.link(cam);sc.camera=cam;d.type='ORTHO';d.ortho_scale=.39
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=600;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.55
 return cam,target

for sex in ('Male','Female'):
 source=R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend';bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
 body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));face=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Face_'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 for o in bpy.data.objects:o.hide_render=o not in (body,face)
 bpy.context.view_layer.update();eyeids={i for p in face.data.polygons if 'Sclera' in face.data.materials[p.material_index].name for i in p.vertices};eye=sum((face.matrix_world@face.data.vertices[i].co for i in eyeids),Vector())/len(eyeids)
 original=[v.co.copy() for v in body.data.vertices];oldweights=[{g.group:g.weight for g in v.groups} for v in body.data.vertices]
 base=(.50,.29,.17) if sex=='Male' else (.66,.40,.25)
 bevel=eye_bevel(body,face,eye.z);pigment,contours=colour_skin(body,sex,base);feat,featureReport=features(body,face,rig,sex);face.hide_render=True;feat.hide_render=False;body.hide_render=False;body.name='Body'
 # Source poses/weights and every original vertex remain unmodified.
 poserror=max((body.data.vertices[i].co-p).length for i,p in enumerate(original));werror=max((max((abs({g.group:g.weight for g in body.data.vertices[i].groups}.get(k,0)-w) for k,w in weights.items()),default=0) for i,weights in enumerate(oldweights)),default=0)
 assert poserror<1e-7 and werror<1e-7,(sex,poserror,werror)
 cam,target=studio(sc,eye)
 for angle,delta in [('front',(0,-1.1,.015)),('threequarter',(.42,-1.1,.025))]:
  cam.location=eye+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex.lower()}_seam_pilot_{angle}.png');bpy.ops.render.render(write_still=True)
 sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_OriginalSeamPilot.blend'))
 REPORT[sex]={'canonicalSource':str(source),'oldBodyVertices':len(original),'newBodyVertices':len(body.data.vertices),'originalPositionMaxDeltaMetres':poserror,'originalWeightMaxDelta':werror,'boneCount':len(rig.data.bones),'eyeMidWorld':list(eye),'bevels':bevel,'surfacePigment':pigment,'contours':contours,'features':featureReport,'removedFaceRegions':[m.name for m in face.data.materials if m.name not in featureReport['keptOriginalMaterialRegions']]}
 (O/'seam-pilot-manifest.json').write_text(json.dumps(REPORT,indent=2));print('ORIGINAL_SEAM_PILOT',sex,poserror,werror,bevel,pigment,featureReport)
