"""Run chosen gate functions of the verifier on one .blend or .fbx (fast iteration; not the full check).
usage: blender -b --factory-startup --python run_gate.py -- <hole> <file.blend|file.fbx> <GATE_FN[,GATE_FN...]> [look_dir]
GATE_FN = the function name in postcard_look_verify, e.g. g_no_foam_strip,g_rock_variety"""
import sys, os, importlib.util, time
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
hole = int(argv[0]); f = argv[1]; fns = argv[2].split(",")
look = argv[3] if len(argv) > 3 else None
opts = m.parse_args([str(hole)] + (["--look-dir", look] if look else []))
design, dpath = m.load_design(hole, None)
C = m.Ctx(hole, design, dpath, opts)
m.lib_signature()
if f.endswith(".fbx"):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=f); stage = "fbx"
else:
    bpy.ops.wm.open_mainfile(filepath=f, load_ui=False); stage = "blend"
S = m.Snap(stage, C)
FB = m.load_face_baseline(opts["sig_dir"], hole)
NB = m.load_nonup_baseline(opts["sig_dir"], hole)
sig = m.load_signature(opts["sig_dir"], hole)
for fn in fns:
    t = time.time()
    func = getattr(m, fn)
    try:
        if fn == "g_play_faces": r = func(S, C, FB)
        elif fn == "g_play_walls": r = func(S, C, NB)
        elif fn in ("g_one_green", "g_play_grid", "g_play_tops", "g_markers", "g_play_names", "g_reserved", "g_new_prefixes"): r = func(S, C, sig["stages"][stage]) if fn not in ("g_play_grid", "g_play_tops") else func(S, C, sig["stages"][stage], sig)
        else: r = func(S, C)
    except Exception as e:
        import traceback; traceback.print_exc(); r = (False, f"EXC {e}")
    print(f"RG {fn}@{stage} {'PASS' if r[0] else 'FAIL'} ({time.time()-t:.1f}s) - {r[1]}")
