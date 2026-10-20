"""Gate 2(b)+(c): prefab fingerprint before vs after the kit (MatchHeroKitBaseline output).  python3 scripts/compare_fp.py -> data/gate2_prefab.json"""
import json
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed'
b = json.load(open(W + '/baseline/prefab_before.json'))
a = json.load(open(W + '/baseline/prefab_after.json'))
res = {'heroes': {}}
ok = True
for hb, ha in zip(b['heroes'], a['heroes']):
    sex = hb['sex']
    assert sex == ha['sex']
    r = {}
    # nodes: every before-node must exist after with identical fields; after may only add Kit_* nodes
    nb = {n['path']: n for n in hb['nodes']}
    na = {n['path']: n for n in ha['nodes']}
    missing = [p for p in nb if p not in na]
    added = [p for p in na if p not in nb]
    changed = []
    for p, n in nb.items():
        if p in na:
            m = na[p]
            for k in ('parent', 'pos', 'rot', 'scale'):
                if n[k] != m[k]:
                    changed.append((p, k))
            if p != '.' and n['components'] != m['components']:
                changed.append((p, 'components'))
    root_before = nb['.']['components']
    root_after = na['.']['components']
    r['nodes'] = dict(before=len(nb), after=len(na), missing=missing, added=added, changed=changed, root_components_equal=root_before == root_after)
    r['added_only_kit'] = all(p.startswith('Kit_') for p in added) and len(added) == 6
    # meshes
    mb = {m['renderer']: m for m in hb['meshes']}
    ma = {m['renderer']: m for m in ha['meshes']}
    mdiff = []
    for k, m in mb.items():
        if k not in ma:
            mdiff.append((k, 'missing'))
            continue
        for f in ('mesh', 'kind', 'vertexCount', 'triangleCount', 'boneCount', 'subMeshCount', 'positionsSha', 'weightsSha', 'bindposesSha', 'trianglesSha', 'materials', 'bones', 'rootBone'):
            if m.get(f) != ma[k].get(f):
                mdiff.append((k, f))
    r['meshes'] = dict(before=len(mb), after=len(ma), differing=mdiff, added=[k for k in ma if k not in mb])
    # clips
    cb = {c['name']: c for c in hb['clips']}
    ca = {c['name']: c for c in ha['clips']}
    r['clips'] = dict(count=len(cb), differing=[k for k in cb if cb[k]['sha'] != ca[k]['sha'] or cb[k]['curveCount'] != ca[k]['curveCount'] or abs(cb[k]['length'] - ca[k]['length']) > 1e-6])
    r['animator_avatar_equal'] = hb['animatorAvatar'] == ha['animatorAvatar']
    r['pass'] = bool(not missing and not changed and r['added_only_kit'] and r['nodes']['root_components_equal'] and not mdiff and not r['clips']['differing'] and r['animator_avatar_equal'] and set(r['meshes']['added']) == {m for m in ma if m.startswith('Kit_')} and len(r['meshes']['added']) == 6)
    ok &= r['pass']
    res['heroes'][sex] = r
    print(sex, 'nodes', r['nodes']['before'], '->', r['nodes']['after'], 'added', added, 'changed', changed, 'mesh diffs', mdiff, 'clip diffs', r['clips']['differing'], 'PASS' if r['pass'] else 'FAIL')
res['pass'] = ok
json.dump(res, open(W + '/data/gate2_prefab.json', 'w'), indent=1)
print('GATE2_PREFAB', 'PASS' if ok else 'FAIL')
