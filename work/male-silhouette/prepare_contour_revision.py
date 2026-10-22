"""Primary-plate contour deltas in metres, for edits to the existing mesh."""
from pathlib import Path
from PIL import Image
import numpy as np,json
W=Path(__file__).parent;R=W.parents[1];P=R/'ArtDir/hero/base_lock/proof/male_silhouette'
views=json.loads((W/'reference-cameras.json').read_text())['views'][:2]
s=1.7/593
def spans(mask,v,y):
    py=round(v['sole_y']-(654-y)*s/v['metres_per_pixel'])
    if not 0<=py<720:return []
    xs=np.where(mask[py])[0]
    if not len(xs):return []
    x=(xs-v['centre_x'])*v['metres_per_pixel']/s
    if v['angle_degrees']==180:x=-x
    x=np.sort(x);cuts=np.where(np.diff(x)>4)[0]+1
    return [[float(a[0]),float(a[-1])] for a in np.split(x,cuts)]
arrays=[]
for v in views:
    arrays.append((v,np.array(Image.open(W/(v['name']+'_target.png')))>127,
                   np.array(Image.open(W/'micro1-baseline'/(v['name']+'.png')).getchannel('A'))>127))
def mean_profile(y,kind):
    out=[]
    for index in [1,2]:
        measurements=[]
        for v,t,m in arrays:
            sp=spans(t if index==1 else m,v,y)
            if not sp:continue
            if kind=='outer':
                measurements.append([(sp[-1][1]-sp[0][0])/2])
            elif kind=='body':
                central=[a for a in sp if a[0]<=0<=a[1]]
                if central:measurements.append([(central[0][1]-central[0][0])/2])
            elif kind=='arms' and len(sp)>=3:
                measurements.extend([[abs(sp[0][1]),abs(sp[0][0])],[sp[-1][0],sp[-1][1]]])
            elif kind=='legs' and len(sp)==2:
                measurements.extend([[abs(sp[0][1]),abs(sp[0][0])],[sp[-1][0],sp[-1][1]]])
        out.append(np.mean(measurements,axis=0).tolist() if measurements else None)
    return out
def rows(lo,hi,kind):
    data=[]
    for y in range(lo,hi+1):
        target,current=mean_profile(y,kind)
        if target is not None and current is not None:data.append([y,*current,*target])
    a=np.array(data)
    # Smooth contour measurements over seven source rows; never smooth the mesh.
    k=np.array([1,2,3,4,3,2,1],float);k/=k.sum()
    for c in range(1,a.shape[1]):a[:,c]=np.convolve(np.pad(a[:,c],(3,3),mode='edge'),k,mode='valid')
    return a.tolist()
report={'metres_per_canonical_pixel':s,'outer':rows(64,379,'outer'),'body':rows(234,379,'body'),'arms':rows(234,371,'arms'),'legs':rows(390,651,'legs'),
        'method':'Shared symmetric front/back contour corrections applied to existing Body_M vertices; fixed source masks and cameras. No depth, topology, object-transform or image changes.'}
(W/'contour-revision.json').write_text(json.dumps(report,indent=2))
print({k:len(report[k]) for k in ['outer','body','arms','legs']})
