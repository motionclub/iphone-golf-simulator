from pathlib import Path
S=Path.cwd()/'work/reference-rebuild/garment-weight-transition/mask3/author_local_cloth_frontcull.py';__file__=str(S);exec(S.read_text().split('regions=np.array')[0])
exec((R/'work/reference-rebuild/garment-gusset1/lod_context.py').read_text())
Z=R/'work/reference-rebuild/garment-gusset1';Z=Z/'lod' if os.environ.get('GUSSET_LOD')=='1' else Z;p=np.load(Z/'patch.npz');nt=p['triangles'];oi=p['sourceids'];ow=p['sourceweights'];inds=p['indices'];wg=p['weights'];alias=p['aliases'];free=p['free'];freeids=np.where(free)[0];bvfaces=p['bodyfaces'];regions=np.array(json.loads((W/'reusable-underarm/full-strength-source-audit.json').read_text())['regionFaces']);oldtt=tt.copy();tt=nt
cl=ctypes.CDLL(str(R/'work/reference-rebuild/garment-gusset1/clearance.dylib'));cl.project.argtypes=[ctypes.c_void_p]*3+[ctypes.c_int,ctypes.c_void_p,ctypes.c_int]+[ctypes.c_void_p]*4
cl.outward.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p]
proxyvertices=np.unique(bt[regions]);proxyfaces=np.where(np.isin(bt,proxyvertices).any(1)&keep)[0];T=np.ascontiguousarray(bt[proxyfaces],np.int32)
np.savez_compressed(Z/'collision-proxy.npz',bodyFaceIds=proxyfaces,bodyVertexIds=np.unique(T),triangles=T)
def deform(label):
 bp,before=replay(label);mp=next(q for q in json.loads((D/'matrices'/f'{label}.json').read_text())['parts'] if q['name']==top['name']);sm=arr(mp,'skinMatrices',16).reshape(-1,4,4);rt=arr(mp,'rendererToRoot',4);shapeW=np.array(mp['shapeWeights'])/100;sw=np.array([shapeW[mp['shapeNames'].index('TailoredSleeve_'+a['shape'])] for a in profile['anchors']]);dv=np.array([a['deltas'] for a in profile['anchors']]).reshape(len(sw),-1,3);v=base+np.einsum('k,kni->ni',sw,dv);newv=np.einsum('nk,nkj->nj',ow,v[oi]);after=xf(rt,skin({'indices':inds,'weights':wg},newv,sm));rawafter=after.copy()
 n=np.zeros_like(bp);areas=np.cross(bp[bt[:,1]]-bp[bt[:,0]],bp[bt[:,2]]-bp[bt[:,0]])
 for j in range(3):np.add.at(n,bt[:,j],areas)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);n=np.ascontiguousarray(n);points=np.ascontiguousarray(after[freeids]);near=np.zeros_like(points);normal=np.zeros_like(points);sd=np.zeros(len(points));faces=np.zeros(len(points),np.int32)
 cl.project(bp.ctypes.data,n.ctypes.data,T.ctypes.data,len(T),points.ctypes.data,len(points),near.ctypes.data,normal.ctypes.data,sd.ctypes.data,faces.ctypes.data)
 # Select the outward Body exit along the gusset normal, which also covers
 # the case where the stretched garment chord lies behind the whole Body.
 garmentn=np.zeros_like(after);area=np.cross(after[nt[:,1]]-after[nt[:,0]],after[nt[:,2]]-after[nt[:,0]])
 for j in range(3):np.add.at(garmentn,nt[:,j],area)
 garmentn/=np.maximum(np.linalg.norm(garmentn,axis=1)[:,None],1e-12)
 directions=np.ascontiguousarray(garmentn[freeids]);distance=np.zeros(len(points));rf=np.zeros(len(points),np.int32)
 cl.outward(bp.ctypes.data,T.ctypes.data,len(T),points.ctypes.data,directions.ctypes.data,len(points),distance.ctypes.data,rf.ctypes.data)
 amount=np.where(rf>=0,np.clip(distance+.003,0,.04),0);delta=np.zeros_like(after);delta[freeids]=directions*amount[:,None]
 # Duplicate UV vertices and coincident cuff aliases share one physical shift.
 sums=np.zeros((alias.max()+1,3));count=np.bincount(alias,minlength=len(sums));np.add.at(sums,alias,delta);delta=sums[alias]/count[alias,None];delta[~free]=0
 after+=delta
 # Resolve triangle-interior contact, not just vertices. All constraints refer
 # to the same small visible-Body proxy and use the patch's outward orientation.
 contactfaces=np.where(np.isin(p['parents'],p['selectedSourceFaces']) & free[nt].any(1))[0];ct=nt[contactfaces];contactCounts=[]
 for iteration in range(6):
  q=after[ct];cent=np.ascontiguousarray(q.mean(1));directions=np.ascontiguousarray(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]));directions/=np.maximum(np.linalg.norm(directions,axis=1)[:,None],1e-12);distance=np.zeros(len(ct));rf=np.zeros(len(ct),np.int32)
  cl.outward(bp.ctypes.data,T.ctypes.data,len(T),cent.ctypes.data,directions.ctypes.data,len(ct),distance.ctypes.data,rf.ctypes.data)
  amount2=np.where(rf>=0,np.clip(distance+.003,0,.008),0);contactCounts.append(int((amount2>.0003).sum()))
  pushes=directions*amount2[:,None]*3/np.maximum(free[ct].sum(1)[:,None],1);update=np.zeros_like(after);counts=np.zeros(len(after))
  for j in range(3):
   np.add.at(update,ct[:,j],pushes);np.add.at(counts,ct[:,j],(amount2>0).astype(float))
  update/=np.maximum(counts[:,None],1);update[~free]=0;delta=after+update-rawafter;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.04/np.maximum(length,1e-12))[:,None]
  sums=np.zeros((alias.max()+1,3));count=np.bincount(alias,minlength=len(sums));np.add.at(sums,alias,delta);delta=sums[alias]/count[alias,None];delta[~free]=0;after=rawafter+delta
 stats={'maxClearanceMoveMm':float(np.linalg.norm(delta,axis=1).max()*1000),'capVertices':int((amount>=.03999).sum()),'penetratingBefore':int((sd<-.0005).sum()),'triangleContacts':contactCounts,'proxyFaces':len(T),'proxyVertices':len(np.unique(T))}
 return bp,before,after,rawafter,stats
# Background component gate: only newly lost pixels disconnected from original
# background count as new interior holes; silhouette shrink is recorded separately.
def holes(lost,old):
 seen=set();total=0;h,w=lost.shape
 for y,x in zip(*np.where(lost)):
  if (y,x) in seen:continue
  seen.add((y,x));stack=[(y,x)];n=0;touch=False
  while stack:
   yy,xx=stack.pop();n+=1
   for y2 in range(max(0,yy-1),min(h,yy+2)):
    for x2 in range(max(0,xx-1),min(w,xx+2)):
     if old[y2,x2]:touch=True
     if lost[y2,x2] and (y2,x2) not in seen:seen.add((y2,x2));stack.append((y2,x2))
  if not touch:total+=n
 return total
import sys
labels=['female_Forehand_1','female_EmoteSpike_1','female_Serve_4','female_CelebratePoint_1','female_Ready_0'] if '--all' not in sys.argv else [q.stem for q in sorted((D/'matrices').glob('female_*.json'))];rows=[]
for ix,label in enumerate(labels):
 bp,before,after,rawafter,stats=deform(label);row={'sample':label,**stats,'views':[]}
 for view in ['front','rear']:
  cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
  bpz,bpid=image(bp,bt[keep]);physical=np.full_like(bpid,-1);hit=bpid>=0;physical[hit]=np.where(keep)[0][bpid[hit]];region=np.isin(physical,regions);bz,bid=image(before,oldtt);az,aid=image(after,nt);beforepixels=region&(bid>=0)&(bpz<bz-.0008);afterpixels=region&(aid>=0)&(bpz<az-.0008)
  # render() uses global tt (new topology), so baseline must be rasterized here.
  rb=np.where(bz<bpz,bid+100000,bpid);rb[(~np.isfinite(bz))&(~np.isfinite(bpz))]=-1;ra=np.where(az<bpz,aid+100000,bpid);ra[(~np.isfinite(az))&(~np.isfinite(bpz))]=-1;lost=(rb>=0)&(ra<0);newskin=(rb>=100000)&(ra>=0)&(ra<100000)
  targetregion=np.isin(physical,[6385,6386,6396,6397,6753,6754,15928,15929,15931,15934,15936,15937,19373]);rec={'view':view,'regionBefore':int(beforepixels.sum()),'regionAfter':int(afterpixels.sum()),'targetBefore':int((beforepixels&targetregion).sum()),'targetAfter':int((afterpixels&targetregion).sum()),'newBackgroundPixels':int(lost.sum()),'newHolePixels':holes(lost,rb<0),'newSkinPixels':int(newskin.sum())};row['views'].append(rec)
  if '--all' not in sys.argv or label in ['female_Forehand_1','female_EmoteSpike_1','female_Serve_4','female_CelebratePoint_1']:
   ims=[]
   for pic in [rb,ra]:
    rgb=np.full((1200,900,3),218,np.uint8);rgb[(pic>=0)&(pic<100000)]=[220,155,100];rgb[pic>=100000]=[162,191,73];ims.append(Image.fromarray(rgb).crop((200,250,650,650)))
   plate=Image.new('RGB',(900,426),(24,24,24));dr=ImageDraw.Draw(plate)
   for j,(im,lab) in enumerate(zip(ims,['ORIGINAL','GUSSET CLEARANCE'])):plate.paste(im,(450*j,26));dr.text((450*j+5,5),label+' '+view+' '+lab,fill='white')
   plate.save(Z/(label+'_'+view+'-contact.png'))
 rows.append(row);print(label,row,flush=True)
report={'poses':len(rows),'views':len(rows)*2,'regionBefore':sum(v['regionBefore'] for r in rows for v in r['views']),'regionAfter':sum(v['regionAfter'] for r in rows for v in r['views']),'newHoleViews':sum(v['newHolePixels']>0 for r in rows for v in r['views']),'maxNewHolePixels':max(v['newHolePixels'] for r in rows for v in r['views']),'maxNewBackgroundPixels':max(v['newBackgroundPixels'] for r in rows for v in r['views']),'rows':rows};(Z/('source-motion-contact-report.json' if '--all' in sys.argv else 'targeted-contact-report.json')).write_text(json.dumps(report,indent=2))
