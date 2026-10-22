import bpy, sys, json
ARGV = sys.argv[sys.argv.index("--")+1:]
res = {}
for path in ARGV:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    rig = next(o for o in bpy.data.objects if o.type=='ARMATURE')
    b = rig.data.bones
    def L(a,c): return round((b[c].head_local-b[a].head_local).length,4) if a in b and c in b else None
    info = dict(nbones=len(b), bones=[x.name for x in b][:80],
        meshes=[(o.name,len(o.data.vertices), o.parent_bone if o.parent_type=='BONE' else None) for o in bpy.data.objects if o.type=='MESH'],
        actions=[(a.name, tuple(a.frame_range)) for a in bpy.data.actions],
        rigscale=tuple(rig.scale), rigrot=tuple(rig.rotation_euler),
        upper=L('LeftUpperArm','LeftLowerArm'), fore=L('LeftLowerArm','LeftHand'), thigh=L('LeftUpperLeg','LeftLowerLeg'), shin=L('LeftLowerLeg','LeftFoot'),
        hipz=round(b['Hips'].head_local.z,4) if 'Hips' in b else None,
        headz=round(b['Head'].head_local.z,4) if 'Head' in b else None,
        shoulder_w=L('LeftUpperArm','RightUpperArm'))
    res[path.split('/')[-1]] = info
print("INSPECT_JSON", json.dumps(res))
