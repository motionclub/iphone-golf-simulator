"""Binary gates from proof/metrics/*.json (measured on the re-imported FBX) -> GATE_RESULTS.md + gates.json.
System python3:  python3 gates.py
SHAPE_MATCH is an author read of the side-by-side sheet (target crop vs matching-angle render) against each asset's feature
checklist; Adnan's eye is final, so every line says what still differs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOD1_BAND = (0.25, 0.60)      # LOD1 / LOD0 triangles (brief: ~40 %)

# Author reads after the final build (sheets/<Name>.jpg). PASS = every checklist feature is present and the silhouette reads
# as the target's object at phone distance; the note says what still differs.
SHAPE = {
    'Lighthouse': (True, 'all 7 features; target tower a touch more slender, gallery house white'),
    'StepTemple': (True, 'tiers, centre stair, shrine; target stone is darker and mossier (in-game AO/shader will darken)'),
    'TwinFallsIsle': (True, 'jungle isle + summit temple + two-stage twin falls; outline rounder and more regular than the craggy target, '
                            'falls are flat white cards until the Unity scrolling water shader is on them'),
    'CalderaVolcano': (True, 'ridged cone, glowing crater, three lava rivers, plume card; target flank has more gullies'),
    'CalderaWall_A': (True, 'dark fluted caldera cliff, glowing lava line, lava-fall channel + card; target walls are more stepped'),
    'CalderaWall_B': (True, 'plain segment of the same ring'),
    'LookoutTower': (True, 'legs, braces, railed platform, red pyramid roof, flag; target roof is a deeper hip with log balcony rails'),
    'WitchCottage': (True, 'crooked stone + timber body, tall leaning purple roof, cauldron chimney with glow, smoke; target is more crooked'),
    'RopeBridge': (True, 'posts, sagging plank deck, two hand-lines, hangers'),
    'AlpineChalet': (True, 'log walls, thick snow roof, glowing windows, balcony, chimney + smoke, drifts'),
    'IceFishingHut': (True, 'plank hut on skids, snow roof, stovepipe, glowing window, fishing hole'),
    'Waterwheel': (True, 'brief-only (no ref view shows it): mill house, separate wheel, chute'),
    'MesaArch': (True, 'red sandstone arch with strata and flaring legs; target arch is more massive and blocky'),
    'WaterTower': (True, 'barrel tank with hoops, conical roof, trestle, ladder'),
    'StoneGate': (True, 'two carved pillars with tiki faces + lintel + vines (brief: carved stone gate); the tee target only shows one tall '
                        'totem pillar edge-on, with more stacked faces'),
    'StiltHut': (True, 'layered conical thatch, hut on railed deck, braced stilts, ladder, pier'),
    'Windmill': (True, 'brick base, red octagon body, white trims, gallery, dark cap, 4 lattice sails (separate part)'),
    'CanalBridge': (True, 'brick humpback arch with voussoir ring, parapets, coping, white rail'),
    'Farmhouse': (True, 'red brick, steep red roof, white barge boards, white-framed windows, green door, flower boxes'),
    'StoneGazebo': (True, 'round steps, 8 columns, entablature, ribbed terracotta dome, finial'),
    'Balustrade': (True, 'plinth, rail, turned balusters, capped post'),
    'Planter': (True, 'plinth, cream urn, mixed flower clump'),
    'ToriiGate': (True, 'brief-only (no ref view shows the h10 tee gate): basalt torii, curved kasagi, nuki, ember plaque'),
    'StoneLantern': (True, 'hex base, post, glowing light box, wide roof, finial'),
    'RangerHut': (True, 'plank hut, layered thatch, porch posts, glowing window, lava-glass sign; target thatch is shaggier palm-leaf'),
    'ObsidianArch': (True, 'chunky black arch, ember crack lines, boulder feet, glowing base seam'),
    'BasaltSpire': (True, 'ridged bullet spire with glowing trough seams + hex column ring'),
    'ShoreBand': (True, 'grass lip -> sand -> wet sand -> shallows, wavy, tiles'),
    'ShoreBand_Arc': (True, 'same profile on a 10-tile ring'),
    'BlackSandShore': (True, 'black sand with glowing tide line'),
    'CliffSkirt': (True, 'grass cap, cream limestone face, dark wet foot, boulders'),
    'FoamRing': (True, 'annulus foam card (look comes from the shore shader texture)'),
    'FoamStrip': (True, 'foam card following the ShoreBand waterline'),
    'RockShelf': (True, 'low limestone shelf with three tide pools, moss and anemone dots'),
}


def lods(m):
    re = m['reimport']
    shared = set(m.get('fx_shared', []))
    sh_names = {f"{m['name']}_{k}" for k in shared}
    t0 = sum(v['tris'] for n, v in re.items() if n.endswith('_LOD0'))
    t0s = sum(v['tris'] for n, v in re.items() if n in sh_names)
    t1 = sum(v['tris'] for n, v in re.items() if n.endswith('_LOD1'))
    t2 = sum(v['tris'] for n, v in re.items() if n.endswith('_LOD2'))
    return t0, t0s, t1, t2


def gate(m):
    name = m['name']
    re = m['reimport']
    out = {}
    t0, t0s, t1, t2 = lods(m)
    total0 = t0 + t0s
    out['TRIS'] = (total0 <= m['budget'] and t1 < t0, f'LOD0 {total0:,} (incl. {t0s} shared FX) <= {m["budget"]:,}; LOD1 {t1:,}; LOD2 {t2}')
    r = t1 / max(1, t0)
    has0 = any(n.endswith('_LOD0') for n in re); has1 = any(n.endswith('_LOD1') for n in re); has2 = any(n.endswith('_LOD2') for n in re)
    imp_ok = has2 if not m.get('no_impostor') else True
    out['LOD'] = (has0 and has1 and imp_ok and LOD1_BAND[0] <= r <= LOD1_BAND[1],
                  f'LOD0+LOD1 present, LOD1 = {r:.0%} of LOD0 (band {LOD1_BAND[0]:.0%}-{LOD1_BAND[1]:.0%}); ' +
                  ('LOD2 impostor cross-card present' if has2 else f"no LOD2 by design: {m.get('no_impostor_why', '')}"))
    lo, hi = m['bbox_fbx']
    dims = [hi[i] - lo[i] for i in range(3)]
    root = m['root']
    ident = all(v['rot_identity'] and all(abs(s - 1) < 1e-4 for s in v['scale']) for v in re.values())
    root_ok = root['found'] and all(abs(c) < 1e-6 for c in root['loc']) and all(abs(s - 1) < 1e-6 for s in root['scale'])
    static_at_origin = all(all(abs(c) < 1e-5 for c in v['loc']) for n, v in re.items()
                           if not any(n.startswith(f"{name}_{a}") for a, _ in m.get('animated', [])) and
                           not any(n == f"{name}_{k}" for k in m.get('fx_shared', [])))
    piv = m.get('pivot', 'base')
    inside = lo[0] <= 0 <= hi[0] and lo[1] <= 0 <= hi[1]
    if piv == 'base':
        zr = m.get('minz') or (-0.06, 0.06)
        zok = zr[0] <= lo[2] <= zr[1]; zt = f'min z {lo[2]:+.2f} in [{zr[0]}, {zr[1]}]'
    elif piv == 'waterline':
        zok = lo[2] < 0 < hi[2] or abs(lo[2] - hi[2]) < 1e-3; zt = f'spans sea level (z {lo[2]:+.2f}..{hi[2]:+.2f})'
    elif piv == 'anchor':
        zok = lo[2] < 0 < hi[2]; zt = f'posts rise above, deck sags below the anchor (z {lo[2]:+.2f}..{hi[2]:+.2f})'
    else:
        zok = True; zt = 'centre pivot'
    dim_ok = True; dtxt = []
    for ax, (a, b) in m['dims_expect'].items():
        v = dims['xyz'.index(ax)]
        dim_ok &= a <= v <= b; dtxt.append(f'{ax} {v:.2f} m in [{a}, {b}]')
    out['PIVOT_SCALE'] = (ident and root_ok and static_at_origin and inside and zok and dim_ok,
                          f"root at origin, scale 1: {root_ok}; all objects scale 1 / no rotation: {ident}; static meshes at origin: {static_at_origin}; "
                          f"pivot inside footprint: {inside}; {zt}; {', '.join(dtxt)}")
    bad = {n: v['check'] for n, v in re.items() if any(v['check'].values())}
    nclosed = sum(1 for v in re.values() if v['closed'])
    out['CLEAN'] = (not bad, f'{len(re)} meshes ({nclosed} closed solids checked for non-manifold/flipped; open cards checked for >2-face edges, '
                             f'loose, wire, degenerate): ' + ('all 0' if not bad else json.dumps(bad)))
    if m.get('tile_spec'):
        ts = m['tile']
        ok = bool(ts) and all(t['max_err_mm'] is not None and t['max_err_mm'] <= 1.0 for t in ts.values())
        out['TILE'] = (ok, '; '.join(f"{k}: ends {t['ends'][0]}/{t['ends'][1]} verts, worst {t['max_err_mm']} mm" for k, t in ts.items()))
    s_ok, s_note = SHAPE.get(name, (False, 'not reviewed'))
    tgt = m.get('target')
    out['SHAPE_MATCH'] = (s_ok, (f"vs targets/{tgt}.jpg: " if tgt else 'brief-only: ') + s_note)
    mats = sorted({mm for v in re.values() for mm in v['mats']})
    body = [x for x in mats if x.endswith('_Mat')]
    out['MATERIALS'] = (len(body) <= 1, f"{len(body)} body material ({', '.join(mats)})")
    return out, (t0 + t0s, t1, t2, dims, mats)


def main():
    ms = [json.loads(p.read_text()) for p in sorted((ROOT / 'proof/metrics').glob('*.json'))]
    order = ['A', 'B', 'C']
    ms.sort(key=lambda m: (m['kind'].startswith('shore'), not m['kind'].startswith('course landmark'), order.index(m['course']), m['name']))
    allg = {}
    rows = []
    names = ['SHAPE_MATCH', 'TRIS', 'LOD', 'PIVOT_SCALE', 'CLEAN', 'TILE', 'MATERIALS']
    fails = []
    for m in ms:
        g, info = gate(m)
        allg[m['name']] = {k: dict(pass_=v[0], why=v[1]) for k, v in g.items()}
        rows.append((m, g, info))
        for k, (ok, why) in g.items():
            if not ok:
                fails.append(f"- {m['name']} {k}: {why}")
    overall = not fails
    L = ['# GATE_RESULTS: Majestic landmark kit (L)', '',
         f"**GATE: LANDMARK_KIT {'PASS' if overall else 'FAIL'}** ({len(ms)} assets; gates measured on the re-imported FBX by "
         "`scripts/build.py`, judged by `scripts/gates.py`)", '']
    if fails:
        L += ['Failed lines:', ''] + fails + ['']
    L += ['SHAPE_MATCH is an author read of each side-by-side sheet (`sheets/<Name>.jpg`: target crop | matching-angle render | turntable, '
          'LOD1, LOD2). Adnan\'s eye is final; each line says what still differs.', '',
          '| asset | course | ' + ' | '.join(names) + ' |', '|' + '---|' * (len(names) + 2)]
    for m, g, info in rows:
        L.append(f"| {m['name']} | {m['course']} | " + ' | '.join(('PASS' if g[n][0] else '**FAIL**') if n in g else '-' for n in names) + ' |')
    L += ['', '## Detail', '']
    for m, g, info in rows:
        L.append(f"### {m['name']}")
        for n in names:
            if n in g:
                L.append(f"- `GATE: {n} {'PASS' if g[n][0] else 'FAIL'}` {g[n][1]}")
        L.append('')
    (ROOT / 'GATE_RESULTS.md').write_text('\n'.join(L))
    (ROOT / 'proof/gates.json').write_text(json.dumps(allg, indent=1))
    print('overall', 'PASS' if overall else 'FAIL'); print('\n'.join(fails))
    return rows


if __name__ == '__main__':
    main()
