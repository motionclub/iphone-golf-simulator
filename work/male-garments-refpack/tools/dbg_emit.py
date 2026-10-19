import bpy, numpy as np, sys, bmesh
exec(open('tools/render_npz.py').read().replace("a = sys.argv[sys.argv.index('--') + 1:]","a = ['build/dbg_emit','out/MatchHero_Male/unity','Kit_Shoe_R:ShoeR','dist=.95']").replace("me.polygons.foreach_set('material_index', np.asarray(mat, np.int32))","""me.polygons.foreach_set('material_index', np.asarray(mat, np.int32))
    keep = g['kind'] == 19
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(~keep)[0]], context='FACES'); bm.to_mesh(me); bm.free()
    em = bpy.data.materials.new('E'); em.use_nodes = True; nt = em.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tM = nt.nodes.new('ShaderNodeTexImage'); tM.image = imM; sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tM.outputs['Color'], sep.inputs['Color'])
    e = nt.nodes.new('ShaderNodeEmission'); nt.links.new(sep.outputs['Blue'], e.inputs['Color']); nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs[0])
    me.materials.clear(); me.materials.append(em)""").replace("views = [('lateral'","views = [('lateral', Vector((side, 0, .10)))]\n    _x = [('lateral'"))
