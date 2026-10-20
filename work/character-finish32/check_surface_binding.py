import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
w=Path('work/character-finish32');d=json.loads((w/'surface/poses/male_intro.json').read_text());b=d['parts'][0];t=next(p for p in d['parts'] if p['name']=='Kit_Top');BP=np.array(b['vertices']).reshape(-1,3);TP=np.array(t['vertices']).reshape(-1,3);BN=np.array(b['normals']).reshape(-1,3);bw=np.array(b['weights']).reshape(-1,4);bi=np.array(b['indices']).reshape(-1,4);tw=np.array(t['weights']).reshape(-1,4);ti=np.array(t['indices']).reshape(-1,4);kd=KDTree(len(BP))
for j,p in enumerate(BP):kd.insert(Vector(p),j)
kd.balance();rows=[]
for i,p in enumerate(TP):
 if not .18<abs(p[0])<.32 or not 1.20<p[2]<1.38:continue
 _,j,dist=kd.find(Vector(p));err=sum(abs(sum(tw[i][ti[i]==k])-sum(bw[j][bi[j]==b['bones'].index(n)])) for k,n in enumerate(t['bones']) if n in b['bones']);rows.append([i,j,dist,err])
a=np.array(rows);print('binding',np.quantile(a[:,3],[0,.5,.9,.99,1]),'rows',len(a),flush=True)
for clip in [3,4,8]:
 d=json.loads((w/f'collision-poses/matrices/male_SliceApproach_{clip}.json').read_text());bm=np.array(d['parts'][0]['skinMatrices']).reshape(-1,4,4);mp={n:bm[j] for j,n in enumerate(b['bones'])};M=(np.array([mp[n] for n in t['bones']])[ti]*tw[:,:,None,None]).sum(1);BM=(bm[bi]*bw[:,:,None,None]).sum(1);S=np.linalg.svd(M[:,:3,:3],compute_uv=False);BS=np.linalg.svd(BM[:,:3,:3],compute_uv=False);print('pose',clip,'minSingular',np.quantile(S[a[:,0].astype(int),-1],[0,.1,.5,.9,1]),flush=True)
print('worst',a[np.argsort(-a[:,3])[:8]],flush=True)
