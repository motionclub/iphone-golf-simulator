"""Read actual FBX interpolation and transforms, rather than Blender's forced-linear approximation.
Only supports this pipeline's pivot-free XYZ/RSrs FBX. Asserts unsupported transforms, validates against
Blender re-import on original linear files. Cubic slopes are read from the file, never invented here.
"""
from pathlib import Path
import sys,json,math
import numpy as np
from mathutils import Matrix,Euler
sys.path.insert(0,str(Path(__file__).parent))
import fbx_curves as FB
TIME=46186158000.
_CACHE={}
def expand(curve,key,width=1):
 raw=np.asarray(FB.data(curve,key));counts=np.asarray(FB.data(curve,b'KeyAttrRefCount'))
 if width>1:raw=raw.reshape(-1,width)
 return np.repeat(raw,counts,axis=0)
def evaluate(curve,t):
 if id(curve) not in _CACHE:_CACHE[id(curve)]=(curve,np.array(FB.data(curve,b'KeyTime'),float)/TIME,np.array(FB.data(curve,b'KeyValueFloat'),float),expand(curve,b'KeyAttrFlags'),expand(curve,b'KeyAttrDataFloat',4))
 _,keys,vals,flags,tangent=_CACHE[id(curve)];idx=int(np.clip(np.searchsorted(keys,t,side='right')-1,0,len(keys)-2));h=keys[idx+1]-keys[idx];u=np.clip((t-keys[idx])/h,0,1);mode=int(flags[idx])&14
 if mode==2:return vals[idx]
 if mode==4:return vals[idx]*(1-u)+vals[idx+1]*u
 if mode!=8:raise ValueError(('Unsupported FBX interpolation',mode))
 a,b=tangent[idx,:2]
 return (2*u**3-3*u*u+1)*vals[idx]+(u**3-2*u*u+u)*h*a+(-2*u**3+3*u*u)*vals[idx+1]+(u**3-u*u)*h*b

def read_pose(path,names,nframes,rate=1):
 root,version,models,channels=FB.read(path);connections=next(x for x in root.elems if x.id==b'Connections');parents={int(x.props[1]):int(x.props[2]) for x in connections.elems if x.props[0]==b'OO' and x.props[1] in models and x.props[2] in models};byname={m.props[1].split(b'\0')[0].decode():mid for mid,m in models.items()};props={}
 for mid,m in models.items():
  pp=next((e for e in m.elems if e.id==b'Properties70'),None);d={p.props[0].decode():p.props[4:] for p in pp.elems if p.id==b'P'} if pp else {}
  for attr in ['PreRotation','PostRotation','RotationOffset','RotationPivot','ScalingOffset','ScalingPivot','GeometricTranslation','GeometricRotation']:
   if attr in d and np.max(np.abs(d[attr]))>1e-9:raise ValueError(('Unsupported transform',m.props[1],attr,d[attr]))
  if d.get('RotationOrder',[0])[0]!=0:raise ValueError('Only XYZ supported')
  if d.get('InheritType',[1])[0]!=1:raise ValueError('Only RSrs supported')
  props[mid]=d
 globalM=Euler((math.pi/2,0,0),'XYZ').to_matrix().to_4x4();count=(nframes-1)*rate+1;M=np.zeros((count,len(names),4,4));HR=np.zeros((count,4,4));RC=np.zeros_like(HR);ARM=np.zeros_like(HR);SCALE=np.zeros((count,len(names),3));LOCAL=np.zeros_like(M)
 for f in range(count):
  t=f/(30*rate);worlds={};locals={};scales={}
  def pose(mid):
   if mid in worlds:return worlds[mid]
   nm=models[mid].props[1].split(b'\0')[0].decode();p=props[mid]
   def vec(prop,default):return np.array([evaluate(channels[nm,prop,a],t) if (nm,prop,a) in channels else p.get(prop,default)[i] for i,a in enumerate('XYZ')])
   tr=vec('Lcl Translation',[0,0,0]);rot=vec('Lcl Rotation',[0,0,0]);scale=vec('Lcl Scaling',[1,1,1]);R=Euler(tuple(rot*math.pi/180),'XYZ').to_matrix();local=R.to_4x4()
   for j in range(3):
    for i in range(3):local[i][j]*=float(scale[j])
   local.translation=tuple(tr);worlds[mid]=(pose(parents[mid]) if mid in parents else globalM)@local;locals[mid]=local;scales[mid]=scale;return worlds[mid]
  for j,nm in enumerate(names):mid=byname[nm];M[f,j]=np.array(pose(mid));LOCAL[f,j]=np.array(locals[mid]);SCALE[f,j]=scales[mid]
  for nm,arr in [('Hand_Racket',HR),('Racket_Classic',RC)]:arr[f]=np.array(pose(byname[nm]))
  armnm=next(nm for nm in byname if nm.startswith('Rig_'));ARM[f]=np.array(pose(byname[armnm]))
 return dict(M=M,HR=HR,RC=RC,ARM=ARM,SCALE=SCALE,LOCAL=LOCAL),channels

if __name__=='__main__':
 W=Path(__file__).resolve().parents[1];errors=[]
 for p in sorted((W/'data/before').glob('trace_*.npz')):
  z=np.load(p);meta=json.loads(str(z['meta']));native,channels=read_pose(meta['path'],meta['bones'],len(z['M']));delta=np.linalg.norm(native['M'][...,:3,3]-z['M'][...,:3,3],axis=-1).max()*1000;matrix=np.max(np.abs(native['M']-z['M']));errors.append(dict(clip=meta['clip'],hero=meta['hero'],worst_position_mm=float(delta),worst_matrix_element=float(matrix)));print('NATIVE_VALIDATION',meta['hero'],meta['clip'],delta,matrix,flush=True)
 (W/'proof/native_reader_validation.json').write_text(json.dumps(errors,indent=2))
