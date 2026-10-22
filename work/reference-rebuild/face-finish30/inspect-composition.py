import bpy,pathlib,numpy as np,json,hashlib
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30';report={}
for sex in ('Male','Female'):
 d=np.load(R/f'work/reference-rebuild/face-finish30-lids/{sex.lower()}-operation.npz');mask=d['mask']>0;n=len(mask);arr={}
 for label,path in [('broad',O/f'final/{sex}_OriginalFaceFinish30Final.blend'),('ears',O/f'ears/{sex}_OriginalFaceFinish30Ears.blend')]+([('standalone',R/f'work/reference-rebuild/face-finish30-lids/{sex}_Face30Lids.blend'),('composed',O/f'composed-female/{sex}_OriginalFaceFinish30Composed.blend')]if sex=='Female'else[]):
  bpy.ops.wm.open_mainfile(filepath=str(path));m=bpy.data.objects['Body'].data;arr[label]={k.name:np.array([v.co[:]for v in k.data])[:n]for k in m.shape_keys.key_blocks};arr[label]['mesh']=np.array([v.co[:]for v in m.vertices])[:n]
 report[sex]={'earMaskPositionErrorMm':float(np.linalg.norm(arr['ears']['mesh'][mask]-arr['broad']['mesh'][mask],axis=1).max()*1000),'operationSha256':hashlib.sha256((R/f'work/reference-rebuild/face-finish30-lids/{sex.lower()}-operation.npz').read_bytes()).hexdigest()}
 if sex=='Female':
  report[sex]['composedVsStandaloneActiveMm']={k:float(np.linalg.norm(arr['standalone'][k][mask]-arr['composed'][k][mask],axis=1).max()*1000)for k in arr['composed']};report[sex]['composedVsExpectedActiveMm']={k:float(np.linalg.norm(arr['composed'][k][mask]-arr['broad'][k][mask]-d[k if k!='mesh'else'Basis'][mask],axis=1).max()*1000)for k in arr['composed']}
(O/'COMPOSITION_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2));print(report)
