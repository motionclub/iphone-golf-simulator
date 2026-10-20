"""Apply the legs/feet zone patch (Micro-parallel chat 4) to ANY newer base of HeroBase_Male_Silhouette.blend.
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python merge_legs.py -- <target.blend> [<out.blend>] [--dry]
Only the leg-zone vertex indices in legs_zone_patch.npz are written; the target's coordinates at those indices must still be the ORIGINAL
start coordinates (bit-identical float32), otherwise it aborts (somebody else touched the legs zone).  All other vertices/objects are left exactly as they are."""
import sys, numpy as np, bpy, os, hashlib
here=os.path.dirname(os.path.abspath(__file__))
argv=sys.argv[sys.argv.index('--')+1:]
dry='--dry' in argv; argv=[a for a in argv if a!='--dry']
target=argv[0]; out=argv[1] if len(argv)>1 else target
P=np.load(os.path.join(here,'legs_zone_patch.npz'))
idx=P['indices']; old=P['old']; new=P['new']
bpy.ops.wm.open_mainfile(filepath=target)
me=bpy.data.objects['Body_M'].data; n=len(me.vertices)
assert n>=int(P['verts']), f'target has {n} verts < patch base {int(P["verts"])}'
cur=np.empty(n*3,np.float64); me.vertices.foreach_get('co',cur); cur=cur.reshape(-1,3)
cur32=cur.astype(np.float32)
same_old=np.all(cur32[idx]==old,axis=1); same_new=np.all(cur32[idx]==new,axis=1)
print('zone verts at ORIGINAL coords:',int(same_old.sum()),'/',len(idx),' already patched:',int(same_new.sum()))
if same_new.all(): print('ALREADY_PATCHED'); sys.exit(0)
if not (same_old|same_new).all():
    print('ABORT: legs-zone vertices differ from both the original and the patched state; not touching the file'); sys.exit(2)
if dry: print('DRY_OK'); sys.exit(0)
cur[idx]=new.astype(np.float64)
me.vertices.foreach_set('co',cur.reshape(-1)); me.update()
tmp=out+'.tmp.blend'
bpy.ops.wm.save_as_mainfile(filepath=tmp,compress=True,relative_remap=(os.path.abspath(out)!=os.path.abspath(target)))
os.replace(tmp,out); print('MERGE_WRITTEN',out)
