import sys
from PIL import Image, ImageChops
pre=sys.argv[1]
im=Image.open('../../ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
panels={'front':((22,66,432,352),(1230,858)),'left':((440,66,834,352),(1182,858)),'q3R':((440,388,834,668),(1182,840)),'q3L':((22,388,432,668),(1230,840))}
out=[]
for n,(box,size) in panels.items():
    p=im.crop(box).resize(size,Image.LANCZOS); m=Image.open(f'{pre}_{n}.png').convert('RGB').resize(size)
    b=Image.blend(p,m,0.5); out.append((n,b))
    b.save(f'{pre}_ov_{n}.png')
print('ok')
