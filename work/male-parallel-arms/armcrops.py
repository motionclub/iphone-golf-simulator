import sys
from PIL import Image
A=sys.argv[1]+'/'; out=sys.argv[2]
f=Image.open(A+'bald_front_overlay.png'); b=Image.open(A+'bald_back_overlay.png')
def crop(img,box,sc=4): c=img.crop(box); return c.resize((c.width*sc,c.height*sc),Image.NEAREST)
boxes=[(f,(100,160,330,390)),(f,(380,160,610,390)),(b,(660,160,890,390)),(b,(940,160,1170,390))]
tiles=[crop(i,bx,3) for i,bx in boxes]
W=tiles[0].width; H=tiles[0].height
S=Image.new('RGB',(W*2+10,H*2+10),(0,0,0))
for i,t in enumerate(tiles): S.paste(t,((i%2)*(W+10),(i//2)*(H+10)))
S.save(out); print(S.size)
