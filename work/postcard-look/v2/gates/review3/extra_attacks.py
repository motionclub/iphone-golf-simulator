"""Round-3 extra attacks of the builder (not the skeptic's): blender -b --factory-startup --python extra_attacks.py -- <hole> <name,name|all>
Positives: v2/gates/st3 (hole 8) / review_V/st2. Prints MUT <hole> <name> -> FAILED [...] (blend + fbx)."""
import sys, os, importlib.util, math, shutil
import numpy as np, bpy, bmesh
from mathutils import Vector
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
argv = sys.argv[sys.argv.index("--") + 1:]
H = int(argv[0]); ONLY = argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else None
ST = f"{REPO}/work/postcard-look/v2/review_V/st2/h{H}"
BLEND, POSFBX, LOOK = f"{ST}/hole_{H:02d}_pos.blend", f"{ST}/hole_{H:02d}_pos.fbx", f"{ST}/Look"
OUT = f"{REPO}/work/postcard-look/v2/gates/review3/out/extra"; os.makedirs(OUT, exist_ok=True)
OPTS = m.parse_args([str(H)])
MUTS = []
def mut(name):
    def d(fn): MUTS.append((name, fn)); return fn
    return d

@mut("foam_vertical_curtain_6m_offshore_continuous")
def _(C): m._skirt(C, "WATER_SURF_90", "LK_SURF", nz=None, run=0.0, drop=2.5, z_top=2.5, o_in=6.0)
@mut("foam_sloped_skirt_underwater_z-1")
def _(C): m._skirt(C, "WATER_SURF_91", "LK_SURF", nz=0.4, run=1.5, z_top=-0.5)
@mut("foam_skirt_at_9m_offshore_continuous_steep")
def _(C): m._skirt(C, "WATER_SURF_92", "LK_SURF", nz=0.2, run=1.0, z_top=3.0, o_in=9.0)
@mut("foam_skirt_11m_offshore_continuous")
def _(C): m._skirt(C, "WATER_SURF_93", "LK_SURF", nz=0.3, run=1.0, z_top=3.0, o_in=11.0)
@mut("foam_white_skirt_named_FLAG")
def _(C): m._skirt(C, "FLAG_SKIRT", "LK_SURF", nz=0.45, run=1.5, z_top=3.0)
@mut("rock_welded_icos_edge_shared_aligned")
def _(C):
    def mk(k):
        P0, F0 = m._cluster_template("ico12", "LK_ROCK")
        rng = np.random.default_rng(k)
        bm = bmesh.new(); verts = {}
        cells = [P0.copy()]
        for i in range(1, 8):
            Pj = cells[int(rng.integers(0, len(cells)))]
            # reflect the cell through one of its faces' plane -> shares a whole FACE with Pj (3 vertices)
            f = F0[int(rng.integers(0, len(F0)))]
            a, b, c = Pj[f[0]], Pj[f[1]], Pj[f[2]]
            n = np.cross(b - a, c - a); n /= np.linalg.norm(n)
            cells.append(Pj - 2 * ((Pj - a) @ n)[:, None] * n)
        for P in cells:
            loc = []
            for p in P:
                key = tuple(np.round(p, 5))
                if key not in verts: verts[key] = bm.verts.new(tuple(p))
                loc.append(verts[key])
            for f in F0:
                try: bm.faces.new([loc[i] for i in f])
                except ValueError: pass
        me = m.st_bm_mesh(f"FACESHARE{k}", bm, m._rm(C)); m.st_box_uv(me); return me
    m._swap_all_rocks(mk)
@mut("rock_poked_icosahedra_bundle_welded")
def _(C):
    def mk(k):
        rng = np.random.default_rng(k)
        P0, F0 = m._cluster_template("ico12", "LK_ROCK")
        bm = bmesh.new(); verts = {}; placed = []
        for i in range(7):
            Pn = P0 * rng.uniform(0.7, 1.1)
            if i:
                Pj = placed[int(rng.integers(0, i))]; Pn = Pn + (Pj[int(rng.integers(0, len(Pj)))] - Pn[int(rng.integers(0, len(Pn)))])
            placed.append(Pn)
        for P in placed:
            loc = []
            for p in P:
                key = tuple(np.round(p, 5))
                if key not in verts: verts[key] = bm.verts.new(tuple(p))
                loc.append(verts[key])
            for f in F0:
                try: bm.faces.new([loc[i] for i in f])
                except ValueError: pass
        bm.faces.ensure_lookup_table()
        fs = [bm.faces[int(i)] for i in rng.choice(len(bm.faces), 14, replace=False)]
        bmesh.ops.poke(bm, faces=fs, offset=0.05)
        me = m.st_bm_mesh(f"POKED{k}", bm, m._rm(C)); m.st_box_uv(me); return me
    m._swap_all_rocks(mk)

def main():
    for name, fn in MUTS:
        if ONLY and not any(k in name for k in ONLY): continue
        bpy.ops.wm.open_mainfile(filepath=BLEND, load_ui=False)
        C = m.st_ctx(H, dict(OPTS, look_dir=LOOK))
        try:
            fn(C)
        except Exception as e:
            print(f"MUT {H} {name} -> HARNESS-ERROR {type(e).__name__}: {e}", flush=True); continue
        mb = f"{OUT}/h{H}_{name}.blend"; bpy.ops.wm.save_as_mainfile(filepath=mb, copy=True)
        mf = f"{OUT}/h{H}_{name}.fbx"; m.st_export(H, mf)
        o = dict(OPTS, hole=H, blend=mb, fbx=mf, no_fbx=False, look_dir=LOOK, json=None)
        fails, res, _ = m.quiet_check(H, o)
        f0 = [f for f in fails]
        det = [r for r in res if not r["ok"] and r["name"].split("@")[0] in ("NO_FOAM_STRIP", "ROCK_NOT_ICOSAHEDRON", "ROCK_VARIETY")][:2]
        print(f"MUT {H} {name} -> FAILED {f0}", flush=True)
        for r in det: print("    ", r["name"], r["detail"][:260], flush=True)
        for p in (mb, mf):
            if os.path.exists(p): os.remove(p)
main()
