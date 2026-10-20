import sys; sys.path.insert(0,'.')
from metric import *
tags=sys.argv[2:]; out=sys.argv[1]
name,img,(x0,y0,x1,y1),rf,off,(s1,s2)=REG[0]   # back_glute; widen to see context
x0-=40; x1+=40; y0-=30; y1+=40
A=dog(PL,s1,s2)[y0:y1,x0:x1]
tiles=[A]
for t in tags:
    d=render(t); m=np.asarray(Image.open(d/'back.png').convert('L')).astype('float32'); tiles.append(dog(m,s1,s2)[y0:y1,x0:x1])
def norm(a): return np.clip(128+a*4.5,0,255).astype('uint8')
ims=[Image.fromarray(norm(a)).resize(((x1-x0)*5,(y1-y0)*5),Image.LANCZOS) for a in tiles]
w,h=ims[0].size; s=Image.new('L',(w*len(ims)+8*(len(ims)-1),h),20); x=0
for im in ims: s.paste(im,(x,0)); x+=w+8
s.save(out); print(out,s.size)
