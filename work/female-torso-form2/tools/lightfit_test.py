import sys; sys.path.insert(0,'tools')
from fplate import *
from PIL import Image, ImageDraw
M=Mesh(); N=M.normals(); co=M.co
# fit region: legs (z<0.75, above ankle), upper+fore arms (arm-flag, z in .90-1.33, |x|>.14), exclude head/hands/feet/torso zone
legs=(co[:,2]<0.74)&(co[:,2]>0.14)
arms=(M.arm)&(co[:,2]>0.93)&(co[:,2]<1.30)&(np.abs(co[:,0])>0.15)
fitmask=(legs|arms)&~M.T
print('fit verts',fitmask.sum(),'legs',(legs&~M.T).sum(),'arms',arms.sum())
res={}
for name in ('front','back'):
    vw=View(name)
    for bname,B in (('sh2x',sh2c),('sh2full',sh2c_full)):
        c,r2,nv=fit_sh(vw,co,N,fitmask,sigma=2.5,basis=B)
        print(f'{name} {bname}: R2 {r2:.3f} n {nv}  coeffs {np.round(c,1)}')
        res[(name,bname)]=c
# predicted luminance image (splat) and residual vs plate, torso crops
def splat(vw,L,mask,res=3.0,rad=2,box=None):
    col,row=vw.project(co); dep=vw.depth(co)
    H,Wd=int(720*res),int(1280*res)
    img=np.zeros((H,Wd)); zb=np.full((H,Wd),-1e9)
    ci=np.round(col*res).astype(int); ri=np.round(row*res).astype(int)
    order=np.argsort(dep)    # far -> near
    for i in order:
        if not mask[i]: continue
        r0,r1=ri[i]-rad,ri[i]+rad+1; c0,c1=ci[i]-rad,ci[i]+rad+1
        if r0<0 or c0<0 or r1>H or c1>Wd: continue
        img[r0:r1,c0:c1]=L[i]; 
    return img
out=[]
for name,box in (('front',(340,110,540,300)),('back',(747,220,947,400))):
    vw=View(name)
    c=res[(name,'sh2x')]; Lp=sh2c(N,vw)@c
    vis=visible(vw,co,N,sel=co[:,2]<1.45)
    img=splat(vw,Lp,vis,res=3.0,rad=2)
    pred=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).crop(tuple(int(b*3) for b in box))
    pl=Image.fromarray(BALD.astype(np.uint8)).crop(box).resize(pred.size,Image.LANCZOS)
    a=np.asarray(pl).astype(float); b=np.asarray(pred).astype(float)
    ab=gblur(a,6)
    rs=np.clip(128+(a-b)*3,0,255)
    out.append((name,pl,pred,Image.fromarray(rs.astype(np.uint8))))
Wd=out[0][1].width+out[1][1].width
H=max(o[1].height for o in out)
sheet=Image.new('L',(Wd*1,H*3))
x=0
for name,pl,pred,rs in out:
    sheet.paste(pl,(x,0)); sheet.paste(pred,(x,H)); sheet.paste(rs,(x,2*H)); x+=pl.width
sheet.save('data/lightfit_resid.png'); print(sheet.size)
np.save('data/sh_front.npy',res[('front','sh2x')]); np.save('data/sh_back.npy',res[('back','sh2x')])
