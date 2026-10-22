"""Exercise the helper's explicit custom-corner-normal preservation path."""
import os,sys,json
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import bpy,numpy as np
import postcard_lib as P
import postcard_look_lib as L
import hole09_masonry as HM
D=P.start('hole09_design',out_dir=os.path.dirname(__file__))
mat=L.look_material('LK_MASONRY',D)
objects=[]
for j in range(2):
    ob=P.new_mesh_object(f'DRESS_RUIN_CONTROL_{j}','STRUCTURES')
    ob.data.from_pydata([(j*2,0,0),(j*2+1,0,0),(j*2,.7,0),(j*2+.3,.3,.8)],[],
                        [(0,2,1),(0,1,3),(1,2,3),(2,0,3)])
    ob.data.materials.append(mat)
    ob.data.uv_layers.new(name='UVMap')
    ob.data.polygons.foreach_set('use_smooth',[True]*4)
    ob.data.update()
    normals=np.asarray([tuple(p.normal) for p in ob.data.polygons for i in p.loop_indices],float)
    normals+=np.array([.013,-.017,.009])
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    ob.data.normals_split_custom_set(normals.tolist())
    D.objects[ob.name]=ob
    objects.append(ob)
def snapshot(objects):
    out={}
    for ob in objects:
        normals=np.asarray([tuple(n.vector) for n in ob.data.corner_normals],float)
        for p in ob.data.polygons:
            key=tuple(tuple(ob.data.vertices[i].co) for i in p.vertices)
            out[key]=normals[list(p.loop_indices)]
    return out
before=snapshot(objects)
result=HM.merge_static_masonry(D,objects,max_faces=490,max_span_m=12)
after=snapshot(result['objects'])
delta=max(float(np.abs(before[k]-after[k]).max()) for k in before)
ok=before.keys()==after.keys() and delta==0
row=dict(pass_=ok,corner_normal_max_abs_delta=delta,custom_normals_present=all(o.data.has_custom_normals for o in result['objects']),stats=result['stats'])
with open(os.path.dirname(__file__)+'/custom_normals.json','w') as f:json.dump(row,f,indent=2)
print(f"GATE: MASONRY_CUSTOM_NORMALS {'PASS' if ok else 'FAIL'} exact delta {delta:g}",flush=True)
sys.exit(0 if ok else 1)
