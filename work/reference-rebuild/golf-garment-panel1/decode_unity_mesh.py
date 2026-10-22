"""Read-only Unity YAML mesh decoder for the production fitted golf shirts.
The decoded arrays retain exact imported vertex/bind/shape order.
"""
from pathlib import Path
import re, json, hashlib
import numpy as np

R = Path.cwd()
W = R / 'work/reference-rebuild/golf-garment-panel1'

def decode(path):
    text = Path(path).read_text()
    vertex_section = text[text.index('  m_VertexData:'):]
    count = int(re.search(r'm_VertexCount: (\d+)', vertex_section)[1])
    channels = [tuple(map(int, m)) for m in re.findall(
        r'- stream: (\d+)\s+offset: (\d+)\s+format: (\d+)\s+dimension: (\d+)', vertex_section)]
    data = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)', vertex_section)[1])
    sizes = {0: 4, 1: 2, 2: 1, 3: 1, 4: 2, 5: 2, 6: 1, 7: 1, 8: 2, 9: 2, 10: 4, 11: 4}
    dtypes = {0: '<f4', 1: '<f2', 6: 'u1', 7: 'i1', 8: '<u2', 9: '<i2', 10: '<u4', 11: '<i4'}
    strides = {}
    for stream, offset, fmt, dim in channels:
        if dim: strides[stream] = max(strides.get(stream, 0), offset + sizes[fmt] * dim)
    offsets, at = {}, 0
    for stream, stride in sorted(strides.items()):
        offsets[stream] = at
        at = (at + count * stride + 15) // 16 * 16
    assert at == len(data), (at, len(data), strides)
    arrays = {}
    for i, (stream, offset, fmt, dim) in enumerate(channels):
        if not dim: continue
        arrays[i] = np.ndarray((count, dim), dtype=np.dtype(dtypes[fmt]), buffer=data,
            offset=offsets[stream] + offset, strides=(strides[stream], sizes[fmt])).copy()
    index_format = int(re.search(r'm_IndexFormat: (\d+)', text)[1])
    triangles = np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)', text)[1]),
        dtype='<u2' if index_format == 0 else '<u4').reshape(-1, 3).copy()
    bind_section = text[text.index('  m_BindPose:'):text.index('  m_BoneNameHashes:')]
    bind_values = list(map(float, re.findall(r'e\d\d: ([-+\deE.]+)', bind_section)))
    binds = np.asarray(bind_values).reshape(-1, 4, 4)
    shape_section = text[text.index('  m_Shapes:'):text.index('  m_BindPose:')]
    names = re.findall(r'- name: (.+)', shape_section)
    blocks = [tuple(map(int, q)) for q in re.findall(r'- firstVertex: (\d+)\s+vertexCount: (\d+)', shape_section)]
    pattern = (r'- vertex: \{x: ([-+\deE.]+), y: ([-+\deE.]+), z: ([-+\deE.]+)\}'
        r'\s+normal: \{x: ([-+\deE.]+), y: ([-+\deE.]+), z: ([-+\deE.]+)\}'
        r'\s+tangent: \{x: ([-+\deE.]+), y: ([-+\deE.]+), z: ([-+\deE.]+)\}'
        r'\s+index: (\d+)')
    sparse = np.array(re.findall(pattern, shape_section), dtype=float).reshape(-1, 10)
    dv = np.zeros((len(names), count, 3)); dn = dv.copy(); dt = dv.copy()
    for s, (first, n) in enumerate(blocks):
        row = sparse[first:first + n]; indices = row[:, 9].astype(int)
        assert len(indices) == len(set(indices)) and indices.max() < count
        dv[s, indices] = row[:, :3]; dn[s, indices] = row[:, 3:6]; dt[s, indices] = row[:, 6:9]
    return {'vertices': arrays[0], 'normals': arrays[1], 'tangents': arrays[2], 'uv': arrays[4],
        'weights': arrays[12], 'indices': arrays[13], 'bindposes': binds, 'triangles': triangles,
        'shapeNames': np.array(names), 'shapeDeltas': dv, 'shapeNormalDeltas': dn, 'shapeTangentDeltas': dt}

if __name__ == '__main__':
    report = {}
    for sex in ('Male', 'Female'):
        source = R / f'Unity/Assets/Resources/Golf/Fitted_{sex}_Top.asset'
        data = decode(source)
        np.savez_compressed(W / (sex + '_production-top.npz'), **data)
        sums = data['weights'].sum(1)
        report[sex] = {'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'vertexCount': len(data['vertices']), 'triangleCount': len(data['triangles']),
            'boneCount': len(data['bindposes']), 'shapeNames': data['shapeNames'].tolist(),
            'weightSumError': float(abs(sums - 1).max()),
            'bounds': [data['vertices'].min(0).tolist(), data['vertices'].max(0).tolist()],
            'maxDeltaMm': {str(n): float(np.linalg.norm(d, axis=1).max() * 1000)
                for n, d in zip(data['shapeNames'], data['shapeDeltas'])}}
    (W / 'production-source.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
