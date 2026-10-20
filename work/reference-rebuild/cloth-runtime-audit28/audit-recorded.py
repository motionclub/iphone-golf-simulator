"""Read-only exact current-profile reconstruction on existing actual DQ matrices."""
from pathlib import Path
import json,numpy as np,hashlib
R=Path.cwd();O=R/'work/reference-rebuild/cloth-runtime-audit28';D=R/'proof/reference-rebuild/gusset-dq1';p=json.loads((R/'Unity/Assets/Resources/Tennis/Correctives/UnderarmGusset_Female_Full.json').read_text());sleeve=json.loads((R/'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_Female.json').read_text())
helper=(R/'work/reference-rebuild/gusset-actual-repair/check_dq.py').read_text();exec(helper[helper.index('def arr'):helper.index('src=arr')])
src=arr(p,'sourceVertices',3);oi=arr(p,'sourceIndices',3).astype(int);ow=arr(p,'sourceWeights',3);bi=arr(p,'boneIndices',4).astype(int);bw=arr(p,'weights',4);free=np.array(p['freeVertices']);aliases=np.array(p['aliases']);strength=np.zeros(p['vertexCount']);strength[free]=p['cageStrengths'];deltas=np.array([a['deltas']for a in sleeve['anchors']]).reshape(-1,len(src),3);anchorIds={a['shape']:i for i,a in enumerate(sleeve['anchors'])}
aliascount=np.bincount(aliases);groups={}
for i,g in enumerate(aliases):groups.setdefault(int(g),[]).append(i)
def expand(v):return (v[oi]*ow[...,None]).sum(1)
def state(m,weights,useDQ):
 v=expand(src+np.einsum('k,kni->ni',weights,deltas));raw=skin(v,bi,bw,m)
 if not useDQ:return raw
 proposed=dq(v,bi,bw,m);delta=np.zeros_like(v);delta[free]=(proposed-raw)[free]*strength[free,None]
 sums=np.zeros((len(aliascount),3));np.add.at(sums,aliases[free],delta[free]);delta[free]=sums[aliases[free]]/aliascount[aliases[free],None];return raw+delta
rows=[]
for matrix in sorted((D/'matrices').glob('female*.json')):
 snap=json.loads((D/'poses'/matrix.name).read_text());top=snap['parts'][1];part=json.loads(matrix.read_text())['parts'][1];m=rootmat(part);weights=np.zeros(len(deltas))
 for name,w in zip(part['shapeNames'],part['shapeWeights']):
  if name.startswith('TailoredSleeve_'):weights[anchorIds[name[len('TailoredSleeve_'):]]]=w*.01
 lbsOff=state(m,weights*0,False);lbsOn=state(m,weights,False);dqOff=state(m,weights*0,True);dqOn=state(m,weights,True)
 actual=arr(top,'posedVertices',3);rt=arr(top,'rendererToRoot',4);actual=actual@rt[:3,:3].T+rt[:3,3]
 def stats(delta):
  d=np.linalg.norm(delta[free],axis=1)*1000;return {'maxMm':float(d.max()),'p95Mm':float(np.percentile(d,95)),'verticesOver10mm':int((d>10).sum())}
 def gaps(pos):return max(float(np.linalg.norm(pos[g]-pos[g[0]],axis=1).max())for g in groups.values())*1000
 row={'sample':matrix.stem,'anchorWeightsPercent':{name:float(w*100)for name,w in zip(anchorIds,weights)if w!=0},'totalAnchorPercent':float(weights.sum()*100),'dqOnVersusActual':stats(dqOn-actual),'anchorEffectWithLBS':stats(lbsOn-lbsOff),'anchorEffectWithDQ':stats(dqOn-dqOff),'DQEffectNoAnchors':stats(dqOff-lbsOff),'DQEffectWithAnchors':stats(dqOn-lbsOn),'maxAliasGapMmLBS':gaps(lbsOn),'maxAliasGapMmDQ':gaps(dqOn)}
 rows.append(row)
# Dense physical binding equality ignores slot ordering / duplicate zero slots.
def dense(indices,weights):
 v=np.zeros((len(indices),len(p['bones'])));np.add.at(v,(np.arange(len(indices))[:,None],indices),weights);return v
canonical=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json').read_text())['parts'][1];pw=dense(bi,bw);cw=dense(arr(canonical,'indices',4).astype(int),arr(canonical,'weights',4));error=np.abs(pw[:len(src)]-cw).sum(1);freemask=np.zeros(len(aliases),bool);freemask[free]=True
aliasWeights=max(float(np.abs(pw[g]-pw[g[0]]).sum(1).max())for g in groups.values());mixed=sum(any(freemask[g])and not all(freemask[g])for g in groups.values())
report={'source_bindings_vs_captured_canonical':{'changedVertices':int((error>1e-6).sum()),'maxL1':float(error.max())},'alias_bindings_maxL1':aliasWeights,'mixed_free_nonfree_alias_groups':int(mixed),'samples':rows,'algorithm':'same recorded bones/shapes, exact profile weights; LBS and runtime DQ four CPU controls; no new geometry/render','noUnityOrGpu':True}
(O/'recorded-contract.json').write_text(json.dumps(report,indent=2)+'\n')
for x in rows:print(x['sample'],'anchors',round(x['totalAnchorPercent'],2),'actualerr',round(x['dqOnVersusActual']['maxMm'],4),'anchLBS',round(x['anchorEffectWithLBS']['maxMm'],2),'anchDQ',round(x['anchorEffectWithDQ']['maxMm'],2),'DQnoanch',round(x['DQEffectNoAnchors']['maxMm'],2),'aliasgap',round(x['maxAliasGapMmDQ'],4))
