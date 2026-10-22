import argparse,json,math
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('snapshot');p.add_argument('--out');a=p.parse_args()
d=json.loads(Path(a.snapshot).read_text());axes=np.array([d['right'],d['up'],d['forward']],float).T
bp=np.array(d['body']['positions'],float).reshape(-1,3)@axes
bt=np.array(d['body']['triangles'],int).reshape(-1,3)
tri=bp[bt];lo=tri[:,:,:2].min(1);hi=tri[:,:,:2].max(1)
grid={};cell=.004
for t in range(len(bt)):
    for x in range(math.floor(lo[t,0]/cell),math.floor(hi[t,0]/cell)+1):
        for y in range(math.floor(lo[t,1]/cell),math.floor(hi[t,1]/cell)+1):grid.setdefault((x,y),[]).append(t)
report={'label':d['label'],'parts':[]}
for part in d['face']:
    if not part['triangles']:continue
    fp=np.array(part['positions'],float).reshape(-1,3);fn=np.array(part['normals'],float).reshape(-1,3);ft=np.array(part['triangles'],int).reshape(-1,3);ids=np.unique(ft)
    fpp=(fp+fn*part['paintLift'])@axes
    cross=np.cross(fp[ft[:,1]]-fp[ft[:,0]],fp[ft[:,2]]-fp[ft[:,0]])@axes[:,2]
    r={'name':part['name'],'role':part['role'],'vertices':len(ids),'min':fpp[ids].min(0).tolist(),'max':fpp[ids].max(0).tolist(),'frontWinding':int((cross>0).sum()),'backWinding':int((cross<0).sum())}
    if part['role'] in (3,4,9):
        gaps=[];miss=0
        for x,y,z in fpp[ids]:
            candidates=grid.get((math.floor(x/cell),math.floor(y/cell)),[]);best=-1e9
            for t in candidates:
                aa,bb,cc=tri[t];den=(bb[1]-cc[1])*(aa[0]-cc[0])+(cc[0]-bb[0])*(aa[1]-cc[1])
                if abs(den)<1e-14:continue
                wa=((bb[1]-cc[1])*(x-cc[0])+(cc[0]-bb[0])*(y-cc[1]))/den
                wb=((cc[1]-aa[1])*(x-cc[0])+(aa[0]-cc[0])*(y-cc[1]))/den;wc=1-wa-wb
                if min(wa,wb,wc)<-1e-5:continue
                best=max(best,aa[2]*wa+bb[2]*wb+cc[2]*wc)
            if best==-1e9:miss+=1
            else:gaps.append(z-best)
        r.update(occluded=int(sum(q<-.0001 for q in gaps)),tested=len(gaps),unmatched=miss,minClearanceMetres=min(gaps,default=None),maxClearanceMetres=max(gaps,default=None),medianClearanceMetres=float(np.median(gaps)) if gaps else None)
    report['parts'].append(r)
output=Path(a.out or str(Path(a.snapshot).with_suffix('.placement.json')));output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
