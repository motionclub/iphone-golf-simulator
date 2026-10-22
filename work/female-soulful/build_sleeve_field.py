"""Build a source-pattern sleeve field, with no animation/pose samples.

Run with ordinary Python+numpy. Only writes experiments/sleeve-field.
The JSON is intentionally shared by the C# and a prospective Swift evaluator.
"""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parent


def vec(p):
    return dict(zip(('x', 'y', 'z'), map(float, p)))


def closest(p, triangles):
    """Closest point on every candidate triangle, including its edges."""
    a, b, c = triangles.transpose(1, 0, 2)
    ab, ac, ap = b-a, c-a, p-a
    aa, bb, cc = (ab*ab).sum(1), (ac*ac).sum(1), (ab*ac).sum(1)
    u = (bb*(ap*ab).sum(1)-cc*(ap*ac).sum(1))/np.maximum(aa*bb-cc*cc, 1e-20)
    v = (aa*(ap*ac).sum(1)-cc*(ap*ab).sum(1))/np.maximum(aa*bb-cc*cc, 1e-20)
    bary = np.stack((1-u-v, u, v), 1)
    candidates = [bary]
    for i, j in ((0, 1), (1, 2), (2, 0)):
        edge = triangles[:, j]-triangles[:, i]
        t = np.clip(((p-triangles[:, i])*edge).sum(1)/np.maximum((edge*edge).sum(1), 1e-20), 0, 1)
        q = np.zeros_like(bary); q[:, i] = 1-t; q[:, j] = t
        candidates.append(q)
    bs = np.stack(candidates, 1)
    ds = (((bs[..., None]*triangles[:, None]).sum(2)-p)**2).sum(2)
    ds[:, 0][(bary < 0).any(1)] = np.inf
    k, j = np.unravel_index(ds.argmin(), ds.shape)
    return k, bs[k, j]


def main():
    clean = np.load(ROOT/'cage-prototype/unprojected-top.npz')
    current = np.load(ROOT/'out/GolfKitHero_Female/unity/Kit_Top_final.npz')
    p, tri = clean['pos'], clean['tri']
    assert np.max(np.abs(p-current['pos'])) < 1e-6
    manifest = json.loads((ROOT/'out/GolfKitHero_Female/unity/manifest.json').read_text())
    piece = next(x for x in manifest['pieces'] if x['name'] == 'Kit_Top')
    hero = json.loads((ROOT/'dump-polo/GolfKitHero_Female/hero.json').read_text())
    palette = hero['parts'][0]['bones']
    remap = np.array([piece['bones'].index(b) if b in piece['bones'] else -1 for b in palette])
    bi, bw = remap[current['bi']], current['bw']
    assert not np.any((bi < 0) & (bw > 0))
    bi = np.maximum(bi, 0)
    pattern = json.loads((ROOT/'source/golf_sleeve_pattern.json').read_text())
    controls, centers, ring_t, sides, faces = [], [], [], [], []
    nr, nc = np.asarray(pattern['-1']).shape[:2]
    for si, side in enumerate((-1, 1)):
        rings = np.asarray(pattern[str(side)])
        assert rings.shape == (nr, nc, 3)
        controls.extend(rings.reshape(-1, 3)); centers.extend(rings.mean(1))
        ring_t.extend(np.repeat(np.linspace(0, 1, nr), nc)); sides.extend([si]*(nr*nc))
        base = si*nr*nc
        for r in range(nr-1):
            for k in range(nc):
                a = base+r*nc+k; b = base+r*nc+(k+1)%nc; c = base+(r+1)*nc+k; d = base+(r+1)*nc+(k+1)%nc
                faces.extend(((a, c, b), (b, c, d)))
    controls, centers, faces = np.asarray(controls), np.asarray(centers), np.asarray(faces)
    # Root ring follows the same torso skin field as the sewn pattern.
    root_weights = []
    torso = np.unique(tri[np.isin(clean['panel'], (0, 1))])
    for point in controls:
        nearest = torso[np.argmin(((p[torso]-point)**2).sum(1))]
        root_weights.append(dict(ids=bi[nearest].tolist(), values=bw[nearest].tolist()))
    sleeve = np.zeros(len(p), bool)
    sleeve[np.unique(tri[np.isin(clean['panel'], (2, 3, 6))])] = True
    _, weld = np.unique(np.round(p, 5), axis=0, return_inverse=True)
    group = np.zeros(weld.max()+1, bool); np.logical_or.at(group, weld, sleeve); sleeve = group[weld]
    ts = controls[faces]; centroids = ts.mean(1); mappings = []
    max_error = 0.; max_offset = 0.; vertex_ring_t = np.zeros(len(p))
    for i in np.flatnonzero(sleeve):
        side = 0 if p[i, 0] < 0 else 1
        ids = np.flatnonzero(np.asarray(sides)[faces[:, 0]] == side)
        near = np.argpartition(((centroids[ids]-p[i])**2).sum(1), 15)[:16]
        candidates = ids[near]; k, bary = closest(p[i], ts[candidates]); fi = int(candidates[k]); verts = faces[fi]
        a, b, c = controls[verts]; u = b-a; u /= np.linalg.norm(u)
        n = np.cross(b-a, c-a); n /= np.linalg.norm(n); v = np.cross(n, u)
        q = (controls[verts]*bary[:, None]).sum(0); delta = p[i]-q
        offset = np.array((delta@u, delta@v, delta@n))
        t = float(np.asarray(ring_t)[verts]@bary)
        vertex_ring_t[i] = t
        # At the sewn boundary preserve exactly the original skinning. The
        # complete cuff, including thick edge detail, has full field influence.
        alpha = np.clip(t/.16, 0, 1); alpha = alpha*alpha*(3-2*alpha)
        recon = q+u*offset[0]+v*offset[1]+n*offset[2]
        max_error = max(max_error, np.linalg.norm(recon-p[i])); max_offset = max(max_offset, np.linalg.norm(offset))
        normal = clean['nrm'][i]
        mappings.append(dict(vertex=int(i), triangle=fi, bary=vec(bary), offset=vec(offset), normal=vec((normal@u, normal@v, normal@n)), alpha=float(alpha)))
    # One welded outer shell carries contact displacement for all thickness
    # layers and details. Never push outer/lining/cuff independently.
    outer = tri[(clean['part'] == 0) & np.isin(clean['panel'], (0, 1, 2, 3))]
    outer_ids = np.unique(outer)
    _, representatives, shell_inverse = np.unique(np.round(p[outer_ids], 5), axis=0, return_index=True, return_inverse=True)
    shell_source = outer_ids[representatives]
    source_to_shell = np.full(len(p), -1); source_to_shell[outer_ids] = shell_inverse
    shell_tri = source_to_shell[outer]
    st = p[shell_source[shell_tri]]; sc = st.mean(1)
    contact_map = []
    for i, point in enumerate(p):
        near = np.argpartition(((sc-point)**2).sum(1), 15)[:16]
        k, bary = closest(point, st[near]); fi = int(near[k])
        contact_map.append(dict(vertex=i, triangle=fi, bary=vec(bary)))
    edges = np.unique(np.sort(np.concatenate((shell_tri[:, (0, 1)], shell_tri[:, (1, 2)], shell_tri[:, (2, 0)])), axis=1), axis=0)
    rest_shell = p[shell_source]
    edge_lengths = np.linalg.norm(rest_shell[edges[:, 1]]-rest_shell[edges[:, 0]], axis=1)
    # Opposite-vertex distances regularize bending without imposing a changing
    # body/animation-derived rest shape. Exactly two faces share each seam edge.
    edge_opposites = {}
    for a, b, c in shell_tri:
        for x, y, opposite in ((a, b, c), (b, c, a), (c, a, b)):
            edge_opposites.setdefault(tuple(sorted((int(x), int(y)))), []).append(int(opposite))
    bend_pairs = np.array([v for v in edge_opposites.values() if len(v) == 2], dtype=np.int32)
    bend_lengths = np.linalg.norm(rest_shell[bend_pairs[:, 1]]-rest_shell[bend_pairs[:, 0]], axis=1)
    cross = np.cross(st[:, 1]-st[:, 0], st[:, 2]-st[:, 0]); areas = np.linalg.norm(cross, axis=1)
    rest_normals = cross/np.maximum(areas[:, None], 1e-20)
    outer_panels = clean['panel'][(clean['part'] == 0) & np.isin(clean['panel'], (0, 1, 2, 3))]
    triangle_side = np.full(len(shell_tri), -1)
    sleeve_tri = np.isin(outer_panels, (2, 3))
    triangle_side[sleeve_tri] = (st[sleeve_tri].mean(1)[:, 0] > 0).astype(int)
    triangle_t = vertex_ring_t[shell_source[shell_tri]].mean(1)
    triangle_blend = triangle_t*triangle_t*(3-2*triangle_t)
    mobility = np.ones(len(rest_shell))
    # Freeze the accepted neckline and lower garment placement; cuff boundaries
    # follow the noncollapsing arm-driven field, including collision clearance.
    mobility[(rest_shell[:, 2] < 1.075) | ((rest_shell[:, 2] > 1.375) & (abs(rest_shell[:, 0]) < .10))] = 0
    boundary = [edge for edge, opposite in edge_opposites.items() if len(opposite) == 1]
    for a, b in boundary:
        if abs(rest_shell[[a, b], 0]).min() > .145 and rest_shell[[a, b], 2].max() < 1.26:
            mobility[[a, b]] = 0
    data = dict(version=1, contactMode=0, vertexCount=len(p), ringCount=nr, ringSize=nc,
                controls=list(map(vec, controls)), centers=list(map(vec, centers)),
                triangles=faces.ravel().tolist(), rootWeights=root_weights,
                mapping=mappings, boneNames=piece['bones'],
                armBones=[piece['bones'].index('LeftUpperArm'), piece['bones'].index('RightUpperArm')],
                chestBone=piece['bones'].index('UpperChest'),
                collisionSource=shell_source.tolist(), collisionTriangles=shell_tri.ravel().tolist(),
                collisionEdges=edges.ravel().tolist(), collisionMap=contact_map,
                collisionEdgeLengths=edge_lengths.tolist(), collisionBendPairs=bend_pairs.ravel().tolist(),
                collisionBendLengths=bend_lengths.tolist(), collisionRestNormals=list(map(vec, rest_normals)),
                collisionRestAreas=areas.tolist(), collisionTriangleSide=triangle_side.tolist(),
                collisionTriangleBlend=triangle_blend.tolist(), collisionMobility=mobility.tolist())
    out = ROOT/'experiments/sleeve-field'; out.mkdir(parents=True, exist_ok=True)
    existing = out/'golf_sleeve_field.json'
    if existing.exists():
        previous = json.loads(existing.read_text())
        for key in ('sourceToHero', 'heroToSource'):
            if key in previous: data[key] = previous[key]
    (out/'golf_sleeve_field.json').write_text(json.dumps(data, separators=(',', ':')))
    report = dict(controls=len(controls), mappedVertices=len(mappings), collisionSamples=len(shell_source), restReconstructionErrorMetres=float(max_error), maxDetailOffsetMetres=float(max_offset), animationInputs=0)
    (out/'BUILD_REPORT.json').write_text(json.dumps(report, indent=2)); print(report)


if __name__ == '__main__':
    main()
