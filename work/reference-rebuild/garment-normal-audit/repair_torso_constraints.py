"""Constraint-only repair of the already-rendered torso candidate. No new fairing."""
import bpy,json,pathlib,numpy as np,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-normal-audit';D=R/'proof/full-visual-overhaul/character-pose-data-1/poses';S=R/'work/full-visual-overhaul/garment-coverage/sleeve-geometry-9';REPORT={}
exec((W/'fair_existing_torso.py').read_text().split("for sex in ('Male','Female'):")[0])
for sex in ('Male','Female'):
    label=sex.lower()+'_intro';data=json.loads((D/(label+'.json')).read_text());body,top=data['parts'];source=json.loads((S/(label+'.json')).read_text())
    profile=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());anchor=next(a for a in profile['anchors'] if a['shape']==label)
    base=np.array(profile['vertices']).reshape(-1,3);oldDelta=np.array(anchor['deltas']).reshape(-1,3);oldNormalDelta=np.array(anchor['normalDeltas']).reshape(-1,3);file=W/f'{sex.lower()}_torso_fairing_target.json';out=json.loads(file.read_text())
    weights=np.array(source['parts'][1]['weights']).reshape(-1,4);bodyWeights=np.array(source['parts'][0]['weights']).reshape(-1,4)
    before,mix=pose(top,base+oldDelta,weights);after,_=pose(top,base+np.array(out['deltas']).reshape(-1,3),weights);initial=after.copy();bp,_=pose(body,arr(body,'vertices',3),bodyWeights);tt=arr(top,'triangles',3).astype(int);bt=arr(body,'triangles',3).astype(int);tm=np.array(top['rendererToRoot']).reshape(4,4)
    bv=BVHTree.FromPolygons([Vector(v) for v in bp],[tuple(t) for t in bt],all_triangles=True)
    def signed(v):
        hit,n,_,_=bv.find_nearest(Vector(v));return float((Vector(v)-hit).dot(n)) if hit is not None else 0
    originalSigned=np.array([signed(p) for p in before]);changed=np.linalg.norm(after-before,axis=1)>1e-8
    groups={}
    for i,p in enumerate(base):groups.setdefault(tuple(np.round(p*100000).astype(int)),[]).append(i)
    # UV aliases form one physical seam. Constraint rollback must apply to
    # every copy, otherwise a repaired single triangle opens the shared edge.
    aliases=[g for g in groups.values() if len(g)>1]
    aliasRepairs=0
    for g in aliases:
        displacement=after[g]-before[g]
        if np.max(np.linalg.norm(displacement-displacement[0],axis=1))>1e-7:
            conservative=displacement[np.argmin(np.linalg.norm(displacement,axis=1))]
            after[g]=before[g]+conservative;aliasRepairs+=len(g)
    edges=np.unique(np.sort(np.concatenate([tt[:,[0,1]],tt[:,[1,2]],tt[:,[2,0]]]),axis=1),axis=0);neighbors=[set() for _ in range(len(base))]
    for a,b in edges:neighbors[a].add(b);neighbors[b].add(a)
    for g in aliases:
        joined=set(g).union(*(neighbors[i] for i in g))
        for i in g:neighbors[i].update(joined-{i})
    _,oldArea=normals(before,tt);aLength=np.linalg.norm(oldArea,axis=1);rolled=set();clamped=set()
    for cycle in range(8):
        _,area=normals(after,tt);flip=np.where((aLength>1e-7)&(np.sum(oldArea*area,axis=1)<0))[0]
        if len(flip):
            seed=set(tt[flip].ravel().tolist());ring=set(seed);fade={i:0. for i in seed}
            for weight in (.35,.7):
                nextRing=set().union(*(neighbors[i] for i in ring))-set(fade)
                for i in nextRing:fade[i]=weight
                ring=nextRing
            for i,factor in fade.items():
                if changed[i]:after[i]=before[i]+(after[i]-before[i])*factor;rolled.add(i)
        bad=[]
        for i in np.where(changed & (originalSigned>0))[0]:
            # Retain strictly positive clearance, and at least .2mm where the
            # accepted original had that room. Candidate->source rollback is
            # guaranteed to converge because Body/source poses are identical.
            minimum=min(.0002,originalSigned[i]*.5)
            if signed(after[i])<minimum:
                delta=after[i]-before[i];factor=1.
                for n in range(24):
                    factor*=.5;point=before[i]+delta*factor
                    if signed(point)>=minimum:after[i]=point;break
                else:after[i]=before[i]
                clamped.add(int(i));bad.append(int(i))
        _,area=normals(after,tt);flip=np.where((aLength>1e-7)&(np.sum(oldArea*area,axis=1)<0))[0]
        if not len(flip) and not bad:break
    finalSigned=np.array([signed(p) for p in after]);newIntersections=np.where((originalSigned>0)&(finalSigned<=0)&changed)[0]
    assert len(newIntersections)==0, f'{sex} new Body intersections {newIntersections}'
    assert len(flip)==0, f'{sex} triangle reversals {flip}'
    moved=np.linalg.norm(after-before,axis=1);pinned=~changed;after[pinned]=before[pinned]
    local=xf(np.linalg.inv(tm),after);hom=np.column_stack([local,np.ones(len(local))]);bindTarget=np.einsum('nij,nj->ni',np.linalg.inv(mix),hom)[:,:3];delta=bindTarget-base;delta[pinned]=oldDelta[pinned]
    normal,_=normals(after,tt);normalLocal=normal@tm[:3,:3];bindNormals=np.einsum('nij,nj->ni',np.linalg.inv(mix[:,:3,:3]),normalLocal);bindNormals/=np.maximum(np.linalg.norm(bindNormals,axis=1)[:,None],1e-10);nd=bindNormals-np.array(profile['normals']).reshape(-1,3);nd[pinned]=oldNormalDelta[pinned]
    out.update({'deltas':delta.ravel().tolist(),'normalDeltas':nd.ravel().tolist(),'meaningfulTriangleFlipCount':int(len(flip)),'triangleReversals':[],'newBodyIntersectionCount':int(len(newIntersections)),'minimumRemainingPositiveClearanceMetres':float(finalSigned[changed&(originalSigned>0)].min()),'sourceExistingNonpositiveClearanceVertices':int((originalSigned<=0).sum()),'remainingNonpositiveClearanceVertices':int((finalSigned<=0).sum()),'rollbackVertices':len(rolled),'pairedUvAliasConstraintVertices':aliasRepairs,'clearanceClampVertices':len(clamped),'maximumConstraintRepairDisplacementMetres':float(np.linalg.norm(after-initial,axis=1).max()),'maximumPosedDisplacementMetres':float(moved.max()),'fixedVertexErrorMetres':float(np.linalg.norm(after[pinned]-before[pinned],axis=1).max()),'outsideChangedFieldPositionDeltaError':float(np.max(np.abs(delta[pinned]-oldDelta[pinned]))),'outsideChangedFieldNormalDeltaError':float(np.max(np.abs(nd[pinned]-oldNormalDelta[pinned]))),'status':'WORK-ONLY SOURCE CANDIDATE; constraint repair complete; root actual visual review required'})
    file.write_text(json.dumps(out,separators=(',',':')));REPORT[sex]={k:v for k,v in out.items() if k not in ('deltas','normalDeltas')};print('CONSTRAINTS',REPORT[sex],flush=True)
    bpy.ops.wm.read_factory_settings(use_empty=True);skin=mat('Existing Body',(.57,.29,.17));cloth=mat('Plain unchanged garment material',(.70,.105,.060) if sex=='Male' else (.35,.53,.05))
    for offset,p,name in [(0,before,'BEFORE'),(.85,after,'AFTER')]:mesh(name+'_Body',bp,bt,skin,offset);mesh(name+'_Top',p,tt,cloth,offset)
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1600;sc.render.resolution_y=950;sc.render.resolution_percentage=100
    sc.world=bpy.data.worlds.new('Same plain studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';target=Vector((.425,0,1.25))
    for pos,power,size in [((-.7,-2,3),420,3),((2,-1,1.7),160,3)]:
        bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(.425,-3.8,1.38));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=1.85;sc.camera=cam
    for angle,pos in [('front',(.425,-3.8,1.38)),('threequarter',(1.45,-3.8,1.38))]:
        cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(W/f'{sex.lower()}_torso_fairing_{angle}.png');bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_LocalizedTorsoFairing.blend'))
    (W/'torso-fairing-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
