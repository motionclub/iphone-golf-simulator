import bpy, time
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend")
body = bpy.data.objects['Body_M']
ng = bpy.data.node_groups.new("TestSDF", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
nin = ng.nodes.new('NodeGroupInput'); nout = ng.nodes.new('NodeGroupOutput')
m2s = ng.nodes.new('GeometryNodeMeshToSDFGrid')
off = ng.nodes.new('GeometryNodeSDFGridOffset')
g2m = ng.nodes.new('GeometryNodeGridToMesh')
for n in (m2s, off, g2m):
    for s in list(n.inputs)+list(n.outputs):
        print(n.bl_idname, 'IN' if s.is_output==False else 'OUT', s.name, s.type, getattr(s,'structure_type',None), getattr(s,'display_shape',None))
l1 = ng.links.new(nin.outputs[0], m2s.inputs['Mesh'])
l2 = ng.links.new(m2s.outputs[0], off.inputs[0])
l3 = ng.links.new(off.outputs[0], g2m.inputs[0])
l4 = ng.links.new(g2m.outputs[0], nout.inputs[0])
for l in (l1,l2,l3,l4): print("link valid", l.is_valid, l.from_socket.name, '->', l.to_socket.name, l.is_muted)
print([ (n.name, n.mute) for n in ng.nodes])
