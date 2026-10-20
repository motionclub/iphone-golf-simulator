import bpy, json, pathlib, sys, bmesh
ROOT=pathlib.Path(__file__).resolve().parents[3]
sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH': continue
 if not ('Body' in o.name or 'Face' in o.name): continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
 edges=[e for e in bm.edges if e.is_boundary]
 rows.append(dict(name=o.name,vertices=len(o.data.vertices),matrix=[list(r) for r in o.matrix_world],materials=[m.name for m in o.data.materials],boundaryEdges=len(edges),
  parent=o.parent.name if o.parent else None,parentType=o.parent_type,parentBone=o.parent_bone,local=[list(r) for r in o.matrix_basis],
  materialBounds={mat.name:[[min(o.data.vertices[i].co[d] for p in o.data.polygons if p.material_index==k for i in p.vertices) for d in range(3)],[max(o.data.vertices[i].co[d] for p in o.data.polygons if p.material_index==k for i in p.vertices) for d in range(3)]] for k,mat in enumerate(o.data.materials)},
  boundaryVertices=[dict(index=v.index,co=list(v.co)) for v in bm.verts if v.is_boundary],
  bounds=[list(o.matrix_world@v) for v in [min((v.co for v in bm.verts),key=lambda v:v.z),max((v.co for v in bm.verts),key=lambda v:v.z)]]))
 bm.free()
out=ROOT/f'proof/full-visual-overhaul/characters/eye-boundary-{sex}.json';out.write_text(json.dumps(rows,indent=2))
print('EYE_BOUNDARY',out,[(r['name'],r['vertices'],r['boundaryEdges']) for r in rows])
