"""Coordinate-only anatomical volume repair of the current saved male mesh."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).parent;R=W.parents[1];data=np.load(W/'baseline/mesh.npz');base=data['co'];edges=data['edges'];co=base.copy()
s=1.7/593;offset=8.6606529209622
def smooth(a,b,v):
    t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
count=np.bincount(edges.ravel(),minlength=len(co))[:,None]
def lap(p):
    total=np.zeros_like(p);np.add.at(total,edges[:,0],p[edges[:,1]]);np.add.at(total,edges[:,1],p[edges[:,0]])
    return total/np.maximum(count,1)-p
row=654-base[:,2]/s;ax=np.abs(base[:,0])/s;dep=base[:,1]/s-offset
jaw=(1-smooth(31,40,ax))*smooth(120,130,row)*(1-smooth(156,169,row))
neck=(1-smooth(24,32,ax))*smooth(139,147,row)*(1-smooth(171,181,row))
feet=smooth(587,610,row)
shoulder=smooth(25,45,ax)*(1-smooth(112,145,ax))*smooth(163,180,row)*(1-smooth(239,259,row))
# Suppress small field ridges while retaining the existing connected mesh.
weights=np.maximum(jaw,np.maximum(neck*.6,shoulder*.65))
for _ in range(90):
    co+=.48*weights[:,None]*lap(co);co-=.50*weights[:,None]*lap(co)
for _ in range(65):
    delta=lap(co);co[:,1]+=.34*shoulder*delta[:,1]
for _ in range(55):
    delta=lap(co);co[:,1:]+=.46*feet[:,None]*delta[:,1:]
    delta=lap(co);co[:,1:]-=.49*feet[:,None]*delta[:,1:]
# Round the lower chin, retracting the old cap into the throat instead of
# leaving the head surface to close toward a forward-projecting point.
z=co[:,2];chin=np.array([[1.432,-.106],[1.441,-.114],[1.447,-.142],[1.456,-.167],
 [1.468,-.176],[1.486,-.174],[1.502,-.173],[1.517,-.171],[1.528,-.170]])
rows=[]
for height in np.arange(1.433,1.529,.002):
    ix=(abs(z-height)<.002)&(ax<15)
    if ix.any():rows.append([height,float(co[ix,1].min())])
rows=np.array(rows);front=np.interp(z,rows[:,0],rows[:,1]);target=np.interp(z,chin[:,0],chin[:,1])
chinweight=smooth(1.430,1.442,z)*(1-smooth(1.514,1.531,z))*(1-smooth(-.130,-.097,co[:,1]))*(1-smooth(25,35,ax))
co[:,1]+=(target-front)*chinweight
for _ in range(45):
    co+=.47*(jaw*.8+neck*.2)[:,None]*lap(co)
    co-=.49*(jaw*.8+neck*.2)[:,None]*lap(co)
under=smooth(1.421,1.440,co[:,2])*(1-smooth(1.466,1.489,co[:,2]))*(1-smooth(25,35,ax))
rear=smooth(-.175,-.103,co[:,1])*(1-smooth(-.100,-.074,co[:,1]))
co[:,2]+=.008*under*rear
for _ in range(30):
    delta=lap(co);co[:,1:]+=.46*(jaw*.65+neck*.35)[:,None]*delta[:,1:]
    delta=lap(co);co[:,1:]-=.48*(jaw*.65+neck*.35)[:,None]*delta[:,1:]
# Build smooth envelopes from this existing mesh, not from a replacement mesh.
def envelopes(rows,selection):
    ys=654-co[:,2]/s;out=[]
    for r in rows:
        ix=(abs(ys-r)<2.7)&selection(r)
        if ix.any():out.append([r,float(co[ix,1].min()),float(co[ix,1].max())])
    a=np.array(out);kernel=np.array([1,2,3,2,1],float)/9
    for c in [1,2]:a[:,c]=np.convolve(np.pad(a[:,c],(2,2),mode='edge'),kernel,mode='valid')
    return a
arm_sections=np.array(json.loads((R/'work/male-silhouette/blockout-sections.json').read_text())['arm'])
ax=np.abs(co[:,0])/s;ys=654-co[:,2]/s
axis=lambda y:np.interp(y,arm_sections[:,0],arm_sections[:,1])
width=lambda y:np.interp(y,arm_sections[:,0],arm_sections[:,2])
old_arm=envelopes(range(188,355),lambda r:ax>axis(r)-.35*width(r))
oldlo=np.interp(ys,old_arm[:,0],old_arm[:,1]);oldhi=np.interp(ys,old_arm[:,0],old_arm[:,2]);oldcentre=(oldlo+oldhi)/2
# A circular section normal to the diagonal arm has a smaller depth radius
# than its horizontal X extent. Full, oval deltoids blend into that cylinder.
targets=np.array([[185,-.025,.074],[200,-.037,.086],[218,-.039,.085],[235,-.035,.073],
 [250,-.036,.059],[270,-.047,.056],[290,-.061,.053],[310,-.081,.041],[330,-.098,.034],[350,-.105,.026],[358,-.105,.022]])
centre=np.interp(ys,targets[:,0],targets[:,1]);radius=np.interp(ys,targets[:,0],targets[:,2])
armweight=smooth(175,190,ys)*(1-smooth(346,362,ys))*smooth(axis(ys)-width(ys)-5,axis(ys)-width(ys)+8,ax)
mapped=centre+(co[:,1]-oldcentre)*radius/np.maximum((oldhi-oldlo)/2,.01)
co[:,1]=co[:,1]*(1-armweight)+mapped*armweight
# Blend the deltoid/pectoral join by fairing depth, leaving the existing
# front/back silhouette coordinates nearly unchanged.
for _ in range(150):
    delta=lap(co);co[:,1]+=.30*shoulder*delta[:,1]
# Fill the depression at the front deltoid/pectoral join with a smooth union
# of their rounded envelopes. Existing X/Z contour coordinates remain intact.
ys=654-co[:,2]/s;axm=np.abs(co[:,0]);z=co[:,2]
torso=np.array(json.loads((R/'work/male-silhouette/blockout-sections.json').read_text())['torso'])
tw=np.interp(ys,torso[:,0],torso[:,1])*s;td=np.interp(ys,torso[:,0],torso[:,2])*s;tc=(np.interp(ys,torso[:,0],torso[:,3])+offset)*s
u=1-(axm/np.maximum(tw,.01))**2;tf=tc-td*np.sqrt(np.maximum(u,0));tf[u<0]=10
v=1-((axm-.245)/.095)**2-((z-1.275)/.14)**2;df=-.032-.098*np.sqrt(np.maximum(v,0));df[v<0]=10
k=.018;h=np.maximum(k-np.abs(tf-df),0)/k;envelope=np.minimum(tf,df)-h*h*k*.25
fill=shoulder*smooth(.105,.145,axm)*(1-smooth(.305,.345,axm))*(1-smooth(-.038,-.018,co[:,1]))
co[:,1]+=np.minimum(0,envelope-co[:,1])*fill
for _ in range(65):
    delta=lap(co);co[:,1]+=.28*shoulder*delta[:,1]
# Fair the joined upper torso in all three coordinates so the original
# intersection crease does not survive as a normal discontinuity/cavity.
upper=(1-smooth(.34,.42,np.abs(co[:,0])))*smooth(1.09,1.17,co[:,2])*(1-smooth(1.38,1.43,co[:,2]))
for _ in range(100):
    co+=.46*upper[:,None]*lap(co);co-=.48*upper[:,None]*lap(co)
for _ in range(50):co+=.32*upper[:,None]*lap(co)
# Give the existing foot a lower rounded toe, an instep slope and a heel.
oldfoot=envelopes(range(587,654),lambda r:ax>30)
ys=654-co[:,2]/s;z=co[:,2]
fl=np.interp(ys,oldfoot[:,0],oldfoot[:,1]);fh=np.interp(ys,oldfoot[:,0],oldfoot[:,2]);fc=(fl+fh)/2
foot=np.array([[0,-.194,.052],[.012,-.217,.070],[.032,-.222,.076],[.050,-.218,.073],
 [.075,-.188,.066],[.10,-.137,.064],[.13,-.119,.059],[.16,-.097,.054],[.20,-.089,.050],[.25,-.077,.045]])
lo=np.interp(z,foot[:,0],foot[:,1]);hi=np.interp(z,foot[:,0],foot[:,2]);newc=(lo+hi)/2
footweight=(1-smooth(.20,.25,z))
# Refit the existing horizontal sections to rounded volumes. Transverse
# widths and height are retained; only the front/back depth is assigned.
sections=[]
for r in range(551,655):
    ix=(abs(ys-r)<2.7)&(ax>30)
    if ix.any():sections.append([r,float(ax[ix].min()),float(ax[ix].max())])
sections=np.array(sections);kernel=np.array([1,2,3,2,1],float)/9
for c in [1,2]:sections[:,c]=np.convolve(np.pad(sections[:,c],(2,2),mode='edge'),kernel,mode='valid')
xlo=np.interp(ys,sections[:,0],sections[:,1]);xhi=np.interp(ys,sections[:,0],sections[:,2])
u=(ax-(xlo+xhi)/2)/np.maximum((xhi-xlo)/2,1)
radial=np.sqrt(np.maximum(.004,1-u*u));sign=np.where(co[:,1]>=fc,1,-1)
ratio=2*(co[:,1]-fc)/np.maximum(fh-fl,.015)
ratio=ratio/(1+(np.abs(ratio)/1.04)**12)**(1/12)
continuous=newc+ratio*(hi-lo)/2
circular=newc+sign*radial*(hi-lo)/2
projection=.65*smooth(.009,.035,z)
mapped=continuous*(1-projection)+circular*projection
co[:,1]=co[:,1]*(1-footweight)+mapped*footweight
for _ in range(95):
    delta=lap(co);co[:,1:]+=.46*feet[:,None]*delta[:,1:]
    delta=lap(co);co[:,1:]-=.49*feet[:,None]*delta[:,1:]
fair=1-smooth(.17,.25,co[:,2])
for _ in range(90):
    co+=.46*fair[:,None]*lap(co);co-=.48*fair[:,None]*lap(co)
for _ in range(35):co+=.32*fair[:,None]*lap(co)
# Broad planar contact patches underneath the toe and heel, with a soft fade.
z=co[:,2];ground=.0025;low=z<.028
t=np.clip((z-.006)/.022,0,1);flattened=ground+(z-ground)*(.12+.88*t*t*(3-2*t))
co[low,2]=flattened[low]
disp=np.linalg.norm(co-base,axis=1);np.save(W/'revised_coordinates.npy',co)
report={'method':'Existing vertex coordinates only: regional fairing, round arm-depth sections, swept rounded chin/throat, profiled instep/toe/heel and planar sole contact. No remesh or replacement mesh.',
 'source_baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],
 'changed_vertices':int((disp>1e-8).sum()),'maximum_displacement_metres':float(disp.max()),'height_metres':float(np.ptp(co[:,2])),
 'arm_targets':targets.tolist(),'foot_targets':foot.tolist(),'ground_metres':ground,'scope':'Male form D; latest user silhouette threshold 2%.'}
(W/'coordinate-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['changed_vertices','maximum_displacement_metres','height_metres']},indent=2))
