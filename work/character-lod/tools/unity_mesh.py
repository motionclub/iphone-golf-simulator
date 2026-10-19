"""Read a Unity YAML Mesh asset (.asset, serializedVersion 12, uncompressed) into numpy arrays.
Used offline by the character-LOD tools: triangle accounting and simplifier tests on the real garment meshes."""
import re, struct, sys
import numpy as np

FMT = {0: ('f', 4), 1: ('e', 2), 2: ('B', 1), 3: ('b', 1), 4: ('H', 2), 5: ('h', 2), 6: ('B', 1), 7: ('b', 1),
       8: ('H', 2), 9: ('h', 2), 10: ('I', 4), 11: ('i', 4)}
CH = ['pos', 'normal', 'tangent', 'color', 'uv0', 'uv1', 'uv2', 'uv3', 'uv4', 'uv5', 'uv6', 'uv7', 'weights', 'indices']


def read(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    name = re.search(r'm_Name: (.*)', s).group(1).strip()
    head = s[:s.find('m_Shapes:')]
    subs = [(int(a), int(b)) for a, b in re.findall(r'firstByte: (\d+)\n\s+indexCount: (\d+)', head)]
    ifmt = int(re.search(r'm_IndexFormat: (\d)', s).group(1))
    ib = bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]*)', s).group(1))
    vd = s[s.find('m_VertexData:'):]
    nv = int(re.search(r'm_VertexCount: (\d+)', vd).group(1))
    chans = [tuple(int(x) for x in m) for m in re.findall(r'- stream: (\d+)\n\s+offset: (\d+)\n\s+format: (\d+)\n\s+dimension: (\d+)', vd)]
    data = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]*)', vd).group(1))
    # stream strides
    strides = {}
    for i, (st, off, f, dim) in enumerate(chans):
        if dim == 0: continue
        dim &= 0xF
        strides[st] = max(strides.get(st, 0), off + FMT[f][1] * dim)
    starts, pos = {}, 0
    for st in sorted(strides):
        pos = (pos + 15) // 16 * 16 if st > 0 else pos
        starts[st] = pos; pos += strides[st] * nv
    out = {'name': name, 'vertexCount': nv}
    for i, (st, off, f, dim) in enumerate(chans):
        dim &= 0xF
        if dim == 0: continue
        code, size = FMT[f]
        dt = np.dtype('<' + code)
        raw = np.frombuffer(data, dtype=np.uint8, count=strides[st] * nv, offset=starts[st]).reshape(nv, strides[st])
        a = raw[:, off:off + size * dim].copy().view(dt).reshape(nv, dim)
        out[CH[i]] = a
    idt = np.uint16 if ifmt == 0 else np.uint32
    isz = 2 if ifmt == 0 else 4
    out['submeshes'] = [np.frombuffer(ib, dtype=idt, count=c, offset=fb).astype(np.int64) for fb, c in subs]
    out['triangles'] = sum(c for _, c in subs) // 3
    out['shapes'] = len(re.findall(r'^\s+- firstVertex:', s[s.find('m_Shapes:'):s.find('m_BindPose:')], re.M))
    return out


def write_bin(m, path):
    """Simple dump for the mono test harness: nv, nsub, pos, weights(4)+indices(4), normals, uv0, then per submesh count+indices."""
    nv = m['vertexCount']
    with open(path, 'wb') as f:
        f.write(struct.pack('<ii', nv, len(m['submeshes'])))
        f.write(m['pos'].astype('<f4').tobytes())
        w = m.get('weights'); ix = m.get('indices')
        if w is None: w = np.zeros((nv, 4), 'f4'); ix = np.zeros((nv, 4), 'i4')
        f.write(np.asarray(w, '<f4').tobytes()); f.write(np.asarray(ix, '<i4').tobytes())
        f.write(np.asarray(m.get('normal', np.zeros((nv, 3))), '<f4').tobytes())
        uv = m.get('uv0'); uv = np.zeros((nv, 2)) if uv is None else uv
        f.write(np.asarray(uv[:, :2], '<f4').tobytes())
        for sub in m['submeshes']:
            f.write(struct.pack('<i', len(sub))); f.write(np.asarray(sub, '<i4').tobytes())


if __name__ == '__main__':
    for p in sys.argv[1:]:
        if p.endswith('.bin'): continue
        m = read(p)
        print(f"{m['name']}: verts {m['vertexCount']} tris {m['triangles']} subs {len(m['submeshes'])} shapes {m['shapes']} "
              f"channels {[k for k in CH if k in m]}")
