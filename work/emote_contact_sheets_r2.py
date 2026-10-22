from pathlib import Path
import csv,json
from PIL import Image,ImageDraw,ImageFont
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emote-overhaul')
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',18)
manifest=[]
for sex in ['male','female']:
 for clip,times,views in [('Emote_Scuba',[1.,2.],['front','side']),('Emote_Thrust',[.45,.6,35/30,1.7],['side'])]:
  d=r/'film_r2'/sex/clip
  rows=list(csv.DictReader((d/'trace.csv').open()))
  captures=[(idx//2,row) for idx,row in enumerate(rows) if idx%2==1 and row['emoteActive']=='True']
  s=Image.new('RGB',(1440,2*750),(20,20,24));draw=ImageDraw.Draw(s)
  for j,t in enumerate(times):
   idx,row=min(captures,key=lambda z:abs(float(z[1]['clipTime'])-t))
   for k,view in enumerate(views):
    file=d/f'{view}_{idx:05d}.png';im=Image.open(file).convert('RGB')
    col,rowidx=(k,j) if clip=='Emote_Scuba' else (j%2,j//2)
    x,y=col*720,rowidx*750
    s.paste(im,(x,y+30));draw.text((x+8,y+4),f'{clip} {sex} {view} t={float(row["clipTime"]):.4f}s',font=font,fill='white')
    manifest.append(dict(hero=sex,clip=clip,view=view,requested_t=t,captured_t=float(row['clipTime']),image=str(file)))
  out=r/'proof_r2'/f'{clip}_{sex}_requested_sheet.png';s.save(out);print(out)
(r/'proof_r2/contact_manifest.json').write_text(json.dumps(manifest,indent=2))
