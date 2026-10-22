"""Reviewer: run the LIB_GROUND.md section-1 copy-paste blocks verbatim (plus the per-hole lines) on a frozen baseline build
redirected to a scratch out_dir. Blender -b --factory-startup --python doc_examples.py -- --hole 08"""
import sys, os, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import postcard_lib as P
args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2)
OUT = os.path.join(REPO, "work", "postcard-look", "review_ground", f"doc_hole{H}")
_o = P.start
P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit:
    pass
D = P._ST["D"]

# ------------------------------------------------------------- verbatim from LIB_GROUND.md section 1 (+ per-hole lines)
import postcard_look_lib as L

L.look_materials(D)                      # LK_* materials (call early; props libs reuse them by name)
snap = L.snapshot_ground(D)              # proof that play surfaces do not move
# ... the hole's own scenery: rocks, sea stacks, arch, plants (A4's postcard_props_lib) ...
if H != "10":
    L.retarget_materials(D)                  # MAT_* -> LK_*, WATER_FOAM* deleted (idempotent: call again after more MAT_* geometry)
if H == "09":
    R = D.SCENERY["ridge"]
    print("[doc] ridge width_yd =", R["width_yd"], "-> doc half width", max(R["width_yd"]) / 2 + 12.0, "(lib docstring uses 33.0)")
    L.assign_region_material(D, L.spine_polygon(R["spine"], max(R["width_yd"]) / 2 + 12.0), "LK_SCRUB")   # before assign_uvs
if H != "10":
    L.build_cliff_skin(D, style="strata")    # Needle / Split
    if H == "08":
        L.build_sea(D, shelf_m=(6.0, 14.0))                                   # default (10, 24) also passes the gates
        L.build_path(D, [(-9.0, -6.0), (-8.5, 12.0), (-6.0, 28.0), (-3.0, 40.0)], width_m=2.6)   # course yards -> DRESS_PATH_01
        bx0, by0, bx1, by1 = P._shore_bbox_m(D)
        x_m, y_m = bx1 + 8.0, (by0 + by1) / 2                                # a sea point east of the pads (doc leaves x_m, y_m open)
        L.surf_patch(D, (x_m, y_m), radius_m=6.0)                             # whitewater at the waterfall foot (WATER_SURF_nn)
    else:
        L.build_sea(D)                           # Needle / Split: ocean grid, WATER_SHELF, WATER_SURF_nn
else:
    L.retarget_materials(D, overrides=L.CRATER_OVERRIDES)                 # MAT_CLIFF / MAT_CLIFF_DARK / MAT_ROCK_DARK -> LK_BASALT
    loops = L.terrain_top_loops(D)
    pin = P.m(*D.hole.pin)
    pillar = [i for i, (Pl, _) in enumerate(loops) if P.point_in_poly(pin, [tuple(p) for p in Pl])]
    rim = [i for i in range(len(loops)) if i not in pillar]
    L.build_cliff_skin(D, style="basalt", loops=rim)                                  # vertical columns into the lava
    L.build_cliff_skin(D, style="basalt", loops=pillar, follow_undercut=1.0, seed=1)  # tapered bowl like crater.jpg
    L.build_lava(D, lights=4)                                                         # WATER_LAVA + LAVA_LIGHT_01..04
L.assign_uvs(D)                          # LAST (after any region material)
ok, detail = L.compare_ground(D, snap)   # must be True
print(f"GATE: DOC_COMPARE_GROUND {'PASS' if ok else 'FAIL'} - {detail}")
for name, ok, detail in L.audit_look(D):
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}")
P.render_overview(D); P.save(D)
L.export_look_fbx(D)                     # NOT P.export_fbx (see section 4)
# ------------------------------------------------------------- idempotency: second run of the re-runnable passes
n_before = sorted(o.name for o in L.bpy.data.objects)
L.retarget_materials(D, overrides=L.CRATER_OVERRIDES if H == "10" else None)
if H != "10":
    L.build_sea(D, shelf_m=(6.0, 14.0)) if H == "08" else L.build_sea(D)
L.assign_uvs(D)
n_after = sorted(o.name for o in L.bpy.data.objects)
ok2, d2 = L.compare_ground(D, snap)
print(f"GATE: DOC_RERUN_IDEMPOTENT {'PASS' if (n_before == n_after and ok2) else 'FAIL'} - objects {len(n_before)} -> {len(n_after)} "
      f"(added {sorted(set(n_after) - set(n_before))[:6]}, removed {sorted(set(n_before) - set(n_after))[:6]}); ground {d2}")
skins = [o for o in L.bpy.data.objects if o.name.startswith("ROCK_SKIN")]
L.build_cliff_skin(D, style="strata" if H != "10" else "basalt")       # what a careless second call (replace default False) does
skins2 = [o for o in L.bpy.data.objects if o.name.startswith("ROCK_SKIN")]
print(f"INFO: build_cliff_skin called a second time with the default replace=False: ROCK_SKIN objects {len(skins)} -> {len(skins2)}")
