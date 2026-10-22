import numpy as np, colorsys
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
C=np.asarray(Image.open(L+'Lava_C.png').convert('RGB'))/255.
E=np.asarray(Image.open(L+'Lava_E.png').convert('RGB'))/255.
N=np.asarray(Image.open(L+'Lava_N.png').convert('RGB'))/255.
print(C.shape,E.shape,N.shape)
# shader: sampled linear then pow .4545 => back to painted (gamma) values
def lum(a): return a@np.array([.2126,.7152,.0722])
def rgb(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16)/255 for i in (0,2,4)])
stops=[np.array([150,33,10])/255,np.array([186,43,13])/255,np.array([224,79,17])/255,np.array([255,128,28])/255]
def run(bias,gain,rel=.15,ha=1.5,hg=1.5):
    n=(N*2-1); 
    h=lum(C)*ha+lum(E)*hg+bias+(n[...,0]+n[...,1])*.5*rel
    h=np.clip((h-.5)*gain+.5,0,1)
    lin=[s2l(s) for s in stops]
    o=np.zeros(h.shape+(3,))
    for k in range(3):pass
    m1=h<.2; m2=(h>=.2)&(h<.6); m3=h>=.6
    t1=(h*5)[...,None]; t2=((h-.2)*2.5)[...,None]; t3=((h-.6)*2.5)[...,None]
    o=np.where(m1[...,None],lin[0]+(lin[1]-lin[0])*t1,np.where(m2[...,None],lin[1]+(lin[2]-lin[1])*t2,lin[2]+(lin[3]-lin[2])*t3))
    return h,l2s(o)*255
for b,g in ((-.15,1.4),(-.10,1.5),(0,1.4),(-.3,1.4)):
    h,o=run(b,g)
    m=o.reshape(-1,3).mean(0)
    hh=np.array([colorsys.rgb_to_hsv(*(p/255))[0]*360 for p in o.reshape(-1,3)[::50]])
    print('bias',b,'gain',g,'mean',m.round(0),'hue %.1f'%colorsys.rgb_to_hsv(*(m/255))[0],'heat q',np.percentile(h,[10,25,50,75,90]).round(2),'hot>.9 %.3f crust<.157 %.3f'%((h>.9).mean(),(h<.157).mean()),'hue range %.1f-%.1f'%(hh.min(),hh.max()))
# raw map stats
for nm,a in (('C',C),('E',E)):
    print(nm,'mean',(a*255).reshape(-1,3).mean(0).round(1),'max',(a*255).reshape(-1,3).max(0).round(0))
lc=lum(C); print('lum C dark<.25',(lc<.25).mean(),'bright >.5',(lc>.5).mean())
# E peak under multipliers (Lit fallback), flat light
Lc=np.array([1.421,.866,.742])
for tint,mult in ((.75,(1,.65,.5)),(1,(1,.65,.5)),(1,(1.3,1.3,1.3))):
    lin=s2l(C)*tint**2.2*Lc+s2l(E)*np.array(mult)
    o=l2s(np.clip(lin,0,1))*255
    print('lit tint',tint,mult,'mean',o.reshape(-1,3).mean(0).round(0),'cream(G>200&B>110)',((o[...,1]>200)&(o[...,2]>110)).mean(),'clipR',(lin[...,0]>1).mean())

h,o=run(-.15,1.4)
img=Image.fromarray(o.astype(np.uint8))
t=Image.new('RGB',(1536,1536))
s=img.resize((512,512),Image.BOX)
for i in range(3):
  for j in range(3): t.paste(s,(i*512,j*512))
t.save('lava_shader_3x3.png')
# grazing perspective: floor plane viewed at ~15 deg, 6 tiles deep
W,H=900,500; out=np.zeros((H,W,3),np.uint8)
ys,xs=np.mgrid[0:H,0:W]
hor=-30.; d=(ys-hor)  # distance param
z=300./np.maximum(d,1)  # depth
u=(xs-W/2)*z/260.; v=z*1.2
U=(u%1*1024).astype(int); V=(v%1*1024).astype(int)
out=o[V,U].astype(np.uint8)
Image.fromarray(out).save('lava_shader_graze.png')
# structure on shader heat map
from collections import deque
hh=Image.fromarray((h*255).astype(np.uint8)).resize((512,512),Image.BOX); hq=np.asarray(hh)/255.
for name,mask in (('crust h<.25',hq<.25),('dark h<.35',hq<.35)):
    H,W=mask.shape; lab=np.zeros((H,W),int); regs=[]
    for y in range(H):
      for x in range(W):
        if mask[y,x] and not lab[y,x]:
          q=deque([(y,x)]); lab[y,x]=1; pts=[]
          while q:
            a,b=q.popleft(); pts.append((a,b))
            for da,db in ((1,0),(-1,0),(0,1),(0,-1)):
              aa,bb=(a+da)%H,(b+db)%W
              if mask[aa,bb] and not lab[aa,bb]: lab[aa,bb]=1; q.append((aa,bb))
          regs.append(np.array(pts))
    big=[r for r in regs if len(r)>=30]; asp=[]
    for r in big:
        c=np.cov((r-r.mean(0)).T); ev=np.sort(np.linalg.eigvalsh(c))[::-1]; asp.append(np.sqrt(ev[0]/max(ev[1],1e-6)))
    asp=np.array(asp); sz=np.array([len(r) for r in big])
    print(name,'frac %.3f'%mask.mean(),'regions',len(big),'median aspect %.2f'%np.median(asp),'compact<1.5 area share %.2f'%(sz[asp<1.5].sum()/sz.sum()),'largest region share %.2f'%(sz.max()/sz.sum()))
# isotropy of gradient edges
g=hq-hq.mean(); gy,gx=np.gradient(hq); ang=np.arctan2(gy,gx); mag=np.hypot(gx,gy)
hist,_=np.histogram(ang[mag>np.percentile(mag,80)]%np.pi,bins=12,range=(0,np.pi)); print('edge orient hist (12 bins)',(hist/hist.sum()).round(3))
F=np.fft.fft2(g); ac=np.fft.ifft2(np.abs(F)**2).real; ac/=ac[0,0]; ac[0:6,0:6]=0; ac[-6:,0:6]=0;ac[0:6,-6:]=0;ac[-6:,-6:]=0
print('max autocorr off-origin %.3f'%ac.max())
yy,xx=np.mgrid[0:512,0:512]; yy=np.minimum(yy,512-yy); xx=np.minimum(xx,512-xx); r=np.hypot(yy,xx)
a2=np.fft.ifft2(np.abs(F)**2).real; a2/=a2[0,0]
for rm in (10,20,40,80):
    m=a2.copy(); m[r<rm]=0; i=np.unravel_index(m.argmax(),m.shape); print('autocorr excl r<%d: max %.3f at lag %s'%(rm,m.max(),i))
