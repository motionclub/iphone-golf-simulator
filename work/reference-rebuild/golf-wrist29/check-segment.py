exec(open('work/reference-rebuild/golf-wrist29/analyze.py').read().split('report={}')[0])
rows=[]
for sex in ('Male','Female'):
 d=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text());rig=d['rig'];names=rig['bones'];raw=(W/f'{sex}.rig.raw').read_bytes();p=next(x for x in rig['parts'] if x['part']=='Body');bind=np.frombuffer(raw,'<f4',len(p['bones'])*16,p['inverseBindOffset']).reshape(-1,4,4);rest=np.linalg.inv(bind)
 for ci in rig['clips']:
  if not ci['id'].startswith('golf'):continue
  tr=np.frombuffer(raw,'<f4',ci['frames']*rig['trackCount']*10,ci['offset']).reshape(ci['frames'],rig['trackCount'],10)
  for side in ('Left','Right'):
   l=names.index(side+'LowerArm');h=names.index(side+'Hand');L=p['bones'].index(l);H=p['bones'].index(h);v=bind[L,:3,:3]@(rest[H,:3,3]-rest[L,:3,3]);angles=[];offset=[]
   for track in tr:
    pred=qmat(track[l,3:7])@(v*track[l,7:10]);actual=track[h,:3]-track[l,:3];angle=np.degrees(np.arccos(np.clip(pred@actual/np.linalg.norm(pred)/np.linalg.norm(actual),-1,1)));angles.append(angle);offset.append(np.linalg.norm(pred-actual)*1000)
   rows.append(dict(sex=sex,clip=ci['id'],side=side,addressAxisAngle=float(angles[0]),maxAxisAngle=float(max(angles)),addressWristTailOffsetMm=float(offset[0]),maxWristTailOffsetMm=float(max(offset)),restSegmentLocal=v.tolist()))
(W/'segment-axis-contract.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows: print(r['sex'],r['clip'],r['side'],round(r['addressAxisAngle'],1),round(r['maxAxisAngle'],1),round(r['addressWristTailOffsetMm'],1))
