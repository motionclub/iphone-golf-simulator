"""Read-only binding adapter for the established P3 cliff outline method.

The chord predicate is compiled verbatim from the existing P3 script. Needle
uses its actual five-bed topology and exact shared endpoint columns. This
script never saves a Blender scene or exports/rebuilds any geometry.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[6]
V3 = ROOT / 'work/postcard-look/v3'
ROUND = V3 / 'p7/round1'
ESTABLISHED = V3 / 'hole09/scenery_metrics.py'
sys.path.insert(0, str(ROOT / 'blender/scripts'))
import postcard_lib as P
import postcard_look_lib as L

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

source = ESTABLISHED.read_text()
predicate = source[source.index('xy=np.asarray(outline);'):source.index('result=dict(blend=blend,')]
predicate_code = compile(predicate, str(ESTABLISHED), 'exec')

def original_run(outline):
    scope = dict(np=np, outline=outline)
    exec(predicate_code, scope)
    return dict(points=int(scope['n']), max_straight_run_m=float(scope['longest']),
                run_endpoints=scope['maxends'], chord_deviation_m=.10,
                limit_m=4., pass_gate=bool(scope['longest'] <= 4.))

result = dict(native_unmeasured=True, geometry_changed=False,
              established_script=str(ESTABLISHED), established_sha256=sha(ESTABLISHED),
              verbatim_predicate_sha256=hashlib.sha256(predicate.encode()).hexdigest(),
              original_chord_deviation_m=.10, original_limit_m=4., holes={})

# Use the original Split script without changing its source or extraction.
h9 = ROUND / 'rebuild/hole09/stage/hole_09.blend'
h9_raw = ROUND / 'round1_cliff_outline_h09_raw.json'
if h9_raw.exists():
    raise RuntimeError('Refusing to overwrite existing outline evidence')
sys.argv = [str(ESTABLISHED), '--', '--blend', str(h9), '--json', str(h9_raw)]
state = runpy.run_path(str(ESTABLISHED), run_name='__main__')
raw9 = state['result']
result['holes']['09'] = dict(blend=str(h9), blend_sha256=sha(h9),
    raw_json=str(h9_raw), raw_json_sha256=sha(h9_raw), native_unmeasured=True,
    method='Original P3 script unchanged: actual four-bed thirteen-row vertices',
    binding=dict(beds=4, rows_per_column=13, chunks=raw9['cliff']['chunks'],
                 loops=raw9['frozen_boundary']['loops']), cliff=raw9['cliff'],
    status='PASS' if raw9['cliff']['pass_gate'] else 'FAIL')

# Needle: change only extraction for its actual sixteen-row/five-bed topology.
h8 = ROUND / 'rebuild/hole08/stage/hole_08.blend'
entry = dict(blend=str(h8), native_unmeasured=True,
    method='Original P3 verbatim chord predicate; actual five-bed sixteen-row closed components',
    status='FAIL')
try:
    entry['blend_sha256'] = sha(h8)
    D = P.start('hole08_design', out_dir=str(ROUND / 'shared_checks'))
    bpy.ops.wm.open_mainfile(filepath=str(h8), load_ui=False)
    D.terrain = bpy.data.objects[D.terrain_name]
    terrain_loops = L.terrain_top_loops(D, D.terrain)
    D.loops = [xy.tolist() for xy, ids in terrain_loops]
    D._distfield = None
    skins = sorted((o for o in bpy.data.objects if o.type == 'MESH'
        and o.name.startswith('ROCK_SKIN_')
        and not all(c.name == 'ASSET_LIBRARY' for c in o.users_collection)), key=lambda o:o.name)
    nr = 16
    chunks = []
    for ob in skins:
        w = L._mesh_arrays(ob)[0]
        if len(w) % nr:
            raise RuntimeError(f'{ob.name}: unexpected five-bed topology')
        cols = w.reshape(-1, nr, 3)
        if len(ob.data.polygons) != (len(cols)-1)*(nr-1):
            raise RuntimeError(f'{ob.name}: not the actual complete sixteen-row strip')
        chunks.append(dict(name=ob.name, cols=cols,
            first=tuple(cols[0].ravel()), last=tuple(cols[-1].ravel())))
    starts = {}
    for i, chunk in enumerate(chunks):
        starts.setdefault(chunk['first'], []).append(i)
    if any(len(v) != 1 for v in starts.values()):
        raise RuntimeError('Ambiguous exact shared endpoint columns')
    unused = set(range(len(chunks)))
    components = []
    while unused:
        first = min(unused)
        current = first
        start_key = chunks[first]['first']
        columns = []
        names = []
        while True:
            if current not in unused:
                raise RuntimeError('Endpoint component repeats before exact closure')
            unused.remove(current)
            chunk = chunks[current]
            names.append(chunk['name'])
            columns.extend(chunk['cols'][:-1])
            if chunk['last'] == start_key:
                break
            followers = starts.get(chunk['last'], [])
            if len(followers) != 1:
                raise RuntimeError('Endpoint component has no unique exact continuation')
            current = followers[0]
        cols = np.asarray(columns)
        signed = P.signed_dist_m(D, cols[:,:,0].ravel(), cols[:,:,1].ravel()).reshape(-1,nr)
        xy = cols[np.arange(len(cols)), np.argmax(signed,axis=1), :2]
        outline = []
        for p in xy:
            if not outline or not np.array_equal(p,outline[-1]):
                outline.append(p.copy())
        if len(outline)>1 and np.array_equal(outline[-1],outline[0]):
            outline.pop()
        metric = original_run(outline)
        metric.update(chunks=names, exact_full_column_endpoint_closure=True,
                      outline_xy_m=np.asarray(outline).tolist())
        components.append(metric)
    complete = len(terrain_loops)==3 and len(components)==3 and bool(chunks) and not unused
    entry['binding'] = dict(beds=5, rows_per_column=nr, chunks=len(chunks),
        frozen_terrain_loops=len(terrain_loops), actual_exact_closed_components=len(components),
        every_skin_chunk_used_once=not unused, completeness_pass=complete)
    entry['cliff'] = dict(components=components,
        max_straight_run_m=max((x['max_straight_run_m'] for x in components),default=None),
        chord_deviation_m=.10, limit_m=4.,
        pass_gate=complete and all(x['pass_gate'] for x in components))
    entry['status'] = 'PASS' if entry['cliff']['pass_gate'] else 'FAIL'
except Exception as error:
    entry['error'] = f'{type(error).__name__}: {error}'
result['holes']['08'] = entry

h10 = ROUND / 'rebuild/hole10/stage/hole_10.blend'
result['holes']['10'] = dict(blend=str(h10), blend_sha256=sha(h10),
    status='FAIL', measured=False, native_unmeasured=True,
    reason='Actual legacy basalt prisms/backing have no strata outline or thirteen/sixteen-row binding; the established strata extractor is unsupported. No fabricated four-metre PASS.')
result['status'] = 'PASS' if all(x['status']=='PASS' for x in result['holes'].values()) else 'FAIL'
out = ROUND / 'round1_cliff_outline_current.json'
if out.exists():
    raise RuntimeError('Refusing to overwrite existing combined outline evidence')
out.write_text(json.dumps(result,indent=2)+'\n')
for hole, row in result['holes'].items():
    measured = row.get('cliff',{}).get('max_straight_run_m')
    print(f'GATE: CLIFF_OUTLINE_RUN_H{hole} {row["status"]} max_straight={measured} limit4m, native_unmeasured=True',flush=True)
print('RESULT: '+result['status'],flush=True)
