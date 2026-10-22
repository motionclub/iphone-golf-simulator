import sys
from PIL import Image
# usage: compose.py out.png prefix  -> 2x2 plates vs mine (front,left,q3R,q3L)
pre=sys.argv[2]; out=sys.argv[1]
D='../../ArtDir/hero/base_lock/male_head_detail.jpg'
im=Image.open(D).convert('RGB')
panels={'front':(22,66,432,352),'left':(440,66,834,352),'q3R':(440,388,834,668),'q3L':(22,388,432,668)}
tiles=[]
for name in ['front','left','q3R','q3L']:
    p=im.crop(panels[name]); p=p.resize((p.width*3,p.height*3),Image.LANCZOS)
    m=Image.open(f'{pre}_{name}.png').convert('RGB').resize(p.size)
    row=Image.new('RGB',(p.width*2+10,p.height),(0,0,0)); row.paste(p,(0,0)); row.paste(m,(p.width+10,0)); tiles.append(row)
W=max(t.width for t in tiles); H=sum(t.height for t in tiles)
sheet=Image.new('RGB',(W,H),(0,0,0)); y=0
for t in tiles: sheet.paste(t,(0,y)); y+=t.height
sheet=sheet.resize((sheet.width//2,sheet.height//2),Image.LANCZOS); sheet.save(out); print(out,sheet.size)
