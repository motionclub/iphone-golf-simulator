"""bake_view.py <final.npz> <M.png> <out.png>: numpy painter of the baked maps on the exported mesh (trim = navy, G cavity), lateral/medial/back/front/top/sole."""
import numpy as np, sys
from PIL import Image, ImageDraw
g=np.load(sys.argv[1]); M=np.asarray(Image.open(sys.argv[2])).astype(float)/255
P=g['pos']; T=g['tri']; uv=g['uv']; res=M.shape[0]; k=g['kind']
c=uv[T].mean(1)*res; col=M[np.clip((res-1-c[:,1]).astype(int),0,res-1), np.clip(c[:,0].astype(int),0,res-1)]
outer = k!=21
base=np.array([244,244,240.]); trim=np.array([34,48,90.])
def draw(view, size=(560,360), sc=1200):
    W,H=size; img=Image.new('RGB',size,(205,203,200)); dr=ImageDraw.Draw(img)
    V=np.asarray(view,float); Q=(P-P.mean(0))@V.T; dep=Q[T,2].mean(1)
    n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    L=np.array([.35,-.45,.82]); L/=np.linalg.norm(L); sh=np.clip(n@L,0,1)*.5+.5
    vis=(n@V[2])>0
    xs=W/2+Q[T,0]*sc; ys=H/2-Q[T,1]*sc
    for i in np.argsort(dep):
        if not vis[i]: continue
        rgb=(base*(1-col[i,2])+trim*col[i,2])*col[i,1]*sh[i]
        dr.polygon([(xs[i,0],ys[i,0]),(xs[i,1],ys[i,1]),(xs[i,2],ys[i,2])],fill=tuple(int(v) for v in rgb))
    return img
views=[[[0,-1,0],[0,0,1],[1,0,0]],[[0,1,0],[0,0,1],[-1,0,0]],[[-1,0,0],[0,0,1],[0,1,0]],[[1,0,0],[0,0,1],[0,-1,0]],[[0,-1,0],[-1,0,0],[0,0,1]],[[0,-1,0],[1,0,0],[0,0,-1]]]
out=Image.new('RGB',(560*3,720))
for i,v in enumerate(views): out.paste(draw(v),((i%3)*560,(i//3)*360))
out.save(sys.argv[3])
