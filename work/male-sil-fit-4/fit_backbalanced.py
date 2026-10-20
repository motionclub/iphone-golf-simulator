from pathlib import Path
from PIL import Image
import numpy as np,json
W=Path(__file__).resolve().parent;R=W.parents[1];S=R/'work/male-silhouette';v=json.loads((S/'reference-cameras.json').read_text())['views'][:2];s=1.7/593
arrays=[(q,np.array(Image.open(S/(q['name']+'_target.png')).convert('L'))>127,np.array(Image.open(W/'hands'/(q['name']+'.png')).getchannel('A'))>127) for q in v]
def span(mask,view,row,sign):
 py=round(view['sole_y']-(654-row)*s/view['metres_per_pixel']);x=(np.where(mask[py])[0]-view['centre_x'])*view['metres_per_pixel']/s
 if view['angle_degrees']==180:x=-x
 x=np.sort(sign*x[sign*x>170]);cuts=np.where(np.diff(x)>1.6)[0]+1;pieces=[q for q in np.split(x,cuts) if len(q)>1]
 if not pieces:return None
 q=pieces[-1];h=view['metres_per_pixel']/s/2;return [q[0]-h,q[-1]+h]
def profile(sign):
 rows=[]
 for row in range(328,379):
  a=[span(m,q,row,sign) for q,t,m in arrays];t=[span(t,q,row,sign) for q,t,m in arrays]
  if all(p is not None for p in a+t):rows.append([row,*np.mean(a,axis=0),*np.average(t,axis=0,weights=[.30,.70])])
 p=np.array(rows);k=np.exp(-np.arange(-6,7)**2/(2*2.5**2));k/=k.sum()
 for j in range(1,5):p[:,j]=np.convolve(np.pad(p[:,j],(6,6),mode='edge'),k,mode='valid')
 return p
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
c=np.load(W/'hands.npy');b=np.load(W/'baseline/mesh.npz')['co'];o=np.load(W/'original_coordinates.npy');row=654-c[:,2]/s;profiles={}
for sign in [-1,1]:
 p=profile(sign);profiles[str(sign)]=p.tolist();a0,a1,t0,t1=[np.interp(row,p[:,0],p[:,j]) for j in range(1,5)];x=sign*c[:,0]/s
 mapped=t0+(x-a0)*(t1-t0)/np.maximum(a1-a0,3)
 # Thumb preservation starts below the palm fork (canonical row 348).
 thumb=(1-smooth(.593,.617,abs(o[:,0])))*smooth(344,353,row)
 weight=smooth(326,337,row)*(1-smooth(374,380,row))*smooth(.50,.54,abs(o[:,0]))*(1-thumb)
 weight*=np.sign(c[:,0])==sign
 c[:,0]+=sign*np.clip(mapped-x,-6,6)*s*weight*.9
np.save(W/'fit_backbalanced.npy',c)
out={'method':'Existing unfolded hands with continuous shared palm/finger X-envelope correction toward both locked bald views, separate left/right; thumb retains its rounded volume. Reference/cameras/masks unchanged. No remesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'profiles':profiles,'scope':'Distal hands and wrist transition only; all head/torso/legs coordinates retained.'}
(W/'fit_backbalanced-edit.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='profiles'})
