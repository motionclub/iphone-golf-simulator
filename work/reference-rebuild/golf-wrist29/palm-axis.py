exec(open('work/reference-rebuild/golf-wrist29/analyze.py').read().split('report={}')[0])
out=[]
for sex in ('Male','Female'):
 d=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text());rig=d['rig'];names=rig['bones'];raw=(W/f'{sex}.rig.raw').read_bytes();a=np.load(W/f'{sex}-source.npz');V=a['vertices'];bind=a['bindposes'];rest=np.linalg.inv(bind);bm=list(a['boneMap']);weights=a['weights'];indices=a['indices'];dense=np.zeros((len(V),len(names)))
 for k in range(4):dense[np.arange(len(V)),a['boneMap'][indices[:,k]]]+=weights[:,k]
 for side in ('Left','Right'):
  h=names.index(side+'Hand');l=names.index(side+'LowerArm');m=names.index(side+'MiddleProximal');H=bm.index(h);L=bm.index(l);M=bm.index(m);arm=rest[H,:3,3]-rest[L,:3,3];arm/=np.linalg.norm(arm);palm=rest[M,:3,3]-rest[H,:3,3];palm/=np.linalg.norm(palm);delta=V-rest[H,:3,3];along=delta@palm;radial=np.linalg.norm(delta-along[:,None]*palm,axis=1);core=(dense[:,h]>.95)&(radial<.06)
  ids1=np.where(core&(along>.015)&(along<.035))[0];ids2=np.where(core&(along>.055)&(along<.075))[0];C1=V[ids1].mean(0);C2=V[ids2].mean(0);skinAxis=C2-C1;skinAxis/=np.linalg.norm(skinAxis);offset=float(np.degrees(np.arccos(np.clip(skinAxis@palm,-1,1))))
  palmLocal=bind[H,:3,:3]@palm;skinLocal=bind[H,:3,:3]@skinAxis;relative=[]
  for ci in rig['clips']:
   if not ci['id'].startswith('golf'):continue
   t=np.frombuffer(raw,'<f4',ci['frames']*rig['trackCount']*10,ci['offset']).reshape(ci['frames'],rig['trackCount'],10);cirow=[]
   for frame in [0,np.argmin(abs(np.array(ci['times'])-ci['contact']))]:
    tr=t[frame];axis=tr[h,:3]-tr[l,:3];axis/=np.linalg.norm(axis);SP=qmat(tr[h,3:7])@skinLocal;SP/=np.linalg.norm(SP);MP=qmat(tr[h,3:7])@palmLocal;MP/=np.linalg.norm(MP);angle=lambda v:float(np.degrees(np.arccos(np.clip(v@axis,-1,1))));cirow.append({'frame':int(frame),'skeletalPalmAngle':angle(MP),'skinPalmAngle':angle(SP)})
   relative.append({'clip':ci['id'],'samples':cirow})
  out.append({'sex':sex,'side':side,'restSkeletalForearmPalmAngle':float(np.degrees(np.arccos(np.clip(arm@palm,-1,1)))),'rigidSkinPalmVsSkeletalPalmAxisDegrees':offset,'coreBandSampleCounts':[len(ids1),len(ids2)],'restCoreCentres':[C1.tolist(),C2.tolist()],'clips':relative})
(W/'palm-axis-contract.json').write_text(json.dumps(out,indent=2)+'\n')
for r in out:print(r['sex'],r['side'],'rest',round(r['restSkeletalForearmPalmAngle'],2),'skinvsbone',round(r['rigidSkinPalmVsSkeletalPalmAxisDegrees'],2),'samples',r['coreBandSampleCounts'])
