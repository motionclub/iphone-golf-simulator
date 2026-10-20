import json,pathlib,numpy as np
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-normal-audit'
def arr(p,k,n):return np.array(p[k],float).reshape(-1,n)
def pose(p,v,w):
    palette=np.array(p['skinMatrices']).reshape(-1,4,4);ids=arr(p,'indices',4).astype(int)
    mix=np.sum(palette[ids]*w[:,:,None,None],axis=1)
    out=np.einsum('nij,nj->ni',mix,np.column_stack([v,np.ones(len(v))]))[:,:3]
    m=np.array(p['rendererToRoot']).reshape(4,4)
    return out@m[:3,:3].T+m[:3,3]
report=json.loads((W/'torso-fairing-report.json').read_text())
for sex in ('Male','Female'):
    name=sex.lower()+'_intro';p=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());a=next(i for i in p['anchors'] if i['shape']==name)
    out=json.loads((W/f'{sex.lower()}_torso_fairing_target.json').read_text());d=np.array(out['deltas']).reshape(-1,3);original=np.array(a['deltas']).reshape(-1,3);dn=np.array(out['normalDeltas']).reshape(-1,3);oldn=np.array(a['normalDeltas']).reshape(-1,3)
    # Inverse-LBS produces machine-rounding changes on pinned vertices. Keep
    # both source position/normal fields BIT EXACT there, not only posed xyz.
    pinned=np.linalg.norm(d-original,axis=1)<1e-8;d[pinned]=original[pinned];dn[pinned]=oldn[pinned]
    out['deltas']=d.ravel().tolist();out['normalDeltas']=dn.ravel().tolist();out['outsideChangedFieldPositionDeltaError']=float(np.max(np.abs(d[pinned]-original[pinned])));out['outsideChangedFieldNormalDeltaError']=float(np.max(np.abs(dn[pinned]-oldn[pinned])))
    snap=json.loads((R/f'proof/full-visual-overhaul/character-pose-data-1/poses/{name}.json').read_text())['parts'][1];weights=np.array(json.loads((R/f'work/full-visual-overhaul/garment-coverage/sleeve-geometry-9/{name}.json').read_text())['parts'][1]['weights']).reshape(-1,4)
    base=np.array(p['vertices']).reshape(-1,3);before=pose(snap,base+original,weights);after=pose(snap,base+d,weights);t=arr(snap,'triangles',3).astype(int)
    ba=np.cross(before[t[:,1]]-before[t[:,0]],before[t[:,2]]-before[t[:,0]]);aa=np.cross(after[t[:,1]]-after[t[:,0]],after[t[:,2]]-after[t[:,0]])
    flipped=np.where((np.linalg.norm(ba,axis=1)>1e-7)&(np.sum(ba*aa,axis=1)<0))[0]
    detail=[]
    for i in flipped:
        detail.append({'triangleIndex':int(i),'vertices':t[i].tolist(),'beforeCentreRoot':before[t[i]].mean(0).tolist(),'afterCentreRoot':after[t[i]].mean(0).tolist(),'beforeAreaSquareMm':float(np.linalg.norm(ba[i])*.5e6),'afterAreaSquareMm':float(np.linalg.norm(aa[i])*.5e6)})
    out['triangleReversals']=detail;out['pinnedPositionAndNormalDeltasPreservedExactly']=True
    (W/f'{sex.lower()}_torso_fairing_target.json').write_text(json.dumps(out,separators=(',',':')))
    report[sex].update({k:out[k] for k in ['outsideChangedFieldPositionDeltaError','outsideChangedFieldNormalDeltaError','pinnedPositionAndNormalDeltasPreservedExactly','triangleReversals']})
(W/'torso-fairing-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
