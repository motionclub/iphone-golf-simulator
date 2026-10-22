from pathlib import Path
exec((Path(__file__).parent/'diagnose.py').read_text().split("bp,tp=replay('female_Forehand_1')")[0])
from PIL import ImageDraw
m3=json.loads((W/'BodyMask_female-current-matrix-canonical.json').read_text());k3=np.ones(len(bt),bool);k3[m3['alwaysCoveredFaceIndices']]=False
def new_holes(lost,old):
 result=np.zeros_like(lost);seen=set();h,w=lost.shape
 for iy,ix in zip(*np.where(lost)):
  if (iy,ix) in seen:continue
  seen.add((iy,ix));stack=[(iy,ix)];component=[];touch=False
  while stack:
   y,x=stack.pop();component.append((y,x))
   for yy in range(max(0,y-1),min(h,y+2)):
    for xx in range(max(0,x-1),min(w,x+2)):
     if old[yy,xx]:touch=True
     if lost[yy,xx] and (yy,xx) not in seen:seen.add((yy,xx));stack.append((yy,xx))
  if not touch:
   for y,x in component:result[y,x]=True
 return result
added=np.array(m3['addedMixedTorsoArmFaces']);rows=[];worst=[];counts={int(f):dict(newBackgroundPixels=0,newHolePixels=0,replacedByTopPixels=0,views=[]) for f in added}
def colors(pic):
 a=np.full((1200,900,3),218,np.uint8);a[(pic>=0)&(pic<100000)]=[220,155,100];a[pic>=100000]=[162,191,73];return a
for ix,path in enumerate(sorted((D/'matrices').glob('female_*.json'))):
 name=path.stem;bp,tp=replay(name)
 for view in ['front','rear']:
  cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
  before=render(bp,tp,bt[keep]);after=render(bp,tp,bt[k3]);lost=(before>=0)&(after<0);changed=(before>=0)&(before<100000)&((after<0)|(after>=100000));newHole=new_holes(lost,before<0);rows.append({'sample':name,'view':view,'changedSkinPixels':int(changed.sum()),'newBackgroundPixels':int(lost.sum()),'entirelyNewHolePixels':int(newHole.sum())})
  if changed.any():
   mapped=np.full_like(before,-1);hit=(before>=0)&(before<100000);mapped[hit]=np.where(keep)[0][before[hit]]
   for f in np.intersect1d(np.unique(mapped[changed]),added):
    fm=mapped==f;entry=counts[int(f)];bg=int((fm&lost).sum());holes=int((fm&newHole).sum());cloth=int((fm&changed&(after>=100000)).sum());entry['newBackgroundPixels']+=bg;entry['newHolePixels']+=holes;entry['replacedByTopPixels']+=cloth
    if bg:entry['views'].append(dict(sample=name,view=view,bg=bg,holes=holes))
   yy,xx=np.where(changed);box=[max(0,int(xx.min())-35),max(0,int(yy.min())-45),min(900,int(xx.max())+35),min(1200,int(yy.max())+45)];row=rows[-1];row['changeBBox']=box
   if lost.any() or name in ['female_Forehand_1','female_Forehand_2','female_Forehand_4','female_Serve_1','female_EmoteThrust_4','female_IntroPushups_1']:
    panels=[Image.fromarray(colors(p)).crop(box) for p in [before,after]];height=max(p.height for p in panels);plate=Image.new('RGB',(sum(p.width for p in panels),height+26),(28,28,28));x=0
    for p,label in zip(panels,['MASK2','MASK3']):plate.paste(p,(x,26));ImageDraw.Draw(plate).text((x+5,5),label,fill='white');x+=p.width
    out=W/f'{name}_{view}-source-compare.png';plate.save(out);row['plate']=out.name
  if lost.any():print(rows[-1],flush=True)
 if ix%30==0:print('completed',ix+1,flush=True)
report={'scope':'Exact current canonical vertices/weights, exported shape weights and bone matrices; Unity camera pose/FOV900x1200. Clockwise/CullBack software z-raster at pixel centers, flat part IDs. No Unity shaded proof claim. Torso mask2→mask3 difference only.','poses':ix+1,'views':len(rows),'changedViews':sum(x['changedSkinPixels']>0 for x in rows),'newBackgroundViews':sum(x['newBackgroundPixels']>0 for x in rows),'newHoleViews':sum(x['entirelyNewHolePixels']>0 for x in rows),'maxNewBackgroundPixels':max(x['newBackgroundPixels'] for x in rows),'maxNewHolePixels':max(x['entirelyNewHolePixels'] for x in rows),'rows':rows}
(W/'per-face-motion-impact.json').write_text(json.dumps(counts,indent=2));(W/'motion-source-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
