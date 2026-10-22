"""Read-only Phase4 column adapter planning; writes scratch JSON only."""
import os, sys, json, types
sys.dont_write_bytecode = True
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, ROOT + '/blender/scripts')
import bpy, numpy as np
import postcard_lib as P
import postcard_props_lib as PL
import postcard_look_verify as V
rows = []
for height in (12.0, 30.0, 50.0):
    for nrow in (1, 2):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        PL._COUNTERS.clear()
        PL.reset_scatter(None)
        D = P.start('hole10_design', out_dir=ROOT + '/work/postcard-look/v3/hole10/no_export')
        obs = PL.build_column_wall(D, [(0, 0), (24, 0)], height,
                                   width_m=(.6, 1.8), rows=nrow,
                                   seed=4, name='ROCK_WALL_PLAN')
        snap = V.Snap('blend', types.SimpleNamespace(tag='10'))
        chunks = []
        for ob in obs:
            loc = snap.loc(ob)
            shape = V.rock_shape(loc)
            verts, tris = snap.oriented(ob)
            count, side = V.count_columns(verts, tris)
            width = float(np.linalg.norm(np.ptp(np.asarray([v.co[:] for v in ob.data.vertices])[:, :2], axis=0)))
            chunks.append(dict(name=ob.name, polygons=len(ob.data.polygons),
                               triangles=len(tris), pca_r3=float(shape['r3']),
                               pca_ok=shape['r3'] >= V.ROCK_TH['stretch_r3_min'],
                               shape_ok=shape['ok'], shape_why=shape['why'],
                               columns=count, side_area_fraction=side,
                               column_gate_ok=count >= V.TH['columns'] and side >= .45,
                               horizontal_aabb_diagonal=width))
        rows.append(dict(height=height, rows=nrow, chunks=chunks,
                         triangle_total=sum(c['triangles'] for c in chunks)))
with open(ROOT + '/work/postcard-look/v3/hole10/column_measurements.json', 'w') as f:
    json.dump(rows, f, indent=2)
print(json.dumps(rows, indent=2), flush=True)
