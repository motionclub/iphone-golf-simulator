"""One localized fairing of the existing full sleeve9 IntroWave target.
No rebuild. Existing topology, skin palette, rig, skin weights and bind basis
are retained. Only one authored posed garment target is locally relaxed.
"""
import bpy,pathlib,json,numpy as np,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-normal-audit';REPORT={}
D=R/'proof/full-visual-overhaul/character-pose-data-1/poses';S=R/'work/full-visual-overhaul/garment-coverage/sleeve-geometry-9'
def arr(p,k,n):return np.array(p[k],float).reshape(-1,n)
def xf(m,p):return p@m[:3,:3].T+m[:3,3]
def smooth(a,b,x):t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def pose(part,p,weights):
    palette=np.array(part['skinMatrices']).reshape(-1,4,4);ids=arr(part,'indices',4).astype(int)
    mix=np.sum(palette[ids]*weights[:,:,None,None],axis=1)
    local=np.einsum('nij,nj->ni',mix,np.column_stack([p,np.ones(len(p))]))[:,:3]
    return xf(np.array(part['rendererToRoot']).reshape(4,4),local),mix
def normals(p,t):
    n=np.zeros_like(p);area=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
    for j in range(3):np.add.at(n,t[:,j],area)
    return n/np.maximum(1e-10,np.linalg.norm(n,axis=1)[:,None]),area
def mat(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.76;p.inputs['Specular IOR Level'].default_value=.15;return m
def mesh(name,p,t,m,offset):
    q=np.column_stack([p[:,0]+offset,-p[:,2],p[:,1]]);me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],t.tolist());me.update();me.materials.append(m);ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    for f in me.polygons:f.use_smooth=True
    return ob

for sex in ('Male','Female'):
    label=sex.lower()+'_intro';data=json.loads((D/(label+'.json')).read_text());body,top=data['parts']
    profile=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());source=json.loads((S/(label+'.json')).read_text());anchor=next(a for a in profile['anchors'] if a['shape']==label)
    base=np.array(profile['vertices']).reshape(-1,3);oldDelta=np.array(anchor['deltas']).reshape(-1,3)
    weights=np.array(source['parts'][1]['weights']).reshape(-1,4);bodyWeights=np.array(source['parts'][0]['weights']).reshape(-1,4)
    before,mix=pose(top,base+oldDelta,weights);bp,_=pose(body,arr(body,'vertices',3),bodyWeights)
    tt=arr(top,'triangles',3).astype(int);bt=arr(body,'triangles',3).astype(int);tm=np.array(top['rendererToRoot']).reshape(4,4);rootBase=xf(tm,base)
    bv=BVHTree.FromPolygons([Vector(v) for v in bp],[tuple(t) for t in bt],all_triangles=True)
    originalNormals,originalArea=normals(before,tt)
    # Weld only the smoothing field across original source UV splits. The
    # exported vertex/index arrays are untouched.
    group={};parent=[]
    for p in base:parent.append(group.setdefault(tuple(np.round(p*100000).astype(int)),len(group)))
    parent=np.array(parent);count=len(group);sizes=np.bincount(parent)
    points=np.zeros((count,3));np.add.at(points,parent,before);points/=sizes[:,None];initial=points.copy()
    edges=np.unique(np.sort(np.concatenate([parent[tt[:,[0,1]]],parent[tt[:,[1,2]]],parent[tt[:,[2,0]]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
    # Find the actual main sewn shell. Detached collar/placket/button pieces
    # never participate, and connected placket centre is explicitly protected.
    components=np.arange(count)
    def find(i):
        while components[i]!=i:components[i]=components[components[i]];i=components[i]
        return i
    for a,b in edges:
        a=find(a);b=find(b)
        if a!=b:components[b]=a
    comp=np.array([find(i) for i in range(count)]);labels,counts=np.unique(comp,return_counts=True);main=labels[np.argmax(counts)]
    armIDs=[top['bones'].index(n) for n in ['LeftUpperArm','RightUpperArm','LeftShoulder','RightShoulder','LeftLowerArm','RightLowerArm'] if n in top['bones']]
    indices=arr(top,'indices',4).astype(int);arm=(weights*np.isin(indices,armIDs)).sum(1)
    x=np.abs(rootBase[:,0]);y=rootBase[:,1];upper=1.34 if sex=='Male' else 1.30
    field=smooth(1.045,1.070,y)*(1-smooth(upper-.045,upper,y))*(1-smooth(.135,.175,x))*(1-smooth(.15,.45,arm))
    field[(rootBase[:,2]>.025)&(x<.023)&(y>1.115)]=0
    field[comp[parent]!=main]=0
    mask=np.zeros(count);np.minimum.at(mask+1,parent,field) if False else None
    # Every duplicate shares the most conservative constraint, so a pinned
    # seam/collar instance cannot be moved by another UV instance.
    mask[:]=1;np.minimum.at(mask,parent,field)
    selected=np.where(mask>.001)[0];fixed=mask<=.001
    # Retain accepted body clearance up to10mm on outward garment panels.
    # This avoids pulling smooth cloth through skin while allowing excessive
    # local protrusions to relax toward an even fitted shell.
    minimum={}
    for i in selected:
        hit,n,_,dist=bv.find_nearest(Vector(initial[i]))
        if hit is not None and dist<.055:
            signed=float((Vector(initial[i])-hit).dot(n))
            if signed>0:minimum[int(i)]=min(.010,signed)
    ea,eb=edges[:,0],edges[:,1]
    ew=1/np.maximum(np.linalg.norm(initial[ea]-initial[eb],axis=1),.001)
    degree=np.zeros(count);np.add.at(degree,ea,ew);np.add.at(degree,eb,ew)
    for iteration in range(60):
        avg=np.zeros_like(points);np.add.at(avg,ea,points[eb]*ew[:,None]);np.add.at(avg,eb,points[ea]*ew[:,None]);avg/=np.maximum(degree[:,None],1e-10)
        points+=(avg-points)*(.28*mask[:,None])
        delta=points-initial;length=np.linalg.norm(delta,axis=1);cap=length>.022;points[cap]=initial[cap]+delta[cap]*(.022/length[cap])[:,None]
        for i,gap in minimum.items():
            hit,n,_,dist=bv.find_nearest(Vector(points[i]))
            if hit is not None:
                signed=float((Vector(points[i])-hit).dot(n))
                if signed<gap:points[i]+=np.array(n)*(gap-signed)
        points[fixed]=initial[fixed]
    after=points[parent];after[field<=.001]=before[field<=.001]
    moved=np.linalg.norm(after-before,axis=1);pinError=float(moved[field<=.001].max())
    assert pinError<1e-12
    newNormals,newArea=normals(after,tt);areaMagnitude=np.linalg.norm(originalArea,axis=1);normalDot=np.sum(originalArea*newArea,axis=1)
    flips=int(((areaMagnitude>1e-7)&(normalDot<0)).sum())
    minimumLoss=0
    for i,gap in minimum.items():
        hit,n,_,_=bv.find_nearest(Vector(points[i]));signed=float((Vector(points[i])-hit).dot(n));minimumLoss=max(minimumLoss,gap-signed)
    # Static editable target and inverse-LBS data; no production profile edits.
    targetLocal=xf(np.linalg.inv(tm),after);hom=np.column_stack([targetLocal,np.ones(len(targetLocal))]);bindTarget=np.einsum('nij,nj->ni',np.linalg.inv(mix),hom)[:,:3]
    newDelta=bindTarget-base
    targetNormalLocal=newNormals@tm[:3,:3]
    bindNormals=np.einsum('nij,nj->ni',np.linalg.inv(mix[:,:3,:3]),targetNormalLocal);bindNormals/=np.maximum(np.linalg.norm(bindNormals,axis=1)[:,None],1e-10)
    out={'sex':sex,'shape':label,'vertexCount':len(base),'deltas':newDelta.ravel().tolist(),'normalDeltas':(bindNormals-np.array(profile['normals']).reshape(-1,3)).ravel().tolist(),'source':'existing sleeve9 full100 envelope','vertexPositionsChangeOnlyWithinTorsoField':True,'fixedVertexErrorMetres':pinError,'movedVertices':int((moved>1e-6).sum()),'maximumPosedDisplacementMetres':float(moved.max()),'clearanceLossMaxMetres':float(minimumLoss),'meaningfulTriangleFlipCount':flips,'status':'WORK-ONLY SOURCE CANDIDATE; root visual review required'}
    (W/f'{sex.lower()}_torso_fairing_target.json').write_text(json.dumps(out,separators=(',',':')))
    bpy.ops.wm.read_factory_settings(use_empty=True);skin=mat('Existing Body',(.57,.29,.17));cloth=mat('Plain unchanged garment material',(.70,.105,.060) if sex=='Male' else (.35,.53,.05))
    for offset,p,name in [(0,before,'BEFORE'),(.85,after,'AFTER')]:mesh(name+'_Body',bp,bt,skin,offset);mesh(name+'_Top',p,tt,cloth,offset)
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1600;sc.render.resolution_y=950;sc.render.resolution_percentage=100
    sc.world=bpy.data.worlds.new('Same plain studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    target=Vector((.425,0,1.25))
    for pos,power,size in [((-.7,-2,3),420,3),((2,-1,1.7),160,3)]:
        bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.425,-3.8,1.38));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=1.85;sc.camera=cam
    for angle,pos in [('front',(.425,-3.8,1.38)),('threequarter',(1.45,-3.8,1.38))]:
        cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(W/f'{sex.lower()}_torso_fairing_{angle}.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_LocalizedTorsoFairing.blend'))
    REPORT[sex]={k:v for k,v in out.items() if k not in ('deltas','normalDeltas')};(W/'torso-fairing-report.json').write_text(json.dumps(REPORT,indent=2)+'\n');print('TORSO_FAIRING',REPORT[sex])
