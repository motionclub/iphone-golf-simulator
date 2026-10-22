import sys, os, importlib.util
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
argv = sys.argv[sys.argv.index("--") + 1:]
ok, d = m.g_still_floor_selfcheck(); print("SELF", "PASS" if ok else "FAIL", d)
for sd in argv:
    for h in (8, 9, 10):
        opts = m.parse_args([str(h), "--stills-dir", sd])
        design, dpath = m.load_design(h, None)
        C = m.Ctx(h, design, dpath, opts)
        ok, d = m.g_look_stills(C)
        print(f"STILLS {os.path.basename(sd)} hole{h}", "PASS" if ok else "FAIL", d)
