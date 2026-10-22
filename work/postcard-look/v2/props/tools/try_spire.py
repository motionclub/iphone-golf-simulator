import sys, os
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
for k in PL.SPIRE_KINDS:
    ob = PL.library_object(k)
    me = ob.data
    r = PL.seastack_report(me)
    print(k, "faces", r["faces"], "verts", len(me.vertices), "taper %.2f rise %.2f cap %.2f facets %d fills %s slices %d distinct %s ok %s" % (r["taper"], r["band_rise"], r["cap_share"], r["facets"], [round(f,2) for f in r["fills"]], r["slices"], r["distinct"], r["ok"]), r["why"])
    print("   widths", [round(w,2) for w in r["widths"]], "bbox", [round(x,1) for x in ob.dimensions])
    rep = PL.rock_shape_report(me)
    print("   shape", {k2: (round(v,3) if isinstance(v,float) else v) for k2,v in rep.items()})
