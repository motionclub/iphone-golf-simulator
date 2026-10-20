"""Refine the existing coordinates toward both fixed bald plate envelopes."""
from pathlib import Path
from PIL import Image
import numpy as np,json
W=Path(__file__).parent;R=W.parents[1];S=R/'work/male-silhouette';P=R/'ArtDir/hero/base_lock/proof/male_silhouette'
views=json.loads((S/'reference-cameras.json').read_text())['views'][:2];s=1.7/593
arrays=[(v,np.array(Image.open(S/(v['name']+'_target.png')))>127,np.array(Image.open(P/(v['name']+'.png')).getchannel('A'))>127) for v in views]
def spans(mask,v,y):
    py=round(v['sole_y']-(654-y)*s/v['metres_per_pixel']);xs=np.where(mask[max(0,min(719,py))])[0]
    if not len(xs):return []
    x=(xs-v['centre_x'])*v['metres_per_pixel']/s
    if v['angle_degrees']==180:x=-x
    x=np.sort(x);cuts=np.where(np.diff(x)>4)[0]+1;half=v['metres_per_pixel']/s/2
    return [[float(a[0]-half),float(a[-1]+half)] for a in np.split(x,cuts)]
def profile(lo,hi,kind,side):
    data=[]
    for y in range(lo,hi+1):
        values=[]
        for k in [2,1]:
            parts=[]
            for arr in arrays:
                sp=spans(arr[k],arr[0],y)
                if not sp:continue
                if kind=='outer':bounds=sp[0][0] if side<0 else sp[-1][1];parts.append([abs(bounds)])
                elif kind=='body':
                    central=[a for a in sp if a[0]<0<a[1]]
                    if central:parts.append([abs(central[0][0 if side<0 else 1])])
                elif kind=='arm' and len(sp)>=3:
                    a=sp[0] if side<0 else sp[-1];parts.append([abs(a[1]),abs(a[0])] if side<0 else a)
                elif kind=='leg' and len(sp)==2:
                    a=sp[0] if side<0 else sp[-1];parts.append([abs(a[1]),abs(a[0])] if side<0 else a)
            # Balance the two native gate errors while retaining a smooth shared contour.
            weights=[.53,.47] if k==1 and len(parts)==2 else None
            values.append(np.average(parts,axis=0,weights=weights).tolist() if parts else None)
        if all(v is not None for v in values):data.append([y,*values[0],*values[1]])
    a=np.array(data);k=np.array([1,2,3,4,3,2,1],float);k/=k.sum()
    for c in range(1,a.shape[1]):a[:,c]=np.convolve(np.pad(a[:,c],(3,3),mode='edge'),k,mode='valid')
    return a
def interp(a,y):return np.array([np.interp(y,a[:,0],a[:,c]) for c in range(1,a.shape[1])]).T
co=np.load(W/'revised_coordinates.npy');row=654-co[:,2]/s;ax=np.abs(co[:,0])/s
def smooth(a,b,y):t=np.clip((y-a)/(b-a),0,1);return t*t*(3-2*t)
for side in [-1,1]:
    indices=np.where(co[:,0]*side>0)[0];yy=row[indices];xx=ax[indices];nx=xx.copy()
    outer=interp(profile(155,233,'outer',side),yy);body=interp(profile(228,379,'body',side),yy)
    arm=interp(profile(228,372,'arm',side),yy);leg=interp(profile(395,651,'leg',side),yy)
    for j,(y,x) in enumerate(zip(yy,xx)):
        if 155<y<380:
            current,target=outer[j];nx[j]=x*target/current
            if y>=223:
                bc,bt=body[j];inn,out,tinn,tout=arm[j]
                if x<=bc:mapped=x*bt/bc
                elif x<=inn:mapped=bt+(tinn-bt)*(x-bc)/(inn-bc)
                elif x<=out:mapped=tinn+(tout-tinn)*(x-inn)/(out-inn)
                else:mapped=x+tout-out
                weight=smooth(223,231,y);nx[j]=nx[j]*(1-weight)+mapped*weight
        elif y>=390:
            inn,out,tinn,tout=leg[j]
            if x<=inn:mapped=x*tinn/inn
            elif x<=out:mapped=tinn+(tout-tinn)*(x-inn)/(out-inn)
            else:mapped=x+tout-out
            weight=smooth(390,408,y);nx[j]=x*(1-weight)+mapped*weight
    delta=np.clip(nx-xx,-3,3)*.70
    co[indices,0]+=side*delta*s
base=np.load(W/'baseline/mesh.npz')['co']
# The resumed head stage explicitly authorizes upper-head revisions.
# Preserve the current head coordinates; never restore the old scalp here.
np.save(W/'revised_coordinates.npy',co);dist=np.linalg.norm(co-base,axis=1)
report=json.loads((W/'coordinate-edit.json').read_text());report.update({'primary_contour_refinement':'Shared front/back lateral envelopes (front 0.53, back 0.47), separately for left and right, with continuous vertex displacement; no target/camera changes.','maximum_displacement_metres':float(dist.max()),'changed_vertices':int((dist>1e-8).sum()),'upper_head_vertices_unchanged':bool(np.array_equal(co[base[:,2]>1.54],base[base[:,2]>1.54]))})
(W/'coordinate-edit.json').write_text(json.dumps(report,indent=2));print('CONTOUR_REFIT',report['maximum_displacement_metres'])
