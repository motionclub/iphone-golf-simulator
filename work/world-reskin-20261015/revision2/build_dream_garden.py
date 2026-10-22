import bpy,bmesh,math,random,json
from mathutils import Vector,noise
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');OUT=R/'work/world-reskin-20261015/revision2';RES=R/'Unity/Assets/Resources/Environment/LuminousCoast'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/Resort/ReferenceHole12.fbx'),use_anim=False)
source={o.name:o for o in bpy.context.scene.objects}
terrain={n:[o.matrix_world@v.co for v in o.data.vertices] for n,o in source.items() if n.startswith('TERRAIN')}
bridge=[source['BRIDGE_PLANKS'].matrix_world@v.co for v in source['BRIDGE_PLANKS'].data.vertices]
markers={n:source['MARKER_'+n].matrix_world.translation.copy() for n in ['TEE','PIN','UP']}
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
rng=random.Random(84115)
# One mesh per surface family; vertex colour carries baked local variation/occlusion.
meshes={};mats={}
palette={'Stone':(.66,.69,.65),'Plaster':(.83,.83,.75),'Gold':(.55,.29,.105),'Teal':(.027,.22,.22),'Wood':(.43,.30,.18),'Leaf':(.12,.27,.16),'Bloom':(.63,.19,.40),'Glow':(.20,.85,.66),'Waterfall':(.38,.82,.78)}
def group(name):
 if name not in meshes:meshes[name]=[[],[],[]]
 return meshes[name]
def add(name,verts,faces,color=None,ao=None):
 vv,ff,cc=group(name);offset=len(vv);vv.extend(verts);ff.extend(tuple(offset+i for i in f) for f in faces)
 base=palette[name] if color is None else color
 cc.extend([(*[c*(ao[i] if ao else 1) for c in base],1) for i in range(len(verts))])
def tube(name,a,b,r0,r1=None,n=10,color=None):
 a,b=Vector(a),Vector(b);z=(b-a).normalized();x=z.cross(Vector((0,1,0)))
 if x.length<.01:x=z.cross(Vector((1,0,0)))
 x.normalize();y=z.cross(x);r1=r0 if r1 is None else r1
 v=[tuple(p+(x*math.cos(k*math.tau/n)+y*math.sin(k*math.tau/n))*r) for p,r in [(a,r0),(b,r1)] for k in range(n)]
 f=[(k,(k+1)%n,n+(k+1)%n,n+k) for k in range(n)]+[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
 add(name,v,f,color)
def ring(name,c,r0,r1,h,n=64):
 x,y,z=c;v=[]
 for zz,rr in [(z,r0),(z,r1),(z+h,r0),(z+h,r1)]:v.extend((x+math.cos(k*math.tau/n)*rr,y+math.sin(k*math.tau/n)*rr,zz) for k in range(n))
 f=[]
 for k in range(n):
  k1=(k+1)%n;f.extend([(k,k1,2*n+k1,2*n+k),(n+k,3*n+k,3*n+k1,n+k1),(2*n+k,2*n+k1,3*n+k1,3*n+k),(k,n+k,n+k1,k1)])
 add(name,v,f)
def rock(c,scale,seed,name='Stone'):
 rr=random.Random(seed);v=[];n=13;rings=7
 for j in range(rings+1):
  phi=math.pi*(j+.02)/(rings+.04)
  for k in range(n):
   t=k*math.tau/n;unit=Vector((math.sin(phi)*math.cos(t),math.sin(phi)*math.sin(t),math.cos(phi)))
   mod=1+.10*math.sin(t*3+seed)+.065*noise.noise(unit*3+Vector((seed*.1,0,0)))
   v.append(tuple(c[d]+unit[d]*scale[d]*mod for d in range(3)))
 f=[(j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k) for j in range(rings) for k in range(n)]
 f=[tuple(reversed(p)) for p in f]
 # Crevice-dark underside, warmer upper surfaces.
 ao=[.64+.36*max(0,min(1,(p[2]-c[2])/max(.1,scale[2])*.5+.5)) for p in v]
 add(name,v,f,ao=ao)
def leaf(center,length,width,angle,tilt,color,name='Leaf'):
 c=Vector(center);axis=Vector((math.cos(angle)*math.cos(tilt),math.sin(angle)*math.cos(tilt),math.sin(tilt)));side=Vector((-math.sin(angle),math.cos(angle),0))*width
 # Rounded, folded leaf perimeter: small individual lamina, no flat diamonds.
 v=[c+Vector((0,0,width*.20))]
 for k in range(8):
  t=k*math.tau/8
  v.append(c+axis*(math.cos(t)*length*.5)+side*math.sin(t)-Vector((0,0,abs(math.sin(t))*width*.09)))
 add(name,[tuple(x) for x in v],[(0,k+1,(k+1)%8+1) for k in range(8)],color)

def tuft(c,scale,seed,bloom=False):
 rr=random.Random(seed)
 for i in range(20):
  t=rr.random()*math.tau;r=rr.random()*scale*.6;p=Vector(c)+Vector((math.cos(t)*r,math.sin(t)*r,rr.random()*scale*.5))
  leaf(p,scale*rr.uniform(.7,1.6),scale*.08,t,rr.uniform(.5,1.3),(.10+rr.random()*.06,.23+rr.random()*.10,.13))
 if bloom:
  for i in range(7):
   t=rr.random()*math.tau;p=Vector(c)+Vector((math.cos(t)*scale*.5,math.sin(t)*scale*.5,scale*rr.uniform(.8,1.6)))
   tube('Leaf',c,p,.025,n=5)
   for k in range(5):leaf(p,.25,.10,k*math.tau/5,.15,(.72,.21+rr.random()*.09,.40),'Bloom')
# Replace the simple lighthouse with a detailed dream observatory on the same footprint.
x,y,z=11,204,21
for i in range(3):ring('Stone',(x,y,z+i*.22),3.65-i*.15,3.92-i*.15,.22)
tube('Plaster',(x,y,z+.66),(x,y,z+16.4),2.82,2.04,64)
for h,r in [(1,2.88),(4.7,2.66),(9,2.45),(14.9,2.18),(16.2,2.5)]:ring('Gold',(x,y,z+h),r-.13,r+.09,.18)
# Narrow vertical recesses and frames, deliberately modeled rather than a flat tower texture.
for j in range(8):
 t=j*math.tau/8;normal=Vector((math.cos(t),math.sin(t),0));side=Vector((-math.sin(t),math.cos(t),0))
 for h in [4.8,10.4]:
  c=Vector((x,y,z+h))+normal*(2.72-h*.046)
  corners=[c-side*.36,c+side*.36,c+side*.36+Vector((0,0,2.1)),c-side*.36+Vector((0,0,2.1))]
  add('Teal',[tuple(v) for v in corners],[(0,1,2,3)])
  for a,b in [(0,1),(1,2),(2,3),(3,0)]:tube('Gold',corners[a]+normal*.02,corners[b]+normal*.02,.045,n=6)
ring('Plaster',(x,y,z+16.5),2.0,3.45,.36)
for j in range(32):
 t=j*math.tau/32;a=(x+math.cos(t)*3.2,y+math.sin(t)*3.2,z+16.9);tube('Gold',a,(a[0],a[1],a[2]+1.25),.045,n=6)
ring('Gold',(x,y,z+18.1),3.15,3.24,.075)
tube('Teal',(x,y,z+16.9),(x,y,z+20.1),1.9,1.9,32)
for j in range(8):
 t=j*math.tau/8;a=(x+math.cos(t)*1.94,y+math.sin(t)*1.94,z+16.9);tube('Gold',a,(a[0],a[1],z+20.2),.10,n=8)
ring('Gold',(x,y,z+20.1),1.78,2.22,.25)
tube('Gold',(x,y,z+20.4),(x,y,z+22.8),2.45,.05,64)
tube('Gold',(x,y,z+22.8),(x,y,z+23.2),.08,n=8)
# Halo crowns catch directional light, a fantasy landmark still recognizable as a lighthouse.
ring('Gold',(x,y,z+21.3),3.8,3.96,.12)
# Bridge route sampled from authored deck; retain existing deck collider and path.
route=[]
for yy in range(10,132,3):
 pts=[p for p in bridge if abs(p.y-yy)<2.0 and p.z>14]
 if len(pts)>3:route.append(Vector(((min(p.x for p in pts)+max(p.x for p in pts))*.5,yy,max(p.z for p in pts))))
for i in range(len(route)-1):
 a,b=route[i],route[i+1];side=Vector((-(b-a).y,(b-a).x,0)).normalized()*2.45
 for sign in [-1,1]:
  for hh in [.55,1.32]:tube('Gold',a+side*sign+Vector((0,0,hh)),b+side*sign+Vector((0,0,hh)),.055,n=6)
  if i%2==0:tube('Plaster',a+side*sign-Vector((0,0,.2)),a+side*sign+Vector((0,0,1.4)),.16,.13,8)
# Curved stone arch structure beneath the deck; large silhouettes visible from the tee.
for i in range(0,len(route)-7,7):
 a,b=route[i],route[i+7];delta=b-a;side=Vector((-delta.y,delta.x,0)).normalized();vv=[];steps=20
 for j in range(steps+1):
  t=j/steps;p=a.lerp(b,t);top=p.z-1.0;underside=2+(p.z-4)*math.sin(math.pi*t)**.55
  for lateral,zz in [(-2.4,top),(2.4,top),(-2.4,underside),(2.4,underside)]:vv.append(tuple(Vector((p.x,p.y,zz))+side*lateral))
 ff=[]
 for j in range(steps):
  q=j*4;ff.extend([(q,q+4,q+5,q+1),(q+2,q+3,q+7,q+6),(q,q+2,q+6,q+4),(q+1,q+5,q+7,q+3)])
 add('Stone',vv,ff)
# Organic limestone feet and planted border pockets, outside all playable surface overlays.
for name,V in terrain.items():
 pts={tuple(round(v[k],2) for k in range(3)) for v in V if v.z<1}
 pts=list(pts)
 for idx,p in enumerate(pts[::max(1,len(pts)//38)]):
  rock((p[0],p[1],.6),(rng.uniform(2,4.2),rng.uniform(2,4),rng.uniform(1.4,3.5)),idx+len(name)*13)
# Perimeter gardens, no plants on the green/tee or carry corridor.
for i in range(100):
 t=i/100*math.tau;xx=math.cos(t)*40;yy=167+math.sin(t)*53
 if yy<122 or (xx>27 and yy<147):continue
 tuft((xx,yy,21.05),rng.uniform(.55,1.0),i+700,True)
for i in range(42):
 t=i/42*math.tau;xx=math.cos(t)*29;yy=-9+math.sin(t)*19
 if yy>7:continue
 tuft((xx,yy,15.03),rng.uniform(.7,1.4),i+900,True)
# Three dimensional fantasy landforms: curved sea arch, suspended islands, real silhouette/parallax.
def monumental_arch(center,radius,width,depth,seed,angle=0):
 c=Vector(center);v=[];steps=90;cross=12;rot=math.radians(angle)
 for i in range(steps+1):
  t=.06+(math.pi-.12)*i/steps
  for k in range(cross):
   q=k*math.tau/cross;rough=1+.10*math.sin(t*17+q*3)+.04*math.sin(t*31-q*7)
   rr=radius+math.cos(q)*width*rough*(.85+.40*abs(math.cos(t)))
   px=math.cos(t)*rr;py=math.sin(q)*depth*rough;pz=math.sin(t)*rr*(1+.09*math.sin(t*3+.8))
   v.append(tuple(c+Vector((px*math.cos(rot)-py*math.sin(rot),px*math.sin(rot)+py*math.cos(rot),pz))))
 f=[]
 for i in range(steps):
  for k in range(cross):f.append((i*cross+k,i*cross+(k+1)%cross,(i+1)*cross+(k+1)%cross,(i+1)*cross+k))
 add('Stone',v,f,ao=[.72+.28*(p[2]-c.z)/(radius+width) for p in v])
 for edge in [-.70,.70]:
  for i in range(80):
   def point(t):
    rr=radius+edge*width*(.85+.40*abs(math.cos(t)))
    px=math.cos(t)*rr;py=-depth*.85;pz=math.sin(t)*rr*(1+.09*math.sin(t*3+.8))
    return c+Vector((px*math.cos(rot)-py*math.sin(rot),px*math.sin(rot)+py*math.cos(rot),pz))
   tube('Gold',point(.07+(math.pi-.14)*i/80),point(.07+(math.pi-.14)*(i+1)/80),.16,n=6)
 for i in range(25):
  t=.72+(math.pi-1.44)*i/24;rr=radius+width
  px=math.cos(t)*rr;pz=math.sin(t)*rr*(1+.09*math.sin(t*3+.8))
  tuft(c+Vector((px*math.cos(rot),px*math.sin(rot),pz)),2.2,seed*100+i,True)

monumental_arch((-15,300,0),50,7.0,12,31,-9)
monumental_arch((112,271,1),39,5.6,10,61,35)
def floating_island(c,r,seed):
 rr=random.Random(seed);v=[];N=49
 for j in range(9):
  f=j/8;rad=r*(.06+.94*math.sin(f*math.pi*.5)**.65);z=c[2]-r*1.65*(1-f)
  for k in range(N):
   t=k*math.tau/N;w=1+.07*math.sin(t*5+seed)+.045*math.sin(t*11)
   v.append((c[0]+math.cos(t)*rad*w,c[1]+math.sin(t)*rad*.72*w,c[2] if j==8 else z+math.sin(t*7)*r*.09*f+math.sin(t*13+f*12)*r*.035))
 f=[(j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k) for j in range(8) for k in range(N)]
 add('Stone',v,f,ao=[.43+.57*max(0,(p[2]-c[2]+r*1.4)/(r*1.4)) for p in v])
 add('Leaf',v[-N:]+[tuple(c)],[(N,k,(k+1)%N) for k in range(N)],(.15,.32,.20))
 for i in range(14):
  t=rr.random()*math.tau;d=rr.random()*r*.72;tuft((c[0]+math.cos(t)*d,c[1]+math.sin(t)*d*.72,c[2]),rr.uniform(1.3,2.4),seed*100+i,True)
 # Falling ribbons are separate from the opaque islands.
 start=(c[0]+r*.2,c[1]-r*.67,c[2]);vv=[]
 for j in range(25):
  f=j/24;zz=start[2]*(1-f);xx=start[0]+math.sin(f*3)*2;yy=start[1]-f*5
  width=1.7+f*f*2.3
  vv.extend([(xx-width,yy,zz),(xx+width,yy,zz)])
 add('Waterfall',vv,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(24)])
for c,r,s in [((-65,205,51),12,15),((5,325,77),14,19),((82,248,58),12,23),((137,160,49),9,29)]:floating_island(c,r,s)
# Metal arc filigree around suspended garden: a restrained warm counterpoint to turquoise.
for j in range(45):
 t=j/44*math.tau;t2=(j+1)/44*math.tau;c=Vector((5,325,77))
 a=c+Vector((math.cos(t)*16,math.sin(t)*11,2+math.sin(t)*5));b=c+Vector((math.cos(t2)*16,math.sin(t2)*11,2+math.sin(t2)*5));tube('Gold',a,b,.10,n=6)

def flush(name,geo):
 vs,fs,cs=geo;m=bpy.data.meshes.new('Dream '+name);m.from_pydata(vs,[],fs);m.update()
 
 if name in ['Stone','Plaster','Gold','Teal']:
  bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(m);bm.free()
 mat=bpy.data.materials.get('Dream_'+name) or bpy.data.materials.new('Dream_'+name);mat.diffuse_color=(*palette.get(name,(.3,.5,.2)),1);m.materials.append(mat)
 col=m.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for i,c in enumerate(cs):col.data[i].color=c
 m.color_attributes.active_color=col
 ob=bpy.data.objects.new('DREAM_'+name,m);bpy.context.collection.objects.link(ob)
 for p in m.polygons:p.use_smooth=name in ['Stone','Plaster','Gold','Leaf','Bloom']
 # World coordinates give stable material detail without camera-dependent tricks.
 uv=m.uv_layers.new(name='UVMap')
 for l in m.loops:
  p=m.vertices[l.vertex_index].co;uv.data[l.index].uv=(l.vertex_index%2,p.z*.25) if name=='Waterfall' else (p.x*.25,p.z*.25)
 return ob
for name,geo in meshes.items():flush(name,geo)
for name,p in markers.items():
 ob=bpy.data.objects.new('DREAM_ANCHOR_'+name,None);bpy.context.collection.objects.link(ob);ob.location=p
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'DreamGarden.blend'))
bpy.ops.export_scene.fbx(filepath=str(RES/'DreamGarden.fbx'),use_selection=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,object_types={'MESH','EMPTY'})
budget={o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH'}
(OUT/'garden-budget.json').write_text(json.dumps(budget,indent=2))
# Tree kit: fine curved leaves on a branching jacaranda/olive silhouette, no sphere crowns.
bpy.ops.wm.read_factory_settings(use_empty=True)
for variant in range(4):
 for lod in [0,1]:
  meshes={};rr=random.Random(920+variant)
  tube('Wood',(0,0,0),(.25,.05,4.0),.24,.10,10)
  for b in range(9):
   t=b*2.399+variant*.4;end=Vector((math.cos(t)*rr.uniform(1.8,3.2),math.sin(t)*rr.uniform(1.8,3.1),rr.uniform(5,6.8)))
   fork=Vector((.2,0,3.0+rr.random()))
   joint=fork.lerp(end,.65)+Vector((0,0,.4));tube('Wood',fork,joint,.11,.055,8);tube('Wood',joint,end,.055,.012,7)
   for twig in range(7):
    angle=t+twig*2.399;tip=end+Vector((math.cos(angle)*rr.uniform(.4,1.3),math.sin(angle)*rr.uniform(.4,1.2),rr.uniform(-.3,.7)))
    tube('Wood',end,tip,.027,.007,5)
    for q in range(52 if lod==0 else 9):
     a=rr.random()*math.tau;r=rr.random()**.5*1.0;dz=rr.uniform(-.55,.55)
     p=tip+Vector((math.cos(a)*r,math.sin(a)*r,dz))
     bloom=(variant!=3 and rr.random()<.61)
     shade=rr.uniform(.72,1.18)*(0.80+.20*(dz+.55)/1.1)
     co=tuple(x*shade for x in ((.40,.10,.23) if bloom else (.16,.31,.14)))
     leaf(p,rr.uniform(.26,.44)*(1 if lod==0 else 1.45),rr.uniform(.075,.13)*(1 if lod==0 else 1.4),rr.random()*math.tau,rr.uniform(-.5,.8),co,'Leaf')
  # Collapse bark and leaves into a single instanced material. Vertex alpha marks botanical surface.
  vs=[];fs=[];cs=[]
  for name,(v,f,c) in meshes.items():
   off=len(vs);vs+=v;fs += [tuple(off+i for i in p) for p in f];cs+=c
  name='CONIFER_'+chr(65+variant)+('_FAR' if lod else '')
  m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update();mat=bpy.data.materials.get('Luminous Pine') or bpy.data.materials.new('Luminous Pine');m.materials.append(mat)
  col=m.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(cs):col.data[i].color=c
  m.color_attributes.active_color=col
  ob=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(ob)
  for p in m.polygons:p.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'DreamTrees.blend'))
bpy.ops.export_scene.fbx(filepath=str(RES/'CoastalPines.fbx'),use_selection=False,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
(OUT/'tree-budget.json').write_text(json.dumps({o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH'},indent=2))

# Real miniature groves on the suspended islets, shared material and joined draw.
template=bpy.data.objects['CONIFER_A_FAR'];tv=[v.co.copy() for v in template.data.vertices];tf=[list(f.vertices) for f in template.data.polygons];tc=[tuple(c.color) for c in template.data.color_attributes['Color'].data]
bpy.ops.wm.open_mainfile(filepath=str(OUT/'DreamGarden.blend'))
vs=[];fs=[];cs=[];rand=random.Random(611)
for c,r,num in [((-65,205,51),12,5),((5,325,77),14,7),((82,248,58),12,4),((137,160,49),9,3)]:
 for i in range(num):
  t=i*2.399;d=r*.50*math.sqrt((i+.3)/num);pos=Vector(c)+Vector((math.cos(t)*d,math.sin(t)*d*.7,.12));scale=rand.uniform(.85,1.45);angle=rand.random()*math.tau;offset=len(vs)
  for v in tv:vs.append(tuple(pos+Vector((v.x*math.cos(angle)-v.y*math.sin(angle),v.x*math.sin(angle)+v.y*math.cos(angle),v.z))*scale))
  fs.extend(tuple(offset+j for j in f) for f in tf);cs.extend(tc)
flush('Bloom',(vs,fs,cs))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'DreamGarden.blend'))
bpy.ops.export_scene.fbx(filepath=str(RES/'DreamGarden.fbx'),use_selection=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,object_types={'MESH','EMPTY'})
(OUT/'garden-budget.json').write_text(json.dumps({o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH'},indent=2))
