import bpy,json,pathlib
R=pathlib.Path.cwd();P=R/'work/reference-rebuild/vendor/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend';bpy.ops.wm.open_mainfile(filepath=str(P));a=[]
for o in bpy.data.objects:
 if o.name.startswith(('GEO-head_animation_realistic','GEO-head_stylized','GEO-body_female_stylized')):
  if o.type!='MESH':continue
  a.append(dict(name=o.name,parent=o.parent.name if o.parent else None,worldMatrix=[list(row) for row in o.matrix_world],localMatrix=[list(row) for row in o.matrix_local],materials=[m.name for m in o.data.materials],materialFaces={m.name:sum(p.material_index==i for p in o.data.polygons) for i,m in enumerate(o.data.materials)},modifiers=[dict(name=m.name,type=m.type,levels=getattr(m,'levels',None),render=getattr(m,'render_levels',None)) for m in o.modifiers],worldBounds=[list(o.matrix_world@v.co) for v in list(o.data.vertices)[:2]],vertexGroups=[v.name for v in o.vertex_groups]))
(R/'work/reference-rebuild/characters/candidate-metadata.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
