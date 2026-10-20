"""Read-only states of the existing sleeve9 IntroWave envelope.
Exact same body, skin weights, source triangles and bind vertices at each
column; only the existing authored corrective weight differs. No new sculpt.
"""
import bpy, pathlib, json, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=pathlib.Path.cwd(); W=R/'work/reference-rebuild/garment-normal-audit'; W.mkdir(exist_ok=True)
D=R/'proof/full-visual-overhaul/character-pose-data-1/poses'
S=R/'work/full-visual-overhaul/garment-coverage/sleeve-geometry-9'
report={}

def arr(p,k,n):return np.array(p[k],float).reshape(-1,n)
def transform(m,p):return p@m[:3,:3].T+m[:3,3]
def pose(part,positions,weights):
    palette=np.array(part['skinMatrices']).reshape(-1,4,4); ids=arr(part,'indices',4).astype(int)
    mixed=np.sum(palette[ids]*weights[:,:,None,None],axis=1)
    local=np.einsum('nij,nj->ni',mixed,np.column_stack([positions,np.ones(len(positions))]))[:,:3]
    return transform(np.array(part['rendererToRoot']).reshape(4,4),local)
def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.76;p.inputs['Specular IOR Level'].default_value=.15
    return m
def object(name,p,tri,m,offset):
    q=np.column_stack([p[:,0]+offset,-p[:,2],p[:,1]])
    me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],tri.tolist());me.update();me.materials.append(m)
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    for f in me.polygons:f.use_smooth=True
    return ob

for sex in ('Male','Female'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    label=sex.lower()+'_intro';data=json.loads((D/(label+'.json')).read_text());body,top=data['parts']
    profile=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text())
    authored=json.loads((S/(label+'.json')).read_text());anchor=next(a for a in profile['anchors'] if a['shape']==label)
    base=np.array(profile['vertices']).reshape(-1,3);dv=np.array(anchor['deltas']).reshape(-1,3)
    topWeights=np.array(authored['parts'][1]['weights']).reshape(-1,4)
    bodyWeights=np.array(authored['parts'][0]['weights']).reshape(-1,4)
    bodyPose=pose(body,arr(body,'vertices',3),bodyWeights)
    bt=arr(body,'triangles',3).astype(int);tt=arr(top,'triangles',3).astype(int)
    bvh=BVHTree.FromPolygons([Vector(q) for q in bodyPose],[tuple(q) for q in bt],all_triangles=True)
    bodyMat=material('Existing Body',(.57,.29,.17));clothMat=material('Plain existing polo',(.70,.105,.060) if sex=='Male' else (.35,.53,.05))
    states=[]
    for column,weight in enumerate((0,.5,1)):
        positions=pose(top,base+weight*dv,topWeights)
        signed=[]
        # Measure only the main torso shell, away from neck/cuff contact and
        # excluding source turned lining by its closest skin-facing direction.
        rootBase=transform(np.array(top['rendererToRoot']).reshape(4,4),base)
        for i in np.where((rootBase[:,1]>1.055)&(rootBase[:,1]<1.34)&(np.abs(rootBase[:,0])<.17))[0]:
            hit,n,_,dist=bvh.find_nearest(Vector(positions[i]))
            if hit is not None and dist<.04:signed.append(float((Vector(positions[i])-hit).dot(n)))
        signed=np.array(signed)
        offset=column*.72
        object(f'Body_{weight}',bodyPose,bt,bodyMat,offset)
        object(f'Top_envelope_{weight}',positions,tt,clothMat,offset)
        states.append({'envelopeWeight':weight,'comparedTorsoVertices':len(signed),'penetrationsOver1mm':int((signed<-.001).sum()),'maximumPenetrationMetres':float(max(0,-signed.min())) if len(signed) else 0,'posedSourceVertices':len(positions),'poseBounds':[positions.min(0).tolist(),positions.max(0).tolist()]})
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True
    sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1800;sc.render.resolution_y=850;sc.render.resolution_percentage=100
    sc.world=bpy.data.worlds.new('Plain garment review');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    target=Vector((.72,0,1.25))
    for pos,power,size in [((-.7,-2.0,3),420,3),((2,-1,1.7),160,3)]:
        bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.72,-3.8,1.38));cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.14;sc.camera=cam
    sc.render.filepath=str(W/f'{sex.lower()}_envelope_0_50_100.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_ExistingEnvelopeComparison.blend'))
    report[sex]={'columns':'left0, middle50%, right100% existing sleeve9 envelope','sameBindVerticesNormalsTrianglesUVWeightsRig':True,'poses':states,'warning':'Nearest signed samples include garment linings; visual body-poke review remains required. No final coverage PASS.'}
    (W/'existing-envelope-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print('EXISTING_ENVELOPE',sex,states)
