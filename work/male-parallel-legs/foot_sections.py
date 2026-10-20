import sys; sys.path.insert(0,'.')
from leglib import *
from PIL import Image, ImageDraw
VA=np.load(sys.argv[1] if len(sys.argv)>1 else 'data/V_A40.npy')
out=sys.argv[2] if len(sys.argv)>2 else 'proof/cA/foot_sections.png'
ys=[-0.21,-0.19,-0.17,-0.15,-0.13,-0.11,-0.09,-0.07,-0.05,-0.02,0.01,0.03,0.05,0.065]
S=900; sc=2600  # px per metre
W=len(ys)*S//3
tiles=[]
cols=4; rowsn=(len(ys)+cols-1)//cols
img=Image.new('RGB',(cols*400,rowsn*330),(30,30,34)); d=ImageDraw.Draw(img)
for i,y0 in enumerate(ys):
    ox=(i%cols)*400+200; oy=(i//cols)*330+300
    d.rectangle([ox-200,oy-300,ox+199,oy+29],outline=(60,60,70))
    d.text((ox-195,oy-295),'y=%.3f'%y0,fill=(255,255,0))
    s=LEFT&(np.abs(VA[:,1]-y0)<0.004)&(VA[:,2]<0.21)
    for p in VA[s]:
        X=ox+(p[0]-0.20)*sc; Z=oy-p[2]*sc
        d.ellipse([X-1.6,Z-1.6,X+1.6,Z+1.6],fill=(120,220,255))
    # ground line & x ticks
    d.line([ox-200,oy,ox+200,oy],fill=(90,90,40))
    for xx in (0.14,0.17,0.20,0.23,0.26):
        X=ox+(xx-0.20)*sc; d.line([X,oy,X,oy+6],fill=(200,200,0)); d.text((X-8,oy+8),'%d'%round(xx*100),fill=(200,200,0))
img.save(out); print(img.size)
