"""Blender -b STAGE.blend --python render_smoke_trial.py -- --cards cards.json --shots ... (render_views args): replace the DRESS_SMOKE cards by the cards of the json (smoke_probe format) and render with the stand-in smoke material."""
import sys, json, bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import postcard_props_lib as PL
a = sys.argv[sys.argv.index("--") + 1:]
cj = a[a.index("--cards") + 1]
rest = [x for i, x in enumerate(a) if not (x == "--cards" or (i > 0 and a[i - 1] == "--cards"))]
items = json.load(open(cj))
for o in [o for o in bpy.data.objects if o.name.startswith("DRESS_SMOKE")]:
    bpy.data.objects.remove(o, do_unlink=True)
root = bpy.data.objects["HOLE_10_ROOT"]
for (x, y, z, w, h, seed, fx, fy) in items:
    for ob in PL.build_smoke_cards(None, [((x, y, z), w, h)], seed=seed, face=(fx, fy)):
        ob.parent = root
sys.argv = [sys.argv[0], "--"] + rest
exec(open(REPO + "/work/postcard-look/v2/hole10/repair_r2/render_smoke_view.py").read())
