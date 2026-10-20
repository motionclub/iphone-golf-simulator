import bpy

EXPRS = ('happy', 'cheer', 'focus', 'surprise')


def show_expression(name):
    for e in EXPRS:
        c = bpy.data.collections.get('Face_' + e)
        if c is not None:
            c.hide_render = (e != name)
            c.hide_viewport = (e != name)


def set_visible(prefixes_hidden=()):
    pass
