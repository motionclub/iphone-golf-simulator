import bpy,pathlib,json,numpy as np
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish29/smooth-mouth1';out={}
def take(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));b=bpy.data.objects['Body'];m=b.data;a=np.array([tuple(v.co) for v in m.vertices]);return a,np.array([tuple(u.uv) for u in m.uv_layers[0].data]),np.array([tuple(c.color) for c in m.color_attributes['SkinPigment'].data]),np.array([tuple(n.vector) for n in m.corner_normals]),np.array([l.vertex_index for l in m.loops]),np.any(np.array([np.linalg.norm(np.array([tuple(p.co) for p in k.data])-a,axis=1)>1e-7 for k in m.shape_keys.key_blocks if k.name!='Basis']),axis=0)
for sex in ('Male','Female'):
 a,uv,col,n,ids,blink=take(R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend');b,v,c,nn,j,_=take(O/f'{sex}_OriginalFaceFinish29Smooth1.blend');assert np.array_equal(ids,j)
 ud=np.max(abs(uv-v),axis=1)>1e-7;cd=np.max(abs(col-c),axis=1)>1e-7
 z0=1.50648 if sex=='Male' else 1.476;region=(abs(a[:,0])<.041)&(abs(a[:,2]-z0)<.036)&(a[:,1]<-.08)
 assert not np.any(ud & ~region[ids]);assert not np.any(cd&~region);assert np.max(abs(a[blink]-b[blink]))==0
 dn=np.linalg.norm(n-nn,axis=1);eyeMax=float(dn[blink[ids]].max());print('EYE_NORMAL',sex,eyeMax,'count',int(np.sum(dn[blink[ids]]>1e-5)),flush=True)
 out[sex]={'gate':'PASS','uvChangedLoops':int(ud.sum()),'colorChangedVertices':int(cd.sum()),'uvColorOutsideMouthExact':True,'blinkActivePositionsExact':True,'maxBlinkActiveCornerNormalDelta':eyeMax,'mouthRegionRestBounds':{'absXMax':.041,'absZFromCentreMax':.036,'frontYMax':-.08},'maxCornerNormalDelta':float(dn.max())}
(O/'mouth-bounds-gate.json').write_text(json.dumps({'gate':'PASS','results':out},indent=2)+'\n');print(json.dumps(out,indent=2))
