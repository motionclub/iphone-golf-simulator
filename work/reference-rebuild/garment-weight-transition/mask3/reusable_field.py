from pathlib import Path
__file__=str(Path(__file__).parent/'author_local_cloth_frontcull.py');src=Path(__file__).read_text();exec(src[:src.index('regions=np.array')])
U=W/'reusable-underarm';U.mkdir(exist_ok=True)
proven=json.loads((W/'local-cloth-frontcull/UnderarmTrace_Female.json').read_text());left=arr(proven['anchors'][0],'deltas',3);leftn=arr(proven['anchors'][0],'normalDeltas',3);rt=arr(top,'rendererToRoot',4);mirror=tr.copy();mirror[:,0]*=-1;chosen=np.where(tr[:,0]<-.035)[0];right=np.zeros_like(left);rightn=np.zeros_like(leftn);nearest=np.full(len(left),-1,int);dist=np.full(len(left),np.inf)
for chunk in np.array_split(np.where(tr[:,0]>.035)[0],16):
 if not len(chunk):continue
 d=((mirror[chunk,None]-tr[chosen][None])**2).sum(2);j=np.argmin(d,axis=1);nearest[chunk]=chosen[j];dist[chunk]=np.sqrt(d[np.arange(len(chunk)),j])
sel=(nearest>=0)&(dist<.016);ref=nearest[sel];dr=left[ref]@rt[:3,:3].T;dr[:,0]*=-1;right[sel]=dr@rt[:3,:3];nr=leftn[ref]@rt[:3,:3].T;nr[:,0]*=-1;rightn[sel]=nr@rt[:3,:3]
# Synchronize physical UV aliases on the mirrored target.
_,groups=np.unique(np.round(tr,5),axis=0,return_inverse=True)
for g in np.unique(groups):
 ids=np.where(groups==g)[0]
 if len(ids)<2:continue
 mx=ids[np.linalg.norm(right[ids],axis=1).argmax()];right[ids]=right[mx];rightn[ids]=rightn[mx]
profile2={'vertexCount':len(left),'vertices':proven['vertices'],'normals':proven['normals'],'fields':[{'side':'Left','deltas':left.ravel().tolist(),'normalDeltas':leftn.ravel().tolist()},{'side':'Right','deltas':right.ravel().tolist(),'normalDeltas':rightn.ravel().tolist()}]};(U/'Fields_Female.json').write_text(json.dumps(profile2,separators=(',',':')))
bodyregion=(abs(rest[:,0])<.143)&(abs(rest[:,0])>.117)&(rest[:,1]>1.15)&(rest[:,1]<1.22)&(head<.035);regionfaces=np.where(keep&bodyregion[bt].all(1)&(arm[bt].min(1)<.81))[0];print('regionfaces',len(regionfaces),'rightmirror maxgap',dist[sel].max(),flush=True)
rows=[]
for ix,path in enumerate(sorted((D/'matrices').glob('female_*.json'))):
 label=path.stem;mp=next(q for q in json.loads(path.read_text())['parts'] if q['name']==top['name']);m=arr(mp,'skinMatrices',16).reshape(-1,4,4);mr=arr(mp,'rendererToRoot',4);mix=(m[ti]*tw[:,:,None,None]).sum(1);lin=np.einsum('ij,njk->nik',mr[:3,:3],mix[:,:3,:3]);bp,tp=replay(label);dl=np.einsum('nij,nj->ni',lin,left);dr=np.einsum('nij,nj->ni',lin,right);f=feature(mp);row={'sample':label,'features':f.tolist(),'views':[]}
 for view in ['front','rear']:
  cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
  bz,bid=image(bp,bt[keep]);physical=np.full_like(bid,-1);hit=bid>=0;physical[hit]=np.where(keep)[0][bid[hit]];leftreg=np.isin(physical,regionfaces[rest[bt[regionfaces],0].mean(1)<0]);rightreg=np.isin(physical,regionfaces[rest[bt[regionfaces],0].mean(1)>0]);before=render(bp,tp,bt[keep]);after=render(bp,tp+dl+dr,bt[keep]);tz,tid=image(tp,tt);tz2,tid2=image(tp+dl+dr,tt);frontvisible=(bid>=0)&(tid>=0)&(bz<tz-.0005);aftervisible=(bid>=0)&(tid2>=0)&(bz<tz2-.0005);loss=(before>=0)&(after<0)
  row['views'].append({'view':view,'leftBefore':int((frontvisible&leftreg).sum()),'leftAfter':int((aftervisible&leftreg).sum()),'rightBefore':int((frontvisible&rightreg).sum()),'rightAfter':int((aftervisible&rightreg).sum()),'newBackground':int(loss.sum()),'newSkin':int(((before>=100000)&(after>=0)&(after<100000)).sum())})
 rows.append(row)
 if ix%40==0:print('done',ix+1,flush=True)
(U/'full-strength-source-audit.json').write_text(json.dumps({'scope':'Corrected front-face CullBack900x1200 all165poses two views; both reusablefields applied fullstrength only as diagnostic. Regional skin pixels may include legitimate arm overlap; these counts are localization, not automatic shipping gates.','rows':rows,'regionFaces':regionfaces.tolist()},indent=2));print('complete',flush=True)
