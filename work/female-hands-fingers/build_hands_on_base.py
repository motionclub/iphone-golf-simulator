"""Rebuild the hands on a NEWER base blend (use when the wrist rings moved, so the delta guard refuses):
  1. blender -b <base.blend> --python dump_mesh.py -- data/mesh_base.npz          (Body_F dump, limbs vertex order)
  2. BASE_MESH=data/mesh_base.npz ./py.sh build_hands_on_base.py <params.json> <tag>   -> data/cand_<tag>.npz
  3. blender -b <base.blend> --python write_blend_f.py -- data/cand_<tag>.npz <out.blend>
The index sets data/start_hand_ring_*.npy / start_hand_verts_*.npy are valid for any base that still carries the limbs SDF hands."""
import sys, json
import fit_f, asm_f
x = json.load(open(sys.argv[1]))['params'] if sys.argv[1].endswith('.json') else json.loads(sys.argv[1])
par, pose = fit_f.split({**fit_f.DEFAULT, **x})
Vn, polys, si, removed = asm_f.assemble(par, pose)
asm_f.save(asm_f.W / f'data/cand_{sys.argv[2]}.npz', Vn, polys, removed)
print('saved', sys.argv[2], 'tris', asm_f.tri_count(polys))
