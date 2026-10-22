from pathlib import Path
__file__=str(Path(__file__).parent/'author_local_cloth_frontcull.py');src=Path(__file__).read_text();exec(src[:src.index('regions=np.array')])
B=W/'underarm-basis';B.mkdir(exist_ok=True)
flds=json.loads((W/'reusable-underarm/Fields_Female.json').read_text());regionfaces=np.array(json.loads((W/'reusable-underarm/full-strength-source-audit.json').read_text())['regionFaces']);leftFaces=regionfaces[rest[bt[regionfaces],0].mean(1)<0];rightFaces=regionfaces[rest[bt[regionfaces],0].mean(1)>0]
rt=arr(top,'rendererToRoot',4);bases=[]
for side in range(2):
 raw=arr(flds['fields'][side],'deltas',3);rootraw=raw@rt[:3,:3].T;amplitude=np.linalg.norm(rootraw,axis=1);scalar=amplitude/np.max(amplitude)*.033
 b0=raw;b1=(np.column_stack([scalar*(-1 if side==0 else 1),np.zeros(len(raw)),np.zeros(len(raw))]))@rt[:3,:3];b2=(np.column_stack([np.zeros(len(raw)),scalar,np.zeros(len(raw))]))@rt[:3,:3];bases.extend([b0,b1,b2])
bases=np.array(bases);vertexInfluence=np.linalg.norm(bases,axis=2).max(0);movedFace=vertexInfluence[tt].max(1)>.0005

def setcam(view):
 global cam,fw,camRight,camUp
 cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
def baryscreen(v,tri,x,y):
 projected=project(v);a,b,c=projected[tri[:,0]],projected[tri[:,1]],projected[tri[:,2]];px=x+.5;py=y+.5;den=(b[:,0]-a[:,0])*(c[:,1]-a[:,1])-(b[:,1]-a[:,1])*(c[:,0]-a[:,0]);u=((b[:,0]-px)*(c[:,1]-py)-(b[:,1]-py)*(c[:,0]-px))/den;q=((c[:,0]-px)*(a[:,1]-py)-(c[:,1]-py)*(a[:,0]-px))/den;w=np.column_stack([u,q,1-u-q])/np.column_stack([a[:,2],b[:,2],c[:,2]]);return w/w.sum(1)[:,None]
def constraints(after,modes,cache):
 As=[];gs=[];counts=[0,0]
 for view,c in cache.items():
  setcam(view);tz,tid=image(after,tt);valid=c['region']&(tid>=0)&(c['bz']<tz-.0008)&((tz-c['bz'])<.065);valid&=np.where(tid>=0,movedFace[np.maximum(tid,0)],False)
  for side,reg in enumerate([c['left'],c['right']]):counts[side]+=int((valid&reg).sum())
  y,x=np.where(valid)
  if len(x)==0:continue
  # One constraint per second pixel keeps fitting independent of image resolution.
  choose=(x+y)%2==0;y=y[choose];x=x[choose];faces=tid[y,x];tri=tt[faces];bary=baryscreen(after,tri,x,y);a=-np.einsum('nki,k->ni',np.einsum('nj,knjl->nlk',bary,modes[:,tri,:]),fw) if False else None
  displacement=np.einsum('nj,knjl->knl',bary,modes[:,tri,:]);a=-np.einsum('knl,l->nk',displacement,fw);As.append(a);gs.append(tz[y,x]-c['bz'][y,x]+.0025)
 return (np.concatenate(As) if As else np.zeros((0,6))), (np.concatenate(gs) if gs else np.zeros(0)),counts

def metrics(after,cache):
 result=[]
 for view,c in cache.items():
  setcam(view);pic=render(c['bp'],after,bt[keep]);before=c['pic'];z,ids=image(after,tt);visible=c['region']&(ids>=0)&(c['bz']<z-.0008)&((z-c['bz'])<.065)
  result.append({'view':view,'left':int((visible&c['left']).sum()),'right':int((visible&c['right']).sum()),'newBackground':int(((before>=0)&(pic<0)).sum()),'newSkin':int(((before>=100000)&(pic>=0)&(pic<100000)).sum())})
 return result
reports=[];controls=[]
for ix,path in enumerate(sorted((D/'matrices').glob('female_*.json'))):
 name=path.stem;mp=next(q for q in json.loads(path.read_text())['parts'] if q['name']==top['name']);m=arr(mp,'skinMatrices',16).reshape(-1,4,4);mr=arr(mp,'rendererToRoot',4);mix=(m[ti]*tw[:,:,None,None]).sum(1);lin=np.einsum('ij,njk->nik',mr[:3,:3],mix[:,:3,:3]);bp,tp=replay(name);modes=np.einsum('nij,knj->kni',lin,bases);cache={}
 for view in ['front','rear']:
  setcam(view);bz,bid=image(bp,bt[keep]);physical=np.full_like(bid,-1);hit=bid>=0;physical[hit]=np.where(keep)[0][bid[hit]];lr=np.isin(physical,leftFaces);rr=np.isin(physical,rightFaces);cache[view]={'bp':bp,'bz':bz,'region':lr|rr,'left':lr,'right':rr,'pic':render(bp,tp,bt[keep])}
 coeff=np.zeros(6);A,g,initial=constraints(tp,modes,cache);best=(sum(initial),coeff.copy());allA=[];allb=[]
 # Preserve the proven exact field as the starting point for its sample.
 if name=='female_Forehand_1':coeff[0]=1
 for iteration in range(6):
  after=tp+np.einsum('k,kni->ni',coeff,modes);A,g,remaining=constraints(after,modes,cache)
  if sum(remaining)<best[0]:best=(sum(remaining),coeff.copy())
  if not len(g):break
  # Linearized positive-clearance constraints. Smooth least-norm projected fit.
  allA.append(A);allb.append(g+A@coeff);aa=np.concatenate(allA);bb=np.concatenate(allb);c=coeff.copy()
  lipschitz=np.linalg.norm(aa,2)**2/max(len(aa),1)+.000012
  for solve in range(140):
   residual=np.minimum(aa@c-bb,0);grad=aa.T@residual/max(len(aa),1)+.000012*c;c-=grad/max(lipschitz,1e-9);c=np.clip(c,-1.5,1.5)
   delta=np.einsum('k,kni->ni',c,modes);mx=np.linalg.norm(delta,axis=1).max()
   if mx>.05:c*=.05/mx
  coeff=c
 coeff=best[1];after=tp+np.einsum('k,kni->ni',coeff,modes);final=metrics(after,cache);baseline=metrics(tp,cache);reports.append({'sample':name,'initialTargetPixels':initial,'remainingTargetPixels':best[0],'coefficients':coeff.tolist(),'maxPosedDisplacementMm':float(np.linalg.norm(after-tp,axis=1).max()*1000),'before':baseline,'after':final});controls.append({'sample':name,'feature':feature(mp).tolist(),'coefficients':coeff.tolist()})
 if ix%20==0:print(ix+1,name,initial,'→',best[0],coeff.round(2),flush=True)
 if name in ['female_Forehand_1','female_Forehand_2','female_Forehand_4','female_MatchLose_1','female_RunLeft_1','female_EmoteSpike_1','female_Volley_1']:
  for view in ['front','rear']:
   setcam(view);panels=[]
   for v in [tp,after]:
    pic=render(bp,v,bt[keep]);rgb=np.full((1200,900,3),218,np.uint8);rgb[(pic>=0)&(pic<100000)]=[220,155,100];rgb[pic>=100000]=[162,191,73];panels.append(Image.fromarray(rgb).crop((200,250,650,650)))
   plate=Image.new('RGB',(900,426),(26,26,26));dr=ImageDraw.Draw(plate)
   for j,(im,lab) in enumerate(zip(panels,['BEFORE','BASIS FIT'])):plate.paste(im,(j*450,26));dr.text((j*450+6,5),name+' '+view+' '+lab,fill='white')
   plate.save(B/(name+'_'+view+'.png'))
(B/'controls.json').write_text(json.dumps(controls,indent=2));(B/'source-fit-report.json').write_text(json.dumps(reports,indent=2));np.savez_compressed(B/'basis.npz',bases=bases);print('COMPLETE',flush=True)
