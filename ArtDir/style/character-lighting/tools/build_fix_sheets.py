from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,sys
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);base=Path(__file__).resolve().parent.parent
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
rows=json.loads((src/'metrics.json').read_text());metrics={r['shot']:r for r in rows}
# Equal-size face panels, with source masks establishing identical crop coordinates.
canvas=Image.new('RGB',(1600,4*465),'#f2f3f5');draw=ImageDraw.Draw(canvas)
for row,hero in enumerate(['MatchHero_Male','MatchHero_Female','GolfKitHero_Male','GolfKitHero_Female']):
 n=hero+('__tennis_resort' if hero.startswith('Match') else '__golf_07_clear')+'__b_close'
 if n not in metrics:continue
 ids=np.array(Image.open(src/(n+'.mask.png')).convert('RGB'));yy,xx=np.where((ids[:,:,0]>240)&(ids[:,:,1]<10)&(ids[:,:,2]<10));cx=int(np.median(xx));cy=int(np.median(yy));box=(cx-110,cy-130,cx+110,cy+110)
 paths=[src/'paired-before'/(n+'.png'),base/'after/captures'/(n+'.jpg'),src/(n+'.png'),base/'after/lobby-reference'/(hero+'_head.png')]
 # Reference path retained in prior report may include native subfolder; fall back to raw.
 if not paths[3].exists():paths[3]=Path('/private/tmp/hero-lighting-lookdev/native/reference')/(hero+'_head.png')
 for col,(label,path) in enumerate(zip(['BEFORE','AFTER — flat test','AFTER2','REF — lobby'],paths)):
  im=Image.open(path).convert('RGB')
  if col<3:im=im.crop(box)
  else:
   w,h=im.size;im=im.crop((w*.20,h*.25,w*.85,h*.85))
  im=im.resize((385,420),Image.Resampling.LANCZOS);x=col*400;y=row*465;canvas.paste(im,(x+7,y+26));draw.text((x+7,y+3),label,fill='black',font=font)
  if col==2:draw.text((x+7,y+445),f"{hero} · face L {metrics[n]['after']['face']['L']:.1f}",font=font,fill='black')
canvas.save(out/'faces_before_after_after2_ref.jpg',quality=94)
# Fixed W gameplay cases, with the same r1–r5 target family as the combined plan.
cases=[('W1','MatchHero_Male__tennis_volcano__a_gameplay','r4',1),('W2','MatchHero_Male__tennis_skyscraper__a_gameplay','r4',0),('W3','GolfKitHero_Male__golf_16_clear__a_gameplay','r4',3),('W4','GolfKitHero_Male__golf_07_clear__b_close','r3',None)]
for tag,n,r,q in cases:
 if n not in metrics:continue
 ref=Image.open(base.parent/'refs'/(r+'.png')).convert('RGB')
 if q is not None:
  w,h=ref.size;x=(q%2)*w//2;y=(q//2)*h//2;ref=ref.crop((x,y,x+w//2,y+h//2))
 sheet=Image.new('RGB',(2560,440),'#f2f3f5');d=ImageDraw.Draw(sheet)
 imgs=[Image.open(src/'paired-before'/(n+'.png')),Image.open(base/'after/captures'/(n+'.jpg')),Image.open(src/(n+'.png')),ref]
 for col,(im,label) in enumerate(zip(imgs,['BEFORE','AFTER — flat test','AFTER2','REF — '+r])):
  sheet.paste(im.convert('RGB').resize((640,360)),(col*640,45));d.text((col*640+8,12),label,font=font,fill='black')
 d.text((8,414),n+' | AFTER2 edge/ring dL '+str(metrics[n]['after']['silhouetteDeltaL']),font=font,fill='black');sheet.save(out/(tag+'_before_after_after2_ref.jpg'),quality=94)
