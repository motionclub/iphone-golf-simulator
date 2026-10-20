"""blender_compare.py  (run inside Blender: blender -b <HeroBase_<Sex>_MatchAnims.blend> --python blender_compare.py -- <sex> <out.json>)
Evaluates the armature in Blender at every frame of the clips Unity exported (data/unity_bones_<sex>_<clip>.json) and reports, per clip, the distance between
each bone's head in Blender and in Unity (both in Blender's axes, hero space)."""
import bpy, json, sys, math, os
sex, out = sys.argv[sys.argv.index('--')+1:][:2]
root = os.path.dirname(os.path.dirname(os.path.abspath(bpy.data.filepath))) if False else "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-mainstay/data"
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
res = {}
for clip in ("Ready", "Forehand", "Backhand", "Serve", "Smash", "Volley", "Return"):
    path = f"{root}/unity_bones_{sex}_{clip}.json"
    if not os.path.exists(path): continue
    d = json.load(open(path))
    action_name = {"Ready": "ReadyIdle", "Smash": "Overhead", "Volley": "VolleyForehand"}.get(clip, clip)
    act = bpy.data.actions[action_name]
    arm.animation_data.action = act
    worst = 0; total = 0; n = 0; worst_bone = ""; worst_frame = -1; per_frame_max = []
    for f, frame in enumerate(d["frames"]):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        fmax = 0
        for name, p in zip(d["bones"], frame):
            pb = arm.pose.bones.get(name)
            if pb is None: continue
            h = arm.matrix_world @ pb.head
            e = math.dist((h.x, h.y, h.z), p)
            total += e; n += 1; fmax = max(fmax, e)
            if e > worst: worst, worst_bone, worst_frame = e, name, f
        per_frame_max.append(fmax)
    res[d["clip"]] = {"frames": len(d["frames"]), "bones": len(d["bones"]), "max_mm": round(worst*1000, 4), "mean_mm": round(total/max(1,n)*1000, 4), "worst_bone": worst_bone, "worst_frame": worst_frame}
json.dump(res, open(out, "w"), indent=1)
print("BLENDER_COMPARE", sex, json.dumps(res))
