exec((Path('work/reference-rebuild/gusset-actual-repair/check_dq.py') if 'Path' in globals() else __import__('pathlib').Path('work/reference-rebuild/gusset-actual-repair/check_dq.py')).read_text().split('rows=[]')[0])
a=json.loads((O/'annulus-prototype.json').read_text());av=np.array(a['vertices']);at=np.array(a['triangles'],np.int32);records=a['records'];maps=[{int(k):v for k,v in x.items()} for x in a['sourceMaps']]
for i,la,lb,lw,ha,hb,hw,t in records:
 d={}
 for vi,vw in [(la,(1-t)*(1-lw)),(lb,(1-t)*lw),(ha,t*(1-hw)),(hb,t*hw)]:
  for j,w in maps[vi].items():d[j]=d.get(j,0)+w*vw
 maps.append(d)
assert len(maps)==len(av)
dense=np.zeros((len(src),len(p['bones'])))
for k in range(4):dense[np.arange(len(src)),oldbi[:,k]]+=oldbw[:,k]
aw=np.array([sum(dense[j]*w for j,w in d.items()) for d in maps]);ai=np.argsort(aw,axis=1)[:,-4:][:,::-1];aw=np.take_along_axis(aw,ai,1);aw/=aw.sum(1)[:,None]
# Exact source-correspondence shape transfer supports static native exporting.
ad=np.array([[sum(delta[j]*w for j,w in d.items()) for d in maps] for delta in deltas])
rows=[]
for label in ['female_intro','female_Forehand_1','female_Forehand_2']:
 if label=='female_intro':tm=introM;bm=rootmat(body);weights=introWeights
 else:
  parts=json.loads((D/'matrices'/f'{label}.json').read_text())['parts'];tp=next(x for x in parts if x['name']=='Kit_Top');bp=next(x for x in parts if x['name']=='Body_F');tm=rootmat(tp);bm=rootmat(bp);weights=np.array([tp['shapeWeights'][tp['shapeNames'].index('TailoredSleeve_'+an['shape'])]/100 for an in sleeve['anchors']])
 shaped=src+np.einsum('k,kni->ni',weights,deltas);before=skin(shaped,oldbi,oldbw,tm);sh=av+np.einsum('k,kni->ni',weights,ad);static=skin(sh,ai,aw,tm)
 loft=np.array([sum(before[j]*w for j,w in d.items()) for d in maps]);bv=skin(basis,bbi,bbw,bm)
 for mode,after in [('static',static),('posedloft',loft)]:
  row={'sample':label,'mode':mode,'views':[]}
  for view in ['front','rear']:
   old=raster(bv,before,oldtt,view);new=raster(bv,after,at,view);newskin=(old>=100000)&(new>=0)&(new<100000);removedskin=(new>=100000)&(old>=0)&(old<100000);newbackground=(old>=0)&(new<0);row['views'].append({'view':view,'newSkinPixels':int(newskin.sum()),'coveredSkinPixels':int(removedskin.sum()),'newBackgroundPixels':int(newbackground.sum())});plate=Image.new('RGB',(900,476),(24,24,24));draw=ImageDraw.Draw(plate)
   for j,(pix,title) in enumerate([(old,'BASELINE'),(new,mode)]):plate.paste(picture(pix).crop((200,250,650,700)),(450*j,26));draw.text((450*j+5,7),label+' '+view+' '+title,fill='white')
   plate.save(O/f'annulus_{mode}_{label}_{view}.png')
  rows.append(row)
np.savez_compressed(O/'annulus-static.npz',vertices=av,triangles=at,boneIndices=ai,weights=aw,shapeDeltas=ad)
(O/'annulus-targeted.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
