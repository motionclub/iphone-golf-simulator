"""Runs the verifier's sway gate rules (PLANT_SWAY_COLORS / PLANT_SWAY_CAPS) on the props library's OWN plant meshes (postcard_props_lib.library_object), as they are on disk right now.
usage: Blender -b --factory-startup --python props_lib_sway_probe.py"""
import sys, os
import bpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../../.."))
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import postcard_look_verify as V
import postcard_props_lib as PL

class Stub:
    def oriented(self, o):
        n = len(o.data.vertices)
        co = np.empty(n * 3); o.data.vertices.foreach_get("co", co)
        return co.reshape(-1, 3) @ np.array(o.matrix_world.to_3x3()).T, None

kinds = list(PL.PLANT_KINDS)
if not kinds:
    kinds = [k for k in getattr(PL, "KINDS", []) if k.startswith("PLANT_")]
print("kinds", len(kinds), kinds[:6])
amp, cross = V.sway_constants()
bad, rows = [], []
for k in kinds:
    ob = PL.library_object(k)
    st = V.sway_mesh_stats(Stub(), ob)
    kind, cap = V.sway_kind(k)
    if "rgba" not in st:
        bad.append(f"{k}: no colours"); continue
    tmin = V.SWAY_TH["tip_min_low"] if kind in V.SWAY_LOW_KINDS else V.SWAY_TH["tip_min"]
    disp = amp * np.sqrt(1 + cross ** 2) * st["tip"]
    prob = []
    if st["ncol"] != 1: prob.append("ncol")
    if st["root"] > V.SWAY_TH["root_max"]: prob.append(f"root {st['root']:.2f}")
    if st["tip"] <= tmin: prob.append(f"tip {st['tip']:.2f}")
    if st["b"] > V.SWAY_TH["b_max"]: prob.append("B")
    if st["a"] < V.SWAY_TH["a_min"]: prob.append("A")
    if st["corr"] < V.SWAY_TH["rise_corr"]: prob.append(f"corr {st['corr']:.2f}")
    if disp > cap + 1e-6: prob.append(f"cap {disp:.4f}>{cap}")
    rows.append(f"{k:18s} {kind:6s} nv {st['nv']:4d} root {st['root']:.3f} tip {st['tip']:.2f} corr {st['corr']:.2f} disp20 {disp:.4f} (cap {cap}) {'OK' if not prob else 'PROBLEM ' + ','.join(prob)}")
    if prob: bad.append(f"{k}: {prob}")
print("\n".join(rows))
print("PROBE:", "ALL OK" if not bad else f"{len(bad)} problem(s): {bad}")
