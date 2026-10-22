from pathlib import Path
__file__=str(Path(__file__).parent/'author_local_cloth_frontcull.py');src=Path(__file__).read_text();exec(src[:src.index('regions=np.array')]);import copy
Z=W/'body-correspondent-weights';change=json.loads((Z/'UnderarmWeights_Female.json').read_text());newtop={**top,'indices':change['indices'],'weights':change['weights']};regionfaces=np.array(json.loads((W/'reusable-underarm/full-strength-source-audit.json').read_text())['regionFaces']);rows=[]
def new_holes(lost,old):
 seen=set();total=0;h,w=lost.shape
 for iy,ix in zip(*np.where(lost)):
  if (iy,ix) in seen:continue
  seen.add((iy,ix));stack=[(iy,ix)];n=0;touch=False
  while stack:
   y,x=stack.pop();n+=1
   for yy in range(max(0,y-1),min(h,y+2)):
    for xx in range(max(0,x-1),min(w,x+2)):
     if old[yy,xx]:touch=True
     if lost[yy,xx] and (yy,xx) not in seen:seen.add((yy,xx));stack.append((yy,xx))
  if not touch:total+=n
 return total
for ix,path in enumerate(sorted((D/'matrices').glob('female_*.json'))):
 name=path.stem;mp=next(q for q in json.loads(path.read_text())['parts'] if q['name']==top['name']);sm=arr(mp,'skinMatrices',16).reshape(-1,4,4);rm=arr(mp,'rendererToRoot',4);shapeW=np.array(mp['shapeWeights'])/100;sw=np.array([shapeW[mp['shapeNames'].index('TailoredSleeve_'+a['shape'])] for a in profile['anchors']]);dv=np.array([a['deltas'] for a in profile['anchors']]).reshape(len(sw),-1,3);v=arr(profile,'vertices',3)+np.einsum('k,kni->ni',sw,dv);bp,before=replay(name);after=xf(rm,skin(newtop,v,sm));row={'sample':name,'maxPoseChangeMm':float(np.linalg.norm(after-before,axis=1).max()*1000),'views':[]}
 for view in ['front','rear']:
  cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
  bpz,bpid=image(bp,bt[keep]);physical=np.full_like(bpid,-1);hit=bpid>=0;physical[hit]=np.where(keep)[0][bpid[hit]];region=np.isin(physical,regionfaces);bz,bid=image(before,tt);az,aid=image(after,tt);beforePixels=region&(bid>=0)&(bpz<bz-.0008);afterPixels=region&(aid>=0)&(bpz<az-.0008);rb=render(bp,before,bt[keep]);ra=render(bp,after,bt[keep]);lost=(rb>=0)&(ra<0);newskin=(rb>=100000)&(ra>=0)&(ra<100000);newRegionSkin=newskin&region
  row['views'].append({'view':view,'regionBefore':int(beforePixels.sum()),'regionAfter':int(afterPixels.sum()),'newBackgroundPixels':int(lost.sum()),'newHolePixels':new_holes(lost,rb<0),'newSkinPixels':int(newskin.sum()),'newRegionSkinPixels':int(newRegionSkin.sum())})
  if name in ['female_Forehand_1','female_Forehand_2','female_Forehand_4','female_EmoteSpike_1','female_MatchLose_1','female_Serve_4','female_Ready_0']:
   panels=[]
   for pic in [rb,ra]:
    rgb=np.full((1200,900,3),218,np.uint8);rgb[(pic>=0)&(pic<100000)]=[220,155,100];rgb[pic>=100000]=[162,191,73];panels.append(Image.fromarray(rgb).crop((200,250,650,650)))
   plate=Image.new('RGB',(900,426),(24,24,24));dr=ImageDraw.Draw(plate)
   for j,(im,lab) in enumerate(zip(panels,['ORIGINAL WEIGHTS','LOCAL BODY WEIGHTS'])):plate.paste(im,(450*j,26));dr.text((450*j+5,5),name+' '+view+' '+lab,fill='white')
   plate.save(Z/(name+'_'+view+'.png'))
 rows.append(row)
 if ix%40==0:print('done',ix+1,flush=True)
report={'scope':'Same rest positions, normals, triangleindices, UVs, named bones/bindposes and original10sleeveanchor arrays; bodymask2. Only1358local mainTop weights transferred with cuffdistance falloff. Correct-facing CullBack source replay all165poses/330views. Region skin counts are localization rather than automatic proof of cloth penetration.','poses':len(rows),'views':len(rows)*2,'regionBefore':sum(v['regionBefore'] for r in rows for v in r['views']),'regionAfter':sum(v['regionAfter'] for r in rows for v in r['views']),'newHoleViews':sum(v['newHolePixels']>0 for r in rows for v in r['views']),'maxNewHolePixels':max(v['newHolePixels'] for r in rows for v in r['views']),'maxNewBackgroundPixels':max(v['newBackgroundPixels'] for r in rows for v in r['views']),'maxPoseChangeMm':max(r['maxPoseChangeMm'] for r in rows),'rows':rows};(Z/'source-motion-report.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='rows'},flush=True)
