"""Binary FBX curve access. Preserve all geometry, skeleton IDs, and unowned connections."""
import array
import numpy as np
from io_scene_fbx import parse_fbx,encode_bin

def read(path):
    root,version=parse_fbx.parse(str(path));objects=next(x for x in root.elems if x.id==b'Objects');connections=next(x for x in root.elems if x.id==b'Connections')
    models={int(x.props[0]):x for x in objects.elems if x.id==b'Model'};nodes={int(x.props[0]):x for x in objects.elems if x.id==b'AnimationCurveNode'};curves={int(x.props[0]):x for x in objects.elems if x.id==b'AnimationCurve'}
    properties={};channels={}
    for c in connections.elems:
        p=c.props
        if len(p)>=4 and p[0]==b'OP' and p[1] in nodes and p[2] in models:properties[p[1]]=(models[p[2]].props[1].split(b'\0')[0].decode(),p[3].decode())
    for c in connections.elems:
        p=c.props
        if len(p)>=4 and p[0]==b'OP' and p[1] in curves and p[2] in properties:
            name,prop=properties[p[2]];channels[(name,prop,p[3].decode().split('|')[-1])]=curves[p[1]]
    return root,version,models,channels

def data(curve,key):return next(e for e in curve.elems if e.id==key).props[0]
def assign(curve,key,value):
    e=next(e for e in curve.elems if e.id==key);e.props[0]=value

def write(path,root,version):
    def convert(el):
        n=encode_bin.FBXElem(el.id)
        methods={ord('Y'):'add_int16',ord('B'):'add_bool',ord('C'):'add_char',ord('Z'):'add_int8',ord('I'):'add_int32',ord('F'):'add_float32',ord('D'):'add_float64',ord('L'):'add_int64',ord('R'):'add_bytes',ord('S'):'add_string',ord('f'):'add_float32_array',ord('d'):'add_float64_array',ord('l'):'add_int64_array',ord('i'):'add_int32_array',ord('b'):'add_bool_array',ord('c'):'add_byte_array'}
        for typ,value in zip(el.props_type,el.props):getattr(n,methods[typ])(value)
        n.elems.extend(convert(e) for e in el.elems)
        return n
    encode_bin.write(str(path),convert(root),version)
