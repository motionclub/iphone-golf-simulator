exec(__import__('pathlib').Path('work/reference-rebuild/gusset-actual-repair/check_bodyband.py').read_text().rsplit('rows=[]',1)[0])
def depth(v,faces,view):
 cam=np.array([2.4,1.3,4.1])*(1 if view=='front' else np.array([-1,1,-1]));target=np.array([0,.83,.1]);fw=target-cam;fw/=np.linalg.norm(fw);right=np.cross([0,1,0],fw);right/=np.linalg.norm(right);up=np.cross(fw,right);z=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32);d=v-cam;dp=d@fw;scale=600/np.tan(np.deg2rad(17));xy=np.ascontiguousarray(np.column_stack([450+d@right/dp*scale,600-d@up/dp*scale,dp]));faces=np.ascontiguousarray(faces,np.int32);lib.draw(xy.ctypes.data,faces.ctypes.data,len(faces),900,1200,z.ctypes.data,ids.ctypes.data,0);return z,ids
rows=[]
for label in ['female_Forehand_1','female_Forehand_2']:
 parts=json.loads((D/'matrices'/f'{label}.json').read_text())['parts'];tp=next(x for x in parts if x['name']=='Kit_Top');bp=next(x for x in parts if x['name']=='Body_F');tm=rootmat(tp);bm=rootmat(bp);weights=np.array([tp['shapeWeights'][tp['shapeNames'].index('TailoredSleeve_'+an['shape'])]/100 for an in sleeve['anchors']]);sh=av+np.einsum('k,kni->ni',weights,ad);after=skin(sh,ai,aw,tm);bv=skin(basis,bbi,bbw,bm)
 before=skin(src+np.einsum('k,kni->ni',weights,deltas),oldbi,oldbw,tm)
 gn=np.zeros_like(bv);ft=np.cross(bv[bt[:,1]]-bv[bt[:,0]],bv[bt[:,2]]-bv[bt[:,0]])
 for k in range(3):np.add.at(gn,bt[:,k],ft)
 gn/=np.maximum(np.linalg.norm(gn,axis=1)[:,None],1e-12)
 for l in a['layers']:
  for i in range(l['vertexStart'],l['vertexStart']+l['vertexCount']):
   d=bmapped[i];pos=sum(bv[j]*w for j,w in d.items());norm=sum(gn[j]*w for j,w in d.items());norm/=max(np.linalg.norm(norm),1e-12);after[i]=pos+norm*(.004 if l['layer']==1 else .0025)
 for i,g in enumerate(gm):
  if g:after[i]=sum(before[j]*w for j,w in g.items())

 bz,bid=depth(bv,bt[keep],'front');tz,tid=depth(after,at,'front');gap=(bz<tz-.0008)&(tz-bz<.06);ids,cnt=np.unique(tid[gap],return_counts=True);o=np.argsort(-cnt);entries=[]
 for k in o[:20]:
  f=int(ids[k]);group='retained'
  for l in a['layers']:
   if l['faceStart']<=f<l['faceStart']+l['faceCount']:group=str((l['side'],l['layer']))+' body'
   elif l['faceStart']+l['faceCount']<=f<l['faceStart']+l['faceCount']+l['connectorFaces']:group=str((l['side'],l['layer']))+' connector'
  entries.append({'face':f,'pixels':int(cnt[k]),'group':group,'vertices':at[f].tolist(),'armMass':[(aw[i]*(ai[i]==p['bones'].index(('Left' if after[at[f],0].mean()<0 else 'Right')+'UpperArm'))).sum() for i in at[f]]})
 rows.append({'sample':label,'gapPixels':int(gap.sum()),'leading':entries})
(O/'bodyband-cpu-gap.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
