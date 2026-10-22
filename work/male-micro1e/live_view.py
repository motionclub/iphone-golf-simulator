"""Helpers for the live Blender viewport (MCP). Orthographic look-at views."""
import bpy, math
from mathutils import Vector


def _space():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == 'VIEW_3D')
    return area, area.spaces[0], area.spaces[0].region_3d


def look(target, from_dir, dist=0.3, up=(0, 0, 1), wire=False, cavity=True):
    """Put the viewport at target + from_dir*dist looking at target (ortho)."""
    area, space, r3d = _space()
    f = Vector(from_dir).normalized()
    q = (-f).to_track_quat('-Z', 'Y')
    # make 'up' respected: build rotation from forward and up
    fwd = -f
    upv = Vector(up)
    right = fwd.cross(upv).normalized()
    upv2 = right.cross(fwd).normalized()
    from mathutils import Matrix
    m = Matrix((right, upv2, -fwd)).transposed()
    r3d.view_rotation = m.to_quaternion()
    r3d.view_location = Vector(target)
    r3d.view_distance = dist
    r3d.view_perspective = 'ORTHO'
    space.overlay.show_wireframes = wire
    space.overlay.wireframe_threshold = 1.0
    space.shading.show_cavity = cavity
    space.overlay.show_floor = False
    space.overlay.show_axis_x = False
    space.overlay.show_axis_y = False
    space.overlay.show_cursor = False
    space.overlay.show_extras = False
    space.overlay.show_outline_selected = False
    return True
