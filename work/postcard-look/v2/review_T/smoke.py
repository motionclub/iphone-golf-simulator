import numpy as np
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
im=Image.open(L+'Smoke_C.png'); print(im.mode,im.size)
a=np.asarray(im.convert('RGBA')).astype(float)/255; al=a[...,3]; H,W=al.shape
print('alpha max %.3f mean %.3f'%(al.max(),al.mean()),'frac>0.05 %.3f >0.2 %.3f'%((al>.05).mean(),(al>.2).mean()))
b=int(.12*W); m=np.ones_like(al,bool); m[b:-b,b:-b]=False; print('border alpha max',al[m].max())
for e in (0,1,2,3): print('edge row/col',e,'max a',al[e,:].max(),al[:,e].max(),al[-1-e,:].max(),al[:,-1-e].max())
# hard edge: max gradient
gy,gx=np.gradient(al); print('max grad %.4f'%np.hypot(gx,gy).max())
# aspect
yy,xx=np.indices(al.shape); w=al/al.sum(); cx=(w*xx).sum(); cy=(w*yy).sum()
cov=np.array([[(w*(xx-cx)**2).sum(),(w*(xx-cx)*(yy-cy)).sum()],[0,(w*(yy-cy)**2).sum()]]); cov[1,0]=cov[0,1]
ev=np.sort(np.linalg.eigvalsh(cov))[::-1]; print('aspect %.2f'%np.sqrt(ev[0]/ev[1]),'centroid',cx/W,cy/H)
print('rgb premult mean',(a[...,:3]*255)[al>.05].mean(0).round(0))
# alpha-weighted quantile of alpha: how opaque
print('alpha pcts among >0.02',np.percentile(al[al>.02],[50,90,99]).round(3))
for name,bg in (('red',(200,40,30)),('grey',(110,110,110))):
    B=np.ones((H,W,3))*np.array(bg)/255; out=B*(1-al[...,None])+a[...,:3]*al[...,None]
    Image.fromarray((out*255).astype(np.uint8)).save(f'smoke_on_{name}.png')
# also with tint (.62,.56,.56,.85) alpha*0.85
al2=al*.85; col=a[...,:3]*np.array([.62,.56,.56])
B=np.ones((H,W,3))*np.array((200,40,30))/255; Image.fromarray(((B*(1-al2[...,None])+col*al2[...,None])*255).astype(np.uint8)).save('smoke_tinted_red.png')
sheet=np.concatenate([np.asarray(Image.open(f'smoke_on_{n}.png')) for n in ('red','grey')]+[np.asarray(Image.open('smoke_tinted_red.png'))],1); Image.fromarray(sheet).save('smoke_sheet.png')
