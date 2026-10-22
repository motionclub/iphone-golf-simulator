"""Read-only diagnosis of actual control body/shirt evaluation."""
import json,pathlib,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-normal-audit';D=R/'proof/reference-rebuild/character-cloth14-control/poses';report={}
def arr(p,k,n):return np.array(p[k],float).reshape(-1,n)
def xf(m,p):return p@m[:3,:3].T+m[:3,3]
def pose(part,v):
    ids=arr(part,'indices',4).astype(int);w=arr(part,'weights',4);skin=np.array(part['skinMatrices']).reshape(-1,4,4);mix=np.sum(skin[ids]*w[:,:,None,None],axis=1);q=np.einsum('nij,nj->ni',mix,np.column_stack([v,np.ones(len(v))]))[:,:3];return xf(np.array(part['rendererToRoot']).reshape(4,4),q)
def s(a,b,x):t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
for label in ['male_Serve_1','male_Forehand_1']:
    snap=json.loads((D/(label+'.json')).read_text());body,top=snap['parts'][:2];bp=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'posedVertices',3));tp=xf(np.array(top['rendererToRoot']).reshape(4,4),arr(top,'posedVertices',3));tb=xf(np.array(top['rendererToRoot']).reshape(4,4),arr(top,'vertices',3));plain=pose(top,arr(top,'vertices',3));bt=arr(body,'triangles',3).astype(int);bvh=BVHTree.FromPolygons([Vector(p) for p in bp],[tuple(t) for t in bt],all_triangles=True)
    bone=np.array(top['rendererToRoot']).reshape(4,4)[None,:,:]@np.array(top['skinMatrices']).reshape(-1,4,4)@np.linalg.inv(np.array(top['bindposes']).reshape(-1,4,4));name=top['bones'];directions=[]
    for a,b in segments:
        v=bone[name.index(b),:3,3]-bone[name.index(a),:3,3];directions.append(v/np.linalg.norm(v))
    feature=np.array([directions[i]@directions[j] for i in range(8) for j in range(i+1,8)])
    profile=json.loads((W/'before-production/SleeveFit_Male.json').read_text());dist=np.array([np.mean((feature-np.array(a['feature']))**2) for a in profile['anchors']]);weight=1/np.maximum(dist,1e-8)**2;confidence=1-s(.025,.30,dist.min());weight*=confidence/weight.sum();delta=sum((np.array(a['deltas']).reshape(-1,3)*w for a,w in zip(profile['anchors'],weight)));predict=pose(top,arr(top,'vertices',3)+delta);error=np.linalg.norm(predict-tp,axis=1)
    ids=arr(top,'indices',4).astype(int);weights=arr(top,'weights',4);chosen=np.where((tb[:,1]>1.08)&(tb[:,1]<1.38)&(np.abs(tb[:,0])>.065)&(np.abs(tb[:,0])<.24))[0];samples=[]
    for i in chosen:
        hit,n,_,distance=bvh.find_nearest(Vector(tp[i]));signed=float((Vector(tp[i])-hit).dot(n));rawHit,rawN,_,_=bvh.find_nearest(Vector(plain[i]));rawSigned=float((Vector(plain[i])-rawHit).dot(rawN))
        if signed<-.001 and distance<.06:
            samples.append({'vertex':int(i),'bindRoot':tb[i].tolist(),'posedRoot':tp[i].tolist(),'signedBodyClearanceMm':signed*1000,'uncorrectedClearanceMm':rawSigned*1000,'correctiveDisplacementMm':float(np.linalg.norm(tp[i]-plain[i])*1000),'boneWeights':{name[k]:float(w) for k,w in zip(ids[i],weights[i]) if w>.00001}})
    samples.sort(key=lambda i:i['signedBodyClearanceMm'])
    report[label]={'bakeOracleMaxMm':max(body['bakeOracleMaxMetres'],top['bakeOracleMaxMetres'])*1000,'profileReconstructionMaxMm':float(error.max()*1000),'nearestFeatureDistance':float(dist.min()),'correctiveConfidence':float(confidence),'activeAnchors':[{ 'shape':a['shape'],'weightPercent':float(w*100),'featureDistance':float(d)} for a,w,d in zip(profile['anchors'],weight,dist) if w>.005],'axillaSideSampleCount':len(chosen),'clothVerticesMoreThan1mmInsideBody':len(samples),'worstSamples':samples[:8],'limitations':'signed nearest samples include inside lining; geometric mechanism only, actual screenshots establish visibility','rigRightUpperArm':bone[name.index('RightUpperArm'),:3,3].tolist()}
    print(label,report[label],flush=True)
(W/'stroke-coverage-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
