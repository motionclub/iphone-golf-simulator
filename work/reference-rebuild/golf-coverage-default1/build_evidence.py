from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib
r=Path(__file__).resolve().parents[3]
w=r/'work/reference-rebuild/golf-coverage-default1'; p=r/'proof/reference-rebuild'
a=p/'golf-coverage-default1';b=p/'golf-coverage-two-sided1'
results=[]
for f in sorted(a.glob('*.png')):
 q=b/f.name; x=np.asarray(Image.open(f));y=np.asarray(Image.open(q));diff=np.any(x!=y,axis=-1); yy,xx=np.where(diff)
 results.append(dict(image=f.name,changedPixels=int(diff.sum()),bbox=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None,defaultSHA256=hashlib.sha256(f.read_bytes()).hexdigest(),optionalSHA256=hashlib.sha256(q.read_bytes()).hexdigest()))
(w/'pixel-comparison.json').write_text(json.dumps(results,indent=2))
font='/System/Library/Fonts/Supplemental/Arial.ttf'
h1=ImageFont.truetype(font,34);h2=ImageFont.truetype(font,24);label=ImageFont.truetype(font,20)
board=Image.new('RGB',(1472,692),'#101e2a');d=ImageDraw.Draw(board)
d.text((24,18),'Golf shirt coverage — actual Unity captures',fill='#f6f9ff',font=h1)
d.text((24,62),'Before → Current default  |  Matching animation frames, cameras, lighting and unretouched pixels',fill='#b8cedf',font=label)
keys=[('Female · driver backswing','female_Driver_top_front34.png',(300,325,550,565)),('Female · iron backswing','female_Iron_top_front34.png',(300,330,550,570)),('Male · pitching wedge','male_PitchingWedge_top_back34.png',(365,285,615,525))]
manifest=[]
for i,(title,name,crop) in enumerate(keys):
 x=24+i*484;d.text((x,110),title,font=h2,fill='white')
 for j,(cap,caplabel) in enumerate([('golf-cloth-control16','BEFORE'),('golf-coverage-default1','CURRENT DEFAULT')]):
  src=p/cap/name;im=Image.open(src).convert('RGB').crop(crop).resize((230,221),Image.Resampling.LANCZOS)
  # Both crops use the exact same aspect-preserving resize.
  d.text((x+j*235,150),caplabel,font=label,fill='#b8cedf');board.paste(im,(x+j*235,182))
  # Larger context, same source and crop per column.
  context=(180,190,710,720); ci=Image.open(src).convert('RGB').crop(context).resize((230,230),Image.Resampling.LANCZOS);board.paste(ci,(x+j*235,411))
  manifest.append(dict(title=title,image=str(src),crop=list(crop),contextCrop=list(context),sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
d.text((24,659),'Coverage repair: skin no longer breaks through these shirt areas. Sharp pale underarm folds still need refinement.',font=label,fill='#f0d1a1')
out=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/reference-check/golf-clothing-progress.jpg');board.save(out,quality=95,subsampling=0)
(w/'sheet-provenance.json').write_text(json.dumps(manifest,indent=2))
