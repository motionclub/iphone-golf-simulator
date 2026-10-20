"""sheet-scale pelvis comparison: REF (multi-angle plate) | start | candidates, 8 panels. python3 sheet_scale.py out.png tag1 [tag2...]"""
import sys
from PIL import Image, ImageDraw
R='../../ArtDir/hero/base_lock/'
sh=Image.open(R+'male_multiangle_body.jpg').convert('RGB')
out=sys.argv[1]; tags=sys.argv[2:]
# panels: (label, ref box (c0,r0,c1,r1), render file template, render box in render px at its scale)
P=[('front',(100,150,270,270),'sheet_front',1,(100,150,270,270)),
   ('back',(395,150,565,270),'sheet_back',1,(395,150,565,270)),
   ('left',(745,150,845,270),'left',1,(745,150,845,270)),
   ('right',(1030,150,1130,270),'right',1,(1030,150,1130,270)),
   ('q_bl',(690,500,890,600),'reg_q3BL_690_890_500_600_4',4,None),
   ('q_br',(980,500,1180,600),'reg_q3BR_980_1180_500_600_4',4,None),
   ('q_fl',(90,440,290,560),'reg_q3FL_90_290_440_560_4',4,None),
   ('q_fr',(385,440,585,560),'reg_q3FR_385_585_440_560_4',4,None)]
Z=3; cells=[]
for lab,box,tpl,rp,rb in P:
    ref=sh.crop(box); W,H=ref.size; row=[ref.resize((W*Z,H*Z),Image.LANCZOS)]
    for t in ['start']+tags:
        im=Image.open(f'r/{t}_sh/{tpl}.png').convert('RGB')
        if rb is not None: im=im.crop(rb)
        else: im=im.resize((W,H),Image.LANCZOS)
        row.append(im.resize((W*Z,H*Z),Image.LANCZOS))
    cells.append((lab,row))
cw=max(r[0].width for _,r in cells); ch=max(r[0].height for _,r in cells); n=1+1+len(tags)
sheetim=Image.new('RGB',(n*(cw+6)+6,len(cells)*(ch+22)+6),(16,16,16)); d=ImageDraw.Draw(sheetim)
for i,(lab,row) in enumerate(cells):
    for j,im in enumerate(row):
        x=6+j*(cw+6); y=6+i*(ch+22)+16; sheetim.paste(im,(x,y)); d.text((x+4,y-14),(['REF','NOW start']+tags)[j]+' '+lab,fill=(255,200,80))
sheetim.save(out); print(out,sheetim.size)
