"""per-frame angular step (deg) of arm bones in a golfer FBX action. args: --in fbx --actions Drive,IronSwing"""
import bpy, sys, math
A = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return A[A.index(n)+1] if n in A else d
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=arg("--in"))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data_create()
BONES = ["Spine","LeftUpperArm","LeftLowerArm","LeftHand","RightUpperArm","RightLowerArm","RightHand","Club"]
for an in arg("--actions","Drive").split(","):
    act = next(a for a in bpy.data.actions if a.name.endswith("|"+an)); rig.animation_data.action = act
    f0,f1 = [int(x) for x in act.frame_range]; prev = {}; out = {b: [] for b in BONES}
    for f in range(f0, f1+1):
        bpy.context.scene.frame_set(f)
        for b in BONES:
            q = (rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion()
            if b in prev: out[b].append((f, math.degrees(2*math.acos(min(1,abs(q.dot(prev[b])))))))
            prev[b] = q
    print("CLIP", an, f0, f1)
    for b in BONES:
        big = [(f, round(a)) for f, a in out[b] if a > 12]
        print("STEPS", an, b, "max", round(max(a for f,a in out[b])), "frames>12:", big[:14])
