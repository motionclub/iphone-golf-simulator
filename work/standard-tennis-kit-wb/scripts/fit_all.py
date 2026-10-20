"""Full fit audit.  blender -b --factory-startup --python fit_all.py

Per piece vs every body variant (authority + staged candidates):
  min vertex clearance (mm), #vertices below 0 / below 1 mm, #overlapping triangle pairs (BVH).
Layering: polo<->bottom (tucked polo: NO overlapping triangles required; inside/outside is by design), sock<->shoe, bottom<->sock.
Skin coverage (no skin gaps): waist band between polo and bottom, and the whole foot under sock+shoe (rays from the skin along its normal must hit a garment).
Writes proof/fit_results.json.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from fitbody import *
from fitcheck import clearance, overlap_pairs

MIN_OK = 0.001           # 1 mm minimum clearance required


def load_part(name, gender):
    d = np.load(f'{WORK}/data/{name}_{gender}.npz')
    return d['V'], d['F']


def check(Vg, Fg, body, nohand=False):
    tree = body['tree_nohand'] if nohand else body['tree']
    mesh = body['mesh_nohand'] if nohand else (body['V'], body['F'])
    d = clearance(Vg, tree)
    pairs = overlap_pairs(Vg, Fg, *mesh)
    return dict(min_mm=round(float(d.min()) * 1000, 2), neg=int((d < 0).sum()), lt1mm=int((d < MIN_OK).sum()), overlap_pairs=len(pairs), verts=len(Vg), tris=len(Fg))


def body_normals(V, F):
    return vertex_normals(V, F)


def coverage(body, garments, vmask, label, dirs, reach=1.5):
    """tube-closure test: a body vertex counts as covered when a ray from it in EACH direction of `dirs` hits one of the garment meshes
    (rays pass through the body itself).  Any missing hit = a gap in the garment ring at that height or under the foot."""
    V = body['V']
    trees = [bvh_from(g[0], g[1]) for g in garments]
    idx = np.nonzero(vmask)[0]
    miss = []
    for i in idx:
        p = V[i]
        ok = True
        for d in dirs:
            hit = False
            for t in trees:
                loc, n, fi, dist = t.ray_cast((p + np.array(d) * 1e-4).tolist(), list(d), reach)
                if fi is not None:
                    hit = True
                    break
            if not hit:
                ok = False
                break
        if not ok:
            miss.append(i)
    miss = np.array(miss, int)
    res = dict(label=label, tested=int(len(idx)), uncovered=int(len(miss)))
    if len(miss):
        res['uncovered_bbox_min'] = V[miss].min(0).round(3).tolist()
        res['uncovered_bbox_max'] = V[miss].max(0).round(3).tolist()
    return res


def main():
    out = {}
    for gender, parts in (('male', ['polo', 'shorts', 'sock', 'shoe']), ('female', ['polo', 'skort', 'sock', 'shoe'])):
        bodies = load_set(gender)
        add_nohand_trees(bodies, gender)
        res = {}
        for part in parts:
            Vg, Fg = load_part(part, gender)
            for b in bodies:
                if gender == 'female' and part in ('sock', 'shoe') and b['name'] == 'female_authority':
                    r = check(Vg, Fg, b)
                    r['note'] = 'arms-candidate-fit footwear vs the placeholder baseline feet (184 mm, ankle 38 mm forward): informational only'
                    res[f'{part}_armscandfit|{b["name"]}'] = r
                    continue
                nh = (gender == 'female' and part == 'skort' and b['name'] != 'female_authority')
                r = check(Vg, Fg, b, nohand=nh)
                if nh:
                    r['note'] = 'hanging hand/forearm (incl. cupped thumb 2 mm off the hip) excluded for the candidate'
                res[f'{part}|{b["name"]}'] = r
        # (for the female the primary footwear set is the authority-fit one; keep the arms-candidate-fit set under its own keys)
        if gender == 'female':
            for part in ('sock', 'shoe'):
                for key in [k for k in res if k.startswith(f'{part}|')]:
                    res[key.replace(f'{part}|', f'{part}_armscandfit|')] = res.pop(key)
            for part in ('sock', 'shoe'):
                Vg, Fg = load_part(part, 'female_auth')
                for b in bodies:
                    r = check(Vg, Fg, b)
                    if b['name'] != 'female_authority':
                        r['note'] = 'informational (authority-fit footwear on the candidate limbs)'
                    res[f'{part}|{b["name"]}'] = r
        top = load_part('polo', gender)
        bot = load_part('shorts' if gender == 'male' else 'skort', gender)
        sock = load_part('sock', gender if gender == 'male' else 'female_auth')
        shoe = load_part('shoe', gender if gender == 'male' else 'female_auth')
        sock_c = load_part('sock', 'female') if gender == 'female' else None
        shoe_c = load_part('shoe', 'female') if gender == 'female' else None
        gg = {}
        gg['polo_vs_bottom_overlap_pairs'] = len(overlap_pairs(top[0], top[1], bot[0], bot[1]))
        gg['sock_vs_shoe_overlap_pairs'] = len(overlap_pairs(sock[0], sock[1], shoe[0], shoe[1]))
        gg['bottom_vs_sock_overlap_pairs'] = len(overlap_pairs(bot[0], bot[1], sock[0], sock[1]))
        gg['bottom_vs_shoe_overlap_pairs'] = len(overlap_pairs(bot[0], bot[1], shoe[0], shoe[1]))
        gg['polo_vs_sock_overlap_pairs'] = len(overlap_pairs(top[0], top[1], sock[0], sock[1]))
        if sock_c is not None:
            gg['armscandfit_sock_vs_shoe_overlap_pairs'] = len(overlap_pairs(sock_c[0], sock_c[1], shoe_c[0], shoe_c[1]))
        res['garment_vs_garment'] = gg
        # ---- skin coverage on the authority body
        b0 = bodies[0]
        V0 = b0['V']
        cov = []
        if gender == 'male':
            waist = (V0[:, 2] > 0.86) & (V0[:, 2] < 1.02) & (np.abs(V0[:, 0]) < 0.24)
            feet = (V0[:, 2] < 0.27) & (np.abs(V0[:, 0]) > 0.05)
        else:
            waist = (V0[:, 2] > 0.90) & (V0[:, 2] < 1.04) & (np.abs(V0[:, 0]) < 0.125)
            feet = (V0[:, 2] < 0.25) & (np.abs(V0[:, 0]) > 0.03)
        HZ = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
        cov.append(coverage(b0, [top, bot], waist, 'waist band (polo + bottom)', HZ))
        # shoulders / upper chest + back under the polo (neck excluded): body verts with z in [1.20, 1.36] and |x| < 0.20
        if gender == 'male':
            sh = (V0[:, 2] > 1.22) & (V0[:, 2] < 1.36) & (np.abs(V0[:, 0]) < 0.26)
        else:
            sh = (V0[:, 2] > 1.18) & (V0[:, 2] < 1.31) & (np.abs(V0[:, 0]) < 0.16)
        cov.append(coverage(b0, [top], sh, 'shoulders / upper torso (polo)', HZ))
        cov.append(coverage(b0, [sock, shoe], feet, 'feet + ankles (sock + shoe)', HZ + [(0, 0, -1)]))
        res['skin_coverage'] = cov
        out[gender] = res
    os.makedirs(f'{WORK}/proof', exist_ok=True)
    json.dump(out, open(f'{WORK}/proof/fit_results.json', 'w'), indent=1)
    for g, res in out.items():
        print(f'== {g}')
        for k, r in res.items():
            if k == 'garment_vs_garment':
                print('   garment_vs_garment', r)
            elif k == 'skin_coverage':
                for c in r:
                    print('   coverage', c)
            else:
                flag = 'OK ' if (r['neg'] == 0 and r['overlap_pairs'] == 0 and r['min_mm'] >= MIN_OK * 1000) else ('info' if 'note' in r or 'armscandfit|female_authority' in k or (k.startswith(('sock|', 'shoe|')) and not k.endswith('female_authority') and g == 'female') else 'FAIL')
                print(f"   {flag} {k:38s} min {r['min_mm']:+7.2f} mm  neg {r['neg']:4d}  <1mm {r['lt1mm']:4d}  overlap {r['overlap_pairs']:4d}  tris {r['tris']}")


main()
