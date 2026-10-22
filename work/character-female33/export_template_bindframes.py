import bpy,numpy as np,json
from pathlib import Path
w=Path('work/character-female33');bpy.ops.wm.open_mainfile(filepath='work/character-finish32/Male_Polo_CuffRebuilt.blend');r=next(x for x in bpy.data.objects if x.type=='ARMATURE');M={b.name:np.array(r.matrix_world@b.matrix_local) for b in r.data.bones};ML={b.name:(b.tail_local-b.head_local).length for b in r.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Baseline.blend'));r=next(x for x in bpy.data.objects if x.type=='ARMATURE');F={b.name:np.array(r.matrix_world@b.matrix_local) for b in r.data.bones};FL={b.name:(b.tail_local-b.head_local).length for b in r.data.bones};J=np.diag([-1,1,1,1]);T={}
for name in M:
 cross=.77 if name in ['Hips','Spine','Chest'] else .84 if name in ['Neck','Head'] else .76 if 'Shoulder' in name else .73 if 'Arm' in name else .80
 S=np.diag([cross,np.clip(FL[name]/ML[name],.7,1.3),cross,1]);T[name]=(J@F[name]@S@np.linalg.inv(M[name])@J).tolist()
(w/'template-bindframes.json').write_text(json.dumps(T));print('DONE')
