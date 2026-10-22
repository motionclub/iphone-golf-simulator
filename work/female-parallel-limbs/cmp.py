import sys
from PIL import Image
plate=Image.open('../../ArtDir/hero/base_lock/female_body_plain.jpg').convert('RGB')
pre,out=sys.argv[1],sys.argv[2]
f=Image.open(f'{pre}_front.png').convert('RGB'); b=Image.open(f'{pre}_back.png').convert('RGB')
# crop full-body column: front x 300-580, back x 710-990, y 0-720 -> save halves
def row(p,cx): return p.crop((cx-170,0,cx+170,720))
W=Image.new('RGB',(340*4,720))
W.paste(row(plate,440),(0,0)); W.paste(row(f,440),(340,0)); W.paste(row(plate,847),(680,0)); W.paste(row(b,847),(1020,0))
W.save(out)
