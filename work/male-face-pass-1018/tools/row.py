# tools/row.py out.jpg H label1=img1 label2=img2 ... : images side by side, same height, labels on top (crop: img@x0,y0,x1,y1)
import sys
from PIL import Image, ImageDraw, ImageFont
out, H = sys.argv[1], int(sys.argv[2]); tiles=[]
for a in sys.argv[3:]:
    lab, p = a.split('=',1); box=None
    if '@' in p: p,b=p.split('@'); box=tuple(int(v) for v in b.split(','))
    im=Image.open(p).convert('RGB')
    if box: im=im.crop(box)
    im=im.resize((max(1,round(im.width*H/im.height)),H), Image.LANCZOS); tiles.append((lab,im))
W=sum(t.width for _,t in tiles); canvas=Image.new('RGB',(W,H+30),(255,255,255)); d=ImageDraw.Draw(canvas); x=0
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
except Exception: f=None
for lab,im in tiles: canvas.paste(im,(x,30)); d.text((x+6,4),lab,fill=(0,0,0),font=f); x+=im.width
canvas.save(out,quality=90); print(out, canvas.size)
