import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy, hashlib
from kitlib import *
cands = [
 ('female_authority', FEMALE_BLEND),
 ('female_arms_candidate', ROOT+'/work/female-arms-form2/export/HeroBase_Female_arms_candidate.blend'),
 ('female_limbs', ROOT+'/work/female-parallel-limbs/HeroBase_Female_limbs.blend'),
 ('female_torso_form4', ROOT+'/work/female-torso-form4/export/HeroBase_Female_torso_form4_candidate.blend'),
 ('female_preview_composite', ROOT+'/work/female-torso-form4/export/PREVIEW_form4_torso_plus_limbs_plus_arms_UNOFFICIAL.blend'),
 ('male_authority', MALE_BLEND),
 ('male_pelvis_f2_merged', ROOT+'/work/male-pelvis-form2/export/merged_fd04bc28.blend'),
]
for nm, p in cands:
    try:
        sha = hashlib.sha256(open(p,'rb').read()).hexdigest()[:12]
        bpy.ops.wm.open_mainfile(filepath=p)
        objs = [o for o in bpy.data.objects if o.type=='MESH']
        print(f"== {nm}  sha {sha}  objects {[(o.name, len(o.data.vertices)) for o in objs]}")
        for o in objs:
            if o.name.startswith('Body'):
                V,F = mesh_arrays(o)
                print("   ", o.name, "tris", len(F), "bbox", V.min(0).round(3).tolist(), V.max(0).round(3).tolist())
                # foot length near z<0.05 for x>0
                m = (V[:,2]<0.06)&(V[:,0]>0)
                print("    right foot y-range", V[m,1].min().round(3), V[m,1].max().round(3), " x-range", V[m,0].min().round(3), V[m,0].max().round(3))
    except Exception as e:
        print("ERR", nm, e)
