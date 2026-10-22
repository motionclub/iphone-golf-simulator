import bpy
m = bpy.data.materials.get("LK_SMOKE")
print("MAT", m, m.use_nodes if m else None, getattr(m, "surface_render_method", None), getattr(m, "blend_method", None))
if m and m.node_tree:
    for n in m.node_tree.nodes:
        print("NODE", n.type, n.name, [ (i.name, i.is_linked, getattr(i, "default_value", None) if not i.is_linked else "linked") for i in n.inputs if i.name in ("Alpha", "Base Color", "Emission Strength")])
    for l in m.node_tree.links:
        print("LINK", l.from_node.name, l.from_socket.name, "->", l.to_node.name, l.to_socket.name)
