"""Scratch-only genuine closed cut-stone body around the frozen tee square."""
import os,sys,json,random,math
import bpy,numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
sys.path.insert(0,os.path.dirname(__file__))
import postcard_lib as P,postcard_look_lib as L,postcard_props_lib as PL
import postcard_look_verify as V,hole10_look as HL
from compact_columns import _closed_cut_column
OUT=os.path.dirname(__file__)+'/tee_platform_filled'
os.makedirs(OUT,exist_ok=True)
D=P.start('hole10_design',out_dir=OUT)
D.mod.SCENERY['tee_box_m']=(D.scenery['tee_box']['width']*P.YD,D.scenery['tee_box']['depth']*P.YD)
P.build_terrain(D,undercut_m=6.)
P.build_play_surfaces(D)
P.build_gameplay(D)
L.look_materials(D)
pad=bpy.data.objects['TEE_BOX'];hull=HL.pad_outline(pad)
centerline=HL.inset_polygon(hull,.75)
closed=np.vstack([centerline,centerline[:1]])
segments=np.diff(closed,axis=0);lengths=np.linalg.norm(segments,axis=1)
arc=np.r_[0.,np.cumsum(lengths)];total=float(arc[-1])
count=int(round(total/1.20));rng=random.Random(10245)
mb=PL._MB(('LK_BASALT',));columns=[]
z=float(max(v.co.z for v in pad.data.vertices))+.0115
for k in range(count):
 s=total*(k+.5)/count
 j=min(len(segments)-1,int(np.searchsorted(arc,s,side='right')-1))
 t=(s-arc[j])/lengths[j];p=centerline[j]+segments[j]*t
 tangent=segments[j]/lengths[j]
 width=rng.uniform(1.13,1.25)
 angle=math.atan2(tangent[1],tangent[0])+math.pi/6+rng.uniform(-.1,.1)
 n=6 if k%4==0 else 5
 xy=np.array([p+.5*width*np.array([math.cos(angle+math.tau*i/n),math.sin(angle+math.tau*i/n)]) for i in range(n)])
 vertices,faces,spec=_closed_cut_column(xy,-1.6,z,rng,cuts=1)
 base=len(mb.V);mb.V.extend(tuple(v) for v in vertices)
 for f in faces:mb.f(tuple(base+i for i in f))
 columns.append(spec)
# The first perimeter-only body was a real hollow ring and failed the original
# sphere-like radius test. These actual buried stone piers fill its interior and
# support the grass square; they are not extra points on the failed ring.
for gx in (-3.,-1.,1.,3.):
 for gy in (-2.1,0.,2.1):
  p=np.array([gx,gy]);width=rng.uniform(.95,1.3)
  angle=rng.uniform(-.2,.2);n=6 if rng.random()<.25 else 5
  xy=np.array([p+.5*width*np.array([math.cos(angle+math.tau*i/n),math.sin(angle+math.tau*i/n)]) for i in range(n)])
  vertices,faces,spec=_closed_cut_column(xy,-1.6,z-.07,rng,cuts=1)
  base=len(mb.V);mb.V.extend(tuple(v) for v in vertices)
  for f in faces:mb.f(tuple(base+i for i in f))
  columns.append(spec)
mesh=PL._finalize('DRESS_PADRIM_V3',mb,'box',smooth_angle=None,library=False)
ob=bpy.data.objects.new('DRESS_PADRIM_V3',mesh);PL._collection_for('DRESS_').objects.link(ob);PL._parent(D,ob)
HL.UV_STATS[ob.name]=HL.author_uv(mesh,random.Random(10246),uf=.7,vf=.32,p_glow=.3)
bpy.context.view_layer.update()
C=type('C',(),dict(hole=10,tag='10'))()
S=V.Snap('blend',C)
shape=V.rock_shape(S.loc(ob))
W=L._mesh_arrays(ob)[0]
edge=np.roll(hull,-1,axis=0)-hull
normal=np.stack([-edge[:,1],edge[:,0]],1)/np.linalg.norm(edge,axis=1)[:,None]
top=W[:,2]>z-.002
inside=float(np.einsum('kij,ij->ki',W[top,None,:2]-hull[None,:,:],normal).min())
markers=[np.array(bpy.data.objects[n].matrix_world.translation)[:2] for n in ('TEE_MARKER_1','TEE_MARKER_2','MARKER_TEE','BALL_START')]
clear=min(float(np.linalg.norm(W[top,:2]-m,axis=1).min()) for m in markers)
r3=float(shape.get('r3',0.))
result=dict(geometry=shape,columns=len(columns),polygons=len(mesh.polygons),triangles=sum(len(f)-2 for f in mb.F),top_z=z,
 top_inside_m=inside,marker_clearance_m=clear,horizontal_span_m=float(np.linalg.norm(np.ptp(W[:,:2],axis=0))),
 notes='Real closed stone bodies reach below lava; cap lies11.5mm over frozen tee. Original texture-window checks remain unresolved.',
 cap_placement_pass=inside>=0 and clear>=1.5)
json.dump(result,open(OUT+'/metrics.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/fixture.blend',relative_remap=False)
print('TEE_PLATFORM '+json.dumps(result),flush=True)
