"""blender -b final.blend --python measure_final.py -- vertex_map.npz out.json : dimensions + finger/toe structure of the NEW geometry only."""
import bpy, numpy as np, json, sys
a=sys.argv[sys.argv.index('--')+1:]; vm=np.load(a[0]); out=a[1]
me=bpy.data.objects['Body_F'].data
mat={m.name:i for i,m in enumerate(me.materials)}
n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3)
new=vm['final_to_base']<0
fm=np.zeros(n,bool); hm=np.zeros(n,bool)
for p in me.polygons:
    vs=list(p.vertices)
    if p.material_index==mat['Skin_F']: fm[vs]=True
    elif p.material_index==mat['Base_Grey_F']: hm[vs]=True
feet=new&fm; hands=new&hm&~fm
res={}
def prom_count(xs,ys,bin_=0.002,prom=0.0012,span=7):
    bins=np.arange(xs.min(),xs.max()+bin_,bin_); prof=[]
    for i in range(len(bins)-1):
        m=(xs>=bins[i])&(xs<bins[i+1]); prof.append(ys[m].min() if m.any() else np.nan)
    prof=np.array(prof); ok=~np.isnan(prof); prof=np.interp(np.arange(len(prof)),np.where(ok)[0],prof[ok])
    cand=[]
    for i in range(1,len(prof)-1):
        if prof[i]<=prof[i-1] and prof[i]<=prof[i+1]:
            l=prof[max(0,i-span):i].max()-prof[i]; r=prof[i+1:i+1+span].max()-prof[i]
            if min(l,r)>=prom: cand.append(i)
    merged=[]
    for c in cand:
        if not merged or c-merged[-1]>2: merged.append(c)
    return len(merged)
for sd,name in ((1,'R'),(-1,'L')):
    P=V[feet&(np.sign(V[:,0])==sd)]
    xy=P[:,:2]-P[:,:2].mean(0); w,vec=np.linalg.eigh(np.cov(xy.T)); ax=vec[:,1]; proj=xy@ax
    toe=P[(P[:,1]<P[:,1].min()+0.050)&(P[:,2]<0.030)]
    res[f'foot_{name}']={'new_verts':int(len(P)),'length_along_axis_m':float(proj.max()-proj.min()),'y_length_m':float(P[:,1].max()-P[:,1].min()),
      'axis_toe_out_deg':float(np.degrees(np.arctan2(abs(ax[0]),abs(ax[1])))),'x_range':[float(P[:,0].min()),float(P[:,0].max())],
      'y_range':[float(P[:,1].min()),float(P[:,1].max())],'z_min':float(P[:,2].min()),'toe_tips_counted':prom_count(toe[:,0]*sd,toe[:,1])}
for sd,name in ((1,'R'),(-1,'L')):
    P=V[hands&(np.sign(V[:,0])==sd)]
    ax_=np.abs(P[:,0])
    fing=P[P[:,2]<0.745]
    # finger tips: lowest point per 3 mm bin along the finger-row axis (perpendicular to the finger direction, in the xy plane)
    c=fing[:,:2]-fing[:,:2].mean(0); w,vec=np.linalg.eigh(np.cov(c.T)); row=vec[:,1]
    u=c@row; z=fing[:,2]
    bins=np.arange(u.min(),u.max()+0.003,0.003); prof=[]
    for i in range(len(bins)-1):
        m=(u>=bins[i])&(u<bins[i+1]); prof.append(-z[m].min() if m.any() else np.nan)   # -z so tips are minima
    prof=np.array(prof); ok=~np.isnan(prof); prof=np.interp(np.arange(len(prof)),np.where(ok)[0],prof[ok])
    cand=[i for i in range(1,len(prof)-1) if prof[i]<=prof[i-1] and prof[i]<=prof[i+1] and min(prof[max(0,i-5):i].max()-prof[i],prof[i+1:i+6].max()-prof[i])>=0.0015]
    merged=[]
    for k in cand:
        if not merged or k-merged[-1]>1: merged.append(k)
    res[f'hand_{name}']={'new_verts':int(len(P)),'z_min_fingertip':float(P[:,2].min()),'length_from_wrist_crease_0.8456_m':float(0.8456-P[:,2].min()),
      'x_range':[float(P[:,0].min()),float(P[:,0].max())],'y_range':[float(P[:,1].min()),float(P[:,1].max())],'finger_tips_counted':len(merged)}
json.dump(res,open(out,'w'),indent=1); print(json.dumps(res,indent=1))
