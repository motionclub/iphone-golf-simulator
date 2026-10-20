import bpy, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]; START,FINAL=a
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p); me=bpy.data.objects['Body_F'].data
    n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3)
    cn=np.array([tuple(x.vector) for x in me.corner_normals],np.float32); lv=np.array([l.vertex_index for l in me.loops])
    return V.copy(),cn,lv
sv,scn,slv=load(START); fv,fcn,flv=load(FINAL)
fkey={tuple(p):i for i,p in enumerate(fv)}
# new verts outside tight zone
skeys={tuple(p) for p in sv}
new=np.array([tuple(p) not in skeys for p in fv])
in_zone=lambda P:(P[:,2]<0.58)|((np.abs(P[:,0])>0.195)&(P[:,2]>0.60)&(P[:,2]<0.875))
bad=new&~in_zone(fv)
print('new outside tight zone',bad.sum(),'x range',np.abs(fv[bad][:,0]).min(),np.abs(fv[bad][:,0]).max(),'z range',fv[bad][:,2].min(),fv[bad][:,2].max())
# corner normal diffs on loops of baseline verts present in final (bit identical positions) and outside zone
d=[];
smap={}
for l,v in enumerate(slv): smap.setdefault(tuple(sv[v]),[]).append(l)
fmap={}
for l,v in enumerate(flv): fmap.setdefault(tuple(fv[v]),[]).append(l)
cnt=0; zs=[]; ang=[]
for k,ls in smap.items():
    if k in fmap and not in_zone(np.array([k]))[0]:
        for a_,b_ in zip(ls,fmap[k]) if len(ls)==len(fmap[k]) else []:
            if not np.array_equal(scn[a_],fcn[b_]):
                cnt+=1; zs.append(k[2]); ang.append(np.degrees(np.arccos(np.clip((scn[a_]*fcn[b_]).sum(),-1,1))))
print('differing corners (vertex-position matched, order-matched)',cnt)
if cnt:
    zs=np.array(zs); print('z hist',np.histogram(zs,bins=[0,0.58,0.62,0.7,0.84,0.88,0.95,1.2,1.8])[0],'max angle deg',max(ang))
