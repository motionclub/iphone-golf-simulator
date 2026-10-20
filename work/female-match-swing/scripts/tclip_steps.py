import bpy, sys, math
A = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=A[A.index("--in")+1])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data_create()
act = next(a for a in bpy.data.actions if a.name.startswith("Rig_"))
rig.animation_data.action = act
BONES = ["LeftUpperArm","LeftLowerArm","LeftHand","RightUpperArm","RightLowerArm","RightHand"]
f0,f1 = [int(x) for x in act.frame_range]; prev = {}; out = {b: [] for b in BONES}
for f in range(f0, f1+1):
    bpy.context.scene.frame_set(f)
    for b in BONES:
        q = (rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion()
        if b in prev: out[b].append(math.degrees(2*math.acos(min(1,abs(q.dot(prev[b]))))))
        prev[b] = q
print("CLIPSTEP", A[A.index("--in")+1].split("/")[-1], f0, f1, " ".join(f"{b}:{max(out[b]):.0f}" for b in BONES))
