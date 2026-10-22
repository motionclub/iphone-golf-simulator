import sys; sys.path.insert(0,'tools')
from fplate import *
from PIL import Image, ImageDraw, ImageFont
M=Mesh('data/cand.npz'); co=M.co
O=np.load(W/'data/orig.npz')['co'].astype(np.float64)
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
def plot(zs,half=0.012,scale=1500,W_=1800,H_=420,out='data/xsec.png',arrs=None):
    im=Image.new('RGB',(W_,H_*((len(zs)+2)//3)),(20,20,24)); d=ImageDraw.Draw(im)
    for k,z in enumerate(zs):
        ox=(k%3)*(W_//3); oy=(k//3)*H_; cx=ox+W_//6; cy=oy+H_//2
        d.rectangle([ox,oy,ox+W_//3-1,oy+H_-1],outline=(60,60,70))
        d.text((ox+6,oy+4),f'z={z:.3f} (front=up, +x right)  slab ±{half*1000:.0f} mm',font=FONT,fill=(255,255,255))
        for arr,colz,colo in (arrs or [(co,(120,200,255),(255,140,60))]):
            m=(np.abs(arr[:,2]-z)<half)
            for i in np.where(m)[0]:
                x,y=arr[i,0],arr[i,1]
                col=colz if M.T[i] else colo
                u=cx+x*scale*0.95; v=cy+y*scale*0.95   # y>0 back -> down? we want front up: v=cy+y  (front y<0 -> up)
                d.ellipse([u-2,v-2,u+2,v+2],fill=col)
        # grid 5 cm
        for xm in np.arange(-0.3,0.31,0.05):
            u=cx+xm*scale*0.95; d.line([(u,oy+20),(u,oy+H_)],fill=(45,45,55))
    im.save(out); print(out,im.size)
plot([1.14,1.20,1.25,1.30,0.90,0.83])

if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='orig':
    plot([1.14,1.20,1.25,1.30,1.35,0.97],out='data/xsec_orig.png',arrs=[(O,(120,200,255),(255,140,60))])
