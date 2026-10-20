import sys
from PIL import Image
tag=sys.argv[1]; views=sys.argv[2].split(','); out=sys.argv[3]
crop=(80,160,640,860)
ims=[Image.open(f'proof/{tag}_{v}.png').convert('RGB').crop(crop) for v in views]
w,h=ims[0].size; s=Image.new('RGB',(w*len(ims),h),'white')
for k,i in enumerate(ims): s.paste(i,(k*w,0))
s.save(out)
