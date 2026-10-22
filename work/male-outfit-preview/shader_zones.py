"""Procedural colour zones: crisp stripes / trims that depend on object-space position (resolution independent)."""
import bpy
from preview_common import lin, hex_rgb


class Z:
    """node-graph builder.  All values are (node, socket_name) pairs."""

    def __init__(self, mat):
        self.mat = mat
        self.nt = mat.node_tree
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self.n = 0
        self.tc = self.nodes.new('ShaderNodeTexCoord')
        self.sep = self.nodes.new('ShaderNodeSeparateXYZ')
        self.links.new(self.tc.outputs['Object'], self.sep.inputs[0])
        self.x = self.sep.outputs['X']
        self.y = self.sep.outputs['Y']
        self.z = self.sep.outputs['Z']
        self._absx = None
        self._mir = None

    def _node(self, typ, **props):
        nd = self.nodes.new(typ)
        for k, v in props.items():
            setattr(nd, k, v)
        self.n += 1
        nd.location = (-900 + 160 * (self.n % 8), -300 - 130 * (self.n // 8))
        return nd

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self._node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[i].default_value = v
            else:
                self.links.new(v, nd.inputs[i])
        return nd.outputs[0]

    def absx(self):
        if self._absx is None:
            self._absx = self.math('ABSOLUTE', self.x)
        return self._absx

    def up(self, v, edge, soft=0.0008):
        """0 below edge, 1 above (smooth over `soft` metres)."""
        nd = self._node('ShaderNodeMapRange')
        nd.interpolation_type = 'SMOOTHSTEP'
        nd.clamp = True
        nd.inputs['From Min'].default_value = edge - soft * 0.5
        nd.inputs['From Max'].default_value = edge + soft * 0.5
        nd.inputs['To Min'].default_value = 0.0
        nd.inputs['To Max'].default_value = 1.0
        self.links.new(v, nd.inputs['Value'])
        return nd.outputs['Result']

    def inv(self, m):
        return self.math('SUBTRACT', 1.0, m)

    def mul(self, *ms):
        out = ms[0]
        for m in ms[1:]:
            out = self.math('MULTIPLY', out, m)
        return out

    def add(self, a, b):
        return self.math('ADD', a, b, clamp=True)

    def band(self, v, lo, hi, soft=0.0008):
        return self.mul(self.up(v, lo, soft), self.inv(self.up(v, hi, soft)))

    def ellipse(self, a, ca, ra, b, cb, rb, soft=0.10):
        """1 inside the ellipse ((a-ca)/ra)^2 + ((b-cb)/rb)^2 < 1  (a, b are scalar sockets), smooth edge of `soft` (normalised)."""
        da = self.math('DIVIDE', self.math('SUBTRACT', a, ca), ra)
        db = self.math('DIVIDE', self.math('SUBTRACT', b, cb), rb)
        s = self.math('ADD', self.math('MULTIPLY', da, da), self.math('MULTIPLY', db, db))
        d = self.math('SQRT', s)
        return self.inv(self.up(d, 1.0, soft))

    def mirrored(self):
        """vector (|x|, y, z)"""
        if self._mir is None:
            nd = self._node('ShaderNodeCombineXYZ')
            self.links.new(self.absx(), nd.inputs['X'])
            self.links.new(self.y, nd.inputs['Y'])
            self.links.new(self.z, nd.inputs['Z'])
            self._mir = nd.outputs[0]
        return self._mir

    def arm_s(self, c, a):
        """signed distance along the (mirrored) arm axis from point c."""
        sub = self._node('ShaderNodeVectorMath', operation='SUBTRACT')
        self.links.new(self.mirrored(), sub.inputs[0])
        sub.inputs[1].default_value = tuple(c)
        dot = self._node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        self.links.new(sub.outputs[0], dot.inputs[0])
        dot.inputs[1].default_value = tuple(a)
        return dot.outputs['Value']

    def arm_r(self, c, a):
        """distance from the (mirrored) arm axis line."""
        sub = self._node('ShaderNodeVectorMath', operation='SUBTRACT')
        self.links.new(self.mirrored(), sub.inputs[0])
        sub.inputs[1].default_value = tuple(c)
        dot = self._node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        self.links.new(sub.outputs[0], dot.inputs[0])
        dot.inputs[1].default_value = tuple(a)
        proj = self._node('ShaderNodeVectorMath', operation='SCALE')
        self.links.new(dot.outputs['Value'], proj.inputs['Scale'])
        proj.inputs[0].default_value = tuple(a)
        perp = self._node('ShaderNodeVectorMath', operation='SUBTRACT')
        self.links.new(sub.outputs[0], perp.inputs[0])
        self.links.new(proj.outputs[0], perp.inputs[1])
        ln = self._node('ShaderNodeVectorMath', operation='LENGTH')
        self.links.new(perp.outputs[0], ln.inputs[0])
        return ln.outputs['Value']


def build_material(name, base_hex, zones, rough=.7, spec=.22, sheen=0.0, aa=0.0008):
    """zones: list of (key, hex, mask_fn(Z)->socket) applied in order on top of the base colour.  Colour nodes are named
    'C_<key>' (and 'C_base') so that a colourway swap only has to set their values."""
    old = bpy.data.materials.get(name)
    if old is not None:
        bpy.data.materials.remove(old)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes.get('Principled BSDF')
    pr.inputs['Roughness'].default_value = rough
    pr.inputs['Metallic'].default_value = 0.0
    if 'Specular IOR Level' in pr.inputs:
        pr.inputs['Specular IOR Level'].default_value = spec
    if sheen and 'Sheen Weight' in pr.inputs:
        pr.inputs['Sheen Weight'].default_value = sheen
    zb = Z(m)

    def rgb(key, hx):
        nd = nt.nodes.new('ShaderNodeRGB')
        nd.name = 'C_' + key
        nd.label = key
        nd.outputs[0].default_value = (*lin(hex_rgb(hx)), 1)
        return nd.outputs[0]

    cur = rgb('base', base_hex)
    for key, hx, fn in zones:
        col = rgb(key, hx)
        mask = fn(zb)
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MIX'
        nt.links.new(mask, mx.inputs['Factor'])
        nt.links.new(cur, mx.inputs['A'])
        nt.links.new(col, mx.inputs['B'])
        cur = mx.outputs['Result']
    nt.links.new(cur, pr.inputs['Base Color'])
    m.diffuse_color = (*lin(hex_rgb(base_hex)), 1)
    return m


def set_colors(mat_name, colors):
    """colors: dict key->hex (key 'base' for the base colour)."""
    m = bpy.data.materials.get(mat_name)
    if m is None:
        return
    for k, hx in colors.items():
        nd = m.node_tree.nodes.get('C_' + k)
        if nd is not None:
            nd.outputs[0].default_value = (*lin(hex_rgb(hx)), 1)
