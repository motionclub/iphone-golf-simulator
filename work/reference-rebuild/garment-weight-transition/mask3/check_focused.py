from pathlib import Path
__file__=str(Path(__file__).parent/'author_local_cloth_focused.py');s=Path(__file__).read_text();exec(s[:s.index('regions=np.array')]);from PIL import ImageDraw
q=np.load(O/'female_Forehand_1.npz');bp,before,after=q['body'],q['before'],q['after'];rows=[]
for view in ['front','rear']:
 cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
 b=render(bp,before,bt[keep]);a=render(bp,after,bt[keep]);loss=(b>=0)&(a<0);rows.append({'view':view,'newBackgroundPixels':int(loss.sum()),'newSkinPixels':int(((b>=100000)&(a>=0)&(a<100000)).sum()),'skinPixelsCoveredByTop':int(((b>=0)&(b<100000)&(a>=100000)).sum())})
 panels=[]
 for pic in [b,a]:
  rgb=np.full((1200,900,3),218,np.uint8);rgb[(pic>=0)&(pic<100000)]=[220,155,100];rgb[pic>=100000]=[162,191,73];panels.append(Image.fromarray(rgb).crop((240,340,590,580)))
 plate=Image.new('RGB',(700,266),(28,28,28));dr=ImageDraw.Draw(plate)
 for i,(im,label) in enumerate(zip(panels,['Original mask2 + Original Top','Original mask2 + Local cloth'])):plate.paste(im,(350*i,26));dr.text((350*i+5,5),label,fill='white')
 plate.save(O/f'female_Forehand_1_{view}-FINAL.png')
(O/'final-two-view-source-check.json').write_text(json.dumps(rows,indent=2));print(rows)
