"""Bake the analytic high construction surface into each updated low shell's tangent UV frame."""
from pathlib import Path
import json,math,sys,numpy as np
from PIL import Image
from golf_motion_surface_field import field
R=Path(__file__).resolve().parents[3];W=R/'work/golf-motion-fit';D=W/'maps';D.mkdir(exist_ok=True)
stats=[]
for sex in ['Male','Female']:
 for path in sorted((W/'export').glob(sex+'_Kit_*.npz')):
  piece=path.stem[len(sex)+1:];
  if len(sys.argv)>1 and path.stem!=sys.argv[1]:continue
  data=np.load(path);P=data['P'];UV=data['uv'];CN=data['normal'];tri=data['tri'];tl=data['triloops'];mi=data['material'];roles=data['materials']
  S=2048 if piece=='Kit_Top' else 256 if 'Sock' in piece else 512 if any(k in piece for k in ['Head','Glove']) else 1024
  pos=np.zeros((S,S,3),np.float32);nrm=pos.copy();tan=pos.copy();bit=pos.copy();aogeom=np.zeros((S,S),np.float32);occupied=np.zeros((S,S),bool);mat=np.zeros((S,S),np.uint8);hits=np.zeros((S,S),np.uint8);zone=np.full((S,S),-1,np.float32);zoneTrim=np.zeros((S,S),np.float32)
  a3=a2=0
  for ti,(ids,loops,role) in enumerate(zip(tri,tl,mi)):
   v=P[ids];uv=UV[loops];e1=v[1]-v[0];e2=v[2]-v[0];du=uv[1]-uv[0];dv=uv[2]-uv[0];den=du[0]*dv[1]-du[1]*dv[0]
   a3+=np.linalg.norm(np.cross(e1,e2))*.5;a2+=abs(den)*.5
   if abs(den)<1e-10:continue
   t=(e1*dv[1]-e2*du[1])/den;t/=max(np.linalg.norm(t),1e-10)
   b=(-e1*dv[0]+e2*du[0])/den;b/=max(np.linalg.norm(b),1e-10)
   uv=uv*S;mn=np.maximum(np.floor(uv.min(0)).astype(int),0);mx=np.minimum(np.ceil(uv.max(0)).astype(int),S-1)
   if (mx<mn).any():continue
   xx,yy=np.meshgrid(np.arange(mn[0],mx[0]+1)+.5,np.arange(mn[1],mx[1]+1)+.5);dd=den*S*S
   w1=((xx-uv[0,0])*(uv[2,1]-uv[0,1])-(yy-uv[0,1])*(uv[2,0]-uv[0,0]))/dd
   w2=((uv[1,0]-uv[0,0])*(yy-uv[0,1])-(uv[1,1]-uv[0,1])*(xx-uv[0,0]))/dd;w0=1-w1-w2
   inside=(w0>=0)&(w1>=0)&(w2>=0)
   if not inside.any():continue
   yyidx,xxidx=np.where(inside);iy=yyidx+mn[1];ix=xxidx+mn[0];wt=np.stack([w0[inside],w1[inside],w2[inside]],1)
   q=wt@v;nn=wt@CN[loops];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
   tt=t[None,:]-nn*(nn@t)[:,None];tt/=np.maximum(np.linalg.norm(tt,axis=1)[:,None],1e-9)
   bb=np.cross(nn,tt);bb*=np.sign(bb@b)[:,None]
   pos[iy,ix]=q;nrm[iy,ix]=nn;tan[iy,ix]=tt;bit[iy,ix]=bb;occupied[iy,ix]=True;mat[iy,ix]=role;hits[iy,ix]+=1
   if "ao" in data:aogeom[iy,ix]=wt@data["ao"][ids]
   if "fabric" in data:zone[iy,ix]=data["fabric"][ti];zoneTrim[iy,ix]=data["trim"][ti]
  q=pos[occupied];t=tan[occupied];b=bit[occupied];h,fold,cavity,trim,fabric=field(q,piece,sex)
  r=roles[mat[occupied]]
  if "fabric" in data:
   zz=zone[occupied];valid=zz>=0;fabric[valid]=zz[valid];trim=np.maximum(trim,zoneTrim[occupied])
  # Semantic bands keep their old API but get the same per-garment mask contract.
  band=np.isin(r,['Kit_ShirtTrim','Kit_ShortsBand']);trim[band]=1;fabric[band]=1
  sole=r=='Kit_Sole';fabric[sole & (q[:,2]>-.015)]=4;fabric[sole & (q[:,2]<=-.015)]=3;trim[sole & (q[:,2]<=-.015)]=1
  eps=.00045
  du=(field(q+t*eps,piece,sex)[0]-field(q-t*eps,piece,sex)[0])/(2*eps)
  dv=(field(q+b*eps,piece,sex)[0]-field(q-b*eps,piece,sex)[0])/(2*eps)
  slopes=np.stack([-du,-dv,np.ones_like(du)],1);slopes[:,:2]=np.clip(slopes[:,:2],-.75,.75);slopes/=np.linalg.norm(slopes,axis=1)[:,None]
  normal=np.full((S,S,3),[.5,.5,1],np.float32);mask=np.zeros((S,S,4),np.float32);mask[:]=[1,1,0,0]
  normal[occupied]=slopes*.5+.5;mask[occupied]=np.stack([1-np.maximum(.28*np.clip(fold,0,1),.28*aogeom[occupied]),cavity,trim,fabric/9],1)
  coverage=occupied.mean();overlap=int((hits>1).sum());pad=12 if S==2048 else 6 if S==1024 else 3
  filled=occupied.copy()
  for _ in range(pad):
   target=~filled;count=np.zeros((S,S),np.float32);ns=np.zeros_like(normal);ms=np.zeros_like(mask)
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
    src=np.roll(filled,(dy,dx),(0,1));count+=src;ns+=np.roll(normal,(dy,dx),(0,1))*src[:,:,None];ms+=np.roll(mask,(dy,dx),(0,1))*src[:,:,None]
   grow=target&(count>0);normal[grow]=ns[grow]/count[grow,None];mask[grow]=ms[grow]/count[grow,None];filled|=grow
  name=f'GolfMotion_{sex}_{piece[4:]}'
  for suffix,array in [('N',normal),('M',mask)]:Image.fromarray(np.round(np.clip(array[::-1],0,1)*255).astype(np.uint8)).save(D/f'{name}_{suffix}.png')
  stat={'sex':sex,'piece':piece,'size':S,'tris':len(tri),'uvCoverage':float(coverage),'overlapTexels':overlap,'pxPerCm':float(S/math.sqrt(a3/a2)/100),'paddingPx':pad,'AOmin':float(mask[:,:,0].min()),'fabricIDs':np.unique(fabric).tolist()};stats.append(stat);print(json.dumps(stat),flush=True)
# Four fabric tiles, each with eight repeat gutter texels. Shared normal-xy/thread-break atlas.
S=512;atlas=np.ones((S,S,4),np.float32);atlas[:,:,:2]=.5;atlas[:,:,2]=1/1.28
for row,col,kind in [(0,0,'twill'),(0,1,'knit'),(1,0,'leather'),(1,1,'cap')]:
 yy,xx=np.mgrid[:256,:256];u=((xx-8)/240)%1;v=((yy-8)/240)%1
 if kind=='twill':height=.20*np.cos((u+v)*2*np.pi*8)+.055*np.cos((u-v)*2*np.pi*8)
 elif kind=='knit':height=.18*np.cos(u*2*np.pi*10)*np.cos(v*2*np.pi*10)
 elif kind=='leather':height=.055*np.cos(u*2*np.pi*8)*np.cos(v*2*np.pi*8)
 else:height=.20*np.cos((u+v)*2*np.pi*8)+.04*np.cos(v*2*np.pi*8)
 dy,dx=np.gradient(height);n=np.stack([-dx*3,-dy*3,np.ones_like(dx)],2);n/=np.linalg.norm(n,axis=2)[:,:,None]
 atlas[row*256:(row+1)*256,col*256:(col+1)*256,:2]=n[:,:,:2]*.5+.5
 atlas[row*256:(row+1)*256,col*256:(col+1)*256,2]=(1+.35*height)/1.28
Image.fromarray(np.round(np.clip(atlas[::-1],0,1)*255).astype(np.uint8)).save(D/'GolfMotion_FabricAtlas.png')
(W/'bake_stats.json').write_text(json.dumps(stats,indent=2))
