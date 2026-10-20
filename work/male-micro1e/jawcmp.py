import sys
from PIL import Image
pre=sys.argv[1]
im=Image.open('../../ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
def pair(panel,size,mine,box,out):
    p=im.crop(panel).resize(size,Image.LANCZOS); m=Image.open(mine).convert('RGB').resize(size)
    a=p.crop(box); b=m.crop(box)
    s=Image.new('RGB',(a.width*2+10,a.height),(34,34,38)); s.paste(a,(0,0)); s.paste(b,(a.width+10,0)); s.save(out)
pair((22,66,432,352),(1230,858),f'{pre}_front.png',(300,430,930,760),f'{pre}_jaw_front.png')
pair((440,388,834,668),(1182,840),f'{pre}_q3R.png',(250,420,900,780),f'{pre}_jaw_q3R.png')
pair((440,66,834,352),(1182,858),f'{pre}_left.png',(200,380,800,760),f'{pre}_jaw_left.png')
pair((22,388,432,668),(1230,840),f'{pre}_q3L.png',(300,430,930,780),f'{pre}_jaw_q3L.png')
# stack the three into one tall sheet
ims=[Image.open(f'{pre}_jaw_{n}.png') for n in ('front','q3R','left')]
W=max(i.width for i in ims); H=sum(i.height for i in ims)
S=Image.new('RGB',(W,H),(34,34,38)); y=0
for i in ims: S.paste(i,(0,y)); y+=i.height
S.save(f'{pre}_jaw_all.png'); print(S.size)
