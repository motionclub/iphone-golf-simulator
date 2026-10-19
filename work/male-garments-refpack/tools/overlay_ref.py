import sys; sys.path.insert(0,'tools'); from raster import *; from seg import *
H='MatchHero_Male'; import raster; DUMP2='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/dump'
body=part(H,'body',DUMP2); sock=part(H,'Kit_Sock_R',DUMP2)
P,T=body; keep=(P[T][:,:,2].max(1)<.35)&(P[T][:,:,0].min(1)>.05); body=(P,T[keep])
view=[[0,-1,0],[0,0,1],[1,0,0]]; org=np.array([.18,-0.03,.10]); sc=1800; W,Hh=900,600
im=render([(body[0],body[1],(214,160,120)),(sock[0],sock[1],(240,240,240))],view,sc,org,(W,Hh))
# foot heel/toe extents along -y (screen x)
fP=P[(P[:,2]<.03)&(P[:,0]>.05)]; heel_y=fP[:,1].max(); toe_y=fP[:,1].min()
print('foot len', heel_y-toe_y)
ref=load('13-tennis-shoe-detail')[240:640,40:760]; fg,cls=classify(ref,np.array([217,215,211.]))
Ls=float(sys.argv[1]) if len(sys.argv)>1 else .335; zb=float(sys.argv[2]) if len(sys.argv)>2 else -.028
mpp=Ls/(733-75)
# ref pixel (u,v) in crop: x_orig=u+40, y_orig=v+240 -> along -y from heel: s=(x_orig-75)*mpp ; z = zb+(588-y_orig)*mpp
heel_screen = W/2+(-(heel_y+.012)-(-org[1]))*sc   # heel back of shoe 12 mm behind the foot heel
a=np.array(im).astype(float)
vs,us=np.nonzero(fg)
for v,u,c in zip(vs,us,cls[vs,us]):
    s=(u+40-75)*mpp; z=zb+(588-(v+240))*mpp
    X=int(heel_screen+s*sc); Y=int(Hh/2-(z-org[2])*sc)
    if 0<=X<W and 0<=Y<Hh:
        col={1:(255,255,255),2:(30,50,160),3:(130,130,130),4:(255,170,0)}[int(c)]
        a[Y,X]=a[Y,X]*.45+np.array(col)*.55
Image.fromarray(a.astype(np.uint8)).save(sys.argv[3] if len(sys.argv)>3 else 'trace/overlay13.png')
