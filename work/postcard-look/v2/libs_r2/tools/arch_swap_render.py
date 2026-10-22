"""Replace the installed hole 8 arch mesh by the one the CURRENT lib builds (same params, same placement) and render the Game camera + crops.
usage: Blender -b --factory-startup --python arch_swap_render.py -- OUTDIR [LIB.py]   (not Game-view proof)"""
import sys, os, json, math, importlib.util
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
libpath = a[1] if len(a) > 1 else REPO + "/blender/scripts/postcard_props_lib.py"
os.makedirs(out, exist_ok=True)
spec = importlib.util.spec_from_file_location("pl_under_test", libpath)
PL = importlib.util.module_from_spec(spec); sys.modules["pl_under_test"] = PL; spec.loader.exec_module(PL)
bpy.ops.wm.open_mainfile(filepath=REPO + "/blender/hole_08.blend")
LOOK = REPO + "/Unity/Assets/Resources/Course/Look/"
for im in bpy.data.images:
    if im.name.endswith(".png") and os.path.isfile(LOOK + im.name):
        im.filepath = LOOK + im.name; im.reload()
old = bpy.data.objects["DRESS_ARCH_00"]
mw = old.matrix_world.copy(); parent = old.parent; cols = list(old.users_collection)
r = PL.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=9.144, height_m=12.166265, seed=8, base_rock=False, vines=False, name="DRESS_ARCH_TMP")
new = r["arch"]
me = new.data
bpy.data.objects.remove(new, do_unlink=True)
old_me = old.data
old.data = me
if old_me.users == 0:
    bpy.data.meshes.remove(old_me)
if os.environ.get("DEBUG_MORTAR"):
    red = bpy.data.materials.new("DBG_RED"); red.use_nodes = True
    bsdf = red.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value = (1, 0, 0, 1)
    try:
        bsdf.inputs["Emission Color"].default_value = (1, 0, 0, 1); bsdf.inputs["Emission Strength"].default_value = 2.0
    except Exception:
        pass
    me.materials.append(red)
    uvl = me.uv_layers.active.data
    vr = PL.masonry_grid()[2]
    nred = 0
    for q in me.polygons:
        vs = [uvl[li].uv[1] for li in q.loop_indices]
        if max(vs) - min(vs) < 0.03 and abs(sum(vs) / len(vs) - vr) < 0.02:
            q.material_index = 1; nred += 1
    print("DEBUG red faces", nred, "of", len(me.polygons))
# spire library meshes: every instance of a ROCK_SEASTACK_* / ROCK_SPIRE_A (and _WET twin) mesh gets the CURRENT lib's mesh
allk = tuple(PL.SPIRE_KINDS) + tuple(k + "_WET" for k in PL.SPIRE_KINDS)
inst = [(ob, ob.data.name.split(".")[0]) for ob in bpy.data.objects
        if ob.type == 'MESH' and ob.data is not None and ob.data.name.split(".")[0] in allk and ob.name != ob.data.name]
for k in allk:                                   # drop the stale library objects / meshes of the opened blend so the CURRENT lib rebuilds them
    o_ = bpy.data.objects.get(k)
    if o_ is not None:
        bpy.data.objects.remove(o_, do_unlink=True)
    m_ = bpy.data.meshes.get(k)
    if m_ is not None:
        m_.name = k + "_stale"
repl = {}
for ob, nm in inst:
    if nm not in repl:
        repl[nm] = PL.library_object(nm).data
    ob.data = repl[nm]
print("SPIRE instances swapped", len(inst))
print("SWAPPED faces", len(me.polygons), [m.name for m in me.materials])
cfg = json.load(open(REPO + "/work/postcard-look/v2/hole08/landmarks.json"))
PV.setup_scene()
class DD: play_z = 6.0
D = DD(); YD = P.YD
byname = {s["name"]: s for s in cfg["shots"]}
for nm in os.environ.get("SHOTS", "hole08_arch").split(","):
    sh = byname[nm]
    if sh["kind"] == "address":
        c = PV.address_cam("CAM_F_" + nm, tuple(sh["ball"]), tuple(sh["aim"]), D)
    else:
        pos, look = sh["pos"], sh["look"]
        c = PV.cam("CAM_F_" + nm, (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
    PV.render(c, os.path.join(out, nm + ".png"), (900, 1600), 32)
print("RENDERED")
