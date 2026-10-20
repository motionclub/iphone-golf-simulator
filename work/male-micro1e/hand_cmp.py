import sys
from PIL import Image
pre=sys.argv[1]
D='../../ArtDir/hero/base_lock/'
body=Image.open(D+'male_body_bald.jpg').convert('RGB'); multi=Image.open(D+'male_multiangle_body.jpg').convert('RGB')
fr=Image.open(f'{pre}_front.png').convert('RGB'); bk=Image.open(f'{pre}_back.png').convert('RGB')
def pair(plate,mine,box,sc=6):
    a=plate.crop(box).resize(((box[2]-box[0])*sc,(box[3]-box[1])*sc),Image.LANCZOS)
    b=mine.crop(box).resize(a.size,Image.LANCZOS)
    s=Image.new('RGB',(a.width*2+8,a.height),(34,34,38)); s.paste(a,(0,0)); s.paste(b,(a.width+8,0)); return s
rows=[pair(body,fr,(520,300,610,385)), pair(body,fr,(110,300,200,385)), pair(body,bk,(1050,300,1160,385),5)]
W=max(r.width for r in rows); H=sum(r.height for r in rows)
S=Image.new('RGB',(W,H),(34,34,38)); y=0
for r in rows: S.paste(r,(0,y)); y+=r.height
S.save(f'{pre}_handcmp.png'); print(S.size)
