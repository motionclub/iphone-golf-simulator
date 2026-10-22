"""Independent connected-piece cuboid census from a saved blend or FBX.

The 20% limit is the user's threshold. Cuboids are counted regardless of their
world rotation, so rotating an intact box cannot improve this result. Exact
duplicate spatial vertices from UV/normal splits are welded; no epsilon weld.
"""
import os, sys, json, math
sys.dont_write_bytecode=True
import bpy
import numpy as np

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def opt(k,d=None): return args[args.index(k)+1] if k in args else d
source=opt('--blend') or opt('--fbx')
out=opt('--out',os.path.join(os.path.dirname(__file__),'piece_classifier.json'))
if not source: raise RuntimeError('need --blend or --fbx')
if source.endswith('.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=source)
else: bpy.ops.wm.open_mainfile(filepath=source,load_ui=False)

def cuboid_shape(vertex_count,normals):
    if vertex_count!=8 or len(normals)!=6: return False
    axes=[]
    for n in normals:
        if not any(abs(float(n@a))>math.cos(math.radians(1.)) for a in axes): axes.append(n)
    return (len(axes)==3 and all(abs(float(axes[i]@axes[j]))<math.sin(math.radians(1.))
                               for i in range(3) for j in range(i)))

# Negative controls for the acceptance gate: both intact boxes are counted
# as bad pieces even when rotated. A real extra cut is not an intact cuboid.
axes=np.eye(3); six=np.concatenate([axes,-axes])
angle=.73; rotation=np.array([[math.cos(angle),-math.sin(angle),0.],
                             [math.sin(angle),math.cos(angle),0.],[0.,0.,1.]])
controls={'axis_box_counted':cuboid_shape(8,six),
          'rotated_box_counted':cuboid_shape(8,six@rotation.T),
          'chipped_polyhedron_not_box':not cuboid_shape(12,np.concatenate([six,[[.577,.577,.577]]]))}
if not all(controls.values()): raise RuntimeError('cuboid classifier control FAIL')

def pieces(ob):
    me=ob.data
    mw=np.asarray(ob.matrix_world,dtype=float)
    co=np.asarray([tuple(v.co) for v in me.vertices],float)
    world=co@mw[:3,:3].T+mw[:3,3]
    uniq,inv=np.unique(world,axis=0,return_inverse=True)
    parent=list(range(len(uniq)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return i
    faces=[]
    for f in me.polygons:
        ids=tuple(dict.fromkeys(int(inv[i]) for i in f.vertices))
        if len(ids)<3: continue
        faces.append(ids)
        for i in ids[1:]: parent[find(i)]=find(ids[0])
    groups={}
    for f in faces: groups.setdefault(find(f[0]),[]).append(f)
    for fs in groups.values():
        ids=sorted({i for f in fs for i in f})
        normals=[]
        for f in fs:
            q=uniq[list(f)]; n=np.zeros(3)
            for i in range(len(q)): n+=np.cross(q[i],q[(i+1)%len(q)])
            le=np.linalg.norm(n)
            if le>1e-12:
                n/=le
                if not any(float(n@v)>1-1e-6 for v in normals): normals.append(n)
        # A real intact cuboid has exactly eight spatial corners and six
        # opposing plane directions with three mutually perpendicular axes.
        cuboid=cuboid_shape(len(ids),normals)
        points=uniq[ids]
        yield {'vertices':len(ids),'faces':len(fs),'planes':len(normals),'unbroken_cuboid':bool(cuboid),
               'world_min':points.min(0).tolist(),'world_max':points.max(0).tolist()}

records=[]
for ob in bpy.data.objects:
    if ob.type!='MESH' or not ob.name.startswith(('DRESS_RUIN','DRESS_ARCH','DRESS_BLOCK')): continue
    if ob.users_collection and all(c.name=='ASSET_LIBRARY' for c in ob.users_collection): continue
    for k,p in enumerate(pieces(ob)):
        p['object']=ob.name; p['piece']=k; records.append(p)
n=len(records); boxes=sum(p['unbroken_cuboid'] for p in records)
share=boxes/n if n else 1.
result={'source':os.path.abspath(source),'pieces':n,'unbroken_cuboids':boxes,'share':share,'limit':.20,
        'pass':bool(n and share<=.20),'controls':controls,'classification':'8 exact-welded vertices and 6 opposing orthogonal plane directions; rotation-independent; 1 degree direction classification',
        'records':records}
with open(out,'w') as f: json.dump(result,f,indent=2)
msg=f"GATE: RUIN_PIECE_CUBOIDS {'PASS' if result['pass'] else 'FAIL'} - {boxes}/{n} unbroken cuboids ({share:.3%}) <=20%; rotated intact boxes also counted"
print(msg,flush=True)
with open(os.path.splitext(out)[0]+'.txt','w') as f: f.write(msg+'\n')
sys.exit(0 if result['pass'] else 1)
