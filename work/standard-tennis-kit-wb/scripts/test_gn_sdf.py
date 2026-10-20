import bpy, time, sys
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend")
body = bpy.data.objects['Body_M']
# list available SDF-ish node types
names = [n for n in dir(bpy.types) if ('SDF' in n or 'Grid' in n) and n.startswith('GeometryNode')]
print("GN nodes with SDF/Grid:", names)

ng = bpy.data.node_groups.new("TestSDF", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
nin = ng.nodes.new('NodeGroupInput'); nout = ng.nodes.new('NodeGroupOutput')
try:
    m2s = ng.nodes.new('GeometryNodeMeshToSDFGrid')
    print("MeshToSDFGrid inputs:", [(i.name, i.type) for i in m2s.inputs])
    off = ng.nodes.new('GeometryNodeSDFGridOffset')
    print("SDFGridOffset inputs:", [(i.name, i.type) for i in off.inputs])
    g2m = ng.nodes.new('GeometryNodeGridToMesh')
    print("GridToMesh inputs:", [(i.name, i.type) for i in g2m.inputs])
    for nm in ('GeometryNodeSDFGridFillet','GeometryNodeSDFGridLaplacian','GeometryNodeSDFGridMean','GeometryNodeSDFGridMedian','GeometryNodeSDFGridMeanCurvature'):
        try:
            n = ng.nodes.new(nm); print(nm, [(i.name, i.type) for i in n.inputs]); ng.nodes.remove(n)
        except Exception as e:
            print(nm, "ERR", e)
    ng.links.new(nin.outputs[0], m2s.inputs['Mesh'])
    m2s.inputs['Voxel Size'].default_value = 0.005
    m2s.inputs['Band Width'].default_value = 6
    ng.links.new(m2s.outputs[0], off.inputs[0])
    off.inputs[1].default_value = 0.012
    ng.links.new(off.outputs[0], g2m.inputs[0])
    ng.links.new(g2m.outputs[0], nout.inputs[0])
    mod = body.modifiers.new("T", 'NODES'); mod.node_group = ng
    t0=time.time()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    print("RESULT verts", len(me.vertices), "polys", len(me.polygons), "time", time.time()-t0)
except Exception as e:
    import traceback; traceback.print_exc()
