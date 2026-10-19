"""Re-loft each sewn sleeve between the posed armhole and cuff, retaining topology."""
from pathlib import Path
import numpy as np
import json
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree

def unit(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-12)
def frame(p,t):
 a,b,c=p[t[:,0]],p[t[:,1]],p[t[:,2]];u=unit(b-a);n=unit(np.cross(b-a,c-a));v=np.cross(n,u);return np.stack([u,v,n],axis=2)
def project(p,tree,gap=.012):
 out=p.copy()
 for i,x in enumerate(p):
  for _ in range(3):
   q,n,_,dist=tree.find_nearest(Vector(out[i]),.09)
   if q is None:break
   amount=gap-np.dot(out[i]-np.asarray(q),np.asarray(n))
   if amount<=0:break
   out[i]+=np.asarray(n)*min(.025,amount)
   if amount<.025:break
 return out
class SleeveLofts:
 def __init__(self,g,hero,root,garment_bind=None):
  self.g=g;self.h=hero;self.bind=hero.body.bind if garment_bind is None else garment_bind;self.data=[];p=g['pos'];tri=g['tri']
  for side in [-1,1]:
   R=np.asarray(json.loads((Path(root)/'source/golf_sleeve_pattern.json').read_text())[str(side)]);nr,M,_=R.shape;rp=R.reshape(-1,3)
   rt=np.array([t for j in range(nr-1)for i in range(M)for t in [(j*M+i,j*M+(i+1)%M,(j+1)*M+(i+1)%M),(j*M+i,(j+1)*M+(i+1)%M,(j+1)*M+i)]])
   mask=np.zeros(len(p),bool);mask[tri[np.isin(g['panel'],[2,3,6])].ravel()]=True;ids=np.nonzero(mask&(p[:,0]*side>0))[0]
   tree=BVHTree.FromPolygons(rp.tolist(),rt.tolist(),all_triangles=True);idx=[];bary=[]
   for v in p[ids]:
    q,_,fi,_=tree.find_nearest(Vector(v));t=rt[fi];a,b,c=rp[t];v0=b-a;v1=c-a;v2=np.asarray(q)-a;aa=v0@v0;ab=v0@v1;bb=v1@v1;ac=v0@v2;bd=v1@v2;den=max(aa*bb-ab*ab,1e-20);x=(bb*ac-ab*bd)/den;y=(aa*bd-ab*ac)/den;bc=np.clip([1-x-y,x,y],0,1);bc/=bc.sum();idx.append(t);bary.append(bc)
   idx=np.asarray(idx);bary=np.asarray(bary);base=(rp[idx]*bary[:,:,None]).sum(1);f=frame(rp,idx);off=np.einsum('nji,nj->ni',f,p[ids]-base)
   # The sewing boundary belongs to the actual torso panels, which blend
   # Chest/UpperChest/Neck; a rigid Chest transform pulls it off the shoulder.
   torso=tri[np.isin(g['panel'],[0,1])]
   # Panel IDs are supplied by the source pattern: front=0, back=1.
   tree_root=BVHTree.FromPolygons(p.tolist(),torso.tolist(),all_triangles=True)
   root_weights=np.zeros((len(R[0]),len(hero.body.bones)))
   for ri,v in enumerate(R[0]):
    q,_,fi,_=tree_root.find_nearest(Vector(v));t=torso[fi];a,b,c=p[t];v0=b-a;v1=c-a;v2=np.asarray(q)-a;aa=v0@v0;ab=v0@v1;bb=v1@v1;ac=v0@v2;bd=v1@v2;den=max(aa*bb-ab*ab,1e-20);x=(bb*ac-ab*bd)/den;y=(aa*bd-ab*ac)/den;bc=np.clip([1-x-y,x,y],0,1);bc/=bc.sum()
    for vi,weight in zip(t,bc):
     for bone,amount in zip(g['bi'][vi],g['bw'][vi]):root_weights[ri,bone]+=weight*amount
   self.data.append((side,R,ids,idx,bary,off,root_weights))
 def apply(self,target,skin,bones,bodytree):
  h=self.h;ch=skin[h.body.bones.index('Chest')]
  up=unit(ch[:3,:3]@np.array([0,0,1.]));out=target.copy()
  for side,R,ids,idx,bc,off,root_weights in self.data:
   name='Left' if side<0 else 'Right';ui=h.body.bones.index(name+'UpperArm');li=h.body.bones.index(name+'LowerArm');arm=skin[ui]
   root_matrices=np.einsum("nb,bij->nij",root_weights,skin)
   P0=np.einsum("nij,nj->ni",root_matrices[:,:3,:3],R[0])+root_matrices[:,:3,3]
   c0=P0.mean(0);_,_,vt=np.linalg.svd(P0-c0);d0=vt[2]
   if d0@(ch[:3,:3]@np.array([side,0,0]))<0:d0=-d0
   u0=unit(np.cross(d0,up));v0=np.cross(d0,u0);rel=P0-c0;l2=np.stack([rel@u0,rel@v0],1);lz=rel@d0;theta=np.arctan2(l2[:,1],l2[:,0])
   ad=unit(bones[li,:3,3]-bones[ui,:3,3]);end=arm[:3,:3]@R[-1].mean(0)+arm[:3,3]
   B=np.array([c0,c0+d0*.035,end-ad*.04,end]);ts=np.linspace(0,1,len(R));C=np.array([(1-t)**3*B[0]+3*(1-t)**2*t*B[1]+3*(1-t)*t*t*B[2]+t**3*B[3]for t in ts]);T=unit(np.gradient(C,axis=0));posed=np.zeros_like(R)
   for j,t in enumerate(ts):
    ax=np.cross(d0,T[j]);angle=np.arccos(np.clip(d0@T[j],-1,1));q=Quaternion(ax.tolist()if np.linalg.norm(ax)>1e-9 else u0.tolist(),float(angle));uk=np.asarray(q@Vector(u0));vk=np.asarray(q@Vector(v0))
    w=np.clip(t/.45,0,1);w=w*w*(3-2*w);radius=.064+(.060-.064)*t;sh=(1-w)*l2+w*radius*np.stack([np.cos(theta),np.sin(theta)],1)
    posed[j]=C[j]+sh[:,:1]*uk+sh[:,1:]*vk+((1-w)*lz)[:,None]*T[j]
   # Keep the substantial cuff rigid and round on its upper arm. Transport
   # the sleeve phase into that ring instead of twisting a separate trim surface.
   upper_rest=np.linalg.inv(self.bind[ui]);sh=upper_rest[:3,3]
   local_elbow=(h.body.bind[ui]@np.linalg.inv(h.body.bind[li]))[:3,3];el=upper_rest[:3,:3]@local_elbow+sh;axis=unit(el-sh)
   def cuff_points(points):
    radial=points-sh;radial-=np.outer(radial@axis,axis);radial=unit(radial)
    expanded=points+radial*.012
    return expanded@arm[:3,:3].T+arm[:3,3]
   end_ring=cuff_points(R[-1]);end_center=end_ring.mean(0)
   a=posed[-1]-posed[-1].mean(0);b=end_ring-end_center
   twist=np.arctan2(np.sum(np.cross(a,b)@ad),np.sum(a*b))
   for j,t in enumerate(ts):
    q=Quaternion(T[j].tolist(),float(twist*t));posed[j]=C[j]+np.asarray([q@Vector(v)for v in posed[j]-C[j]])
    w=np.clip((t-.55)/.20,0,1);w=w*w*(3-2*w)
    posed[j]=posed[j]*(1-w)+cuff_points(R[j])*w
   posed[0]=P0
   rp=posed.reshape(-1,3);f=frame(rp,idx);out[ids]=(rp[idx]*bc[:,:,None]).sum(1)+np.einsum('nij,nj->ni',f,off)
   cuff=np.zeros(len(out),bool);cuff[self.g['tri'][self.g['panel']==6].ravel()]=True;cuff&=self.g['pos'][:,0]*side>0
   near_end=np.zeros(len(out),bool)
   near_end[self.g['tri'][np.isin(self.g['panel'],[2,3])].ravel()]=True
   near_end&=(self.g['pos'][:,0]*side>0)&(self.g['a_d_cuff']<.040)
   rigid=cuff|near_end
   out[rigid]=cuff_points(self.g['pos'][rigid])
  return out
