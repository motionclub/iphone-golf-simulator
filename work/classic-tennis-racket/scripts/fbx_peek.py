"""Peek into a binary FBX (GlobalSettings + object transforms) using Blender's own parser."""
import sys, json
import bpy
from io_scene_fbx import parse_fbx
path = sys.argv[sys.argv.index('--') + 1]
root, version = parse_fbx.parse(path)
print('FBX version', version)
def find(elem, name):
    return [e for e in elem.elems if e.id == name.encode() if True]
gs = [e for e in root.elems if e.id == b'GlobalSettings'][0]
props = [e for e in gs.elems if e.id == b'Properties70'][0]
for p in props.elems:
    if p.id == b'P':
        n = p.props[0]
        if n in (b'UpAxis', b'UpAxisSign', b'FrontAxis', b'FrontAxisSign', b'CoordAxis', b'CoordAxisSign', b'OriginalUpAxis', b'OriginalUpAxisSign', b'UnitScaleFactor', b'OriginalUnitScaleFactor'):
            print('  GlobalSettings', n.decode(), p.props[4:])
objs = [e for e in root.elems if e.id == b'Objects'][0]
for m in objs.elems:
    if m.id == b'Model':
        name = m.props[1].decode().split('\x00')[0]
        p70 = [e for e in m.elems if e.id == b'Properties70'][0]
        out = {}
        for p in p70.elems:
            if p.id == b'P' and p.props[0] in (b'Lcl Translation', b'Lcl Rotation', b'Lcl Scaling', b'PreRotation', b'RotationOrder'):
                out[p.props[0].decode()] = list(p.props[4:])
        print('  Model', name, out)
