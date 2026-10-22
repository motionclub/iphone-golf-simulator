import bpy, time, sys, bmesh
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend")
body = bpy.data.objects['Body_M']
bm = bmesh.new(); bm.from_mesh(body.data)
nb = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if not e.is_manifold)
print("edges", len(bm.edges), "boundary", nb, "non-manifold", nm)
bm.free()

def run(vox, offset, band=3, fillet=0):
    ng = bpy.data.node_groups.new("TestSDF", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nin = ng.nodes.new('NodeGroupInput'); nout = ng.nodes.new('NodeGroupOutput')
    m2s = ng.nodes.new('GeometryNodeMeshToSDFGrid')
    m2s.inputs['Voxel Size'].default_value = vox
    m2s.inputs['Band Width'].default_value = band
    off = ng.nodes.new('GeometryNodeSDFGridOffset'); off.inputs['Distance'].default_value = offset
    g2m = ng.nodes.new('GeometryNodeGridToMesh')
    ng.links.new(nin.outputs[0], m2s.inputs['Mesh'])
    ng.links.new(m2s.outputs[0], off.inputs[0])
    ng.links.new(off.outputs[0], g2m.inputs[0])
    ng.links.new(g2m.outputs[0], nout.inputs[0])
    for m in list(body.modifiers): body.modifiers.remove(m)
    mod = body.modifiers.new("T", 'NODES'); mod.node_group = ng
    bpy.context.view_layer.update()
    t0=time.time()
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    print(f"vox={vox} off={offset} band={band}: verts {len(me.vertices)} polys {len(me.polygons)} time {time.time()-t0:.2f}")
    ev.to_mesh_clear()
    return me
run(0.01, 0.012)
run(0.01, 0.0)
run(0.005, 0.012, band=5)
for n in bpy.data.node_groups[-1].nodes: pass
