exec(__import__('pathlib').Path('work/reference-rebuild/gusset-actual-repair/check_dq.py').read_text().split('rows=[]')[0])
a=json.loads((O/'bodyband-prototype.json').read_text());geo=np.load(O/'bodyband-prototype.npz');av=geo['vertices'];at=geo['triangles'].astype(np.int32);gm=[{int(k):v for k,v in x.items()} for x in a['garmentMaps']];bmapped=[{int(k):v for k,v in x.items()} for x in a['bodyMaps']]
bdense=np.zeros((len(basis),53));dense=np.zeros((len(src),53))
for k in range(4):dense[np.arange(len(src)),oldbi[:,k]]+=oldbw[:,k];bdense[np.arange(len(basis)),bbi[:,k]]+=bbw[:,k]
aw=np.array([sum(dense[j]*w for j,w in g.items()) if g else sum(bdense[j]*w for j,w in b.items()) for g,b in zip(gm,bmapped)]);ai=np.argsort(aw,axis=1)[:,-4:][:,::-1];aw=np.take_along_axis(aw,ai,1);aw/=aw.sum(1)[:,None]
ad=np.zeros((len(deltas),len(av),3))
for i,g in enumerate(gm):
 if g:
  for j,w in g.items():ad[:,i]+=deltas[:,j]*w
rows=[]
for label in ['female_intro','female_Forehand_1','female_Forehand_2']:
 if label=='female_intro':tm=introM;bm=rootmat(body);weights=introWeights
 else:
  parts=json.loads((D/'matrices'/f'{label}.json').read_text())['parts'];tp=next(x for x in parts if x['name']=='Kit_Top');bp=next(x for x in parts if x['name']=='Body_F');tm=rootmat(tp);bm=rootmat(bp);weights=np.array([tp['shapeWeights'][tp['shapeNames'].index('TailoredSleeve_'+an['shape'])]/100 for an in sleeve['anchors']])
 shaped=src+np.einsum('k,kni->ni',weights,deltas);before=skin(shaped,oldbi,oldbw,tm);sh=av+np.einsum('k,kni->ni',weights,ad);after=skin(sh,ai,aw,tm);bv=skin(basis,bbi,bbw,bm)
 gn=np.zeros_like(bv);ft=np.cross(bv[bt[:,1]]-bv[bt[:,0]],bv[bt[:,2]]-bv[bt[:,0]])
 for k in range(3):np.add.at(gn,bt[:,k],ft)
 gn/=np.maximum(np.linalg.norm(gn,axis=1)[:,None],1e-12)
 for l in a['layers']:
  for i in range(l['vertexStart'],l['vertexStart']+l['vertexCount']):
   d=bmapped[i];pos=sum(bv[j]*w for j,w in d.items());norm=sum(gn[j]*w for j,w in d.items());norm/=max(np.linalg.norm(norm),1e-12);after[i]=pos+norm*(.004 if l['layer']==1 else .0025)
 for i,g in enumerate(gm):
  if g:after[i]=sum(before[j]*w for j,w in g.items())
 row={'sample':label,'views':[]}
 for view in ['front','rear']:
  old=raster(bv,before,oldtt,view);new=raster(bv,after,at,view);newskin=(old>=100000)&(new>=0)&(new<100000);removedskin=(new>=100000)&(old>=0)&(old<100000);newbackground=(old>=0)&(new<0);row['views'].append({'view':view,'newSkinPixels':int(newskin.sum()),'coveredSkinPixels':int(removedskin.sum()),'newBackgroundPixels':int(newbackground.sum())});plate=Image.new('RGB',(900,476),(24,24,24));draw=ImageDraw.Draw(plate)
  for j,(pix,title) in enumerate([(old,'BASELINE'),(new,'BODY CPU BAND')]):plate.paste(picture(pix).crop((200,250,650,700)),(450*j,26));draw.text((450*j+5,7),label+' '+view+' '+title,fill='white')
  plate.save(O/f'bodyband_cpu_{label}_{view}.png')
 rows.append(row)
np.savez_compressed(O/'bodyband-cpu.npz',vertices=av,triangles=at,boneIndices=ai,weights=aw,shapeDeltas=ad)
(O/'bodyband-cpu-targeted.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
