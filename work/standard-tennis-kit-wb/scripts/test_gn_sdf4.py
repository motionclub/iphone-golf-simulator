import bpy, time
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=32, ring_count=16)
ob = bpy.context.active_object
def evaluate(label):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    print(label, "-> verts", len(me.vertices), "polys", len(me.polygons))
    ev.to_mesh_clear()

def make(chain):
    ng = bpy.data.node_groups.new("T", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nin = ng.nodes.new('NodeGroupInput'); nout = ng.nodes.new('NodeGroupOutput')
    prev = nin.outputs[0]
    for nm, setv in chain:
        n = ng.nodes.new(nm)
        for k,v in setv.items(): n.inputs[k].default_value = v
        ng.links.new(prev, n.inputs[0]); prev = n.outputs[0]
    ng.links.new(prev, nout.inputs[0])
    return ng
for m in list(ob.modifiers): ob.modifiers.remove(m)
evaluate("raw")
ng = make([])
mod = ob.modifiers.new("T",'NODES'); mod.node_group = ng
evaluate("passthrough")
ob.modifiers.remove(mod)
ng = make([('GeometryNodeMeshToSDFGrid', {'Voxel Size':0.005,'Band Width':3}), ('GeometryNodeSDFGridOffset', {'Distance':0.01}), ('GeometryNodeGridToMesh', {'Threshold':0.0,'Adaptivity':0.0})])
mod = ob.modifiers.new("T",'NODES'); mod.node_group = ng
evaluate("sdf sphere +10mm")
