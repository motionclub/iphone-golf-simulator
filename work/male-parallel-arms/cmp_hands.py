import sys
from PIL import Image, ImageDraw
P='../../ArtDir/hero/base_lock/'
A=sys.argv[1]+'/'; out=sys.argv[2]
bald=Image.open(P+'male_body_bald.jpg').convert('RGB'); sheet=Image.open(P+'male_multiangle_body.jpg').convert('RGB')
R={'bald_front':bald,'bald_back':bald,'sheet_front':sheet,'sheet_back':sheet}
# hand boxes in 1280x720 plate framing (x0,y0,x1,y1)
boxes={'bald_front_imgL':('bald_front',(100,300,200,390)),'bald_front_imgR':('bald_front',(500,300,600,390)),
       'bald_back_imgL':('bald_back',(680,300,780,390)),'bald_back_imgR':('bald_back',(1060,300,1160,390)),
       'sheet_front_imgL':('sheet_front',(45,160,125,220)),'sheet_front_imgR':('sheet_front',(250,160,330,220)),
       'sheet_back_imgL':('sheet_back',(355,160,435,220)),'sheet_back_imgR':('sheet_back',(545,160,625,220))}
Z=6; tiles=[]
for k,(v,b) in boxes.items():
    pl=R[v].crop(b); md=Image.open(A+v+'.png').convert('RGB').crop(b)
    w,h=pl.size; pl=pl.resize((w*Z,h*Z),Image.LANCZOS); md=md.resize((w*Z,h*Z),Image.LANCZOS)
    t=Image.new('RGB',(w*Z*2+6,h*Z),(0,0,0)); t.paste(pl,(0,0)); t.paste(md,(w*Z+6,0)); tiles.append((k,t))
W=max(t.width for _,t in tiles)
rows=[tiles[i:i+2] for i in range(0,len(tiles),2)]
H=sum(max(t.height for _,t in r)+8 for r in rows)
S=Image.new('RGB',(W*2+12,H),(20,20,20)); y=0
for r in rows:
    x=0
    for k,t in r: S.paste(t,(x,y)); ImageDraw.Draw(S).text((x+4,y+2),k,fill=(255,255,0)); x+=W+12
    y+=max(t.height for _,t in r)+8
S.save(out); print(S.size)
