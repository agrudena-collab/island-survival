"""RegularDadHouse_V2_Concept: bright toy-style concept build of the new two-storey Regular Dad house (visualization, not final art).

Geometry follows the owner-reviewed drawing set (artifact "Regular Dad House - визуализация и чертёж"): plot 80x76, body 36x44, floors at 1/12/22.
Plot coordinates: x east, z south (stud), h up. Blender coordinates: X = x, Y = -z, Z = h.

Run:  blender -b --factory-startup --python build_house_concept.py -- <out_dir> [shots]
shots = comma list from: front,rear,cut_ground,cut_upper,street,hall,living,kitchen,laundry,uphall,bedroom,lounge,dining (default: all)
"""
import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
WANT = argv[1].split(',') if len(argv) > 1 else None
RES = (int(os.environ.get('RDH_W', '1600')), int(os.environ.get('RDH_H', '1000')))
SAMPLES = int(os.environ.get('RDH_SAMPLES', '48'))
ENGINE = os.environ.get('RDH_ENGINE', 'EEVEE')

HX, HZ = 22.0, 18.0          # house origin in plot coordinates
F0, F1, F2 = 1.0, 12.0, 22.0
OPEN_DOORS = os.environ.get('RDH_OPEN_DOORS', '1') == '1'     # front/back doors stand open so the house can be entered

# ------------------------------------------------------------------ house enlargement (plan warp)
# Rooms stretch, wall bands / trims keep their thickness; heights and all furniture models keep their size.
GROW = float(os.environ.get('RDH_GROW', '1.5'))      # overall growth of the house footprint
BANDS_X = [(-0.7, 1.8), (6.2, 7.8), (13.2, 14.8), (27.2, 28.8), (34.2, 36.5)]
BANDS_Z = [(-2.2, 1.8), (7.2, 8.8), (9.2, 10.8), (15.2, 16.8), (21.2, 22.8), (29.2, 30.8), (42.2, 44.6)]


def _mk_warp(bands, origin):
    gaps = sum(bands[i + 1][0] - bands[i][1] for i in range(len(bands) - 1))
    total = bands[-1][1] - bands[0][0]
    ks = 1.0 + (GROW - 1.0) * total / gaps
    pts, shift = [], 0.0
    for i, (a, b) in enumerate(bands):
        if i:
            shift += (a - bands[i - 1][1]) * (ks - 1.0)
        pts.append((origin + a, origin + a + shift))
        pts.append((origin + b, origin + b + shift))

    def f(x):
        if x <= pts[0][0]:
            return x
        if x >= pts[-1][0]:
            return x + (pts[-1][1] - pts[-1][0])
        for (o0, n0), (o1, n1) in zip(pts, pts[1:]):
            if x <= o1:
                return n0 + (x - o0) * (n1 - n0) / (o1 - o0)
    return f, ks


FX, KSX = _mk_warp(BANDS_X, HX)
FZ0, KSZ = _mk_warp(BANDS_Z, HZ)
DZ = float(os.environ.get('RDH_DZ', '-60'))       # the whole lot (house + yard) is pushed north to the map edge


def FZ(z):
    return FZ0(z) + DZ


HV = float(os.environ.get('RDH_HV', '1.25'))        # storey / roof height growth above the ground slab


def FH(h):
    return h if h <= F0 else F0 + (h - F0) * HV


def warp_v(v, c):
    """vertex (x, -z, h) of an architecture collection -> enlarged house"""
    x, y, h = v
    if c != 'Site':
        h = FH(h)
        return (FX(x), -FZ(-y), h)
    return (FX(x), -FZ0(-y), h)


# rooms (free interior faces, u/v relative to the house origin) used to keep furniture against its wall when the room grows
ROOMS = [
    (0, 28.5, 34.2, 1.8, 7.5), (0, 7.5, 13.5, 1.8, 9.5), (0, 1.8, 6.5, 1.8, 9.5), (0, 1.8, 13.5, 10.5, 21.5), (0, 1.8, 13.5, 22.5, 42.2),
    (0, 14.5, 34.2, 1.8, 21.5), (0, 14.5, 34.2, 22.5, 42.2),
    (1, 1.8, 13.5, 1.8, 9.5), (1, 1.8, 13.5, 10.5, 42.2), (1, 14.5, 34.2, 1.8, 15.5), (1, 14.5, 34.2, 16.5, 29.5), (1, 14.5, 34.2, 30.5, 42.2),
    (1, 17.8, 32.2, -5.2, 0.0),
]


def _g(a, a0, a1, fn, T=3.2):
    n0, n1 = fn(a0), fn(a1)
    span = a1 - a0
    T = min(T, span * 0.3)
    if a <= a0 + T:
        return n0 + (a - a0)
    if a >= a1 - T:
        return n1 - (a1 - a)
    t = (a - (a0 + T)) / (span - 2 * T)
    return n0 + T + t * ((n1 - n0) - 2 * T)


_GRPS = []


def G_(au, av, fl):
    """begin a rigid furniture group: its members keep their offsets to the anchor, the anchor follows the room growth"""
    X, Z = mpos(au, av, fl)
    _GRPS.append((au, av, X, Z))


def G_end():
    _GRPS.pop()


def pos_(u, v, fl):
    if _GRPS:
        au, av, X0, Z0 = _GRPS[-1]
        return (X0 + (u - au), Z0 + (v - av))
    return mpos(u, v, fl)


def mpos(u, v, fl):
    """furniture anchor (u, v relative to house origin) -> absolute enlarged position; wall-hugging items keep their wall gap"""
    fk = 1 if fl >= F1 - 0.5 else 0
    for tol in (0.0, 0.9):
        for (rf, u0, u1, v0, v1) in ROOMS:
            if rf == fk and u0 - tol <= u <= u1 + tol and v0 - tol <= v <= v1 + tol:
                return (_g(HX + u, HX + u0, HX + u1, FX), _g(HZ + v, HZ + v0, HZ + v1, FZ))
    return (FX(HX + u), FZ(HZ + v))

# ------------------------------------------------------------------ palette (variant 2: bright toy)
P = dict(
    siding='#FFD24D', siding_dk='#F2BE2E', trim='#FFFFFF', roof='#E4473D', roof_dk='#B8332B', shutter='#3FA7FF', door='#16B89A', door2='#8A4B1F',
    lawn='#74D43F', lawn2='#66C735', path='#EFE7D3', fence='#FFFFFF', line='#FFC400', trunk='#8A5A33', leaf='#33B54A', leaf2='#5FD36A',
    plinth='#B9B2A0', cab='#F4F1EA', black='#202228', soil='#4B3524', coral='#FF8A7A', terra='#C8684A', cream='#FFF1D6', navy='#2B3A67', lampshade='#FFE9B0', screen='#0E1117', mirror='#CFE3EE', chimney='#C65B45', glass='#BFE8FF', brass='#FFC93C', sky='#7CC4FF', lamp='#FFF3C4',
    wall_hall='#FFE9B8', wall_liv='#FFA98A', wall_kit='#FFF08A', wall_lau='#9ECDF2', wall_bed='#FFA6C4', wall_lounge='#2E9E7A', wall_bath='#C8F0E6', wall_kid='#CFE4FF',
    wall_din='#FFE4A3', wall_uph='#FFF1D0', floor='#DDA05F', floor2='#D3955A', tile_k='#FFE9B0', tile_l='#BFD9F2', tile_b='#9ADBC8', ceiling='#FFFDF6',
    sofa='#4FB848', sofa2='#3A9A35', orange='#FF8A3D', red='#E4473D', blue='#3FA7FF', yellow='#FFD24D', pink='#FF8FB3', white='#FFFFFF', wood='#9A6232', wood2='#B87A42',
    dark='#33343A', metal='#C8D0D8', teal='#16B89A', skin='#F0B27A', hair='#6B4423', jeans='#2F6FD0', purple='#9B6BDB', cardboard='#C9A06E', road='#4A4D55', walk='#D9D3C3',
)
mats = {}


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _new_tree(m):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return nt, bsdf


def _n(nt, kind, **kw):
    node = nt.nodes.new(kind)
    for k, v in kw.items():
        try:
            setattr(node, k, v)
        except Exception:
            node.inputs[k].default_value = v
    return node


def _lin(h):
    return tuple(srgb2lin(c) for c in hexrgb(h)) + (1.0,)


def _shade(h, k):
    r, g, b = hexrgb(h)
    r, g, b = min(1, r * k), min(1, g * k), min(1, b * k)
    return '#%02X%02X%02X' % (int(r * 255), int(g * 255), int(b * 255))


def _setin(node, name, val):
    for k in ([name] if isinstance(name, str) else name):
        if k in node.inputs:
            node.inputs[k].default_value = val
            return


FABRICS = ('sofa', 'sofa2', 'orange', 'pink', 'purple', 'cream', 'navy', 'yellow', 'teal', 'coral')
PLASTER = ('wall_hall', 'wall_liv', 'wall_kit', 'wall_lau', 'wall_bed', 'wall_lounge', 'wall_bath', 'wall_kid', 'wall_din', 'wall_uph')


def mat(name, hexcol=None, rough=0.55, emit=0.0, spec=0.3):
    key = (name, hexcol)
    if key in mats:
        return mats[key]
    m = bpy.data.materials.new(name + (hexcol or ''))
    base = hexcol or P[name]
    nt, bsdf = _new_tree(m)
    _setin(bsdf, 'Roughness', rough)
    _setin(bsdf, ('Specular IOR Level', 'Specular'), spec)
    col = _lin(base)
    tc = _n(nt, 'ShaderNodeTexCoord')
    sep = _n(nt, 'ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])

    def mix(a, b, fac_out):
        mx = _n(nt, 'ShaderNodeMixRGB')
        mx.inputs['Color1'].default_value = _lin(a)
        mx.inputs['Color2'].default_value = _lin(b)
        nt.links.new(fac_out, mx.inputs['Fac'])
        return mx

    def noise(scale, detail=3.0):
        nz = _n(nt, 'ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = detail
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        return nz

    color_out = None
    if name == 'siding':
        d = _n(nt, 'ShaderNodeMath', operation='DIVIDE')
        d.inputs[1].default_value = 1.25
        nt.links.new(sep.outputs['Z'], d.inputs[0])
        fr = _n(nt, 'ShaderNodeMath', operation='FRACT')
        nt.links.new(d.outputs['Value'], fr.inputs[0])
        ramp = _n(nt, 'ShaderNodeValToRGB')
        cr = ramp.color_ramp
        cr.interpolation = 'LINEAR'
        cr.elements[0].position = 0.0
        cr.elements[0].color = _lin(_shade(base, 0.62))
        cr.elements[1].position = 1.0
        cr.elements[1].color = _lin(_shade(base, 1.06))
        e = cr.elements.new(0.10)
        e.color = _lin(_shade(base, 0.78))
        e2 = cr.elements.new(0.16)
        e2.color = _lin(_shade(base, 0.97))
        nt.links.new(fr.outputs['Value'], ramp.inputs['Fac'])
        nz = noise(4.0)
        mul = _n(nt, 'ShaderNodeMixRGB', blend_type='MULTIPLY')
        mul.inputs['Fac'].default_value = 0.12
        nt.links.new(ramp.outputs['Color'], mul.inputs['Color1'])
        nt.links.new(nz.outputs['Color'], mul.inputs['Color2'])
        color_out = mul.outputs['Color']
    elif name in ('roof', 'roof_dk'):
        br = _n(nt, 'ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 3.0
        br.inputs['Row Height'].default_value = 1.2
        br.inputs['Mortar Size'].default_value = 0.05
        br.inputs['Mortar Smooth'].default_value = 0.0
        br.inputs['Bias'].default_value = 0.0
        br.inputs['Color1'].default_value = _lin(base)
        br.inputs['Color2'].default_value = _lin(_shade(base, 0.86))
        br.inputs['Mortar'].default_value = _lin(_shade(base, 0.5))
        comb = _n(nt, 'ShaderNodeCombineXYZ')
        add = _n(nt, 'ShaderNodeMath', operation='ADD')
        nt.links.new(sep.outputs['X'], comb.inputs['X'])
        nt.links.new(sep.outputs['Y'], comb.inputs['Y'])
        nt.links.new(comb.outputs['Vector'], br.inputs['Vector'])
        color_out = br.outputs['Color']
        _setin(bsdf, 'Roughness', 0.7)
    elif name in ('floor', 'floor2'):
        br = _n(nt, 'ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 9.0
        br.inputs['Row Height'].default_value = 1.1
        br.inputs['Mortar Size'].default_value = 0.025
        br.inputs['Mortar Smooth'].default_value = 0.0
        br.inputs['Bias'].default_value = 0.3
        br.inputs['Color1'].default_value = _lin(base)
        br.inputs['Color2'].default_value = _lin(_shade(base, 0.82))
        br.inputs['Mortar'].default_value = _lin(_shade(base, 0.45))
        comb = _n(nt, 'ShaderNodeCombineXYZ')
        nt.links.new(sep.outputs['X'], comb.inputs['X'])
        nt.links.new(sep.outputs['Y'], comb.inputs['Y'])
        nt.links.new(comb.outputs['Vector'], br.inputs['Vector'])
        color_out = br.outputs['Color']
        _setin(bsdf, 'Roughness', 0.38)
    elif name in ('wood', 'wood2', 'door2', 'trunk'):
        wv = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y')
        wv.inputs['Scale'].default_value = 9.0
        wv.inputs['Distortion'].default_value = 1.6
        wv.inputs['Detail'].default_value = 3.0
        nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
        mx = mix(_shade(base, 1.06), _shade(base, 0.84), wv.outputs['Fac'])
        color_out = mx.outputs['Color']
        _setin(bsdf, 'Roughness', 0.5)
    elif name in ('lawn', 'lawn2'):
        nz = noise(0.7, 4.0)
        mx = mix(_shade(base, 0.9), _shade(base, 1.12), nz.outputs['Fac'])
        color_out = mx.outputs['Color']
        bump = _n(nt, 'ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.25
        nz2 = noise(9.0, 2.0)
        nt.links.new(nz2.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        _setin(bsdf, 'Roughness', 0.9)
    elif name in ('path', 'walk', 'plinth'):
        br = _n(nt, 'ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 2.6
        br.inputs['Row Height'].default_value = 1.3
        br.inputs['Mortar Size'].default_value = 0.07
        br.inputs['Color1'].default_value = _lin(base)
        br.inputs['Color2'].default_value = _lin(_shade(base, 0.92))
        br.inputs['Mortar'].default_value = _lin(_shade(base, 0.62))
        comb = _n(nt, 'ShaderNodeCombineXYZ')
        add = _n(nt, 'ShaderNodeMath', operation='ADD')
        nt.links.new(sep.outputs['X'], add.inputs[0])
        nt.links.new(sep.outputs['Y'], add.inputs[1])
        nt.links.new(add.outputs['Value'], comb.inputs['X'])
        nt.links.new(sep.outputs['Z'], comb.inputs['Y'])
        if name != 'plinth':
            nt.links.new(sep.outputs['X'], comb.inputs['X'])
            nt.links.new(sep.outputs['Y'], comb.inputs['Y'])
        nt.links.new(comb.outputs['Vector'], br.inputs['Vector'])
        color_out = br.outputs['Color']
        _setin(bsdf, 'Roughness', 0.85)
    elif name == 'road':
        nz = noise(6.0, 5.0)
        mx = mix(_shade(base, 0.85), _shade(base, 1.2), nz.outputs['Fac'])
        color_out = mx.outputs['Color']
        _setin(bsdf, 'Roughness', 0.9)
    elif name in ('tile_k', 'tile_l', 'tile_b'):
        ck = _n(nt, 'ShaderNodeTexChecker')
        ck.inputs['Scale'].default_value = 0.7
        ck.inputs['Color1'].default_value = _lin(base)
        ck.inputs['Color2'].default_value = _lin(_shade(base, 0.8))
        nt.links.new(tc.outputs['Object'], ck.inputs['Vector'])
        color_out = ck.outputs['Color']
        _setin(bsdf, 'Roughness', 0.25)
    elif name in FABRICS:
        nz = noise(14.0, 2.0)
        mx = mix(_shade(base, 0.93), _shade(base, 1.05), nz.outputs['Fac'])
        color_out = mx.outputs['Color']
        bump = _n(nt, 'ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.35
        nz2 = noise(40.0, 1.0)
        nt.links.new(nz2.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        _setin(bsdf, 'Roughness', 0.95)
    elif name in PLASTER:
        # painted plaster with a white baseboard (floor levels 1 and 12, storey height 11) and a thin crown line
        sub = _n(nt, 'ShaderNodeMath', operation='SUBTRACT')
        sub.inputs[1].default_value = 1.0
        nt.links.new(sep.outputs['Z'], sub.inputs[0])
        md = _n(nt, 'ShaderNodeMath', operation='MODULO')
        md.inputs[1].default_value = 11.0
        nt.links.new(sub.outputs['Value'], md.inputs[0])
        lt = _n(nt, 'ShaderNodeMath', operation='LESS_THAN')
        lt.inputs[1].default_value = 0.85
        nt.links.new(md.outputs['Value'], lt.inputs[0])
        gt = _n(nt, 'ShaderNodeMath', operation='GREATER_THAN')
        gt.inputs[1].default_value = 10.55
        nt.links.new(md.outputs['Value'], gt.inputs[0])
        both = _n(nt, 'ShaderNodeMath', operation='ADD')
        nt.links.new(lt.outputs['Value'], both.inputs[0])
        nt.links.new(gt.outputs['Value'], both.inputs[1])
        nz = noise(5.0, 3.0)
        paint = mix(_shade(base, 0.96), _shade(base, 1.04), nz.outputs['Fac'])
        bb = _n(nt, 'ShaderNodeMixRGB')
        bb.inputs['Color2'].default_value = _lin('#FFFFFF')
        nt.links.new(both.outputs['Value'], bb.inputs['Fac'])
        nt.links.new(paint.outputs['Color'], bb.inputs['Color1'])
        color_out = bb.outputs['Color']
        _setin(bsdf, 'Roughness', 0.75)
    elif name in ('leaf', 'leaf2'):
        vo = _n(nt, 'ShaderNodeTexVoronoi')
        vo.inputs['Scale'].default_value = 1.4
        nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
        mx = mix(_shade(base, 0.82), _shade(base, 1.14), vo.outputs['Distance'])
        color_out = mx.outputs['Color']
        _setin(bsdf, 'Roughness', 0.8)
    elif name == 'chimney':
        br = _n(nt, 'ShaderNodeTexBrick')
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 1.2
        br.inputs['Row Height'].default_value = 0.6
        br.inputs['Mortar Size'].default_value = 0.04
        br.inputs['Color1'].default_value = _lin(base)
        br.inputs['Color2'].default_value = _lin(_shade(base, 0.82))
        br.inputs['Mortar'].default_value = _lin('#D8CFC0')
        comb = _n(nt, 'ShaderNodeCombineXYZ')
        add = _n(nt, 'ShaderNodeMath', operation='ADD')
        nt.links.new(sep.outputs['X'], add.inputs[0])
        nt.links.new(sep.outputs['Y'], add.inputs[1])
        nt.links.new(add.outputs['Value'], comb.inputs['X'])
        nt.links.new(sep.outputs['Z'], comb.inputs['Y'])
        nt.links.new(comb.outputs['Vector'], br.inputs['Vector'])
        color_out = br.outputs['Color']
    elif name == 'glass':
        _setin(bsdf, 'Alpha', 0.16)
        _setin(bsdf, 'Roughness', 0.03)
        _setin(bsdf, ('Specular IOR Level', 'Specular'), 0.9)
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
        try:
            m.blend_method = 'BLEND'
        except Exception:
            pass
    elif name == 'screen':
        _setin(bsdf, 'Roughness', 0.04)
        _setin(bsdf, 'Metallic', 0.2)
    elif name == 'mirror':
        _setin(bsdf, 'Metallic', 1.0)
        _setin(bsdf, 'Roughness', 0.02)
    elif name in ('metal', 'brass'):
        _setin(bsdf, 'Metallic', 0.85)
        _setin(bsdf, 'Roughness', 0.3)
    elif name in ('ceiling',):
        _setin(bsdf, 'Roughness', 0.9)
    if color_out is not None:
        nt.links.new(color_out, bsdf.inputs['Base Color'])
    else:
        _setin(bsdf, 'Base Color', col)
    if name == 'lamp' and emit == 0:
        emit = 6.0
    if name == 'ceiling' and emit == 0:
        emit = 0.18
    if name == 'lampshade' and emit == 0:
        emit = 0.55
    if emit > 0:
        _setin(bsdf, ('Emission Color', 'Emission'), col)
        _setin(bsdf, 'Emission Strength', emit)
    mats[key] = m
    return m


# ------------------------------------------------------------------ geometry accumulation
acc = {}
colls = {}
BOXLOG = []
DOORLOG = []     # (axis, centre, width, h0, height, wall centre, thickness, kind) in pre-warp plot coordinates
ANCH = {}        # gameplay anchors (world x, height, z, front dx, front dz)


def coll(name):
    if name not in colls:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        colls[name] = c
    return colls[name]


def B(c, m, x0, x1, h0, h1, z0, z1):
    if x1 < x0:
        x0, x1 = x1, x0
    if h1 < h0:
        h0, h1 = h1, h0
    if z1 < z0:
        z0, z1 = z1, z0
    assert x1 - x0 > 1e-6 and h1 - h0 > 1e-6 and z1 - z0 > 1e-6, (c, m, x0, x1, h0, h1, z0, z1)
    if c in ('Ground', 'Yard') and h0 >= F1 - 1.5:
        c = 'Upper'
    BOXLOG.append((c, m.name, x0, x1, h0, h1, z0, z1))
    y0, y1 = -z1, -z0
    v = [(x0, y0, h0), (x1, y0, h0), (x1, y1, h0), (x0, y1, h0), (x0, y0, h1), (x1, y0, h1), (x1, y1, h1), (x0, y1, h1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    base = len(vs)
    vs.extend(v)
    fs.extend([tuple(base + i for i in face) for face in f])


def HB(c, m, u0, u1, h0, h1, v0, v1):
    B(c, m, HX + u0, HX + u1, h0, h1, HZ + v0, HZ + v1)


def quadslab(c, m, p, t):
    """p = 4 plot-space points (x,h,z) of one face in order; extrude by t along the face normal (h-ish direction up)."""
    pts = [(a[0], -a[2], a[1]) for a in p]
    a, b, d = Vector(pts[0]), Vector(pts[1]), Vector(pts[3])
    n = (b - a).cross(d - a).normalized()
    if n.z < 0:
        n = -n
    top = [Vector(q) + n * t for q in pts]
    v = [Vector(q) for q in pts] + top
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    base = len(vs)
    vs.extend([tuple(q) for q in v])
    fs.extend([tuple(base + i for i in face) for face in f])


def prism_x(c, m, x0, x1, tri):
    """triangular prism extruded along x: tri = [(z,h),(z,h),(z,h)] in plot space."""
    pts = [(x0, -z, h) for z, h in tri] + [(x1, -z, h) for z, h in tri]
    f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    base = len(vs)
    vs.extend(pts)
    fs.extend([tuple(base + i for i in face) for face in f])


def build_meshes(bevel=0.08):
    for (c, m), (vs, fs) in acc.items():
        if not c.startswith('Furn'):
            vs = [warp_v(v, c) for v in vs]
        me = bpy.data.meshes.new('%s_%s' % (c, m.name))
        me.from_pydata(vs, [], fs)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new('%s_%s' % (c, m.name), me)
        ob.data.materials.append(m)
        coll(c).objects.link(ob)
        if bevel and not c.startswith('Furn'):
            md = ob.modifiers.new('bevel', 'BEVEL')
            md.width = 0.03 if m.name.startswith(('trim', 'glass', 'shutter', 'door', 'metal', 'brass', 'lamp', 'red', 'wall_')) else bevel
            md.segments = 2
            md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(35)
        finish_mesh(me)


def MT(n):
    return mat(n)


# ------------------------------------------------------------------ openings: wall builders (plot coordinates; absolute)
def wall_x(c, m, x0, x1, zc, th, h0, h1, doors=(), wins=()):
    """wall running along x at z = zc (centre), thickness th."""
    z0, z1 = zc - th / 2, zc + th / 2
    ops = sorted([(d[0] - d[1] / 2, d[0] + d[1] / 2, h0, h0 + d[2]) for d in doors] + [(w[0] - w[1] / 2, w[0] + w[1] / 2, h0 + w[2], h0 + w[3]) for w in wins])
    cur = x0
    for a, b, o0, o1 in ops:
        if a - cur > 0.01:
            B(c, m, cur, a, h0, h1, z0, z1)
        if o1 < h1 - 0.01:
            B(c, m, a, b, o1, h1, z0, z1)
        if o0 > h0 + 0.01:
            B(c, m, a, b, h0, o0, z0, z1)
        cur = b
    if x1 - cur > 0.01:
        B(c, m, cur, x1, h0, h1, z0, z1)


def wall_z(c, m, z0, z1, xc, th, h0, h1, doors=(), wins=()):
    x0, x1 = xc - th / 2, xc + th / 2
    ops = sorted([(d[0] - d[1] / 2, d[0] + d[1] / 2, h0, h0 + d[2]) for d in doors] + [(w[0] - w[1] / 2, w[0] + w[1] / 2, h0 + w[2], h0 + w[3]) for w in wins])
    cur = z0
    for a, b, o0, o1 in ops:
        if a - cur > 0.01:
            B(c, m, x0, x1, h0, h1, cur, a)
        if o1 < h1 - 0.01:
            B(c, m, x0, x1, o1, h1, a, b)
        if o0 > h0 + 0.01:
            B(c, m, x0, x1, h0, o0, a, b)
        cur = b
    if z1 - cur > 0.01:
        B(c, m, x0, x1, h0, h1, cur, z1)


def frame_x(c, xc, w, h0, hh, zc, th, trim='trim', pad=0.45, depth=0.3, door=True):
    """white frame around an opening in a wall along x (plane z); covers both faces."""
    t = MT(trim)
    DOORLOG.append(('x', xc, w, h0, hh, zc, th, 'int'))
    z0, z1 = zc - th / 2 - depth, zc + th / 2 + depth
    xa, xb = xc - w / 2, xc + w / 2
    B(c, t, xa - pad, xa, h0, h0 + hh + pad, z0, z1)
    B(c, t, xb, xb + pad, h0, h0 + hh + pad, z0, z1)
    B(c, t, xa - pad, xb + pad, h0 + hh, h0 + hh + pad, z0, z1)
    if not door:
        B(c, t, xa - pad, xb + pad, h0 - pad, h0, z0, z1)


def frame_z(c, zc, w, h0, hh, xc, th, trim='trim', pad=0.45, depth=0.3, door=True):
    t = MT(trim)
    DOORLOG.append(('z', zc, w, h0, hh, xc, th, 'int'))
    x0, x1 = xc - th / 2 - depth, xc + th / 2 + depth
    za, zb = zc - w / 2, zc + w / 2
    B(c, t, x0, x1, h0, h0 + hh + pad, za - pad, za)
    B(c, t, x0, x1, h0, h0 + hh + pad, zb, zb + pad)
    B(c, t, x0, x1, h0 + hh, h0 + hh + pad, za - pad, zb + pad)
    if not door:
        B(c, t, x0, x1, h0 - pad, h0, za - pad, zb + pad)


def mullion_x(c, xc, w, h0, h1, zc, th):
    t = MT('trim')
    B(c, t, xc - 0.08, xc + 0.08, h0, h1, zc - th / 2 - 0.1, zc + th / 2 + 0.1)
    B(c, t, xc - w / 2, xc + w / 2, (h0 + h1) / 2 - 0.08, (h0 + h1) / 2 + 0.08, zc - th / 2 - 0.1, zc + th / 2 + 0.1)


def mullion_z(c, zc, w, h0, h1, xc, th):
    t = MT('trim')
    B(c, t, xc - th / 2 - 0.1, xc + th / 2 + 0.1, h0, h1, zc - 0.08, zc + 0.08)
    B(c, t, xc - th / 2 - 0.1, xc + th / 2 + 0.1, (h0 + h1) / 2 - 0.08, (h0 + h1) / 2 + 0.08, zc - w / 2, zc + w / 2)


# ================================================================== BUILD
def build():
    S = 'Site'
    Y = 'Yard'
    G = 'Ground'
    U = 'Upper'
    R = 'Roof'
    FG = 'Furn_G'
    FU = 'Furn_U'
    # ---------------- world: ground, street, plot
    B(S, MT('lawn'), -70, 160, -2, 0, -60, 150)
    B(S, MT('lawn2'), -70, 160, 0, 0.02, -60, 10)
    B(S, MT('walk'), -70, 160, 0, 0.35, 78, 86)
    B(S, MT('road'), -70, 160, 0, 0.15, 88, 112)
    for x in range(-66, 158, 12):
        B(S, MT('line'), x, x + 6, 0.15, 0.2, 99.5, 100.5)
    B(Y, MT('lawn2'), 0, 80, 0, 0.03, 0, 76)
    B(Y, MT('line'), -0.6, 80.6, 0, 0.1, -0.6, 0.6)
    B(Y, MT('line'), -0.6, 80.6, 0, 0.1, 75.4, 76.6)
    B(Y, MT('line'), -0.6, 0.6, 0, 0.1, 0, 76)
    B(Y, MT('line'), 79.4, 80.6, 0, 0.1, 0, 76)
    # paths
    pc = MT('path')
    B(Y, pc, 29, 34, 0, 0.12, 62, 76)
    B(Y, pc, 29, 34, 0, 0.12, 76, 78)
    B(Y, pc, 30.25, 34.75, 0, 0.12, 11, 18)
    B(Y, pc, 34, 62, 0, 0.12, 66, 70)
    B(Y, pc, 62, 68, 0, 0.12, 0, 70)
    # fence (white pickets, 3.0 high) with gates 28.5..34.5 front and 62..68 back
    fc = MT('fence')

    def fence_x(z, gate):
        for x in [i * 1.6 for i in range(0, 51)]:
            if gate[0] - 0.4 < x < gate[1] + 0.4:
                continue
            B(Y, fc, x, x + 0.5, 0, 3.0, z - 0.2, z + 0.2)
        for a, b in ((0, gate[0]), (gate[1], 80)):
            B(Y, fc, a, b, 0.6, 0.95, z - 0.3, z + 0.3)
            B(Y, fc, a, b, 2.1, 2.45, z - 0.3, z + 0.3)
        for gx in gate:
            B(Y, MT('red'), gx - 0.45, gx + 0.45, 0, 4.6, z - 0.45, z + 0.45)
            B(Y, MT('yellow'), gx - 0.6, gx + 0.6, 4.6, 5.0, z - 0.6, z + 0.6)

    def fence_z(x):
        for z in [i * 1.6 for i in range(0, 48)]:
            B(Y, fc, x - 0.2, x + 0.2, 0, 3.0, z, z + 0.5)
        B(Y, fc, x - 0.3, x + 0.3, 0.6, 0.95, 0, 76)
        B(Y, fc, x - 0.3, x + 0.3, 2.1, 2.45, 0, 76)

    # ---------------- house shell
    sd = MT('siding')
    tr = MT('trim')
    EXT = 1.5
    # slab + plinth
    B(G, MT('plinth'), HX - 0.6, HX + 36.6, 0, F0, HZ - 0.6, HZ + 44.6)
    # floors per room (thin overlays over plinth top)
    fl = MT('floor')
    B(G, fl, HX + 1.5, HX + 34.5, F0, F0 + 0.04, HZ + 1.5, HZ + 42.5)
    def checker(mname, hex2, x0, x1, z0, z1, sq=2.0):
        m1, m2 = MT(mname), mat(mname + '2', hex2)
        nx, nz = int(math.ceil((x1 - x0) / sq)), int(math.ceil((z1 - z0) / sq))
        for i in range(nx):
            for j in range(nz):
                B(G, m1 if (i + j) % 2 == 0 else m2, x0 + i * sq, min(x0 + (i + 1) * sq, x1), F0 + 0.04, F0 + 0.08, z0 + j * sq, min(z0 + (j + 1) * sq, z1))

    checker('tile_k', '#EBC878', HX + 1.5, HX + 13.5, HZ + 10.5, HZ + 21.5)
    checker('tile_l', '#8FB4DC', HX + 7.5, HX + 13.5, HZ + 1.5, HZ + 9.5)
    checker('tile_l', '#8FB4DC', HX + 1.5, HX + 6.5, HZ + 1.5, HZ + 9.5)
    checker('tile_b', '#6BBFA6', HX + 28.5, HX + 34.5, HZ + 1.5, HZ + 7.5)
    # upper floor slab with stair hole u1.5..6 v26.5..42.5
    sl = MT('ceiling')
    uf = MT('floor2')
    for (u0, u1, v0, v1) in ((6, 34.5, 1.5, 42.5), (1.5, 6, 1.5, 26.5)):
        HB(U, sl, u0, u1, F1 - 1, F1, v0, v1)
        HB(U, uf, u0, u1, F1, F1 + 0.04, v0, v1)
    # roof slab (ceiling of 2nd floor)
    HB(R, sl, 0, 36, F2, F2 + 1, 0, 44)
    # exterior walls: ground
    # S wall (z outer = HZ+44): door u7..12 (w5,h8.5) center u9.5 ; windows living u20,u30 ; drawn centre line z = HZ+43.25
    zS, zN, xW, xE = HZ + 43.25, HZ + 0.75, HX + 0.75, HX + 35.25
    wall_x(G, sd, HX, HX + 36, zS, EXT, F0, F1, doors=[(HX + 9.5, 5, 8.5)], wins=[(HX + 20, 5, 3, 7.5), (HX + 30, 5, 3, 7.5)])
    wall_x(G, sd, HX, HX + 36, zN, EXT, F0, F1, doors=[(HX + 10.5, 4.5, 8)], wins=[(HX + 22, 5, 3, 7.5), (HX + 32, 2.5, 3, 7.5)])
    wall_z(G, sd, HZ, HZ + 44, xW, EXT, F0, F1, wins=[(HZ + 16, 4, 3, 7.5)])
    wall_z(G, sd, HZ, HZ + 44, xE, EXT, F0, F1, wins=[(HZ + 11, 5, 3, 7.5), (HZ + 33, 5, 3, 7.5)])
    # upper ext
    wall_x(U, sd, HX, HX + 36, zS, EXT, F1, F2, wins=[(HX + 9.5, 4, 3, 7.5), (HX + 20, 5, 3, 7.5), (HX + 30, 5, 3, 7.5)])
    wall_x(U, sd, HX, HX + 36, zN, EXT, F1, F2, doors=[(HX + 28, 4.5, 8)], wins=[(HX + 7, 3, 3, 7.5), (HX + 21, 5, 3, 7.5)])
    wall_z(U, sd, HZ, HZ + 44, xW, EXT, F1, F2, wins=[(HZ + 5, 3, 3, 7.5), (HZ + 18, 4, 3, 7.5)])
    wall_z(U, sd, HZ, HZ + 44, xE, EXT, F1, F2, wins=[(HZ + 8, 5, 3, 7.5), (HZ + 23, 5, 3, 7.5)])
    # interior lining: paint the inner face of the exterior walls per room
    def line_x(c, spans, zc, h0, h1, doors, wins):
        for x0, x1, mn in spans:
            wall_x(c, MT(mn), x0, x1, zc, 0.3, h0, h1, [d for d in doors if x0 <= d[0] <= x1], [w for w in wins if x0 <= w[0] <= x1])

    def line_z(c, spans, xc, h0, h1, doors, wins):
        for z0, z1, mn in spans:
            wall_z(c, MT(mn), z0, z1, xc, 0.3, h0, h1, [d for d in doors if z0 <= d[0] <= z1], [w for w in wins if z0 <= w[0] <= z1])

    line_x(G, [(HX, HX + 14, 'wall_hall'), (HX + 14, HX + 36, 'wall_liv')], HZ + 42.35, F0, F1, [(HX + 9.5, 5, 8.5)], [(HX + 20, 5, 3, 7.5), (HX + 30, 5, 3, 7.5)])
    line_x(G, [(HX, HX + 14, 'wall_lau'), (HX + 14, HX + 28, 'wall_din'), (HX + 28, HX + 36, 'wall_bath')], HZ + 1.65, F0, F1, [(HX + 10.5, 4.5, 8)], [(HX + 22, 5, 3, 7.5), (HX + 32, 2.5, 3, 7.5)])
    line_z(G, [(HZ, HZ + 10, 'wall_lau'), (HZ + 10, HZ + 22, 'wall_kit'), (HZ + 22, HZ + 44, 'wall_hall')], HX + 1.65, F0, F1, [], [(HZ + 16, 4, 3, 7.5)])
    line_z(G, [(HZ, HZ + 22, 'wall_din'), (HZ + 22, HZ + 44, 'wall_liv')], HX + 34.35, F0, F1, [], [(HZ + 11, 5, 3, 7.5), (HZ + 33, 5, 3, 7.5)])
    line_x(U, [(HX, HX + 14, 'wall_uph'), (HX + 14, HX + 36, 'wall_bed')], HZ + 42.35, F1, F2, [], [(HX + 9.5, 4, 3, 7.5), (HX + 20, 5, 3, 7.5), (HX + 30, 5, 3, 7.5)])
    line_x(U, [(HX, HX + 14, 'wall_bath'), (HX + 14, HX + 36, 'wall_lounge')], HZ + 1.65, F1, F2, [(HX + 28, 4.5, 8)], [(HX + 7, 3, 3, 7.5), (HX + 21, 5, 3, 7.5)])
    line_z(U, [(HZ, HZ + 10, 'wall_bath'), (HZ + 10, HZ + 44, 'wall_uph')], HX + 1.65, F1, F2, [], [(HZ + 5, 3, 3, 7.5), (HZ + 18, 4, 3, 7.5)])
    line_z(U, [(HZ, HZ + 16, 'wall_lounge'), (HZ + 16, HZ + 30, 'wall_kid'), (HZ + 30, HZ + 44, 'wall_bed')], HX + 34.35, F1, F2, [], [(HZ + 8, 5, 3, 7.5), (HZ + 23, 5, 3, 7.5)])
    # corner trim and floor band
    for (cx, cz) in ((HX, HZ), (HX + 36, HZ), (HX, HZ + 44), (HX + 36, HZ + 44)):
        B(G, tr, cx - 0.4, cx + 0.4, F0, F1 - 0.01, cz - 0.4, cz + 0.4)
        B(G, tr, cx - 0.4, cx + 0.4, F1, F2, cz - 0.4, cz + 0.4)
    B(G, tr, HX - 0.3, HX + 36.3, F1 - 0.5, F1 + 0.5, HZ - 0.3, HZ)
    B(G, tr, HX - 0.3, HX + 36.3, F1 - 0.5, F1 + 0.5, HZ + 44, HZ + 44.3)
    B(G, tr, HX - 0.3, HX, F1 - 0.5, F1 + 0.5, HZ, HZ + 44)
    B(G, tr, HX + 36, HX + 36.3, F1 - 0.5, F1 + 0.5, HZ, HZ + 44)
    # ---- openings: every window / door is one clean unit (no coplanar duplicates)
    gl = MT('glass')
    shm = MT('shutter')
    shd = MT('trim')

    def bx(axis, c, m, a0, a1, h0, h1, d0, d1):
        """box in wall-local terms: axis 'x' -> wall runs along x, d is z; axis 'z' -> wall runs along z, d is x."""
        if axis == 'x':
            B(c, m, a0, a1, h0, h1, min(d0, d1), max(d0, d1))
        else:
            B(c, m, min(d0, d1), max(d0, d1), h0, h1, a0, a1)

    def win_unit(axis, ac, w, hb, wc, side, shutters, th=EXT, s0=3.0, s1=7.5):
        c = U if hb >= F1 else G
        o = wc + side * th / 2           # outer face
        i = wc - side * th / 2           # inner face of the structural wall (lining adds 0.3 more)
        y0, y1 = hb + s0, hb + s1
        a0, a1 = ac - w / 2, ac + w / 2
        pad = 0.45
        # outer frame (0.3 proud of the wall) around the opening
        bx(axis, c, tr, a0 - pad, a0, y0 - 0.0, y1 + pad, o, o + side * 0.3)
        bx(axis, c, tr, a1, a1 + pad, y0 - 0.0, y1 + pad, o, o + side * 0.3)
        bx(axis, c, tr, a0 - pad, a1 + pad, y1, y1 + pad, o, o + side * 0.3)
        # sill (single piece, proud 0.7)
        bx(axis, c, tr, a0 - pad - 0.3, a1 + pad + 0.3, y0 - 0.35, y0, o, o + side * 0.7)
        # inner frame
        li = i - side * 0.3
        bx(axis, c, tr, a0 - 0.4, a0, y0 - 0.4, y1 + 0.4, li, li - side * 0.14)
        bx(axis, c, tr, a1, a1 + 0.4, y0 - 0.4, y1 + 0.4, li, li - side * 0.14)
        bx(axis, c, tr, a0 - 0.4, a1 + 0.4, y1, y1 + 0.4, li, li - side * 0.14)
        bx(axis, c, tr, a0 - 0.4, a1 + 0.4, y0 - 0.4, y0, li, li - side * 0.14)
        # glass + 4-pane mullions in the middle of the wall
        bx(axis, c, gl, a0, a1, y0, y1, wc - 0.03, wc + 0.03)
        bx(axis, c, tr, ac - 0.07, ac + 0.07, y0, y1, wc - 0.1, wc + 0.1)
        bx(axis, c, tr, a0, a1, (y0 + y1) / 2 - 0.07, (y0 + y1) / 2 + 0.07, wc - 0.1, wc + 0.1)
        if shutters:
            for sgn in (-1, 1):
                s_in = ac + sgn * (w / 2 + pad + 0.12)
                s_out = ac + sgn * (w / 2 + pad + 1.45)
                bx(axis, c, shm, min(s_in, s_out), max(s_in, s_out), y0 - 0.3, y1 + pad, o, o + side * 0.22)
                for k in range(1, 6):
                    yy = y0 - 0.3 + k * ((y1 + pad - y0 + 0.3) / 6)
                    bx(axis, c, MT('trim'), min(s_in, s_out) + 0.12, max(s_in, s_out) - 0.12, yy, yy + 0.07, o + side * 0.22, o + side * 0.27)

    # south wall (side +1), north wall (side -1): axis 'x'; east (+1) / west (-1): axis 'z'
    for ac, hb, w, sh in ((HX + 20, F0, 5, True), (HX + 30, F0, 5, True), (HX + 9.5, F1, 4, False), (HX + 20, F1, 5, True), (HX + 30, F1, 5, True)):
        win_unit('x', ac, w, hb, zS, +1, sh)
    for ac, hb, w, sh in ((HX + 22, F0, 5, True), (HX + 32, F0, 2.5, False), (HX + 7, F1, 3, False), (HX + 21, F1, 5, True)):
        win_unit('x', ac, w, hb, zN, -1, sh)
    for ac, hb, w, sh in ((HZ + 11, F0, 5, True), (HZ + 33, F0, 5, True), (HZ + 8, F1, 5, True), (HZ + 23, F1, 5, True)):
        win_unit('z', ac, w, hb, xE, +1, sh)
    for ac, hb, w, sh in ((HZ + 16, F0, 4, False), (HZ + 5, F1, 3, False), (HZ + 18, F1, 4, False)):
        win_unit('z', ac, w, hb, xW, -1, sh)
    # flower boxes under ground-floor south windows (clear of the sill)
    for xc in (HX + 20, HX + 30):
        B(Y, MT('wood2'), xc - 2.7, xc + 2.7, F0 + 1.55, F0 + 2.4, HZ + 44.45, HZ + 45.35)
        B(Y, MT('dark'), xc - 2.5, xc + 2.5, F0 + 2.4, F0 + 2.55, HZ + 44.6, HZ + 45.2)
        for i in range(6):
            B(Y, MT(['red', 'yellow', 'pink'][i % 3]), xc - 2.3 + i * 0.9, xc - 1.85 + i * 0.9, F0 + 2.55, F0 + 3.3, HZ + 44.75, HZ + 45.1)
            B(Y, MT('leaf'), xc - 2.35 + i * 0.9, xc - 1.8 + i * 0.9, F0 + 2.55, F0 + 2.85, HZ + 44.7, HZ + 45.15)

    def door_leaf_s(xc, w, hh, col, glass_rect=None, panels=True):
        """closed leaf in the south wall opening, recessed 0.2 from the outer face"""
        o = zS + EXT / 2
        DOORLOG.append(('x', xc, w, F0, hh, zS, EXT, 'front'))
        if OPEN_DOORS:
            # the leaf stands open (swung inwards) so the doorway is passable
            B(G, MT(col), xc + w / 2 - 0.35, xc + w / 2, F0, F0 + hh, o - 0.9 - w * 0.9, o - 0.9)
            B(G, MT('brass'), xc + w / 2 - 0.55, xc + w / 2 - 0.35, F0 + 3.6, F0 + 3.9, o - 0.9 - w * 0.9 + 0.3, o - 0.9 - w * 0.9 + 0.6)
        else:
            B(G, MT(col), xc - w / 2, xc + w / 2, F0, F0 + hh, o - 0.55, o - 0.2)
        B(G, tr, xc - w / 2 - 0.55, xc - w / 2, F0, F0 + hh + 0.55, o - 0.9, o + 0.3)
        B(G, tr, xc + w / 2, xc + w / 2 + 0.55, F0, F0 + hh + 0.55, o - 0.9, o + 0.3)
        B(G, tr, xc - w / 2 - 0.55, xc + w / 2 + 0.55, F0 + hh, F0 + hh + 0.55, o - 0.9, o + 0.3)
        B(G, tr, xc - w / 2, xc + w / 2, F0, F0 + 0.18, o - 0.9, o + 0.45)
        if OPEN_DOORS:
            return
        if glass_rect:
            g0, g1, h0_, h1_ = glass_rect
            B(G, gl, g0, g1, F0 + h0_, F0 + h1_, o - 0.42, o - 0.34)
            B(G, tr, g0 - 0.16, g1 + 0.16, F0 + h0_ - 0.16, F0 + h1_ + 0.16, o - 0.3, o - 0.2)
            B(G, tr, (g0 + g1) / 2 - 0.05, (g0 + g1) / 2 + 0.05, F0 + h0_, F0 + h1_, o - 0.34, o - 0.2)
        if panels:
            for px in (xc - 1.2, xc + 1.2):
                B(G, MT(col), px - 0.85, px + 0.85, F0 + 1.1, F0 + 3.6, o - 0.2, o - 0.1)
        B(G, MT('brass'), xc + w / 2 - 0.75, xc + w / 2 - 0.45, F0 + 3.9, F0 + 4.2, o - 0.2, o + 0.18)
        B(G, MT('brass'), xc + w / 2 - 0.8, xc + w / 2 - 0.4, F0 + 3.45, F0 + 3.75, o - 0.2, o - 0.05)

    # front door + porch (columns, canopy, lantern, mat, number)
    xd = HX + 9.5
    door_leaf_s(xd, 5, 8.5, 'door', glass_rect=(xd - 1.5, xd + 1.5, 5.2, 7.9))
    zf = zS + EXT / 2
    B(G, MT('path'), HX + 5, HX + 14.2, F0 - 0.5, F0, zf, zf + 3.6)
    B(G, MT('path'), HX + 4, HX + 15.2, 0, F0 - 0.5, zf, zf + 5.6)
    B(G, MT('red'), xd - 1.5, xd + 1.5, F0, F0 + 0.1, zf + 0.5, zf + 2.0)
    B(G, tr, HX + 5.2, HX + 14.4, F0 + 8.8, F0 + 9.4, zf - 0.3, zf + 3.9)
    B(G, MT('roof'), HX + 4.8, HX + 14.8, F0 + 9.4, F0 + 10.0, zf - 0.3, zf + 4.3)
    B(G, MT('roof_dk'), HX + 4.8, HX + 14.8, F0 + 10.0, F0 + 10.15, zf - 0.3, zf + 4.3)
    for xx in (HX + 5.7, HX + 13.9):
        B(G, tr, xx - 0.3, xx + 0.3, F0, F0 + 8.8, zf + 3.1, zf + 3.7)
        B(G, tr, xx - 0.45, xx + 0.45, F0, F0 + 0.35, zf + 2.95, zf + 3.85)
        B(G, tr, xx - 0.45, xx + 0.45, F0 + 8.4, F0 + 8.8, zf + 2.95, zf + 3.85)
    B(G, MT('lamp'), HX + 14.5, HX + 15.0, F0 + 6.6, F0 + 7.6, zf, zf + 0.3)
    B(G, tr, HX + 15.1, HX + 16.3, F0 + 3.6, F0 + 4.4, zf, zf + 0.12)
    # back door (wood + glass) + steps
    xb = HX + 10.5
    ob = zN - EXT / 2
    DOORLOG.append(('x', xb, 4.5, F0, 8.0, zN, EXT, 'back'))
    if OPEN_DOORS:
        B(G, MT('door2'), xb - 2.25, xb - 1.9, F0, F0 + 8, ob - 0.3 - 4.0, ob - 0.3)      # leaf swung outwards
        B(G, gl, xb - 2.2, xb - 1.95, F0 + 4.4, F0 + 7.2, ob - 3.4, ob - 0.8)
    else:
        B(G, MT('door2'), xb - 2.25, xb + 2.25, F0, F0 + 8, ob + 0.2, ob + 0.55)
    for sx in (-1, 1):
        B(G, tr, xb + sx * 2.25 + (0 if sx > 0 else -0.5), xb + sx * 2.25 + (0.5 if sx > 0 else 0), F0, F0 + 8.5, ob - 0.3, ob + 0.9)
    B(G, tr, xb - 2.75, xb + 2.75, F0 + 8, F0 + 8.5, ob - 0.3, ob + 0.9)
    if not OPEN_DOORS:
        B(G, gl, xb - 1.3, xb + 1.3, F0 + 4.4, F0 + 7.2, ob + 0.12, ob + 0.2)
        B(G, tr, xb - 1.46, xb + 1.46, F0 + 4.24, F0 + 4.4, ob + 0.1, ob + 0.22)
        B(G, tr, xb - 1.46, xb + 1.46, F0 + 7.2, F0 + 7.36, ob + 0.1, ob + 0.22)
        B(G, tr, xb - 1.46, xb - 1.3, F0 + 4.24, F0 + 7.36, ob + 0.1, ob + 0.22)
        B(G, tr, xb + 1.3, xb + 1.46, F0 + 4.24, F0 + 7.36, ob + 0.1, ob + 0.22)
        B(G, MT('brass'), xb + 1.35, xb + 1.75, F0 + 3.6, F0 + 3.95, ob, ob + 0.3)
    B(G, MT('path'), xb - 3.0, xb + 3.0, 0, 0.5, ob - 2.5, ob - 0.3)
    B(G, MT('path'), xb - 3.0, xb + 3.0, 0.5, F0, ob - 1.2, ob - 0.3)
    B(G, MT('red'), xb - 1.6, xb + 1.6, F0, F0 + 0.1, ob - 1.0, ob - 0.4)
    # balcony door (open leaf) + balcony
    xbd = HX + 28
    ot = zN - EXT / 2
    for sx in (-1, 1):
        B(U, tr, xbd + sx * 2.25 + (0 if sx > 0 else -0.5), xbd + sx * 2.25 + (0.5 if sx > 0 else 0), F1, F1 + 8.5, ot - 0.3, ot + 0.9)
    B(U, tr, xbd - 2.75, xbd + 2.75, F1 + 8, F1 + 8.5, ot - 0.3, ot + 0.9)
    B(U, MT('door'), xbd - 2.25, xbd - 1.7, F1, F1 + 8, ot - 4.0, ot - 0.2)
    B(U, gl, xbd - 2.2, xbd - 1.75, F1 + 3.8, F1 + 7.4, ot - 3.4, ot - 0.8)
    # deck, fascia, balusters, rail
    B(U, MT('wood2'), HX + 17.8, HX + 32.2, F1 - 0.9, F1, HZ - 5.2, HZ)
    B(U, tr, HX + 17.6, HX + 32.4, F1 - 1.5, F1 - 0.9, HZ - 5.4, HZ - 4.6)
    B(U, tr, HX + 17.6, HX + 18.2, F1 - 1.5, F1 - 0.9, HZ - 5.4, HZ)
    B(U, tr, HX + 31.8, HX + 32.4, F1 - 1.5, F1 - 0.9, HZ - 5.4, HZ)
    for x in [HX + 18.4 + i * 1.2 for i in range(12)]:
        if 24.4 < x - HX < 28.0:           # gap in the rail: the ladder top
            continue
        B(U, tr, x, x + 0.35, F1, F1 + 3.2, HZ - 5.2, HZ - 4.85)
    B(U, tr, HX + 17.8, HX + 24.4, F1 + 3.2, F1 + 3.6, HZ - 5.3, HZ - 4.7)
    B(U, tr, HX + 28.0, HX + 32.2, F1 + 3.2, F1 + 3.6, HZ - 5.3, HZ - 4.7)
    ANCH['ladder_top'] = (FX(HX + 26.2), FH(F1), FZ(HZ - 5.2), 0.0, -1.0)
    ANCH['ladder_foot'] = (FX(HX + 26.2), 0.0, FZ(HZ - 5.2) - 1.2, 0.0, -1.0)
    for z in [HZ - 4.4 + i * 1.2 for i in range(4)]:
        B(U, tr, HX + 17.8, HX + 18.15, F1, F1 + 3.2, z, z + 0.35)
        B(U, tr, HX + 31.85, HX + 32.2, F1, F1 + 3.2, z, z + 0.35)
    B(U, tr, HX + 17.8, HX + 18.4, F1 + 3.2, F1 + 3.6, HZ - 5.3, HZ)
    B(U, tr, HX + 31.6, HX + 32.2, F1 + 3.2, F1 + 3.6, HZ - 5.3, HZ)
    # corner posts to the ground (fixes the old floating brackets)
    for x in (HX + 18.0, HX + 32.0):
        B(G, tr, x - 0.3, x + 0.3, 0, F1 - 0.9, HZ - 5.1, HZ - 4.5)
        B(G, tr, x - 0.45, x + 0.45, 0, 0.4, HZ - 5.25, HZ - 4.35)
    # gutters and downspouts
    gut = MT('trim')
    B(R, gut, HX - 1.6, HX + 37.6, F2 - 0.3, F2 + 0.2, HZ + 45.55, HZ + 46.05)
    B(R, gut, HX - 1.6, HX + 37.6, F2 - 0.3, F2 + 0.2, HZ - 2.05, HZ - 1.55)
    for (dx, dz) in ((HX - 0.2, HZ + 45.7), (HX + 36.2, HZ + 45.7), (HX - 0.2, HZ - 1.9), (HX + 36.2, HZ - 1.9)):
        B(G, MT('metal'), dx - 0.2, dx + 0.2, 0, F2 - 0.3, dz - 0.2, dz + 0.2)
    # foundation vents
    for xv in (HX + 4, HX + 30):
        B(G, MT('dark'), xv, xv + 2.0, 0.25, 0.8, HZ + 44.05, HZ + 44.2)
    # ---------------- interior walls (ground)
    iw = MT('wall_hall')
    wall_x(G, MT('wall_kit'), HX + 1.5, HX + 14, HZ + 10, 1, F0, F1, doors=[(HX + 10.5, 4.5, 8)])
    wall_x(G, MT('wall_hall'), HX + 1.5, HX + 14, HZ + 22, 1, F0, F1, doors=[(HX + 9.5, 4.5, 8)])
    wall_z(G, MT('wall_din'), HZ + 1.5, HZ + 42.5, HX + 14, 1, F0, F1, doors=[(HZ + 16, 4.5, 8), (HZ + 34, 4.5, 8)])
    wall_x(G, MT('wall_liv'), HX + 14, HX + 34.5, HZ + 22, 1, F0, F1, doors=[(HX + 25, 5, 8)])
    wall_z(G, MT('wall_lau'), HZ + 1.5, HZ + 9.5, HX + 7, 1, F0, F1, doors=[(HZ + 5.5, 4, 8)])
    wall_z(G, MT('wall_bath'), HZ + 1.5, HZ + 8, HX + 28, 1, F0, F1, doors=[(HZ + 4.5, 3.5, 8)])
    wall_x(G, MT('wall_bath'), HX + 28, HX + 34.5, HZ + 8, 1, F0, F1)
    # frames for interior doors
    for (xc, zc, w, hh, axis) in ((HX + 10.5, HZ + 10, 4.5, 8, 'x'), (HX + 9.5, HZ + 22, 4.5, 8, 'x'), (HX + 25, HZ + 22, 5, 8, 'x')):
        frame_x(G, xc, w, F0, hh, zc, 1, pad=0.4, depth=0.25)
    for (zc, xc, w) in ((HZ + 16, HX + 14, 4.5), (HZ + 34, HX + 14, 4.5), (HZ + 5.5, HX + 7, 4), (HZ + 4.5, HX + 28, 3.5)):
        frame_z(G, zc, w, F0, 8, xc, 1, pad=0.4, depth=0.25)
    # stair walls: stair core enclosed? open stair; left wall of hall is the ext W wall.
    # ---------------- interior walls (upper)
    wall_x(U, MT('wall_bath'), HX + 1.5, HX + 14, HZ + 10, 1, F1, F2, doors=[(HX + 7, 4, 8)])
    wall_z(U, MT('wall_uph'), HZ + 1.5, HZ + 42.5, HX + 14, 1, F1, F2, doors=[(HZ + 13, 4.5, 8), (HZ + 22, 4.5, 8), (HZ + 37, 4.5, 8)])
    wall_x(U, MT('wall_kid'), HX + 14, HX + 34.5, HZ + 16, 1, F1, F2, doors=[(HX + 20, 4.5, 8)])
    wall_x(U, MT('wall_bed'), HX + 14, HX + 34.5, HZ + 30, 1, F1, F2, doors=[(HX + 30, 4.5, 8)])
    for (xc, zc, w) in ((HX + 7, HZ + 10, 4), (HX + 20, HZ + 16, 4.5), (HX + 30, HZ + 30, 4.5)):
        frame_x(G, xc, w, F1, 8, zc, 1, pad=0.4, depth=0.25)
    for (zc, xc, w) in ((HZ + 13, HX + 14, 4.5), (HZ + 22, HX + 14, 4.5), (HZ + 37, HX + 14, 4.5)):
        frame_z(G, zc, w, F1, 8, xc, 1, pad=0.4, depth=0.25)
    # stairs: 15 steps, rise 11/15, run 16/15, width u1.5..6, bottom v 42.5 going north
    rise, run = 11.0 / 15, 16.0 / 15
    for i in range(1, 16):
        v1 = 42.5 - run * (i - 1)
        v0 = 42.5 - run * i
        HB(G, MT('wood2'), 1.5, 6.0, 0, F0 + rise * i, v0, v1)
        HB(G, MT('cardboard'), 1.5, 6.0, F0 + rise * i - 0.0, F0 + rise * i + 0.04, v0, v1)
    # ---------------- roof (gable, ridge along x at z=HZ+22, h 29.4)
    zr = HZ + 22
    ov = 1.6
    rr = MT('roof')
    rd = MT('roof_dk')
    xa, xb2 = HX - ov, HX + 36 + ov
    # south slope (normal up): points eave-left, eave-right, ridge-right, ridge-left
    he, hr = F2 + 0.3, 29.4
    quadslab(R, rr, [(xa, he, HZ + 44 + ov), (xb2, he, HZ + 44 + ov), (xb2, hr, zr), (xa, hr, zr)], 0.9)
    quadslab(R, rr, [(xa, hr, zr), (xb2, hr, zr), (xb2, he, HZ - ov), (xa, he, HZ - ov)], 0.9)
    for t in [0.12 * i for i in range(1, 9)]:
        zS_ = HZ + 44 + ov + (zr - (HZ + 44 + ov)) * t
        hS_ = he + (hr - he) * t
        quadslab(R, rd, [(xa, hS_ + 0.94, zS_), (xb2, hS_ + 0.94, zS_), (xb2, hS_ + 1.09, zS_ - 0.5), (xa, hS_ + 1.09, zS_ - 0.5)], 0.12)
        zN_ = HZ - ov + (zr - (HZ - ov)) * t
        hN_ = he + (hr - he) * t
        quadslab(R, rd, [(xa, hN_ + 0.94, zN_), (xb2, hN_ + 0.94, zN_), (xb2, hN_ + 1.09, zN_ + 0.5), (xa, hN_ + 1.09, zN_ + 0.5)], 0.12)
    B(R, rd, xa, xb2, hr + 0.6, hr + 1.1, zr - 0.6, zr + 0.6)
    B(R, tr, xa, xb2, he - 0.6, he + 0.1, HZ + 44 + ov - 0.3, HZ + 44 + ov + 0.2)
    B(R, tr, xa, xb2, he - 0.6, he + 0.1, HZ - ov - 0.2, HZ - ov + 0.3)
    # gable triangles
    prism_x(R, sd, HX - 0.0, HX + 1.5, [(HZ - 0.0, F2 + 1), (HZ + 44, F2 + 1), (zr, 29.0)])
    prism_x(R, sd, HX + 34.5, HX + 36.0, [(HZ - 0.0, F2 + 1), (HZ + 44, F2 + 1), (zr, 29.0)])
    prism_x(R, tr, HX - 0.35, HX, [(HZ - ov, F2 + 0.4), (HZ + 44 + ov, F2 + 0.4), (zr, 29.8)])
    prism_x(R, tr, HX + 36.0, HX + 36.35, [(HZ - ov, F2 + 0.4), (HZ + 44 + ov, F2 + 0.4), (zr, 29.8)])
    # attic windows
    for xx in (HX - 0.4, HX + 36.0):
        B(R, MT('shutter'), xx, xx + 0.4, 24.2, 27.4, zr - 1.8, zr + 1.8)
        B(R, tr, xx - 0.05, xx + 0.45, 25.6, 25.9, zr - 1.8, zr + 1.8)
        B(R, tr, xx - 0.05, xx + 0.45, 24.2, 27.4, zr - 0.15, zr + 0.15)
    # chimney
    B(R, MT('chimney'), HX + 24, HX + 27, 26, 33.5, HZ + 24.5, HZ + 27.5)
    B(R, MT('dark'), HX + 23.7, HX + 27.3, 33.5, 34.0, HZ + 24.2, HZ + 27.8)
    for i in range(7):
        B(R, MT('plinth'), HX + 24, HX + 27.02, 26.5 + i, 26.7 + i, HZ + 24.48, HZ + 27.52)
    # ---------------- interior lighting fixtures (emissive)
    lamp = MT('lamp')
    for (u, v, hh) in ((7.5, 33, F0 + 9.3), (24, 33, F0 + 9.3), (24, 11, F0 + 9.3), (6.5, 16, F0 + 9.3), (9.5, 5.5, F0 + 9.3), (24, 32, F1 + 9.3), (24, 8, F1 + 9.3), (24, 23, F1 + 9.3), (7, 22, F1 + 9.3), (22, 37, F1 + 9.3), (31, 5, F1 + 9.3)):
        HB('Lamps_U' if hh > F1 else 'Lamps', lamp, u - 0.9, u + 0.9, hh, hh + 0.5, v - 0.9, v + 0.9)
    yard(Y)
    hq_furniture()
    hq_extra()
    hq_yard()
    hq_fill()


def furniture(FG, FU, Y):
    tr = MT('trim')
    wd = MT('wood')
    w2 = MT('wood2')
    # ---- hall (ground)
    HB(FG, MT('teal'), 6.8, 12.8, F0, F0 + 0.1, 23, 41)
    HB(FG, MT('yellow'), 7.4, 12.2, F0 + 0.1, F0 + 0.14, 23.6, 40.4)
    HB(FG, w2, 12.0, 13.5, F0, F0 + 3, 24, 28)                  # console table (hall east wall, near D04)
    HB(FG, MT('red'), 12.4, 13.1, F0 + 3, F0 + 3.9, 25.5, 26.5)
    HB(FG, MT('white'), 13.45, 13.5, F0 + 4.3, F0 + 8, 24.2, 27.8)
    for k, (v, col) in enumerate(((36.5, 'red'), (38.5, 'blue'))):
        HB(FG, tr, 13.2, 13.5, F0 + 4.6, F0 + 7.6, v - 0.9, v + 0.9)
        HB(FG, MT(col), 13.3, 13.5, F0 + 4.9, F0 + 7.3, v - 0.6, v + 0.6)
    # ---- living (u14.5..34.5, v22.5..42.5)
    HB(FG, MT('teal'), 17, 31, F0, F0 + 0.1, 25, 41)
    HB(FG, MT('red'), 17.8, 30.2, F0 + 0.1, F0 + 0.14, 25.8, 40.2)
    HB(FG, MT('sofa'), 26.9, 33.1, F0, F0 + 1.7, 27.4, 29.6)             # seat
    HB(FG, MT('sofa2'), 26, 34, F0, F0 + 3.8, 26.6, 27.4)                 # back
    HB(FG, MT('sofa2'), 26, 26.9, F0, F0 + 2.8, 27.4, 29.6)               # arms
    HB(FG, MT('sofa2'), 33.1, 34, F0, F0 + 2.8, 27.4, 29.6)
    HB(FG, MT('yellow'), 28, 29.5, F0 + 1.7, F0 + 2.8, 27.6, 28.6)
    HB(FG, MT('red'), 30.5, 32, F0 + 1.7, F0 + 2.8, 27.6, 28.6)
    HB(FG, w2, 27, 33, F0 + 1.0, F0 + 1.4, 32, 34.5)
    for (u, v) in ((27.3, 32.3), (32.3, 32.3), (27.3, 34.0), (32.3, 34.0)):
        HB(FG, wd, u, u + 0.5, F0, F0 + 1.0, v, v + 0.5)
    HB(FG, MT('red'), 29, 30, F0 + 1.4, F0 + 1.9, 33, 33.8)
    HB(FG, MT('orange'), 17, 21, F0, F0 + 1.8, 38, 42)            # armchair
    HB(FG, MT('orange'), 20.2, 21, F0, F0 + 3.7, 38, 42)
    HB(FG, MT('orange'), 17, 21, F0, F0 + 2.8, 38, 38.8)
    HB(FG, MT('orange'), 17, 21, F0, F0 + 2.8, 41.2, 42)
    HB(FG, w2, 33, 34.5, F0, F0 + 6.5, 37, 43)                     # bookshelf
    for i, col in enumerate(('red', 'blue', 'yellow', 'teal', 'purple', 'orange')):
        HB(FG, MT(col), 32.9, 33.05, F0 + 0.6 + i * 1.0, F0 + 1.4 + i * 1.0, 37.3, 42.7)
    HB(FG, MT('dark'), 15.0, 15.4, F0 + 3.6, F0 + 6.8, 25.5, 30.5)     # tv on west wall near hall
    HB(FG, MT('dark'), 14.6, 15.4, F0, F0 + 2.0, 25, 31)
    HB(FG, MT('metal'), 33.5, 34.0, F0, F0 + 5.6, 23.2, 23.7)           # floor lamp
    HB(FG, MT('yellow'), 33.0, 34.4, F0 + 5.6, F0 + 6.6, 22.8, 24.2)
    HB(FG, MT('leaf'), 33, 34.4, F0, F0 + 2.8, 31, 32.6)
    HB(FG, w2, 33.2, 34.0, F0, F0 + 1, 31.2, 32.4)
    HB(FG, MT('white'), 34.45, 34.5, F0 + 4.2, F0 + 8.2, 24, 29)          # family picture wall east
    HB(FG, MT('orange'), 34.3, 34.45, F0 + 4.5, F0 + 7.9, 24.3, 28.7)
    HB(FG, MT('skin'), 34.25, 34.4, F0 + 5.4, F0 + 7.2, 25.3, 26.3)
    HB(FG, MT('skin'), 34.25, 34.4, F0 + 5.4, F0 + 7.2, 26.8, 27.8)
    HB(FG, MT('skin'), 34.25, 34.4, F0 + 5.2, F0 + 6.4, 25.9, 26.9)
    # ---- dining (u14.5..34.5, v1.5..21.5)
    HB(FG, MT('red'), 19, 29, F0, F0 + 0.1, 5.5, 14.5)
    HB(FG, w2, 19, 29, F0 + 2.4, F0 + 2.8, 8, 12.5)
    for (u, v) in ((19.4, 8.4), (28.2, 8.4), (19.4, 11.6), (28.2, 11.6)):
        HB(FG, wd, u, u + 0.5, F0, F0 + 2.4, v, v + 0.5)
    for k in range(4):
        HB(FG, MT('red'), 20.5 + k * 1.8, 21.9 + k * 1.8, F0, F0 + 1.8, 6.4, 7.6)
        HB(FG, MT('red'), 20.5 + k * 1.8, 21.9 + k * 1.8, F0 + 1.8, F0 + 3.6, 6.4, 6.7)
        HB(FG, MT('red'), 20.5 + k * 1.8, 21.9 + k * 1.8, F0, F0 + 1.8, 13.0, 14.2)
        HB(FG, MT('red'), 20.5 + k * 1.8, 21.9 + k * 1.8, F0 + 1.8, F0 + 3.6, 13.5, 13.8)
    HB(FG, MT('yellow'), 22, 26, F0 + 2.8, F0 + 3.2, 9.5, 11)
    HB(FG, MT('white'), 20, 21.2, F0 + 2.8, F0 + 3.0, 8.4, 9.6)
    HB(FG, MT('white'), 26.8, 28.0, F0 + 2.8, F0 + 3.0, 8.4, 9.6)
    HB(FG, MT('lamp'), 23.5, 24.5, F0 + 6.8, F0 + 9.5, 10, 10.6)
    HB(FG, w2, 14.5, 16.5, F0, F0 + 3.6, 3, 11)                       # sideboard
    for k in range(4):
        HB(FG, MT(['blue', 'yellow', 'red', 'teal'][k]), 16.5, 16.7, F0 + 3.6, F0 + 4.3, 3.5 + k * 1.8, 4.7 + k * 1.8)
    HB(FG, MT('white'), 14.5, 14.6, F0 + 4.5, F0 + 8.2, 4, 10)
    HB(FG, MT('blue'), 14.6, 14.7, F0 + 4.8, F0 + 7.9, 4.4, 9.6)
    # WC
    HB(FG, MT('white'), 33, 34.4, F0, F0 + 1.8, 2.6, 4.2)
    HB(FG, MT('white'), 33.8, 34.4, F0 + 1.8, F0 + 3.6, 2.6, 4.2)
    HB(FG, MT('white'), 29, 31, F0, F0 + 2.8, 6.2, 7.4)
    # ---- kitchen (u1.5..13.5, v10.5..21.5)
    cab = MT('white')
    HB(FG, cab, 1.5, 3.5, F0, F0 + 3.0, 11, 21)
    HB(FG, MT('yellow'), 1.5, 3.7, F0 + 3.0, F0 + 3.25, 11, 21)
    HB(FG, cab, 1.5, 2.7, F0 + 6.2, F0 + 9.2, 11, 13.6)
    HB(FG, cab, 1.5, 2.7, F0 + 6.2, F0 + 9.2, 18.4, 21)
    HB(FG, MT('metal'), 1.5, 3.4, F0 + 3.25, F0 + 3.5, 14, 17)
    HB(FG, MT('metal'), 12, 13.5, F0, F0 + 7, 11.2, 14.2)             # fridge
    HB(FG, MT('dark'), 12.0, 12.05, F0 + 4, F0 + 4.1, 11.2, 14.2)
    HB(FG, MT('metal'), 3.5, 5.5, F0, F0 + 3.1, 11, 13)               # stove
    HB(FG, MT('dark'), 3.7, 5.3, F0 + 3.1, F0 + 3.2, 11.2, 12.8)
    HB(FG, MT('metal'), 3.3, 5.7, F0 + 6.3, F0 + 8.6, 10.6, 12.2)
    HB(FG, cab, 5, 10, F0, F0 + 3.6, 14, 17.5)                     # island
    HB(FG, MT('teal'), 4.8, 10.2, F0 + 3.6, F0 + 3.9, 13.8, 17.7)
    for u in (6, 8.2):
        HB(FG, MT('red'), u, u + 1.1, F0, F0 + 2.3, 18.1, 19.2)
        HB(FG, MT('red'), u - 0.1, u + 1.2, F0 + 2.3, F0 + 2.6, 18.0, 19.3)
    for u in (6.5, 8.5):
        HB(FG, MT('lamp'), u, u + 0.9, F0 + 7.2, F0 + 8.0, 15.4, 16.2)
    HB(FG, MT('red'), 6.5, 7.8, F0 + 3.9, F0 + 4.7, 15, 16)      # fruit bowl
    # ---- laundry (u7.5..13.5, v1.5..9.5)
    HB(FG, MT('white'), 11.5, 13.5, F0, F0 + 3.4, 3, 6)
    HB(FG, MT('blue'), 11.45, 11.6, F0 + 0.9, F0 + 2.6, 3.6, 5.4)
    HB(FG, MT('white'), 11.5, 13.5, F0, F0 + 3.4, 6.2, 9.2)
    HB(FG, MT('blue'), 11.45, 11.6, F0 + 0.9, F0 + 2.6, 6.8, 8.6)
    HB(FG, w2, 12.5, 13.5, F0 + 5, F0 + 5.3, 2.5, 9)
    for k, col in enumerate(('red', 'blue', 'yellow')):
        HB(FG, MT(col), 12.7, 13.3, F0 + 5.3, F0 + 6.4, 3 + k * 1.8, 4.2 + k * 1.8)
    HB(FG, MT('orange'), 8.2, 9.8, F0, F0 + 1.7, 7.6, 9.2)
    HB(FG, MT('red'), 8.2, 9.3, F0, F0 + 1.6, 2.4, 3.5)
    # ---- closet H1 (u1.5..6.5, v1.5..9.5): open shelving along the west wall, boxes, coats on a rail; floor stays free for hiding
    HB(FG, w2, 1.5, 1.75, F0, F0 + 7.6, 2.0, 9.0)
    for k in range(5):
        HB(FG, w2, 1.75, 2.9, F0 + 1.2 + k * 1.5, F0 + 1.4 + k * 1.5, 2.0, 9.0)
    for k, col in enumerate(('cardboard', 'blue', 'yellow', 'cardboard', 'red')):
        HB(FG, MT(col), 1.9, 2.7, F0 + 1.4 + k * 1.5, F0 + 2.3 + k * 1.5, 2.3 + (k % 3) * 1.8, 3.9 + (k % 3) * 1.8)
    HB(FG, MT('metal'), 3.8, 6.3, F0 + 6.6, F0 + 6.75, 8.6, 8.8)
    for k, col in enumerate(('purple', 'teal', 'orange', 'blue')):
        HB(FG, MT(col), 4.2 + k * 0.45, 4.55 + k * 0.45, F0 + 3.6, F0 + 6.6, 8.3, 9.1)
    # ---- upper hall
    HB(FU, MT('teal'), 6.5, 12.5, F1, F1 + 0.1, 12, 40)
    HB(FU, MT('yellow'), 7.2, 11.8, F1 + 0.1, F1 + 0.14, 12.6, 39.4)
    for k, (v, col) in enumerate(((16, 'red'), (19, 'blue'), (26, 'yellow'))):
        HB(FU, tr, 13.3, 13.5, F1 + 4.5, F1 + 7.5, v - 0.9, v + 0.9)
        HB(FU, MT(col), 13.28, 13.5, F1 + 4.8, F1 + 7.2, v - 0.6, v + 0.6)
    HB(FU, w2, 12, 13.4, F1, F1 + 2.4, 28, 33)
    HB(FU, MT('leaf'), 12.3, 13.1, F1 + 2.4, F1 + 3.8, 29.5, 31)
    HB(FU, MT('red'), 12.3, 13.1, F1 + 2.0, F1 + 2.4, 29.5, 31)
    # bathroom upper
    HB(FU, MT('white'), 1.8, 5.2, F1, F1 + 2.2, 2, 9)
    HB(FU, MT('blue'), 2.0, 5.0, F1 + 1.2, F1 + 2.25, 2.4, 8.6)
    HB(FU, MT('white'), 8, 12, F1, F1 + 3, 1.8, 3.4)
    HB(FU, MT('white'), 7.5, 9, F1, F1 + 1.8, 7.4, 9.0)
    HB(FU, MT('pink'), 1.5, 13.5, F1, F1 + 0.08, 1.5, 9.5)
    # ---- master bedroom (u14.5..34.5, v30.5..42.5)
    HB(FU, MT('pink'), 17, 28, F1, F1 + 0.1, 33.5, 42)
    HB(FU, wd, 16, 22, F1, F1 + 1.6, 33, 42.5)
    HB(FU, MT('pink'), 16.2, 21.8, F1 + 1.6, F1 + 2.7, 33.3, 41.2)
    HB(FU, MT('white'), 20.2, 21.6, F1 + 2.7, F1 + 3.4, 34, 36.5)
    HB(FU, MT('white'), 20.2, 21.6, F1 + 2.7, F1 + 3.4, 38.5, 41)
    HB(FU, MT('red'), 16.2, 21.8, F1 + 2.7, F1 + 2.9, 36.5, 38.5)
    HB(FU, wd, 16, 22, F1 + 1.6, F1 + 4.6, 42.1, 42.5)
    HB(FU, w2, 22.4, 24.4, F1, F1 + 2.2, 33, 35)
    HB(FU, w2, 22.4, 24.4, F1, F1 + 2.2, 40.5, 42.4)
    HB(FU, MT('lamp'), 23, 23.8, F1 + 2.2, F1 + 3.2, 33.6, 34.4)
    HB(FU, w2, 15, 21, F1, F1 + 3.6, 30.8, 33.2)                    # dresser
    HB(FU, MT('white'), 16, 20, F1 + 4.8, F1 + 8.2, 30.5, 30.6)
    HB(FU, MT('blue'), 16.1, 19.9, F1 + 4.9, F1 + 8.1, 30.52, 30.62)
    # wardrobe H2 (u31..34.5, v34..42) : sides, top, back, open door leaves, clothes
    HB(FU, w2, 31, 34.5, F1, F1 + 0.3, 34, 42)
    HB(FU, w2, 31, 34.5, F1 + 8.2, F1 + 8.7, 34, 42)
    HB(FU, w2, 31, 34.5, F1, F1 + 8.7, 33.6, 34.0)
    HB(FU, w2, 31, 34.5, F1, F1 + 8.7, 42, 42.4)
    HB(FU, MT('wood'), 34.3, 34.5, F1, F1 + 8.7, 34, 42)
    HB(FU, MT('metal'), 31.4, 34.0, F1 + 6.4, F1 + 6.7, 37.8, 38.2)
    for k, col in enumerate(('red', 'blue', 'yellow', 'teal', 'white', 'purple', 'orange')):
        HB(FU, MT(col), 31.8 + k * 0.28, 32.0 + k * 0.28, F1 + 2.0 + (k % 2) * 0.4, F1 + 6.3, 34.4 + k * 1.0, 35.2 + k * 1.0)
    HB(FU, w2, 29.4, 31.0, F1, F1 + 8.2, 33.6, 33.9)             # open door leaves
    HB(FU, w2, 29.4, 31.0, F1, F1 + 8.2, 42.1, 42.4)
    # ---- child room (u14.5..34.5, v16.5..29.5)
    HB(FU, MT('yellow'), 19, 29, F1, F1 + 0.1, 19, 27)
    HB(FU, MT('blue'), 31, 34.5, F1, F1 + 5.0, 18, 26)              # bunk bed
    HB(FU, MT('white'), 31.2, 34.3, F1 + 1.4, F1 + 2.0, 18.2, 25.8)
    HB(FU, MT('red'), 31.2, 34.3, F1 + 3.8, F1 + 4.4, 18.2, 25.8)
    HB(FU, MT('red'), 16, 19, F1, F1 + 1.8, 27, 29)
    for k, col in enumerate(('blue', 'yellow', 'teal')):
        HB(FU, MT(col), 20 + k * 1.5, 21.2 + k * 1.5, F1 + 0.1, F1 + 1.3, 22 + k * 0.6, 23.2 + k * 0.6)
    HB(FU, w2, 22, 28, F1, F1 + 2.6, 17, 19.5)
    HB(FU, MT('lamp'), 25, 26.4, F1 + 2.6, F1 + 3.8, 17.6, 18.8)
    HB(FU, MT('orange'), 15.2, 17.2, F1, F1 + 2.0, 21, 23)
    # ---- dad's lounge (u14.5..34.5, v1.5..15.5)
    HB(FU, MT('orange'), 17, 31, F1, F1 + 0.1, 3, 12)
    HB(FU, MT('yellow'), 18, 30, F1 + 0.1, F1 + 0.14, 4, 11)
    HB(FU, w2, 19.5, 22.5, F1, F1 + 2.8, 2.5, 5)               # table
    HB(FU, MT('teal'), 20.4, 21.3, F1 + 2.8, F1 + 3.5, 3.4, 4.2)    # mug on table
    HB(FU, MT('orange'), 16, 20, F1, F1 + 1.8, 5, 9)            # armchair
    HB(FU, MT('orange'), 16, 16.8, F1, F1 + 3.6, 5, 9)
    HB(FU, MT('orange'), 16, 20, F1, F1 + 2.8, 5, 5.8)
    HB(FU, MT('orange'), 16, 20, F1, F1 + 2.8, 8.2, 9)
    HB(FU, w2, 29.5, 31, F1, F1 + 9, 6, 13)                    # tall bookcase H3
    for i in range(7):
        HB(FU, MT(('red', 'blue', 'yellow', 'teal', 'purple', 'orange', 'white')[i]), 29.4, 29.55, F1 + 0.5 + i * 1.2, F1 + 1.5 + i * 1.2, 6.3, 12.7)
        HB(FU, w2, 29.4, 31, F1 + 0.2 + i * 1.2, F1 + 0.4 + i * 1.2, 6, 13)
    HB(FU, MT('white'), 34.45, 34.5, F1 + 4.5, F1 + 8.0, 5.5, 10.5)
    HB(FU, MT('purple'), 34.3, 34.45, F1 + 4.8, F1 + 7.7, 5.9, 10.1)
    HB(FU, MT('leaf'), 33.3, 34.3, F1, F1 + 2.8, 1.9, 3.2)
    HB(FU, MT('red'), 33.3, 34.3, F1, F1 + 1.2, 1.9, 3.2)
    # Regular Dad (static) at the table, back to the room, mug in hand: x=43, z=24.5
    fx, fz = 21.0, 6.8
    for sx in (-0.85, 0.05):
        HB(FU, MT('hair'), fx + sx, fx + sx + 0.8, F1, F1 + 0.5, fz - 0.7, fz + 0.9)
        HB(FU, MT('jeans'), fx + sx, fx + sx + 0.8, F1 + 0.5, F1 + 2.9, fz - 0.4, fz + 0.5)
    HB(FU, MT('teal'), fx - 1.1, fx + 1.1, F1 + 2.9, F1 + 5.1, fz - 0.6, fz + 0.7)
    HB(FU, MT('teal'), fx - 1.55, fx - 1.1, F1 + 3.2, F1 + 5.0, fz - 0.4, fz + 0.5)
    HB(FU, MT('teal'), fx + 1.1, fx + 1.55, F1 + 3.2, F1 + 5.0, fz - 0.4, fz + 0.5)
    HB(FU, MT('skin'), fx - 1.7, fx - 1.1, F1 + 3.2, F1 + 3.6, fz - 0.4, fz + 0.5)
    HB(FU, MT('skin'), fx + 1.1, fx + 1.7, F1 + 4.6, F1 + 5.0, fz - 1.4, fz - 0.4)
    HB(FU, MT('teal'), fx + 1.1, fx + 1.8, F1 + 5.0, F1 + 5.9, fz - 1.8, fz - 1.0)
    HB(FU, MT('skin'), fx - 0.75, fx + 0.75, F1 + 5.1, F1 + 6.7, fz - 0.6, fz + 0.7)
    HB(FU, MT('hair'), fx - 0.85, fx - 0.55, F1 + 5.5, F1 + 6.4, fz - 0.5, fz + 0.6)
    HB(FU, MT('hair'), fx + 0.55, fx + 0.85, F1 + 5.5, F1 + 6.4, fz - 0.5, fz + 0.6)
    HB(FU, MT('hair'), fx - 0.6, fx + 0.6, F1 + 5.6, F1 + 5.9, fz + 0.7, fz + 0.8)



def curtains(FG, FU):
    cur = MT('wall_bed')
    rod = MT('brass')
    # (axis, window centre, width, floor level, face coordinate, inward sign, colour)
    for kind, ac, w, fl, face, inward, col in (('x', HX + 20, 5, F0, HZ + 42.2, -1, 'orange'), ('x', HX + 30, 5, F0, HZ + 42.2, -1, 'orange'),
                                                ('z', HZ + 33, 5, F0, HX + 34.2, -1, 'orange'), ('z', HZ + 11, 5, F0, HX + 34.2, -1, 'yellow'), ('x', HX + 22, 5, F0, HZ + 1.8, +1, 'yellow'),
                                                ('x', HX + 20, 5, F1, HZ + 42.2, -1, 'pink'), ('x', HX + 30, 5, F1, HZ + 42.2, -1, 'pink'), ('z', HZ + 8, 5, F1, HX + 34.2, -1, 'orange')):
        fc = FG if fl == F0 else FU
        y0, y1 = fl + 2.6, fl + 8.6
        for sgn in (-1, 1):
            a0 = ac + sgn * (w / 2 + 0.2) - (0 if sgn > 0 else 1.1)
            a1 = a0 + 1.1
            if kind == 'x':
                d0, d1 = (face - 0.45, face - 0.12) if inward < 0 else (face + 0.12, face + 0.45)
                B(fc, MT(col), a0, a1, y0 - 0.2, y1 - 0.2, d0, d1)
            else:
                d0, d1 = (face - 0.45, face - 0.12) if inward < 0 else (face + 0.12, face + 0.45)
                B(fc, MT(col), d0, d1, y0 - 0.2, y1 - 0.2, a0, a1)
        if kind == 'x':
            B(fc, rod, ac - w / 2 - 1.6, ac + w / 2 + 1.6, y1, y1 + 0.14, (face - 0.5) if inward < 0 else (face + 0.38), (face - 0.38) if inward < 0 else (face + 0.5))
        else:
            B(fc, rod, (face - 0.5) if inward < 0 else (face + 0.38), (face - 0.38) if inward < 0 else (face + 0.5), y1, y1 + 0.14, ac - w / 2 - 1.6, ac + w / 2 + 1.6)


def plants(FG, FU):
    def pot(fc, u, v, fl, s=1.0, col='red'):
        HB(fc, MT(col), u - 0.7 * s, u + 0.7 * s, fl, fl + 1.5 * s, v - 0.7 * s, v + 0.7 * s)
        HB(fc, MT('leaf'), u - 0.9 * s, u + 0.9 * s, fl + 1.5 * s, fl + 3.2 * s, v - 0.9 * s, v + 0.9 * s)
        HB(fc, MT('leaf2'), u - 0.55 * s, u + 0.55 * s, fl + 3.2 * s, fl + 4.0 * s, v - 0.55 * s, v + 0.55 * s)
    pot(FG, 34.0, 41.6, F0, 1.1, 'teal')
    pot(FG, 15.4, 43.0 - 1.0, F0, 0.9, 'orange')
    pot(FG, 33.8, 19.5, F0, 1.0, 'red')
    pot(FU, 13.0, 41.6, F1, 0.9, 'teal')
    pot(FU, 34.0, 29.0, F1, 0.9, 'orange')


def bush(x, z, r=2.0):
    x, z = FX(x), FZ(z)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, -z, r * 0.8))
    o = bpy.context.object
    o.scale = (1.0, 1.0, 0.8)
    o.data.materials.append(MT('leaf'))
    for p in o.data.polygons:
        p.use_smooth = True
    relink(o)


def yard(Y):
    pass   # replaced by hq_yard() (yard_hq.py)



def cyl(c, mname, x, z, y0, h, r, seg=14):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=(x, -z, y0 + h / 2))
    o = bpy.context.object
    o.data.materials.append(MT(mname))
    for p in o.data.polygons:
        p.use_smooth = True
    for cc in list(o.users_collection):
        cc.objects.unlink(o)
    coll('Upper' if (c in ('Yard', 'Ground') and y0 >= F1 - 1.5) else c).objects.link(o)
    return o


def ball(c, mname, x, z, y, r, sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(x, -z, y))
    o = bpy.context.object
    o.data.materials.append(MT(mname))
    for p in o.data.polygons:
        p.use_smooth = True
    for cc in list(o.users_collection):
        cc.objects.unlink(o)
    coll('Upper' if (c in ('Yard', 'Ground') and y >= F1 - 1.5) else c).objects.link(o)
    return o


def slat_rail(c, mname, x0, x1, z0, h0, z1, h1, t=0.4):
    """slanted rail in the YZ plane at x0..x1 from (z0,h0) to (z1,h1)"""
    quadslab(c, MT(mname), [(x0, h0, z0), (x0, h0, z0 + t), (x0, h1, z1 + t), (x0, h1, z1)], x1 - x0)


def ext_details():
    Y = 'Yard'
    zS, zN, xW, xE, EXT = HZ + 43.25, HZ + 0.75, HX + 0.75, HX + 35.25, 1.5
    tr, br, wd, w2, rd = MT('trim'), MT('brass'), MT('wood'), MT('wood2'), MT('red')
    # ---- front door wreath and doorbell, hose reel, meters, AC unit, rain barrel
    xd = HX + 9.5
    zf = zS + EXT / 2
    import math as _m
    for k in range(10):
        a = _m.radians(36 * k)
        cx_, cy_ = xd + 0.95 * _m.cos(a), F0 + 6.4 + 0.95 * _m.sin(a)
        B(Y, MT('leaf2') if k % 2 == 0 else MT('leaf'), cx_ - 0.22, cx_ + 0.22, cy_ - 0.22, cy_ + 0.22, zf - 0.22, zf - 0.02)
    B(Y, rd, xd - 0.45, xd + 0.45, F0 + 5.35, F0 + 5.8, zf - 0.2, zf - 0.02)
    B(Y, br, HX + 12.4, HX + 12.7, F0 + 4.6, F0 + 4.9, zf - 0.2, zf + 0.05)
    # planters with topiary flanking the door
    for px in (HX + 6.6, HX + 12.4):
        B(Y, MT('teal'), px - 0.6, px + 0.6, F0, F0 + 1.3, zf + 1.2, zf + 2.4)
        B(Y, wd, px - 0.08, px + 0.08, F0 + 1.3, F0 + 2.2, zf + 1.74, zf + 1.86)
        ball(Y, 'leaf', px, zf + 1.8, F0 + 2.9, 0.75)
    # step handrails (both sides of the front steps)
    for xx in (HX + 4.35, HX + 14.85):
        B(Y, tr, xx - 0.15, xx + 0.15, 0, 3.0, zf + 4.8, zf + 5.1)
        B(Y, tr, xx - 0.15, xx + 0.15, F0, F0 + 3.0, zf + 0.4, zf + 0.7)
        B(Y, tr, xx - 0.15, xx + 0.15, 2.7, 3.0, zf + 0.4, zf + 5.1)
        for zz in (1.4, 2.6, 3.8):
            B(Y, tr, xx - 0.1, xx + 0.1, 0, 2.7, zf + zz, zf + zz + 0.2)
    # east wall: electric meter, AC unit, hose reel; back door lantern
    B(Y, MT('metal'), xE + 0.75, xE + 1.15, F0 + 3.5, F0 + 5.8, HZ + 38.2, HZ + 40.2)
    B(Y, MT('white'), xE + 1.15, xE + 1.25, F0 + 4.0, F0 + 5.3, HZ + 38.6, HZ + 39.8)
    B(Y, MT('metal'), xE + 1.2, xE + 4.4, 0, 3.0, HZ + 28.0, HZ + 31.4)
    for k in range(7):
        B(Y, MT('dark'), xE + 4.4, xE + 4.5, 0.3 + k * 0.38, 0.5 + k * 0.38, HZ + 28.2, HZ + 31.2)
    B(Y, MT('lamp'), HX + 6.3, HX + 6.8, F0 + 6.8, F0 + 7.8, HZ - 0.8, HZ - 0.5)
    cyl(Y, 'red', HX + 15.2, HZ - 0.9, 1.0, 0.5, 0.9)
    B(Y, MT('metal'), HX + 14.9, HX + 15.5, 1.6, 2.3, HZ - 1.2, HZ - 0.9)
    cyl(Y, 'wood2', xE + 1.6, HZ - 2.0, 0, 3.0, 1.2, 18)
    cyl(Y, 'metal', xE + 1.6, HZ - 2.0, 1.0, 0.18, 1.25, 18)
    cyl(Y, 'metal', xE + 1.6, HZ - 2.0, 2.2, 0.18, 1.25, 18)
    cyl(Y, 'dark', xE + 1.6, HZ - 2.0, 3.0, 0.15, 1.3, 18)
    # roof detail: ridge vents, flashing and chimney cap + pots
    cx0, cz0 = HX + 24, HZ + 24.5
    B('Roof', MT('metal'), cx0 - 0.25, cx0 + 3.25, 28.6, 29.0, cz0 - 0.25, cz0 + 3.25)
    B('Roof', MT('plinth'), cx0 - 0.4, cx0 + 3.4, 33.5, 34.0, cz0 - 0.4, cz0 + 3.4)
    for dx in (0.6, 2.1):
        B('Roof', MT('red'), cx0 + dx, cx0 + dx + 0.8, 34.0, 34.9, cz0 + 1.1, cz0 + 1.9)
        B('Roof', MT('dark'), cx0 + dx + 0.1, cx0 + dx + 0.7, 34.9, 35.0, cz0 + 1.2, cz0 + 1.8)
    for xr in range(int(HX + 2), int(HX + 36), 6):
        B('Roof', MT('dark'), xr, xr + 1.6, 29.55, 30.15, HZ + 21.4, HZ + 22.6)
    # eave soffits (white boards under the overhang) and fascia boards
    ov = 1.6
    B('Roof', tr, HX - ov, HX + 36 + ov, F2 - 0.2, F2 + 0.05, HZ + 44, HZ + 44 + ov)
    B('Roof', tr, HX - ov, HX + 36 + ov, F2 - 0.2, F2 + 0.05, HZ - ov, HZ)
    # ---- back yard: grill, picnic table, raised beds, swing set, sandbox, clothesline, bird house, bins, stepping stones, ladder B
    # barbecue
    B(Y, MT('dark'), 71.0, 74.0, 2.2, 3.3, 8.0, 10.2)
    B(Y, MT('red'), 71.0, 74.0, 3.3, 4.3, 8.0, 10.2)
    for (lx, lz) in ((71.1, 8.1), (73.5, 8.1), (71.1, 9.6), (73.5, 9.6)):
        B(Y, MT('metal'), lx, lx + 0.4, 0, 2.2, lz, lz + 0.4)
    B(Y, MT('metal'), 74.0, 74.5, 2.8, 3.2, 8.2, 10.0)
    cyl(Y, 'dark', 72.5, 10.9, 0, 1.4, 0.4, 10)
    # picnic table with benches and umbrella
    B(Y, wd, 56.0, 62.0, 2.4, 2.8, 56.0, 58.4)
    for bz in (55.0, 58.8):
        B(Y, wd, 56.2, 61.8, 1.5, 1.8, bz, bz + 1.0)
    for lx in (56.5, 61.2):
        B(Y, wd, lx, lx + 0.5, 0, 2.4, 56.4, 58.0)
    cyl(Y, 'trim', 59.0, 57.2, 2.8, 5.0, 0.12, 8)
    quadslab(Y, MT('red'), [(56.0, 7.8, 54.2), (62.0, 7.8, 54.2), (62.0, 7.8, 60.2), (56.0, 7.8, 60.2)], 0.15)
    for (x0, z0) in ((56.0, 54.2), (62.0, 54.2), (62.0, 60.2), (56.0, 60.2)):
        quadslab(Y, MT('yellow'), [(59.0, 8.6, 57.2), (x0, 7.8, z0), (x0 + (0.3 if x0 < 59 else -0.3), 7.8, z0), (59.0, 8.7, 57.2)], 0.05) if False else None
    # raised vegetable beds with rows of plants
    for (bx0, bz0) in ((48.0, 2.5), (48.0, 7.2)):
        B(Y, w2, bx0, bx0 + 8.0, 0, 1.2, bz0, bz0 + 3.6)
        B(Y, MT('dark'), bx0 + 0.3, bx0 + 7.7, 1.2, 1.35, bz0 + 0.3, bz0 + 3.3)
        for i in range(6):
            B(Y, MT(['leaf', 'leaf2', 'red', 'orange', 'leaf', 'yellow'][i]), bx0 + 0.7 + i * 1.2, bx0 + 1.4 + i * 1.2, 1.35, 2.3 + (i % 2) * 0.5, bz0 + 0.9, bz0 + 1.6)
            B(Y, MT(['leaf2', 'leaf', 'orange', 'leaf2', 'red', 'leaf'][i]), bx0 + 0.7 + i * 1.2, bx0 + 1.4 + i * 1.2, 1.35, 2.1 + (i % 3) * 0.3, bz0 + 2.0, bz0 + 2.7)
    # swing set
    for sx in (66.0, 72.0):
        slat_rail(Y, 'wood', sx, sx + 0.4, 45.0, 0, 46.8, 7.4, 0.4)
        slat_rail(Y, 'wood', sx, sx + 0.4, 49.2, 0, 47.4, 7.4, 0.4)
    B(Y, wd, 65.9, 72.5, 7.2, 7.8, 46.6, 47.4)
    for sx in (67.2, 70.2):
        B(Y, MT('metal'), sx, sx + 0.1, 2.0, 7.2, 46.9, 47.0)
        B(Y, MT('metal'), sx + 1.2, sx + 1.3, 2.0, 7.2, 46.9, 47.0)
        B(Y, MT('red'), sx - 0.1, sx + 1.4, 1.7, 2.1, 46.6, 47.4)
    # sandbox with toys, bird house, compost
    B(Y, w2, 70.0, 75.0, 0, 0.8, 30.0, 34.0)
    B(Y, MT('yellow'), 70.3, 74.7, 0.8, 0.95, 30.3, 33.7)
    B(Y, MT('blue'), 71.0, 71.9, 0.95, 1.5, 31.0, 31.8)
    B(Y, MT('red'), 73.0, 73.5, 0.95, 1.9, 32.2, 32.7)
    B(Y, wd, 60.1, 60.5, 0, 5.2, 24.0, 24.4)
    B(Y, MT('red'), 59.5, 61.1, 5.2, 6.3, 23.6, 24.8)
    B(Y, MT('door2'), 59.7, 60.9, 5.2, 5.9, 23.55, 23.62)
    # clothesline
    for px in (HX + 40.0, HX + 40.0):
        pass
    for (px, pz) in ((40.0, 10.0), (52.0, 10.0)):
        pass
    # trash bins by the side path
    cyl(Y, 'leaf', 71.0, 4.0, 0, 2.6, 0.9, 12)
    cyl(Y, 'blue', 73.2, 4.0, 0, 2.6, 0.9, 12)
    # stepping stones (back door to side path) and garden gnome
    for k in range(8):
        B(Y, MT('path'), 44.0 + k * 2.2, 45.4 + k * 2.2, 0, 0.14, 12.0 + (k % 2) * 0.35, 13.4 + (k % 2) * 0.35)
    B(Y, MT('red'), 25.2, 26.2, 0, 0.5, 66.5, 67.5)
    B(Y, MT('blue'), 25.3, 26.1, 0.5, 1.6, 66.6, 67.4)
    B(Y, MT('skin'), 25.4, 26.0, 1.6, 2.1, 66.7, 67.3)
    B(Y, MT('red'), 25.35, 26.05, 2.1, 3.0, 66.65, 67.35)
    B(Y, MT('trim'), 25.3, 26.1, 1.95, 2.25, 67.3, 67.45)
    # ladder B (wood) leaning on the balcony (entry B), rungs between two slanted rails
    for lx in (41.2, 43.8):
        slat_rail(Y, 'wood2', lx - 0.2, lx + 0.2, 9.6, 0, 12.6, 12.2, 0.4)
    for k in range(1, 11):
        t = k / 11.0
        B(Y, w2, 41.0, 44.0, 12.2 * t - 0.12, 12.2 * t + 0.12, 9.9 + 3.0 * t - 0.15, 9.9 + 3.0 * t + 0.15)
    # kid's bike on the front fence and flamingos
    cyl(Y, 'dark', 4.0, 70.5, 0.9, 0.3, 1.2, 12)
    cyl(Y, 'dark', 7.6, 70.5, 0.9, 0.3, 1.2, 12)
    B(Y, MT('red'), 4.0, 7.6, 2.0, 2.3, 70.35, 70.65)
    B(Y, MT('red'), 5.6, 5.9, 1.2, 3.6, 70.35, 70.65)
    for fx in (46.0, 48.0):
        B(Y, MT('metal'), fx, fx + 0.1, 0, 2.6, 71.0, 71.1)
        B(Y, MT('pink'), fx - 0.4, fx + 0.5, 2.6, 3.8, 70.7, 71.5)
        B(Y, MT('pink'), fx + 0.0, fx + 0.2, 3.8, 5.2, 71.0, 71.2)
        B(Y, MT('yellow'), fx - 0.3, fx + 0.5, 5.0, 5.5, 71.0, 71.2)
    # fence gate leaves (open) and caps on the gate posts
    for gx, gz in ((28.5, 76), (34.5, 76)):
        B(Y, MT('trim'), gx - 0.5, gx + 0.5, 4.9, 5.2, gz - 0.5, gz + 0.5)
    # ---- street: parked toy cars, hydrant, signs, crosswalk, bench, trash
    for (cx_, cz_, col) in ((52.0, 91.6, 'blue'), (92.0, 108.4, 'orange')):
        B('Site', MT(col), cx_, cx_ + 8.0, 0.6, 2.6, cz_, cz_ + 3.8)
        B('Site', MT(col), cx_ + 1.8, cx_ + 6.0, 2.6, 4.0, cz_ + 0.3, cz_ + 3.5)
        B('Site', MT('glass'), cx_ + 2.0, cx_ + 5.8, 2.6, 3.9, cz_ + 0.2, cz_ + 3.6)
        for wx in (cx_ + 1.4, cx_ + 6.6):
            for wz in (cz_ - 0.2, cz_ + 3.0):
                B('Site', MT('dark'), wx - 0.8, wx + 0.8, 0.0, 1.6, wz, wz + 1.0)
        B('Site', MT('lamp'), cx_ + 7.9, cx_ + 8.1, 1.0, 1.6, cz_ + 0.3, cz_ + 1.0)
        B('Site', MT('red'), cx_ - 0.1, cx_ + 0.1, 1.0, 1.6, cz_ + 0.3, cz_ + 1.0)
    cyl('Site', 'red', 44.0, 80.0, 0.35, 2.6, 0.55, 10)
    cyl('Site', 'red', 44.0, 80.0, 2.95, 0.4, 0.7, 10)
    B('Site', MT('dark'), 70.0, 70.4, 0.35, 7.0, 80.0, 80.4)
    B('Site', MT('red'), 68.8, 71.6, 7.0, 8.8, 79.9, 80.0)
    B('Site', MT('trim'), 69.1, 71.3, 7.3, 8.5, 79.8, 79.9)
    for k in range(6):
        B('Site', MT('trim'), 28.5 + k * 1.2, 29.2 + k * 1.2, 0.15, 0.2, 88.0, 94.0)
        B('Site', MT('trim'), 28.5 + k * 1.2, 29.2 + k * 1.2, 0.15, 0.2, 106.0, 112.0)
    B('Site', MT('wood2'), 80.0, 85.0, 1.5, 1.9, 79.6, 81.0)
    B('Site', MT('wood2'), 80.0, 85.0, 1.9, 3.6, 81.0, 81.3)
    for lx in (80.3, 84.4):
        B('Site', MT('dark'), lx, lx + 0.3, 0.35, 1.5, 79.8, 80.8)
    cyl('Site', 'metal', 92.0, 80.5, 0.35, 2.2, 0.7, 10)
    cyl('Site', 'dark', 92.0, 80.5, 2.55, 0.25, 0.8, 10)
    # neighbours: windows, doors, chimneys
    for (x, z, w, d, hh) in ((-52, 30, 26, 24, 16), (100, 18, 28, 26, 18), (-48, 4, 22, 20, 14)):
        for k in range(3):
            B('Site', MT('shutter'), x + 2 + k * (w - 4) / 3.0, x + 4.5 + k * (w - 4) / 3.0, 4.5, 9, z + d, z + d + 0.25)
            B('Site', MT('trim'), x + 1.8 + k * (w - 4) / 3.0, x + 4.7 + k * (w - 4) / 3.0, 9.0, 9.4, z + d, z + d + 0.35)
        B('Site', MT('chimney'), x + w - 5, x + w - 3, hh + 1.2, hh + 4.2, z + 3, z + 5)
        B('Site', MT('door'), x + w / 2 - 1.5, x + w / 2 + 1.5, 0.35, 6.5, z + d + 0.25, z + d + 0.45)


def hb(fl, *a):
    HB('Furn_G' if fl == F0 else 'Furn_U', *a)


def int_details():
    wdc, w2c, trm = MT('wood'), MT('wood2'), MT('trim')
    F, U_ = F0, F1
    # ---------------- hall: coat rack with coats, shoe rack, stair runner and newel posts
    hb(F, w2c, 13.2, 13.5, F + 5.8, F + 6.8, 38.2, 42.2)
    for v in (38.8, 40.2, 41.6):
        hb(F, MT('brass'), 12.8, 13.2, F + 6.0, F + 6.3, v - 0.1, v + 0.1)
    for v, col in ((38.4, 'red'), (39.8, 'blue'), (41.2, 'yellow')):
        hb(F, MT(col), 12.6, 13.2, F + 2.6, F + 6.0, v, v + 1.0)
    hb(F, w2c, 11.8, 13.4, F, F + 1.0, 36.8, 38.0)
    hb(F, w2c, 11.8, 13.4, F + 0.5, F + 0.6, 36.8, 38.0)
    for k, col in enumerate(('red', 'dark', 'blue', 'brown' if False else 'wood')):
        hb(F, MT(col), 12.0 + (k % 2) * 0.8, 12.7 + (k % 2) * 0.8, F + 1.0 if k >= 2 else F + 0.6, F + 1.4 if k >= 2 else F + 1.0, 37.0 + (k // 2) * 0.5, 37.5 + (k // 2) * 0.5)
    rise, run = 11.0 / 15, 16.0 / 15
    for i in range(1, 16):
        v1 = 42.5 - run * (i - 1)
        v0 = 42.5 - run * i
        hb(F, MT('red'), 2.5, 5.0, F0 + rise * i + 0.04, F0 + rise * i + 0.1, v0 + 0.1, v1 - 0.05)
    for (v, fl2) in ((42.0, F0), (26.8, F1)):
        hb(F if fl2 == F0 else U_, wdc, 5.6, 6.4, fl2, fl2 + 4.2, v - 0.4, v + 0.4)
        hb(F if fl2 == F0 else U_, trm, 5.5, 6.5, fl2 + 4.2, fl2 + 4.5, v - 0.5, v + 0.5)
        hb(F if fl2 == F0 else U_, MT('brass'), 5.85, 6.15, fl2 + 4.5, fl2 + 4.9, v - 0.15, v + 0.15)
    # ---------------- living: side table with lamp, console items, table items, picture cluster, books
    hb(F, w2c, 24.6, 25.9, F, F + 2.4, 26.8, 28.1)
    hb(F, MT('metal'), 25.15, 25.35, F + 2.4, F + 3.6, 27.35, 27.55)
    hb(F, MT('lamp'), 24.75, 25.75, F + 3.6, F + 4.8, 27.0, 28.0)
    hb(F, MT('black') if 'black' in P else MT('dark'), 14.7, 15.3, F + 2.0, F + 2.35, 26.0, 28.0)
    hb(F, MT('red'), 14.7, 15.1, F + 2.0, F + 2.15, 28.6, 29.8)
    hb(F, MT('yellow'), 28.0, 29.6, F + 1.4, F + 1.46, 32.4, 33.6)
    hb(F, MT('blue'), 28.2, 29.5, F + 1.46, F + 1.52, 32.5, 33.4)
    hb(F, MT('white'), 31.0, 31.6, F + 1.4, F + 1.95, 33.1, 33.7)
    for k, (col, (u0, u1, h0, h1)) in enumerate((('red', (28.0, 29.6, 5.0, 7.4)), ('blue', (29.9, 31.5, 5.6, 7.8)), ('yellow', (31.8, 33.2, 5.0, 6.8)))):
        hb(F, trm, u0, u1, F + h0, F + h1, 22.5, 22.7)
        hb(F, MT(col), u0 + 0.15, u1 - 0.15, F + h0 + 0.15, F + h1 - 0.15, 22.7, 22.82)
    hb(F, MT('trim'), 33.1, 34.4, F + 6.5, F + 6.8, 37.0, 43.0)
    for k, col in enumerate(('red', 'teal', 'yellow', 'blue')):
        hb(F, MT(col), 33.3, 34.2, F + 6.8, F + 7.6 + (k % 2) * 0.4, 37.4 + k * 1.3, 38.2 + k * 1.3)
    ball(('Furn_G'), 'orange', 18.8, 40.0, F + 2.2, 0.55)
    # ---------------- dining: place settings, centerpiece, chandelier ring
    for k in range(4):
        cu = 21.2 + 1.8 * k
        for (v0, v1) in ((8.4, 9.4), (11.1, 12.1)):
            hb(F, MT('white'), cu - 0.55, cu + 0.55, F + 2.8, F + 2.88, v0, v1)
            hb(F, MT(['teal', 'red', 'blue', 'yellow'][k]), cu + 0.5, cu + 0.85, F + 2.8, F + 3.25, v0 + 0.3, v0 + 0.7)
            hb(F, MT('metal'), cu - 0.9, cu - 0.8, F + 2.8, F + 2.84, v0 + 0.1, v1 - 0.1)
    hb(F, MT('blue'), 23.7, 24.3, F + 3.2, F + 4.0, 10.1, 10.7)
    for k, col in enumerate(('red', 'yellow', 'pink')):
        hb(F, MT(col), 23.5 + k * 0.4, 23.8 + k * 0.4, F + 4.0, F + 4.8, 10.2 + (k % 2) * 0.2, 10.5 + (k % 2) * 0.2)
    hb(F, MT('yellow'), 26.4, 27.0, F + 3.2, F + 3.6, 10.3, 10.9)
    for k in range(8):
        import math as _m
        a = _m.radians(45 * k)
        hb(F, MT('lamp'), 24.0 + 1.6 * _m.cos(a) - 0.2, 24.0 + 1.6 * _m.cos(a) + 0.2, F + 6.6, F + 6.9, 10.3 + 1.6 * _m.sin(a) - 0.2, 10.3 + 1.6 * _m.sin(a) + 0.2)
    hb(F, MT('brass'), 23.9, 24.1, F + 7.0, F + 10.0, 10.2, 10.4)
    # ---------------- kitchen: cabinet doors, handles, sink, burners, oven, microwave, clock
    for (v0, v1) in ((13.2, 14.9), (15.1, 16.8), (17.0, 18.7), (18.9, 20.8)):
        hb(F, MT('cab') if 'cab' in P else MT('white'), 3.5, 3.58, F + 0.3, F + 2.8, v0, v1)
        hb(F, MT('brass'), 3.58, 3.72, F + 2.2, F + 2.5, (v0 + v1) / 2 - 0.1, (v0 + v1) / 2 + 0.1)
        hb(F, MT('trim'), 3.58, 3.62, F + 0.3, F + 0.45, v0, v1)
    hb(F, MT('dark'), 1.8, 3.4, F + 3.25, F + 3.3, 14.4, 17.0)
    hb(F, MT('metal'), 2.7, 2.95, F + 3.3, F + 4.5, 15.55, 15.8)
    hb(F, MT('metal'), 2.7, 3.45, F + 4.25, F + 4.5, 15.55, 15.8)
    for (bu, bv) in ((3.8, 11.2), (4.6, 11.2), (3.8, 12.1), (4.6, 12.1)):
        hb(F, MT('dark'), bu, bu + 0.7, F + 3.1, F + 3.18, bv, bv + 0.7)
    hb(F, MT('metal'), 3.9, 4.8, F + 3.18, F + 4.0, 11.4, 12.3)
    hb(F, MT('dark'), 5.5, 5.58, F + 0.4, F + 2.6, 11.3, 12.7)
    hb(F, MT('metal'), 5.58, 5.68, F + 2.3, F + 2.45, 11.2, 12.8)
    hb(F, MT('metal'), 3.8, 5.2, F + 8.6, F + 11.0, 10.6, 11.6)
    hb(F, MT('metal'), 1.9, 3.3, F + 3.25, F + 4.5, 18.6, 20.4)
    hb(F, MT('dark'), 3.3, 3.38, F + 3.4, F + 4.3, 18.8, 20.0)
    hb(F, MT('red'), 1.9, 2.8, F + 3.25, F + 3.9, 13.4, 14.1)
    hb(F, MT('white'), 6.9, 7.9, F + 6.6, F + 7.6, 10.5, 10.62)
    hb(F, MT('dark'), 7.3, 7.5, F + 7.0, F + 7.3, 10.62, 10.7)
    hb(F, MT('dark'), 11.9, 12.0, F + 3.5, F + 5.5, 11.4, 11.6)
    hb(F, MT('dark'), 11.9, 12.0, F + 0.8, F + 2.5, 11.4, 11.6)
    for k, col in enumerate(('red', 'yellow', 'blue')):
        hb(F, MT(col), 11.85, 11.9, F + 5.6 + k * 0.5, F + 6.0 + k * 0.5, 12.0 + k * 0.5, 12.4 + k * 0.5)
    hb(F, MT('yellow'), 12.2, 13.3, F + 7.0, F + 8.2, 11.6, 12.6)
    for (bu, bv) in ((8.2, 15.0), (9.0, 16.0)):
        hb(F, MT('white'), bu, bu + 0.8, F + 3.9, F + 4.1, bv, bv + 0.8)
    hb(F, MT('cab') if 'cab' in P else MT('white'), 5.3, 7.4, F + 0.3, F + 3.2, 17.5, 17.58)
    hb(F, MT('cab') if 'cab' in P else MT('white'), 7.6, 9.7, F + 0.3, F + 3.2, 17.5, 17.58)
    for uu in (6.3, 8.5):
        hb(F, MT('brass'), uu - 0.4, uu + 0.4, F + 2.5, F + 2.7, 17.58, 17.7)
    # ---------------- laundry and closet
    for k in range(3):
        hb(F, MT('red'), 11.4, 11.55, F + 3.0, F + 3.3, 3.3 + k * 0.7, 3.7 + k * 0.7)
    for (v0, v1) in ((3.6, 5.4), (6.8, 8.6)):
        hb(F, MT('glass'), 11.4, 11.5, F + 0.9, F + 2.6, v0, v1)
    hb(F, MT('metal'), 8.0, 9.8, F + 0.1, F + 0.2, 3.0, 5.2)
    for k in range(4):
        hb(F, MT('metal'), 8.0 + k * 0.55, 8.15 + k * 0.55, F + 0.2, F + 4.2, 3.0, 5.2)
    hb(F, MT('trim'), 7.6, 8.0, F, F + 4.5, 5.4, 7.0)
    hb(F, MT('red'), 7.6, 8.0, F + 4.5, F + 4.7, 5.4, 7.0)
    for k, col in enumerate(('red', 'blue', 'dark')):
        hb(F, MT(col), 3.0 + k * 1.1, 4.0 + k * 1.1, F, F + 0.55, 8.0, 8.8)
    hb(F, MT('wood2'), 7.5, 11.1, F + 3.9, F + 4.05, 7.1, 7.3) if False else None
    # ---------------- upper hall, bathroom
    hb(U_, MT('metal'), 12.5, 12.7, F1 + 2.4, F1 + 3.6, 30.6, 30.8)
    hb(U_, MT('lamp'), 12.0, 13.2, F1 + 3.6, F1 + 4.6, 30.2, 31.2)
    hb(U_, MT('red'), 12.6, 13.3, F1 + 2.4, F1 + 2.9, 32.0, 32.8)
    hb(U_, MT('metal'), 3.2, 3.8, F1 + 2.2, F1 + 2.8, 1.5, 2.2)
    for uu in (2.5, 4.4):
        hb(U_, MT('red') if uu < 3 else MT('blue'), uu - 0.2, uu + 0.2, F1 + 2.3, F1 + 2.7, 1.5, 1.8)
    hb(U_, MT('white'), 7.5, 9.0, F1 + 1.8, F1 + 3.6, 8.6, 9.4)
    hb(U_, MT('dark'), 7.5, 9.0, F1 + 1.8, F1 + 1.95, 7.4, 8.6)
    hb(U_, MT('metal'), 9.4, 9.8, F1 + 3.0, F1 + 4.0, 1.8, 2.2)
    hb(U_, MT('white'), 8.5, 11.5, F1 + 4.2, F1 + 7.6, 1.5, 1.62)
    hb(U_, MT('blue'), 8.7, 11.3, F1 + 4.4, F1 + 7.4, 1.62, 1.7)
    for (v0, v1, col) in ((3.0, 4.2, 'red'), (4.6, 5.8, 'blue')):
        hb(U_, MT(col), 13.1, 13.5, F1 + 4.2, F1 + 6.2, v0, v1)
    hb(U_, MT('metal'), 13.3, 13.5, F1 + 6.2, F1 + 6.35, 2.8, 6.0)
    # ---------------- master bedroom: quilt stripes, wall art, dresser drawers, slippers, basket
    for k, col in enumerate(('red', 'white', 'yellow', 'white', 'red')):
        hb(U_, MT(col), 16.2, 21.8, F1 + 2.7, F1 + 2.76, 34.5 + k * 1.2, 35.2 + k * 1.2)
    for k, (u0, u1, col) in enumerate(((17.0, 19.0, 'blue'), (19.6, 21.2, 'yellow'))):
        hb(U_, trm, u0, u1, F1 + 6.0, F1 + 8.6, 42.0, 42.2)
        hb(U_, MT(col), u0 + 0.15, u1 - 0.15, F1 + 6.15, F1 + 8.45, 41.92, 42.0)
    for k in range(3):
        hb(U_, MT('wood2'), 15.3, 20.7, F1 + 0.3 + k * 1.0, F1 + 1.1 + k * 1.0, 33.2, 33.28)
        hb(U_, MT('brass'), 17.7, 18.3, F1 + 0.55 + k * 1.0, F1 + 0.85 + k * 1.0, 33.28, 33.4)
    hb(U_, MT('red'), 19.0, 20.4, F1 + 3.6, F1 + 4.2, 31.4, 32.4)
    hb(U_, MT('teal'), 22.6, 23.6, F1, F1 + 0.3, 39.0, 40.2)
    hb(U_, MT('teal'), 22.6, 23.6, F1, F1 + 0.3, 40.5, 41.7) if False else None
    hb(U_, MT('orange'), 26.0, 27.4, F1, F1 + 1.8, 41.0, 42.3)
    # wardrobe: shoes on the floor and hangers
    for k, col in enumerate(('red', 'dark', 'blue')):
        hb(U_, MT(col), 31.4 + k * 0.4, 32.0 + k * 0.4, F1 + 0.3, F1 + 0.7, 40.6, 41.4)
    # ---------------- child room: bunk ladder, teddy, desk chair, books, ball, posters, whiteboard, toy-chest lid
    for v in (24.4, 25.6):
        hb(U_, wdc, 30.7, 31.0, F1, F1 + 4.6, v, v + 0.2)
    for k in range(5):
        hb(U_, wdc, 30.7, 31.0, F1 + 0.5 + k * 0.9, F1 + 0.7 + k * 0.9, 24.4, 25.8)
    hb(U_, MT('orange'), 32.0, 33.6, F1 + 2.0, F1 + 2.8, 20.0, 21.4)
    hb(U_, MT('orange'), 32.3, 33.3, F1 + 2.8, F1 + 3.6, 20.2, 21.2)
    hb(U_, MT('red'), 32.0, 34.2, F1 + 4.4, F1 + 4.6, 18.2, 25.8)
    hb(U_, MT('blue'), 25.4, 27.2, F1, F1 + 1.5, 19.9, 21.7)
    hb(U_, MT('blue'), 25.4, 27.2, F1 + 1.5, F1 + 3.2, 21.5, 21.7)
    for k, col in enumerate(('red', 'yellow', 'teal')):
        hb(U_, MT(col), 22.3 + k * 1.2, 23.3 + k * 1.2, F1 + 2.6, F1 + 3.2, 17.3, 18.5)
    ball('Furn_U', 'red', 25.0, 24.5, F1 + 0.9, 0.9)
    for k, (v0, v1, col) in enumerate(((25.0, 27.0, 'yellow'), (27.4, 29.0, 'pink'))):
        hb(U_, trm, 14.5, 14.62, F1 + 4.8, F1 + 7.8, v0, v1)
        hb(U_, MT(col), 14.62, 14.7, F1 + 5.0, F1 + 7.6, v0 + 0.15, v1 - 0.15)
    hb(U_, MT('trim'), 24.0, 31.0, F1 + 4.0, F1 + 7.0, 16.5, 16.62)
    hb(U_, MT('white'), 24.2, 30.8, F1 + 4.2, F1 + 6.8, 16.62, 16.7)
    hb(U_, MT('yellow'), 16.0, 19.0, F1 + 1.8, F1 + 1.95, 27.0, 29.0)
    for k, col in enumerate(('blue', 'red', 'yellow', 'teal', 'purple')):
        hb(U_, MT(col), 16.3 + k * 0.5, 16.7 + k * 0.5, F1 + 1.95, F1 + 2.5, 27.6, 28.4)
    # ---------------- father's lounge: trophy shelf, dartboard, bar cart, footstool, floor lamp
    hb(U_, w2c, 14.5, 14.9, F1 + 5.5, F1 + 6.0, 2.5, 8.5)
    for k, col in enumerate(('brass', 'metal', 'brass', 'metal')):
        hb(U_, MT(col), 14.9, 15.4, F1 + 6.0, F1 + 6.8 + (k % 2) * 0.4, 3.0 + k * 1.4, 3.6 + k * 1.4)
    hb(U_, MT('red'), 31.6, 33.4, F1 + 5.0, F1 + 6.8, 1.8, 1.95)
    hb(U_, MT('white'), 31.85, 33.15, F1 + 5.25, F1 + 6.55, 1.95, 2.0)
    hb(U_, MT('dark'), 32.2, 32.8, F1 + 5.6, F1 + 6.2, 2.0, 2.05)
    hb(U_, w2c, 32.6, 34.3, F1, F1 + 2.8, 2.2, 4.4)
    for k, col in enumerate(('red', 'blue', 'teal', 'yellow')):
        hb(U_, MT(col), 32.8 + k * 0.38, 33.1 + k * 0.38, F1 + 2.8, F1 + 3.8, 2.6, 2.9)
    hb(U_, MT('glass'), 33.9, 34.2, F1 + 2.8, F1 + 3.2, 3.5, 3.8)
    hb(U_, MT('orange'), 16.2, 18.0, F1, F1 + 1.4, 9.6, 11.2)
    hb(U_, MT('metal'), 15.0, 15.25, F1, F1 + 5.4, 3.0, 3.25)
    hb(U_, MT('lamp'), 14.6, 15.7, F1 + 5.4, F1 + 6.4, 2.6, 3.7)
    hb(U_, MT('red'), 19.0, 20.0, F1 + 2.8, F1 + 3.0, 3.0, 4.2)


def details():
    ext_details()
    int_details()



# ====================================================================================================
# HQ modelling library: real (non-block) geometry. Coordinates are plot space (x east, h up, z south);
# models are built in a local frame (lx right, h up, lz forward) and placed with tf_push / tf_pop.
# ====================================================================================================
import random as _random

_TF = []


def tf_push(x, z, y0=0.0, rot=0.0):
    if _TF:
        px, pz, py, pc, ps = _TF[-1]
        X = px + x * pc - z * ps
        Z = pz + x * ps + z * pc
        Y0 = py + y0
        a = math.atan2(ps, pc) + math.radians(rot)
    else:
        X, Z, Y0, a = x, z, y0, math.radians(rot)
    _TF.append((X, Z, Y0, math.cos(a), math.sin(a)))


def tf_pop():
    _TF.pop()


def _t(lx, h, lz):
    if not _TF:
        return (lx, h, lz)
    x, z, y0, c, s = _TF[-1]
    return (x + lx * c - lz * s, h + y0, z + lx * s + lz * c)


COVER = []       # low-cover proxies for NPC vision: (name, world x, floor y, world z, width, depth, height, yaw)


def cover(name, w, d, h, lx=0.0, lz=0.0):
    """Registers a vision-only proxy box for a low piece of furniture: footprint w x d centred at local (lx, lz),
    h above the local floor. Yaw is the plan rotation of the current transform (x' = x c - z s, z' = x s + z c)."""
    p = _t(lx, 0.0, lz)
    yaw = math.atan2(_TF[-1][4], _TF[-1][3]) if _TF else 0.0
    COVER.append((name, p[0], p[1], p[2], w, d, h, yaw))


def anchor(name, lx, h, lz):
    p = _t(lx, h, lz)
    if _TF:
        f = (-_TF[-1][4], _TF[-1][3])
    else:
        f = (0.0, 1.0)
    ANCH[name] = (p[0], p[1], p[2], f[0], f[1])


def emit(c, m, verts, faces, two_sided=False):
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    base = len(vs)
    for (lx, h, lz) in verts:
        px, ph, pz = _t(lx, h, lz)
        vs.append((px, -pz, ph))
    for f in faces:
        fs.append(tuple(base + i for i in f))
        if two_sided:
            fs.append(tuple(base + i for i in reversed(f)))


def _bm_out(bm):
    bm.verts.index_update()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


def rbox(c, m, cx, cz, y0, sx, sy, sz, r=0.1, seg=3):
    """rounded box centred on (cx, cz), base at y0 (local)."""
    r = max(0.001, min(r, 0.46 * min(sx, sy, sz)))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = cx + v.co.x * sx
        v.co.y = y0 + sy / 2 + v.co.y * sy
        v.co.z = cz + v.co.z * sz
    bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=r, offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES')
    v, f = _bm_out(bm)
    emit(c, m, v, f)


def lathe(c, m, prof, cx, cz, y0=0.0, seg=24, sx=1.0, sz=1.0, caps=True):
    """revolve profile [(radius, height), ...] about the vertical axis through (cx, cz)."""
    verts = []
    rings = []
    for (r, h) in prof:
        if r < 1e-6:
            verts.append((cx, y0 + h, cz))
            rings.append([len(verts) - 1])
        else:
            idx = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                verts.append((cx + r * sx * math.cos(a), y0 + h, cz + r * sz * math.sin(a)))
                idx.append(len(verts) - 1)
            rings.append(idx)
    faces = []
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(seg):
                faces.append((a[0], b[(i + 1) % seg], b[i]))
        elif len(b) == 1:
            for i in range(seg):
                faces.append((a[i], a[(i + 1) % seg], b[0]))
        else:
            for i in range(seg):
                faces.append((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    if caps:
        for ring, up in ((rings[0], False), (rings[-1], True)):
            if len(ring) > 1:
                faces.append(tuple(ring) if up else tuple(reversed(ring)))
    emit(c, m, verts, faces)


def cylinder(c, m, cx, cz, y0, h, r, seg=20, r2=None):
    lathe(c, m, [(r, 0.0), (r if r2 is None else r2, h)], cx, cz, y0, seg)


def sphere(c, m, cx, cz, cy, rx, ry=None, rz=None, seg=18, rings=10):
    ry = ry or rx
    rz = rz or rx
    prof = []
    for k in range(rings + 1):
        a = math.pi * k / rings
        prof.append((math.sin(a), cy - ry * math.cos(a)))
    lathe(c, m, prof, cx, cz, 0.0, seg, sx=rx, sz=rz, caps=False)


def tube(c, m, pts, r, seg=8, closed=False, caps=True, r_end=None):
    n = len(pts)
    P_ = [Vector(p) for p in pts]
    up = Vector((0, 1, 0))
    rings = []
    verts = []
    for i in range(n):
        if closed:
            t = (P_[(i + 1) % n] - P_[(i - 1) % n]).normalized()
        else:
            t = (P_[min(i + 1, n - 1)] - P_[max(i - 1, 0)]).normalized()
        nn = t.cross(up)
        if nn.length < 1e-4:
            nn = t.cross(Vector((1, 0, 0)))
        nn.normalize()
        bb = t.cross(nn).normalized()
        rr = r if r_end is None else r + (r_end - r) * i / max(1, n - 1)
        idx = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            p = P_[i] + (nn * math.cos(a) + bb * math.sin(a)) * rr
            verts.append((p.x, p.y, p.z))
            idx.append(len(verts) - 1)
        rings.append(idx)
    faces = []
    last = n if closed else n - 1
    for i in range(last):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            faces.append((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if caps and not closed:
        faces.append(tuple(reversed(rings[0])))
        faces.append(tuple(rings[-1]))
    emit(c, m, verts, faces)


def torus(c, m, cx, cz, cy, R, r, plane='xz', seg=28, tseg=8):
    pts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        if plane == 'xz':
            pts.append((cx + R * math.cos(a), cy, cz + R * math.sin(a)))
        elif plane == 'xy':
            pts.append((cx + R * math.cos(a), cy + R * math.sin(a), cz))
        else:
            pts.append((cx, cy + R * math.sin(a), cz + R * math.cos(a)))
    tube(c, m, pts, r, tseg, closed=True)


def leaf(c, m, bx, bh, bz, ang, length, width, lift=0.6, droop=0.9, n=6):
    """curved pointed leaf card (double sided) growing from (bx, bh, bz) toward angle ang (radians, plan view)"""
    dx, dz = math.cos(ang), math.sin(ang)
    verts = []
    for i in range(n + 1):
        u = i / n
        w = width * math.sin(math.pi * (u ** 0.75)) * 0.5
        cxp = bx + dx * length * u
        czp = bz + dz * length * u
        ch = bh + length * (lift * u - droop * u * u * 0.7)
        for sgn in (-1, 1):
            verts.append((cxp - dz * w * sgn, ch, czp + dx * w * sgn))
    faces = []
    for i in range(n):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    emit(c, m, verts, faces, two_sided=True)


def sheet(c, m, x0, x1, y0, y1, z, folds=6, amp=0.18, nx=40, axis='x'):
    """hanging curtain panel with sine folds; axis 'x': panel spans x, z is depth; 'z': spans z, x is depth"""
    verts = []
    for i in range(nx + 1):
        u = i / nx
        for j in (0, 1):
            h = y0 + (y1 - y0) * j
            off = amp * math.sin(2 * math.pi * folds * u) * (1 - 0.35 * j)
            if axis == 'x':
                verts.append((x0 + (x1 - x0) * u, h, z + off))
            else:
                verts.append((z + off, h, x0 + (x1 - x0) * u))
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(nx)]
    emit(c, m, verts, faces, two_sided=True)


def book(c, m, cx, cz, y0, w, h, d, r=0.04):
    rbox(c, m, cx, cz, y0, w, h, d, r=r, seg=2)


def ring_pts(cx, cy, cz, R, n, plane='xz', a0=0.0):
    out = []
    for i in range(n):
        a = a0 + 2 * math.pi * i / n
        out.append((cx + R * math.cos(a), cy, cz + R * math.sin(a)) if plane == 'xz' else (cx + R * math.cos(a), cy + R * math.sin(a), cz))
    return out


# ---------------------------------------------------------------- finishing: smooth shading with sharp edges by angle
def finish_mesh(me, angle_deg=38.0):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    lim = math.radians(angle_deg)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < lim
        else:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------- generic furniture models (local frame: +lz is the front)
def P_(u, v, fl, rot=0.0):
    X, Z = pos_(u, v, fl)
    tf_push(X, Z, FH(fl), rot)


def PK(u, v, fl, rot=0.0):
    """anchor that follows the architecture warp exactly (stairs, rails)"""
    tf_push(FX(HX + u), FZ(HZ + v), FH(fl), rot)


def sofa(c, w=8.6, d=3.5, col='sofa', col2='sofa2', pillows=('yellow', 'red', 'cream')):
    cover('sofa', w, d, 3.1)
    wd, dk = MT('wood2'), MT('dark')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.28, 0), (0.2, 0.25), (0.26, 0.5)], sx * (w / 2 - 0.5), sz * (d / 2 - 0.5), 0, 12)
    rbox(c, MT(col2), 0, 0, 0.5, w - 0.2, 0.75, d - 0.2, 0.18)
    arm = 1.0
    sw = (w - 2 * arm - 0.1) / 3.0
    for k in range(3):
        x = -w / 2 + arm + 0.05 + sw * (k + 0.5)
        rbox(c, MT(col), x, 0.35, 1.1, sw - 0.06, 1.0, d - 1.0, 0.34, 3)
        rbox(c, MT(col), x, -d / 2 + 0.95, 2.0, sw - 0.06, 2.0, 1.0, 0.4, 3)
    rbox(c, MT(col2), 0, -d / 2 + 0.35, 0.5, w, 3.1, 0.75, 0.3, 3)
    for sx in (-1, 1):
        rbox(c, MT(col2), sx * (w / 2 - arm / 2), 0, 0.5, arm, 2.25, d, 0.42, 3)
        cylinder(c, MT(col2), 0, 0, 0, 0.1, 0.1)
    for k, pc in enumerate(pillows):
        tf_push(-2.3 + k * 2.15, 0.15, 1.95, (-25, 12, -8)[k % 3])
        rbox(c, MT(pc), 0, 0, 0, 1.55, 1.55, 0.65, 0.5, 3)
        tf_pop()


def armchair(c, col='orange', col2='orange', w=3.9, d=3.7):
    cover('armchair', w, d, 3.2)
    wd = MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.26, 0), (0.18, 0.25), (0.24, 0.55)], sx * (w / 2 - 0.45), sz * (d / 2 - 0.45), 0, 12)
    rbox(c, MT(col2), 0, 0, 0.55, w - 0.2, 0.7, d - 0.2, 0.18)
    rbox(c, MT(col), 0, 0.3, 1.2, w - 1.7, 0.95, d - 1.0, 0.36, 3)
    rbox(c, MT(col), 0, -d / 2 + 0.7, 1.9, w - 1.2, 2.0, 1.1, 0.45, 3)
    rbox(c, MT(col2), 0, -d / 2 + 0.35, 0.55, w, 3.2, 0.75, 0.3, 3)
    for sx in (-1, 1):
        rbox(c, MT(col2), sx * (w / 2 - 0.42), 0.1, 0.55, 0.85, 1.9, d - 0.2, 0.38, 3)


def coffee_table(c, w=5.6, d=2.8, h=1.5):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.28, w, 0.28, d, 0.12)
    rbox(c, wd, 0, 0, 0.45, w - 0.9, 0.14, d - 0.7, 0.05, 2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.2, 0), (0.15, 0.4), (0.12, 0.8), (0.16, h - 0.28)], sx * (w / 2 - 0.45), sz * (d / 2 - 0.4), 0, 10)


def side_table(c, r=0.95, h=2.4):
    w2 = MT('wood2')
    lathe(c, w2, [(r, h - 0.18), (r, h), (0, h)], 0, 0, 0, 24)
    lathe(c, w2, [(0.1, h - 0.18), (0.18, h - 0.4), (0.1, h - 0.9), (0.28, h - 1.4), (0.14, 0.5), (0.5, 0.2), (0.7, 0.0)], 0, 0, 0, 16)


def table_lamp(c, h=2.0, shade=1.7, base='teal'):
    lathe(c, MT(base), [(0.0, 0), (0.55, 0.0), (0.7, 0.35), (0.62, 0.9), (0.3, 1.25), (0.16, 1.5), (0.1, 1.7)], 0, 0, 0, 20, caps=True)
    lathe(c, MT('lampshade'), [(0.62, 1.55), (shade * 0.5, 2.9)], 0, 0, 0, 24, caps=False)
    lathe(c, MT('lampshade'), [(shade * 0.5, 2.9), (0.62, 1.55)], 0, 0, 0, 24, caps=False)


def floor_lamp(c, h=5.6):
    lathe(c, MT('metal'), [(0.0, 0), (0.7, 0.0), (0.7, 0.12), (0.0, 0.14)], 0, 0, 0, 20)
    cylinder(c, MT('metal'), 0, 0, 0.1, h - 1.6, 0.09, 10)
    lathe(c, MT('lampshade'), [(0.9, h - 1.8), (0.55, h - 0.3)], 0, 0, 0, 24, caps=False)
    lathe(c, MT('lampshade'), [(0.55, h - 0.3), (0.9, h - 1.8)], 0, 0, 0, 24, caps=False)
    sphere(c, MT('lamp'), 0, 0, h - 1.1, 0.28, 0.35, 0.28, 12, 8)


def potted_plant(c, s=1.0, pot='terra', big=False, leaves=11, lcol=('leaf', 'leaf2')):
    lathe(c, MT(pot), [(0.0, 0), (0.55 * s, 0.0), (0.72 * s, 0.1 * s), (0.9 * s, 1.35 * s), (1.0 * s, 1.45 * s), (0.9 * s, 1.5 * s)], 0, 0, 0, 20)
    lathe(c, MT('soil'), [(0.82 * s, 1.35 * s), (0.0, 1.4 * s)], 0, 0, 0, 18)
    rnd = _random.Random(int(s * 100) + leaves)
    for k in range(leaves):
        a = 2 * math.pi * k / leaves + rnd.uniform(-0.2, 0.2)
        L = (1.55 if big else 1.15) * s * rnd.uniform(0.8, 1.15)
        leaf(c, MT(lcol[k % 2]), 0.15 * math.cos(a), 1.4 * s, 0.15 * math.sin(a), a, L, 0.8 * s * (1.3 if big else 1.0), 0.55 + 0.25 * rnd.random(), 0.9)


def mug(c, col='white', s=1.0):
    lathe(c, MT(col), [(0.0, 0), (0.28 * s, 0.0), (0.3 * s, 0.05 * s), (0.32 * s, 0.6 * s), (0.3 * s, 0.62 * s), (0.27 * s, 0.6 * s), (0.27 * s, 0.1 * s), (0.0, 0.08 * s)], 0, 0, 0, 16)
    tube(c, MT(col), [(0.3 * s, 0.5 * s, 0.0), (0.52 * s, 0.5 * s, 0.0), (0.58 * s, 0.35 * s, 0.0), (0.5 * s, 0.18 * s, 0.0), (0.3 * s, 0.14 * s, 0.0)], 0.045 * s, 6)


def vase_flowers(c, vcol='blue', n=7, h=1.3, fcols=('red', 'yellow', 'pink', 'orange')):
    lathe(c, MT(vcol), [(0.0, 0), (0.35, 0.0), (0.5, 0.25), (0.45, 0.7), (0.22, 1.05), (0.28, h), (0.2, h - 0.05), (0.18, h - 0.1)], 0, 0, 0, 16)
    rnd = _random.Random(n)
    for k in range(n):
        a = 2 * math.pi * k / n
        hx_, hz_ = 0.42 * math.cos(a) * rnd.uniform(0.5, 1.0), 0.42 * math.sin(a) * rnd.uniform(0.5, 1.0)
        top = h + 0.8 + rnd.uniform(0.0, 0.7)
        tube(c, MT('leaf'), [(0, h - 0.1, 0), (hx_ * 0.5, h + 0.4, hz_ * 0.5), (hx_, top, hz_)], 0.04, 5)
        sphere(c, MT(fcols[k % len(fcols)]), hx_, hz_, top + 0.12, 0.23, 0.18, 0.23, 10, 6)
        sphere(c, MT('yellow'), hx_, hz_, top + 0.2, 0.09, 0.07, 0.09, 8, 5)


def plate(c, col='white', r=0.62):
    lathe(c, MT(col), [(0.0, 0.0), (r * 0.55, 0.0), (r, 0.12), (r * 1.0, 0.16), (r * 0.62, 0.05), (0.0, 0.04)], 0, 0, 0, 22)


def glass_cup(c, h=0.75, r=0.2):
    lathe(c, MT('glass'), [(0.0, 0.0), (r * 0.8, 0.0), (r, 0.1), (r * 1.1, h), (r * 1.0, h), (r * 0.7, 0.14), (0.0, 0.1)], 0, 0, 0, 14)


def picture(c, w, h, cover='blue', frame='trim', kind='art'):
    """wall picture facing +lz"""
    rbox(c, MT(frame), 0, 0, -h / 2, w, h, 0.16, 0.05, 2)
    rbox(c, MT('white'), 0, 0.06, -h / 2 + 0.18, w - 0.36, h - 0.36, 0.06, 0.02, 1)
    if kind == 'art':
        rbox(c, MT(cover), 0, 0.1, -h / 2 + 0.32, w - 0.7, h - 0.64, 0.05, 0.02, 1)
        sphere(c, MT('yellow'), -w * 0.18, 0.13, h * 0.12, w * 0.12, w * 0.12, 0.03, 10, 6)
        rbox(c, MT('white'), w * 0.1, 0.13, -h * 0.25, w * 0.35, h * 0.12, 0.03, 0.02, 1)
    elif kind == 'family':
        rbox(c, MT('orange'), 0, 0.1, -h / 2 + 0.32, w - 0.7, h - 0.64, 0.05, 0.02, 1)
        for k, (x, s) in enumerate(((-w * 0.2, 1.0), (w * 0.0, 0.8), (w * 0.2, 1.0))):
            sphere(c, MT('skin'), x, 0.14, h * 0.08 + (1 - s) * 0.3, 0.2 * s, 0.22 * s, 0.05, 10, 6)
            rbox(c, MT(('teal', 'pink', 'blue')[k]), x, 0.13, -h * 0.28, 0.4 * s, 0.55 * s, 0.05, 0.05, 2)


def rug(c, w, d, base='red', border='teal', stripe='yellow', fringe=True):
    w, d = w * 1.4, d * 1.4
    rbox(c, MT(border), 0, 0, 0, w, 0.08, d, 0.03, 1)
    rbox(c, MT(base), 0, 0, 0.08, w - 0.9, 0.05, d - 0.9, 0.02, 1)
    sphere(c, MT(stripe), 0, 0, 0.15, min(w, d) * 0.2, 0.03, min(w, d) * 0.2, 20, 4)
    if fringe:
        for sx in (-1, 1):
            for k in range(int(d / 0.28)):
                rbox(c, MT('cream'), sx * (w / 2 + 0.2), -d / 2 + 0.2 + k * 0.28, 0.0, 0.4, 0.04, 0.1, 0.015, 1)


def curtain_pair(c, ac, wspan, y_top, drop, z, axis='x', col='coral', open_=True):
    """two curtains + rod + finials around a window centred at ac"""
    g = MT(col)
    y_top = FH(y_top)
    if axis == 'x':
        ac, z, wspan = FX(ac), FZ(z), wspan * KSX
    else:
        ac, z, wspan = FZ(ac), FX(z), wspan * KSZ
    x0, x1 = ac - wspan / 2, ac + wspan / 2
    if axis == 'x':
        tube(c, MT('brass'), [(x0 - 0.5, y_top, z), (x1 + 0.5, y_top, z)], 0.08, 8)
        for xx in (x0 - 0.55, x1 + 0.55):
            sphere(c, MT('brass'), xx, z, y_top, 0.2, 0.2, 0.2, 10, 6)
        sheet(c, g, x0 - 0.3, x0 + 1.5, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='x')
        sheet(c, g, x1 - 1.5, x1 + 0.3, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='x')
    else:
        tube(c, MT('brass'), [(z, y_top, x0 - 0.5), (z, y_top, x1 + 0.5)], 0.08, 8)
        for zz in (x0 - 0.55, x1 + 0.55):
            sphere(c, MT('brass'), z, zz, y_top, 0.2, 0.2, 0.2, 10, 6)
        sheet(c, g, x0 - 0.3, x0 + 1.5, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='z')
        sheet(c, g, x1 - 1.5, x1 + 0.3, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='z')


def tv_unit(c, w=7.4, d=1.9, h=2.2):
    wd = MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, MT('wood'), [(0.2, 0), (0.14, 0.3), (0.2, 0.6)], sx * (w / 2 - 0.4), sz * (d / 2 - 0.35), 0, 10)
    rbox(c, wd, 0, 0, 0.6, w, h - 0.6, d, 0.12, 2)
    for sx in (-1, 1):
        rbox(c, MT('wood'), sx * w / 4, d / 2 - 0.02, 0.85, w / 2 - 0.35, h - 1.15, 0.07, 0.04, 1)
        sphere(c, MT('brass'), sx * (w / 4 - sx * 0.8), d / 2 + 0.06, h - 0.65, 0.09, 0.09, 0.09, 8, 5)
    rbox(c, MT('black'), 0, 0, h, 0.35, 0.45, 0.35, 0.05, 1)
    rbox(c, MT('black'), 0, 0, h + 0.38, 0.9, 0.12, 0.45, 0.04, 1)
    rbox(c, MT('black'), 0, 0, h + 0.5, 5.4, 3.0, 0.22, 0.08, 2)
    rbox(c, MT('screen'), 0, 0.12, h + 0.6, 5.1, 2.8, 0.05, 0.03, 1)
    rbox(c, MT('black'), 0, d / 2 - 0.5, h, 3.0, 0.22, 0.4, 0.05, 1)


def bookshelf(c, w=6.0, h=6.8, d=1.5, rows=5, seed=1, deco=True):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, wd, -w / 2 + 0.15, 0, 0, 0.3, h, d, 0.05, 2)
    rbox(c, wd, w / 2 - 0.15, 0, 0, 0.3, h, d, 0.05, 2)
    rbox(c, w2, 0, -d / 2 + 0.06, 0, w - 0.2, h, 0.12, 0.02, 1)
    gap = (h - 0.4) / rows
    rnd = _random.Random(seed)
    cols = ['red', 'blue', 'yellow', 'teal', 'purple', 'orange', 'white', 'leaf', 'pink', 'navy']
    for k in range(rows + 1):
        rbox(c, wd, 0, 0, k * gap, w - 0.2, 0.28, d, 0.05, 2)
        if k == rows:
            break
        x = -w / 2 + 0.45
        base = k * gap + 0.28
        while x < w / 2 - 0.9:
            bw = rnd.uniform(0.2, 0.45)
            bh = gap - 0.5 - rnd.uniform(0.0, 0.7)
            tilt = rnd.random() < 0.06
            if deco and rnd.random() < 0.09 and bw > 0.35:
                sphere(c, MT(rnd.choice(cols)), x + 0.3, 0.0, base + 0.35, 0.3, 0.35, 0.3, 10, 6)
                x += 0.8
                continue
            book(c, MT(rnd.choice(cols)), x + bw / 2, -0.05, base, bw, bh, d - 0.45)
            x += bw + 0.02
            if tilt:
                x += 0.5
    rbox(c, wd, 0, 0, h, w, 0.18, d + 0.12, 0.05, 2)


FGc, FUc = 'Furn_G', 'Furn_U'


def dining_chair(c, col='red', seat='cream'):
    wd, w2 = MT('wood'), MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.16, 0), (0.1, 0.5), (0.14, 1.0), (0.1, 1.7)], sx * 0.7, sz * 0.7, 0, 10)
    rbox(c, w2, 0, 0, 1.55, 1.8, 0.18, 1.8, 0.06, 2)
    rbox(c, MT(seat), 0, 0.02, 1.7, 1.6, 0.34, 1.6, 0.14, 3)
    for sx in (-1, 1):
        lathe(c, wd, [(0.11, 1.6), (0.09, 2.6), (0.13, 3.9)], sx * 0.7, -0.78, 0, 10)
    for k in range(3):
        rbox(c, MT(col), 0, -0.8, 2.35 + k * 0.45, 1.35, 0.3, 0.14, 0.05, 2)
    rbox(c, wd, 0, -0.78, 3.8, 1.7, 0.28, 0.2, 0.08, 2)


def dining_table(c, w=10.6, d=4.8, h=2.9):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.34, w, 0.34, d, 0.14, 3)
    rbox(c, wd, 0, 0, h - 0.8, w - 1.0, 0.46, d - 1.0, 0.08, 2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.26, 0), (0.2, 0.3), (0.34, 0.6), (0.2, 1.0), (0.26, 1.5), (0.2, 2.0), (0.28, h - 0.8)], sx * (w / 2 - 0.7), sz * (d / 2 - 0.6), 0, 12)


def place_setting(c, col='teal'):
    plate(c, 'white', 0.62)
    tf_push(0.0, 0.0, 0.16, 0)
    lathe(c, MT(col), [(0.0, 0.0), (0.3, 0.0), (0.46, 0.04), (0.0, 0.02)], 0, 0, 0, 16)
    tf_pop()
    glass_cup(c, 0.75, 0.2) if False else None
    tf_push(0.95, -0.7, 0, 0)
    glass_cup(c, 0.75, 0.2)
    tf_pop()
    rbox(c, MT('metal'), -0.95, 0.0, 0.0, 0.1, 0.05, 0.9, 0.02, 1)
    rbox(c, MT('metal'), 0.95, 0.15, 0.0, 0.1, 0.05, 0.9, 0.02, 1)
    rbox(c, MT('red'), -0.2, 0.9, 0.0, 0.8, 0.07, 0.5, 0.03, 1)


def candle(c, col='white'):
    lathe(c, MT('brass'), [(0.0, 0), (0.28, 0.0), (0.2, 0.1), (0.07, 0.3), (0.1, 0.55), (0.18, 0.62), (0.0, 0.62)], 0, 0, 0, 12)
    cylinder(c, MT(col), 0, 0, 0.55, 0.9, 0.07, 10)
    sphere(c, MT('lamp'), 0, 0, 1.55, 0.07, 0.14, 0.07, 8, 6)


def fruit_bowl(c):
    lathe(c, MT('wood2'), [(0.0, 0.0), (0.4, 0.0), (0.9, 0.35), (1.0, 0.45), (0.92, 0.45), (0.8, 0.3), (0.0, 0.12)], 0, 0, 0, 18)
    rnd = _random.Random(7)
    for k in range(6):
        a = 2 * math.pi * k / 6
        r = 0.36 if k else 0.0
        sphere(c, MT(['red', 'leaf2', 'orange', 'red', 'yellow', 'leaf2'][k]), r * math.cos(a), r * math.sin(a), 0.42 + (0.18 if k == 0 else 0.0), 0.3, 0.28, 0.3, 10, 7)


def chandelier(c, n=6, col='lampshade'):
    cylinder(c, MT('brass'), 0, 0, 0.0, 0.8, 0.05, 8)
    lathe(c, MT('brass'), [(0.0, -0.8), (0.4, -0.8), (0.3, -1.2), (0.12, -1.6), (0.3, -1.9), (0.0, -2.1)], 0, 0, 0, 14)
    for k in range(n):
        a = 2 * math.pi * k / n
        ex, ez = 1.8 * math.cos(a), 1.8 * math.sin(a)
        tube(c, MT('brass'), [(0, -1.4, 0), (ex * 0.5, -1.7, ez * 0.5), (ex, -1.6, ez), (ex, -1.45, ez)], 0.06, 6)
        lathe(c, MT(col), [(0.2, -1.45), (0.36, -0.95), (0.0, -0.95)], ex, ez, 0, 12, caps=False)
        sphere(c, MT('lamp'), ex, ez, -1.3, 0.16, 0.2, 0.16, 8, 6)


def sideboard(c, w=7.0, d=1.8, h=2.8):
    wd, w2 = MT('wood'), MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.18, 0), (0.12, 0.5), (0.18, 0.9)], sx * (w / 2 - 0.4), sz * (d / 2 - 0.35), 0, 10)
    rbox(c, w2, 0, 0, 0.9, w, h - 0.9, d, 0.12, 3)
    rbox(c, wd, 0, 0, h, w + 0.2, 0.14, d + 0.12, 0.05, 2)
    for k in range(3):
        x = -w / 3 + k * w / 3
        rbox(c, wd, x, d / 2 - 0.02, 1.15, w / 3 - 0.25, h - 1.45, 0.08, 0.05, 2)
        rbox(c, w2, x, d / 2 + 0.02, 1.4, w / 3 - 0.8, h - 1.95, 0.05, 0.03, 1)
        sphere(c, MT('brass'), x + (0.3 if k % 2 else -0.3), d / 2 + 0.12, h * 0.55, 0.11, 0.11, 0.11, 8, 6)


def console_table(c, w=4.4, d=1.5, h=3.0):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.24, w, 0.24, d, 0.09, 3)
    rbox(c, wd, 0, 0, h - 0.84, w - 0.5, 0.6, d - 0.3, 0.06, 2)
    rbox(c, MT('wood'), 0, d / 2 - 0.2, h - 0.74, w - 1.2, 0.44, 0.06, 0.03, 1)
    sphere(c, MT('brass'), 0, d / 2 - 0.14, h - 0.52, 0.1, 0.1, 0.1, 8, 6)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.18, 0), (0.12, 0.5), (0.2, 1.0), (0.12, 1.6), (0.15, h - 0.84)], sx * (w / 2 - 0.35), sz * (d / 2 - 0.3), 0, 10)


def mirror_round(c, r=1.7):
    torus(c, MT('brass'), 0, 0, 0, r, 0.14, plane='xy', seg=36, tseg=8)
    lathe(c, MT('mirror'), [(0.0, 0.0), (r, 0.0)], 0, 0, 0, 36, caps=False) if False else None
    sphere(c, MT('mirror'), 0, 0, 0, r - 0.05, r - 0.05, 0.06, 36, 4)


def coat_on_hook(c, col):
    tube(c, MT('metal'), [(0, 0, 0), (0, 0.15, -0.05), (0, 0.3, 0.0)], 0.03, 5)
    rbox(c, MT(col), 0, 0.05, -3.0, 1.5, 3.1, 0.55, 0.22, 3)
    rbox(c, MT(col), -0.9, 0.05, -2.6, 0.38, 2.3, 0.45, 0.16, 2)
    rbox(c, MT(col), 0.9, 0.05, -2.6, 0.38, 2.3, 0.45, 0.16, 2)


def shoe(c, col='wood'):
    rbox(c, MT('dark'), 0, 0, 0, 0.55, 0.14, 1.4, 0.05, 2)
    rbox(c, MT(col), 0, -0.05, 0.12, 0.5, 0.42, 1.0, 0.18, 3)
    rbox(c, MT(col), 0, 0.28, 0.12, 0.5, 0.3, 0.55, 0.14, 3)


def umbrella_stand(c):
    lathe(c, MT('blue'), [(0.0, 0), (0.55, 0.0), (0.65, 0.2), (0.7, 2.0), (0.62, 2.0), (0.0, 0.1)], 0, 0, 0, 18)
    for k, col in enumerate(('red', 'yellow')):
        tube(c, MT('dark'), [(0.15 * (k * 2 - 1), 1.6, 0.0), (0.2 * (k * 2 - 1), 3.2, 0.1), (0.25 * (k * 2 - 1), 4.2, 0.1)], 0.05, 6)
        lathe(c, MT(col), [(0.0, 4.2), (0.1, 3.9)], 0.25 * (k * 2 - 1), 0.1, 0, 10, caps=False)


def newel(c, h=4.3):
    lathe(c, MT('wood'), [(0.5, 0), (0.5, 0.35), (0.3, 0.5), (0.34, 1.8), (0.26, 2.0), (0.34, 2.3), (0.4, 3.3), (0.5, 3.6), (0.5, h - 0.1), (0.38, h)], 0, 0, 0, 16)
    sphere(c, MT('brass'), 0, 0, h + 0.18, 0.28, 0.28, 0.28, 12, 8)


def baluster(c, h=3.0):
    lathe(c, MT('trim'), [(0.12, 0), (0.12, 0.3), (0.2, 0.55), (0.1, 0.9), (0.16, 1.4), (0.09, 1.9), (0.12, h)], 0, 0, 0, 10)


def hq_hall_stairs():
    # console + mirror + lamp + vase on the hall's east wall
    P_(12.65, 26.0, F0, 90)
    console_table(FGc)
    tf_push(-0.9, 0.0, 3.0, 0)
    table_lamp(FGc, base='teal')
    tf_pop()
    tf_push(1.2, 0.1, 3.0, 0)
    vase_flowers(FGc, 'blue', 6, 1.0)
    tf_pop()
    tf_pop()
    P_(13.35, 26.0, F0 + 7.9, 90)
    mirror_round(FGc, 1.6)
    tf_pop()
    # family pictures
    for k, (v, w_, h_, kind, col) in enumerate(((29.2, 2.6, 3.2, 'family', 'orange'),)):
        P_(13.4, v, F0 + 6.4, 90)
        picture(FGc, w_, h_, col, 'trim', kind)
        tf_pop()
    # coat rack with coats and hat shelf
    P_(13.3, 39.6, F0 + 6.8, 90)
    rbox(FGc, MT('wood2'), 0, 0, -0.5, 4.4, 1.2, 0.3, 0.1, 2)
    for k in range(4):
        x = -1.5 + k * 1.0
        sphere(FGc, MT('brass'), x, 0.28, 0.0, 0.14, 0.14, 0.14, 8, 6)
        tf_push(x, 0.3, 0.0, 0)
        coat_on_hook(FGc, ('red', 'blue', 'yellow', 'teal')[k])
        tf_pop()
    tf_pop()
    # shoe rack and shoes, umbrella stand, door mat
    P_(11.9, 36.9, F0, 0)
    rbox(FGc, MT('wood2'), 0, 0, 0.0, 2.4, 0.18, 1.5, 0.05, 2)
    rbox(FGc, MT('wood2'), 0, 0, 0.8, 2.4, 0.18, 1.5, 0.05, 2)
    for k in range(3):
        tf_push(-0.8 + k * 0.8, 0.0, 0.18, 8 * (k - 1))
        shoe(FGc, ('wood', 'dark', 'red')[k])
        tf_pop()
        tf_push(-0.6 + k * 0.7, 0.0, 0.98, -6 * (k - 1))
        shoe(FGc, ('blue', 'wood', 'dark')[k])
        tf_pop()
    tf_pop()
    P_(12.3, 40.9, F0, 0)
    umbrella_stand(FGc)
    tf_pop()
    P_(9.5, 40.6, F0, 0)
    rbox(FGc, MT('red'), 0, 0, 0.0, 4.2, 0.12, 2.2, 0.05, 2)
    rbox(FGc, MT('cream'), 0, 0, 0.12, 3.5, 0.04, 1.6, 0.02, 1)
    tf_pop()
    # stair runner, newel posts, turned balusters, round hand rail (ground floor side u=6)
    rise, run = 11.0 / 15, 16.0 / 15
    for i in range(1, 16):
        v1 = 42.5 - run * (i - 1)
        v0 = 42.5 - run * i
        PK(3.75, (v0 + v1) / 2, F0 + rise * i, 0)
        rbox(FGc, MT('red'), 0, 0, 0.0, 2.9 * KSX, 0.06, run * KSZ - 0.1, 0.02, 1)
        rbox(FGc, MT('cream'), 0, 0, 0.06, 2.9 * KSX, 0.02, 0.12, 0.01, 1)
        tf_pop()
    PK(6.0, 41.6, F0, 0)
    newel(FGc)
    tf_pop()
    PK(6.0, 26.9, F1, 0)
    newel(FUc)
    tf_pop()
    def yf(v):
        return F0 + rise * (42.5 - v) / run
    for k in range(0, 14):
        v = 41.0 - k * run
        PK(6.0, v, yf(v), 0)
        baluster(FGc)
        tf_pop()
    tube(FGc, MT('wood'), [(FX(HX + 6.0), FH(yf(42.0)) + 3.1, FZ(HZ + 42.0)), (FX(HX + 6.0), FH(yf(27.0)) + 3.1, FZ(HZ + 27.0))], 0.2, 10)
    # upper rail turned balusters
    for v in [27.2 + 0.85 * i for i in range(18)]:
        PK(6.0, v, F1, 0)
        baluster(FUc)
        tf_pop()
    tube(FUc, MT('wood'), [(FX(HX + 6.0), FH(F1) + 3.1, FZ(HZ + 26.8)), (FX(HX + 6.0), FH(F1) + 3.1, FZ(HZ + 42.3))], 0.2, 10)


def hq_living():
    G_(24.0, 33.4, F0)
    P_(24.0, 33.4, F0, 0)
    rug(FGc, 14.0, 14.5, 'coral', 'teal', 'cream')
    tf_pop()
    P_(30.0, 26.5, F0, 0)
    sofa(FGc, 8.0, 3.5, 'sofa', 'sofa2')
    tf_pop()
    P_(30.0, 31.4, F0, 0)
    coffee_table(FGc)
    tf_push(-1.4, 0.0, 1.5, 12)
    rbox(FGc, MT('yellow'), 0, 0, 0.0, 1.5, 0.05, 1.0, 0.02, 1)
    rbox(FGc, MT('blue'), 0.1, 0.1, 0.05, 1.4, 0.05, 0.95, 0.02, 1)
    tf_pop()
    tf_push(1.0, 0.2, 1.5, 0)
    mug(FGc, 'white')
    tf_pop()
    tf_push(-0.2, -0.1, 1.5, 0)
    vase_flowers(FGc, 'teal', 5, 0.9)
    tf_pop()
    tf_pop()
    P_(19.6, 38.0, F0, 225)
    armchair(FGc, 'orange', 'orange')
    tf_push(0.9, 0.35, 1.9, -20)
    rbox(FGc, MT('teal'), 0, 0, 0.0, 1.4, 1.4, 0.55, 0.45, 3)
    tf_pop()
    tf_pop()
    P_(24.6, 27.2, F0, 0)
    side_table(FGc)
    tf_push(0.0, 0.0, 2.4, 0)
    table_lamp(FGc, base='teal')
    tf_pop()
    tf_pop()
    G_end()
    P_(15.7, 28.0, F0, -90)
    tv_unit(FGc)
    tf_pop()
    P_(15.4, 23.5, F0, 0)
    floor_lamp(FGc)
    tf_pop()
    P_(16.6, 35.2, F0, 0)
    potted_plant(FGc, 1.0, 'terra', True, 14)
    tf_pop()
    P_(33.3, 38.9, F0, 90)
    bookshelf(FGc, 4.8, 7.0, 1.5, 5, 3)
    tf_pop()
    for k, (u, w_, h_, kind, col) in enumerate(((29.6, 2.6, 3.2, 'art', 'blue'), (32.6, 2.4, 2.6, 'art', 'orange'))):
        P_(u, 22.7, F0 + 6.6, 0)
        picture(FGc, w_, h_, col, 'trim', kind)
        tf_pop()
    # curtains: south windows and east window
    for ac in (HX + 20, HX + 30):
        curtain_pair(FGc, ac, 6.0, F0 + 8.3, 5.8, HZ + 41.7, 'x', 'coral')
    curtain_pair(FGc, HZ + 33, 6.0, F0 + 8.3, 5.8, HX + 33.65, 'z', 'coral')


def hq_dining():
    G_(24.4, 11.0, F0)
    P_(21.8, 11.4, F0, 0)
    rug(FGc, 10.6, 8.4, 'cream', 'red', 'yellow', fringe=True)
    tf_pop()
    P_(22.0, 10.4, F0, 0)
    dining_table(FGc)
    for k in range(3):
        x = -2.6 + k * 2.6
        for (z, rot_) in ((-1.55, 180), (1.55, 0)):
            tf_push(x, z, 2.9, rot_)
            place_setting(FGc, ('teal', 'red', 'blue')[k])
            tf_pop()
    for sx in (-1, 1):
        tf_push(sx * 4.3, 0.0, 2.9, 90 * sx)
        place_setting(FGc, 'yellow')
        tf_pop()
    rbox(FGc, MT('yellow'), 0, 0, 2.9, 8.6, 0.04, 1.1, 0.02, 1)
    tf_push(-0.8, 0.0, 2.9, 0)
    vase_flowers(FGc, 'blue', 9, 1.3)
    tf_pop()
    for sx in (-2.7, 2.7):
        tf_push(sx, 0.35, 2.9, 0)
        candle(FGc)
        tf_pop()
    tf_pop()
    for k in range(3):
        u = 22.0 - 2.6 + k * 2.6
        P_(u, 7.2, F0, 0)
        dining_chair(FGc, 'red', 'cream')
        tf_pop()
        P_(u, 13.6, F0, 180)
        dining_chair(FGc, 'red', 'cream')
        tf_pop()
    P_(16.9, 10.4, F0, -90)
    dining_chair(FGc, 'red', 'cream')
    tf_pop()
    P_(27.1, 10.4, F0, 90)
    dining_chair(FGc, 'red', 'cream')
    tf_pop()
    P_(22.0, 10.4, F0 + 10.0, 0)
    chandelier(FGc)
    tf_pop()
    G_end()
    P_(15.8, 5.6, F0, -90)
    sideboard(FGc)
    tf_push(-1.6, 0.0, 2.95, 0)
    table_lamp(FGc, base='red')
    tf_pop()
    tf_push(1.7, 0.0, 2.95, 0)
    vase_flowers(FGc, 'teal', 6, 1.1)
    tf_pop()
    for k in range(3):
        tf_push(-0.2 + k * 0.0, -0.3 + k * 1.0, 2.95, 0)
        plate(FGc, ('blue', 'white', 'red')[k], 0.5)
        tf_pop()
    tf_pop()
    for k, (u, w_, h_, kind, col) in enumerate(((17.6, 3.2, 2.4, 'art', 'purple'), (30.8, 2.4, 3.0, 'art', 'orange'))):
        P_(u, 21.4, F0 + 6.5, 180)
        picture(FGc, w_, h_, col, 'trim', kind)
        tf_pop()
    for ac in (HX + 22,):
        curtain_pair(FGc, ac, 6.0, F0 + 8.3, 5.8, HZ + 2.3, 'x', 'yellow')
    curtain_pair(FGc, HZ + 11, 6.0, F0 + 8.3, 5.8, HX + 33.65, 'z', 'yellow')



def cabinet(c, w, d, h, n=2, col='cab', top='teal', knob='brass', top_t=0.24, sides_open=False, shelf_h=None):
    """base cabinet, front toward +lz. Counter top slab sits on top."""
    rbox(c, MT('dark'), 0, -0.1, 0.0, w - 0.1, 0.5, d - 0.5, 0.04, 1)
    rbox(c, MT(col), 0, 0, 0.5, w, h - 0.5 - top_t, d, 0.06, 2)
    dw = (w - 0.12) / n
    for k in range(n):
        x = -w / 2 + 0.06 + dw * (k + 0.5)
        rbox(c, MT(col), x, d / 2 - 0.02, 0.62, dw - 0.1, h - 0.5 - top_t - 0.24, 0.1, 0.05, 2)
        rbox(c, MT('trim'), x, d / 2 + 0.06, 0.78, dw - 0.46, h - 0.5 - top_t - 0.56, 0.05, 0.03, 1)
        kx = x + (dw / 2 - 0.35) * (1 if k % 2 == 0 else -1)
        cylinder(c, MT(knob), kx, d / 2 + 0.17, h - top_t - 0.5, 0.07, 0.07, 8)
        sphere(c, MT(knob), kx, d / 2 + 0.28, h - top_t - 0.5, 0.13, 0.13, 0.13, 8, 6)
    rbox(c, MT(top), 0, 0.05, h - top_t, w + 0.1, top_t, d + 0.18, 0.07, 2)


def upper_cabinet(c, w, d=1.1, h=2.9, n=2, col='cab'):
    rbox(c, MT(col), 0, 0, 0.0, w, h, d, 0.07, 2)
    dw = (w - 0.1) / n
    for k in range(n):
        x = -w / 2 + 0.05 + dw * (k + 0.5)
        rbox(c, MT(col), x, d / 2 - 0.02, 0.1, dw - 0.1, h - 0.2, 0.09, 0.05, 2)
        rbox(c, MT('trim'), x, d / 2 + 0.05, 0.28, dw - 0.45, h - 0.56, 0.05, 0.03, 1)
        cylinder(c, MT('brass'), x + (dw / 2 - 0.3) * (-1 if k % 2 == 0 else 1), d / 2 + 0.14, 0.2, 0.06, 0.06, 8)


def faucet(c):
    cylinder(c, MT('metal'), 0, 0, 0, 0.25, 0.22, 12)
    tube(c, MT('metal'), [(0, 0.25, 0), (0, 1.1, 0), (0.0, 1.45, 0.25), (0.0, 1.5, 0.75), (0.0, 1.35, 0.95)], 0.1, 8)
    for sx in (-1, 1):
        cylinder(c, MT('metal'), sx * 0.42, 0, 0.0, 0.5, 0.06, 8)
        sphere(c, MT('red' if sx < 0 else 'blue'), sx * 0.42, 0, 0.52, 0.1, 0.08, 0.1, 8, 6)


def sink_unit(c, w, d, h, col='cab', top='teal'):
    cabinet(c, w, d, h, 2, col, top)
    # basin visible as a dark steel tray set into the counter
    tf_push(0, 0.05, h - 0.02, 0)
    rbox(c, MT('metal'), 0, 0, 0.0, w - 0.9, 0.06, d - 0.7, 0.03, 1)
    rbox(c, MT('dark'), 0, 0, 0.05, w - 1.3, 0.03, d - 1.1, 0.02, 1)
    tf_pop()
    tf_push(0, -d / 2 + 0.35, h, 0)
    faucet(c)
    tf_pop()


def stove(c, w=2.8, d=2.4, h=3.1):
    for sx in (-1, 1):
        cylinder(c, MT('dark'), sx * (w / 2 - 0.2), d / 2 - 0.2, 0.0, 0.2, 0.12, 8)
    rbox(c, MT('metal'), 0, 0, 0.2, w, h - 0.2, d, 0.1, 3)
    rbox(c, MT('black'), 0, 0, h, w - 0.1, 0.1, d - 0.1, 0.04, 2)
    for (bx, bz) in ((-0.65, -0.55), (0.65, -0.55), (-0.65, 0.55), (0.65, 0.55)):
        torus(c, MT('dark'), bx, bz, h + 0.16, 0.34, 0.05, 'xz', 20, 6)
        cylinder(c, MT('dark'), bx, bz, h + 0.1, 0.1, 0.13, 10)
    for k in range(5):
        cylinder(c, MT('dark'), -1.0 + k * 0.5, d / 2 + 0.15, h - 0.5, 0.2, 0.1, 10)
        cylinder(c, MT('metal'), -1.0 + k * 0.5, d / 2 + 0.3, h - 0.5, 0.1, 0.06, 8)
    rbox(c, MT('black'), 0, d / 2 - 0.02, 0.5, w - 0.45, h - 1.35, 0.1, 0.07, 2)
    rbox(c, MT('screen'), 0, d / 2 + 0.05, 0.85, w - 0.95, h - 2.1, 0.05, 0.05, 2)
    tube(c, MT('metal'), [(-w / 2 + 0.5, h - 1.0, d / 2 + 0.28), (w / 2 - 0.5, h - 1.0, d / 2 + 0.28)], 0.07, 8)


def range_hood(c, w=3.0, d=2.1):
    rbox(c, MT('metal'), 0, 0, 0.0, w, 0.5, d, 0.1, 2)
    rbox(c, MT('metal'), 0, -d * 0.2, 0.45, w * 0.55, 1.0, d * 0.6, 0.06, 2)
    rbox(c, MT('metal'), 0, -d * 0.3, 1.3, 1.25, 3.2, 1.2, 0.04, 1)
    rbox(c, MT('dark'), 0, 0.15, -0.02, w - 0.7, 0.04, d - 0.7, 0.02, 1)
    sphere(c, MT('lamp'), -0.7, 0.2, -0.04, 0.12, 0.05, 0.12, 8, 4)
    sphere(c, MT('lamp'), 0.7, 0.2, -0.04, 0.12, 0.05, 0.12, 8, 4)


def fridge(c, w=2.8, d=2.4, h=7.1, col='metal'):
    rbox(c, MT(col), 0, 0, 0.1, w, h - 0.1, d, 0.22, 3)
    rbox(c, MT('dark'), 0, d / 2 - 0.01, 2.55, w - 0.1, 0.07, 0.06, 0.02, 1)
    for k, (y0, hh) in enumerate(((0.35, 2.1), (2.7, h - 2.7 - 0.2))):
        pass
    for hx_ in (-w / 2 + 0.35,):
        tube(c, MT('metal'), [(hx_, 3.0, d / 2 + 0.28), (hx_, 5.2, d / 2 + 0.28)], 0.07, 8)
        tube(c, MT('metal'), [(hx_, 1.0, d / 2 + 0.28), (hx_, 2.2, d / 2 + 0.28)], 0.07, 8)
    for k, mc in enumerate(('red', 'blue', 'yellow', 'teal')):
        sphere(c, MT(mc), -0.2 + (k % 2) * 0.6, d / 2 + 0.05, 4.8 + (k // 2) * 0.55, 0.14, 0.14, 0.05, 8, 5)
    rbox(c, MT('white'), 0.4, d / 2 + 0.03, 4.2, 0.7, 0.9, 0.02, 0.01, 1)
    rbox(c, MT('pink'), -0.2, d / 2 + 0.03, 4.2, 0.55, 0.7, 0.02, 0.01, 1)


def stool(c, col='red', h=2.7):
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        tube(c, MT('wood'), [(0.45 * math.cos(a), 0.0, 0.45 * math.sin(a)), (0.32 * math.cos(a), h - 0.3, 0.32 * math.sin(a))], 0.07, 6)
    torus(c, MT('wood'), 0, 0, 0.9, 0.42, 0.045, 'xz', 20, 6)
    lathe(c, MT(col), [(0.0, h - 0.3), (0.62, h - 0.3), (0.66, h - 0.18), (0.6, h), (0.0, h + 0.02)], 0, 0, 0, 20)


def pendant(c, col='red', drop=3.2):
    tube(c, MT('dark'), [(0, 0, 0), (0, -drop + 0.8, 0)], 0.03, 5)
    lathe(c, MT(col), [(0.15, -drop + 0.8), (0.7, -drop + 0.2), (0.78, -drop)], 0, 0, 0, 20, caps=False)
    lathe(c, MT('lampshade'), [(0.78, -drop), (0.15, -drop + 0.8)], 0, 0, 0, 20, caps=False)
    sphere(c, MT('lamp'), 0, 0, -drop + 0.35, 0.22, 0.28, 0.22, 8, 6)


def kettle(c, col='red'):
    lathe(c, MT(col), [(0.0, 0), (0.45, 0.0), (0.52, 0.2), (0.44, 0.9), (0.26, 1.05), (0.08, 1.12), (0.0, 1.14)], 0, 0, 0, 18)
    tube(c, MT(col), [(0.4, 0.55, 0.0), (0.75, 0.6, 0.0), (0.78, 1.0, 0.0), (0.4, 1.0, 0.0)], 0.06, 6)
    tube(c, MT(col), [(-0.44, 0.45, 0.0), (-0.8, 0.8, 0.0)], 0.06, 6)
    sphere(c, MT('black'), 0, 0, 1.16, 0.1, 0.07, 0.1, 8, 5)


def cooking_pot(c, col='metal', s=1.0, lid=True):
    lathe(c, MT(col), [(0.0, 0), (0.55 * s, 0.0), (0.58 * s, 0.05), (0.58 * s, 0.9 * s), (0.62 * s, 0.95 * s), (0.0, 0.95 * s)], 0, 0, 0, 18, caps=False)
    if lid:
        lathe(c, MT(col), [(0.0, 0.95 * s), (0.6 * s, 0.95 * s), (0.45 * s, 1.1 * s), (0.0, 1.15 * s)], 0, 0, 0, 18, caps=False)
        sphere(c, MT('black'), 0, 0, 1.2 * s, 0.1, 0.09, 0.1, 8, 5)
    for sx in (-1, 1):
        tube(c, MT('black'), [(sx * 0.58 * s, 0.7 * s, 0.0), (sx * 0.85 * s, 0.7 * s, 0.0)], 0.05, 6)


def pan(c):
    lathe(c, MT('dark'), [(0.0, 0.0), (0.6, 0.0), (0.72, 0.28), (0.66, 0.28), (0.54, 0.05), (0.0, 0.04)], 0, 0, 0, 20)
    tube(c, MT('black'), [(0.7, 0.26, 0.0), (1.9, 0.3, 0.0)], 0.07, 6)


def toaster(c):
    rbox(c, MT('metal'), 0, 0, 0.0, 1.5, 0.95, 0.95, 0.22, 3)
    for sx in (-1, 1):
        rbox(c, MT('dark'), sx * 0.34, 0.0, 0.92, 0.5, 0.05, 0.12, 0.02, 1) if False else None
    rbox(c, MT('black'), 0, 0, 0.88, 1.1, 0.06, 0.18, 0.02, 1)
    rbox(c, MT('red'), 0.8, 0.0, 0.5, 0.16, 0.12, 0.28, 0.05, 2)


def microwave(c):
    rbox(c, MT('metal'), 0, 0, 0.0, 2.0, 1.3, 1.5, 0.12, 3)
    rbox(c, MT('screen'), -0.2, 0.7, 0.2, 1.2, 0.85, 0.05, 0.04, 1)
    rbox(c, MT('black'), 0.7, 0.7, 0.2, 0.4, 0.85, 0.05, 0.03, 1)
    sphere(c, MT('red'), 0.7, 0.76, 1.0, 0.07, 0.07, 0.03, 6, 4)


def cutting_board(c):
    rbox(c, MT('wood2'), 0, 0, 0.0, 1.6, 0.12, 1.1, 0.05, 2)
    rbox(c, MT('white'), -0.3, 0.1, 0.12, 0.2, 0.14, 0.2, 0.05, 1) if False else None
    sphere(c, MT('red'), 0.3, 0.1, 0.34, 0.2, 0.18, 0.2, 8, 6)
    sphere(c, MT('orange'), -0.3, -0.1, 0.34, 0.2, 0.18, 0.2, 8, 6)
    rbox(c, MT('metal'), 0.0, -0.4, 0.12, 1.0, 0.05, 0.12, 0.02, 1)


def bowl(c, col='white', r=0.9, h=0.5):
    lathe(c, MT(col), [(0.0, 0.0), (r * 0.4, 0.0), (r, h * 0.9), (r, h), (r * 0.9, h), (r * 0.35, 0.1), (0.0, 0.1)], 0, 0, 0, 20)


def wall_clock(c, r=0.8):
    torus(c, MT('red'), 0, 0, 0, r, 0.1, 'xy', 28, 6)
    sphere(c, MT('white'), 0, 0.02, 0, r - 0.05, r - 0.05, 0.06, 24, 4)
    tube(c, MT('black'), [(0, 0.1, 0), (0, 0.1, r * 0.55)] if False else [(0, 0.1, 0), (0.0, r * 0.55, 0.1)], 0.03, 5)
    tube(c, MT('black'), [(0, 0, 0.1), (r * 0.4, 0.0, 0.1)], 0.03, 5)
    for k in range(12):
        a = math.radians(30 * k)
        sphere(c, MT('black'), (r - 0.18) * math.sin(a), 0.1, (r - 0.18) * math.cos(a), 0.03, 0.03, 0.03, 6, 4)


def hq_kitchen():
    # west run (front faces east): sink under the window, cabinet with microwave
    G_(2.9, 15.2, F0)
    P_(2.9, 15.2, F0, -90)
    sink_unit(FGc, 4.0, 2.1, 3.1)
    tf_pop()
    P_(2.9, 19.2, F0, -90)
    cabinet(FGc, 4.0, 2.1, 3.1, 2, 'cab', 'teal')
    tf_push(0.0, 0.1, 3.1, 0)
    microwave(FGc)
    tf_pop()
    tf_pop()
    G_end()
    # north run (front faces south): cabinet with toaster, stove, hood
    G_(4.0, 11.7, F0)
    P_(4.0, 11.7, F0, 0)
    cabinet(FGc, 3.0, 2.1, 3.1, 2, 'cab', 'teal')
    tf_push(0.0, 0.0, 3.1, 0)
    toaster(FGc)
    tf_pop()
    tf_pop()
    P_(6.9, 11.7, F0, 0)
    stove(FGc)
    tf_push(-0.85, -0.55, 3.26, 0)
    cooking_pot(FGc, 'metal', 1.0)
    tf_pop()
    tf_push(0.65, 0.55, 3.26, 20)
    pan(FGc)
    tf_pop()
    tf_push(1.05, -0.55, 3.26, 0)
    kettle(FGc, 'red')
    tf_pop()
    tf_pop()
    P_(6.9, 11.6, F0 + 6.4, 0)
    range_hood(FGc)
    tf_pop()
    P_(3.8, 11.2, F0 + 6.1, 0)
    upper_cabinet(FGc, 2.6, 1.1, 3.1, 2)
    tf_pop()
    G_end()
    # fridge in the south-east corner (front faces west) and the island with stools
    P_(12.2, 19.6, F0, 90)
    fridge(FGc, 2.8, 2.5, 7.1)
    tf_pop()
    G_(7.6, 15.8, F0)
    P_(7.6, 15.8, F0, 0)
    cabinet(FGc, 5.4, 3.0, 3.5, 3, 'cab', 'teal')
    cover('kitchen_island', 5.4, 3.0, 3.5)
    tf_push(-1.4, 0.2, 3.5, 0)
    cutting_board(FGc)
    tf_pop()
    tf_push(1.2, 0.3, 3.5, 0)
    fruit_bowl(FGc)
    tf_pop()
    tf_push(-0.2, -0.7, 3.5, 0)
    bowl(FGc, 'blue', 0.7, 0.4)
    tf_pop()
    tf_pop()
    for k in range(3):
        P_(5.9 + k * 1.7, 18.4, F0, 0)
        stool(FGc, 'red')
        tf_pop()
    for u in (6.3, 8.9):
        P_(u, 15.8, F0 + 10.0, 0)
        pendant(FGc, 'red')
        tf_pop()
    P_(11.0, 15.4, F0, 0)
    rug(FGc, 4.0, 7.0, 'cream', 'red', 'yellow', False)
    tf_pop()
    G_end()
    curtain_pair(FGc, HZ + 16, 5.2, F0 + 8.0, 3.1, HX + 2.4, 'z', 'red')


# ---------------------------------------------------------------- laundry, closet, WC
def washer(c, col='white', kind='washer'):
    rbox(c, MT(col), 0, 0, 0.0, 2.7, 3.5, 2.4, 0.16, 3)
    rbox(c, MT('metal'), 0, 1.1, 3.0, 2.5, 0.5, 0.15, 0.06, 2)
    for k in range(3):
        cylinder(c, MT('dark'), -0.8 + k * 0.5, 1.18, 3.2, 0.16, 0.12, 10)
    rbox(c, MT('screen'), 0.75, 1.2, 3.1, 0.5, 0.28, 0.05, 0.03, 1)
    tf_push(0, 1.2, 1.5, 0)
    torus(c, MT('metal'), 0, 0, 0, 0.78, 0.1, 'xy', 28, 8)
    sphere(c, MT('glass'), 0, 0.04, 0, 0.7, 0.7, 0.12, 24, 8)
    sphere(c, MT('navy'), 0, -0.06, 0, 0.62, 0.62, 0.1, 24, 8)
    tf_pop()
    rbox(c, MT('metal'), 1.1, 1.3, 1.6, 0.14, 0.9, 0.08, 0.04, 1)


def bottle(c, col='blue', cap='white', h=1.2, r=0.28):
    lathe(c, MT(col), [(0.0, 0), (r, 0.0), (r * 1.05, 0.1), (r * 1.05, h * 0.65), (r * 0.5, h * 0.82), (r * 0.32, h * 0.9), (r * 0.32, h)], 0, 0, 0, 14)
    cylinder(c, MT(cap), 0, 0, h, 0.16, r * 0.38, 10)


def basket(c, col='wood2', clothes=True):
    lathe(c, MT(col), [(0.0, 0), (0.62, 0.0), (0.86, 1.4), (0.92, 1.55), (0.84, 1.55), (0.0, 0.1)], 0, 0, 0, 20, caps=False)
    for sx in (-1, 1):
        tube(c, MT(col), [(sx * 0.9, 1.35, 0.0), (sx * 1.1, 1.65, 0.0), (sx * 0.9, 1.75, 0.0)], 0.05, 6)
    if clothes:
        for k, cc in enumerate(('red', 'blue', 'yellow', 'white')):
            sphere(c, MT(cc), (k % 2 - 0.5) * 0.7, (k // 2 - 0.5) * 0.6, 1.5, 0.4, 0.3, 0.38, 10, 6)


def ironing_board(c):
    rbox(c, MT('metal'), 0, 0, 3.0, 1.1, 0.1, 4.4, 0.05, 1)
    rbox(c, MT('blue'), 0, 0, 3.08, 1.0, 0.06, 4.3, 0.03, 1)
    for sz in (-1, 1):
        tube(c, MT('metal'), [(-0.45, 3.0, sz * 1.0), (0.45, 0.0, sz * 1.4)], 0.05, 6)
        tube(c, MT('metal'), [(0.45, 3.0, sz * 1.0), (-0.45, 0.0, sz * 1.4)], 0.05, 6)


def drying_rack(c):
    for sx in (-1, 1):
        tube(c, MT('metal'), [(sx * 1.4, 0.0, 0.0), (sx * 1.0, 3.2, 0.0)], 0.05, 6)
    for k in range(6):
        tube(c, MT('metal'), [(-1.1, 1.4 + k * 0.28, 0.0), (1.1, 1.4 + k * 0.28, 0.0)], 0.035, 5)
    for k, cc in enumerate(('red', 'yellow', 'blue')):
        rbox(c, MT(cc), -0.5 + k * 0.5, 0.0, 1.5 + k * 0.1, 0.55, 1.2, 0.12, 0.06, 2)


def hq_laundry():
    G_(12.3, 6.05, F0)
    P_(12.3, 4.4, F0, 90)
    washer(FGc, 'white')
    tf_push(-0.3, 0.0, 3.5, 0)
    bottle(FGc, 'blue', 'white', 1.3)
    tf_pop()
    tf_push(0.5, 0.2, 3.5, 0)
    bottle(FGc, 'orange', 'dark', 1.0)
    tf_pop()
    tf_pop()
    P_(12.3, 7.7, F0, 90)
    washer(FGc, 'cream')
    tf_push(0.0, 0.0, 3.5, 0)
    rbox(FGc, MT('red'), 0, 0, 0.0, 1.5, 0.3, 1.1, 0.1, 2)
    rbox(FGc, MT('yellow'), 0.1, 0.0, 0.3, 1.4, 0.3, 1.0, 0.1, 2)
    rbox(FGc, MT('teal'), 0, 0.0, 0.6, 1.3, 0.3, 0.9, 0.1, 2)
    tf_pop()
    tf_pop()
    # wall shelf above the machines
    P_(13.1, 6.0, F0 + 6.2, 90)
    rbox(FGc, MT('wood2'), 0, 0, 0.0, 6.2, 0.2, 0.9, 0.06, 2)
    for sx in (-2.4, 2.4):
        rbox(FGc, MT('metal'), sx, -0.2, -0.7, 0.14, 0.7, 0.6, 0.04, 1)
    for k, (cc, h_) in enumerate((('blue', 1.0), ('red', 1.3), ('yellow', 0.9), ('teal', 1.2), ('purple', 1.0))):
        tf_push(-2.4 + k * 1.2, 0.0, 0.2, 0)
        bottle(FGc, cc, 'white', h_)
        tf_pop()
    tf_pop()
    G_end()
    P_(9.0, 3.4, F0, 0)
    drying_rack(FGc)
    tf_pop()
    P_(8.9, 8.3, F0, 0)
    basket(FGc)
    tf_pop()
    P_(8.8, 5.7, F0, 90)
    ironing_board(FGc)
    tf_pop()
    P_(10.2, 2.4, F0, 0)
    lathe(FGc, MT('red'), [(0.0, 0), (0.5, 0.0), (0.62, 1.4), (0.0, 1.4)], 0, 0, 0, 14, caps=False)
    tube(FGc, MT('wood2'), [(0.0, 1.2, 0.0), (0.2, 4.5, -0.3), (0.3, 5.6, -0.4)], 0.07, 6)
    for k in range(7):
        a = k * 0.9
        tube(FGc, MT('cream'), [(0.0, 1.0, 0.0), (0.45 * math.cos(a), 0.8, 0.45 * math.sin(a))], 0.07, 5)
    tf_pop()
    # closet H1: shelves with boxes and baskets, rail with hung clothes, shoes, broom
    G_(2.7, 5.5, F0)
    P_(2.7, 5.5, F0, -90)
    for k in range(5):
        rbox(FGc, MT('wood2'), 0, 0, 1.2 + k * 1.5, 7.0, 0.16, 1.2, 0.04, 1)
    rbox(FGc, MT('wood'), 0, -0.55, 0.0, 7.0, 7.8, 0.12, 0.03, 1)
    tf_pop()
    rnd = _random.Random(11)
    for k in range(5):
        for j in range(3):
            P_(2.7, 2.6 + j * 2.1, F0, -90)
            tf_push(0.0, 0.0, 1.36 + k * 1.5, 0)      # local height: sits on the shelf board below (not scaled with the storey)
            col = ('cardboard', 'blue', 'cream', 'red', 'yellow', 'teal')[(k + j) % 6]
            rbox(FGc, MT(col), 0, 0, 0.0, 1.7, 0.95, 0.9, 0.12, 2)
            rbox(FGc, MT('white'), 0, 0.46, 0.35, 0.7, 0.3, 0.02, 0.01, 1)
            tf_pop()
            tf_pop()
    G_end()
    G_(4.9, 8.6, F0)
    P_(4.9, 8.6, F0 + 6.5, 0)
    tube(FGc, MT('metal'), [(-1.4, 0, 0), (1.4, 0, 0)], 0.05, 6)
    for k, cc in enumerate(('purple', 'teal', 'orange', 'blue')):
        tf_push(-1.0 + k * 0.7, 0.0, 0.0, 0)
        tube(FGc, MT('metal'), [(0, 0, 0), (0, -0.3, 0), (0.35, -0.5, 0), (-0.35, -0.5, 0), (0, -0.3, 0)], 0.025, 5)
        rbox(FGc, MT(cc), 0, 0, -3.4, 0.55, 2.9, 0.9, 0.2, 2)
        tf_pop()
    tf_pop()
    for k in range(3):
        P_(3.4 + k * 1.2, 8.3, F0, 15 * (k - 1))
        shoe(FGc, ('red', 'dark', 'blue')[k])
        tf_pop()
    G_end()


def toilet(c):
    lathe(c, MT('white'), [(0.0, 0.0), (0.5, 0.0), (0.55, 0.8), (0.7, 1.45), (0.0, 1.45)], 0, 0.15, 0, 20, sx=0.85, sz=1.15, caps=False)
    rbox(c, MT('white'), 0, -0.95, 0.5, 1.5, 1.7, 0.7, 0.14, 3)
    torus(c, MT('white'), 0, 0.15, 1.52, 0.55, 0.1, 'xz', 24, 6)
    sphere(c, MT('white'), 0, -0.95, 2.2, 0.25, 0.1, 0.25, 8, 4)
    lathe(c, MT('white'), [(0.0, 1.55), (0.62, 1.55), (0.62, 1.6), (0.0, 1.62)], 0, 0.15, 0, 20, sx=0.85, sz=1.15)


def pedestal_sink(c):
    lathe(c, MT('white'), [(0.0, 0), (0.55, 0.0), (0.5, 0.2), (0.28, 0.5), (0.3, 2.0), (0.6, 2.2)], 0, 0, 0, 16)
    lathe(c, MT('white'), [(0.0, 2.4), (0.72, 2.6), (1.3, 3.1), (1.35, 3.3), (1.2, 3.3), (0.0, 2.7)], 0, 0.2, 0, 22, sx=1.1, sz=0.85)
    tf_push(0, -0.45, 3.2, 0)
    faucet(c)
    tf_pop()


def bathtub(c):
    rbox(c, MT('white'), 0, 0, 0.5, 3.6, 2.0, 7.4, 0.55, 4)
    rbox(c, MT('mirror'), 0, 0, 2.3, 2.6, 0.12, 6.4, 0.3, 3)
    for sx in (-1, 1):
        cylinder(c, MT('metal'), sx * 1.4, -3.4, 0.0, 0.5, 0.2, 10)
    tf_push(0, -3.1, 2.5, 0)
    faucet(c)
    tf_pop()
    rbox(c, MT('white'), 0, 0.0, 0.0, 3.2, 0.5, 6.9, 0.08, 1)


def hq_wc():
    P_(32.7, 3.0, F0, 90)
    toilet(FGc)
    tf_pop()
    P_(30.3, 6.4, F0, 180)
    pedestal_sink(FGc)
    tf_pop()
    P_(30.3, 7.4, F0 + 5.2, 180)
    rbox(FGc, MT('brass'), 0, 0, -1.4, 2.6, 2.8, 0.12, 0.06, 2)
    rbox(FGc, MT('mirror'), 0, -0.05, -1.25, 2.3, 2.5, 0.06, 0.03, 1)
    tf_pop()
    P_(31.5, 4.5, F0, 0)
    rug(FGc, 2.8, 1.8, 'teal', 'cream', 'yellow', False)
    tf_pop()



def bed(c, w=6.4, l=9.4, quilt='pink', sheet='cream', wood='wood2', pillows=('white', 'cream'), stripe='white'):
    cover('bed', w, l, 2.7)
    wd, w2 = MT('wood'), MT(wood)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.26, 0), (0.2, 0.3), (0.28, 0.6)], sx * (w / 2 - 0.3), sz * (l / 2 - 0.3), 0, 10)
    rbox(c, w2, 0, 0, 0.5, w, 0.7, l, 0.14, 3)
    rbox(c, MT(sheet), 0, 0.1, 1.2, w - 0.35, 0.95, l - 0.6, 0.38, 3)
    rbox(c, MT(quilt), 0, 1.15, 1.95, w - 0.12, 0.62, l * 0.68, 0.3, 3)
    for k in range(5):
        rbox(c, MT(stripe), 0, 1.15 - l * 0.34 + 0.9 + k * (l * 0.68 - 1.8) / 4, 2.5, w - 0.7, 0.06, 0.28, 0.02, 1)
    rbox(c, MT(quilt), 0, l / 2 - 1.2, 2.0, w - 0.3, 0.6, 1.8, 0.3, 3)
    rbox(c, w2, 0, -l / 2 - 0.1, 0.5, w + 0.5, 3.6, 0.55, 0.28, 4)
    for sx in (-1, 1):
        sphere(c, wd, sx * (w / 2 + 0.05), -l / 2 - 0.1, 4.25, 0.3, 0.3, 0.3, 10, 8)
    rbox(c, w2, 0, l / 2 + 0.1, 0.5, w + 0.3, 1.5, 0.45, 0.2, 3)
    for k, pc in enumerate(pillows):
        tf_push(-1.5 + k * 3.0, -l / 2 + 1.1, 2.1, (-6, 5)[k % 2])
        rbox(c, MT(pc), 0, 0, 0.0, 2.6, 0.9, 1.6, 0.42, 3)
        tf_pop()
    tf_push(0.0, -l / 2 + 1.7, 2.0, 0)
    rbox(c, MT('coral'), 0, 0, 0.0, 1.3, 0.9, 0.7, 0.34, 3)
    tf_pop()


def nightstand(c, col='wood2'):
    wd = MT('wood')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.14, 0), (0.1, 0.4), (0.15, 0.8)], sx * 0.75, sz * 0.6, 0, 8)
    rbox(c, MT(col), 0, 0, 0.8, 1.9, 1.5, 1.6, 0.1, 3)
    rbox(c, wd, 0, 0.8, 0.95, 1.6, 0.55, 0.06, 0.04, 1)
    rbox(c, wd, 0, 0.8, 1.65, 1.6, 0.55, 0.06, 0.04, 1)
    sphere(c, MT('brass'), 0, 0.92, 1.2, 0.1, 0.1, 0.1, 8, 6)
    sphere(c, MT('brass'), 0, 0.92, 1.9, 0.1, 0.1, 0.1, 8, 6)
    rbox(c, wd, 0, 0, 2.3, 2.1, 0.14, 1.8, 0.06, 2)


def dresser(c, w=6.0, d=2.4, h=3.7, col='wood2'):
    wd = MT('wood')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.2, 0), (0.14, 0.4), (0.2, 0.8)], sx * (w / 2 - 0.4), sz * (d / 2 - 0.35), 0, 10)
    rbox(c, MT(col), 0, 0, 0.8, w, h - 0.8, d, 0.12, 3)
    rbox(c, wd, 0, 0, h, w + 0.2, 0.14, d + 0.14, 0.05, 2)
    for k in range(3):
        y = 1.0 + k * 0.85
        rbox(c, wd, 0, d / 2 - 0.02, y, w - 0.5, 0.7, 0.08, 0.05, 2)
        for sx in (-1, 1):
            sphere(c, MT('brass'), sx * w * 0.2, d / 2 + 0.12, y + 0.35, 0.12, 0.12, 0.12, 8, 6)
    tf_push(0, -d / 2 + 0.2, h + 0.14, 0)
    rbox(c, MT('brass'), 0, 0, 0.0, w * 0.55, 3.4, 0.14, 0.12, 3)
    rbox(c, MT('mirror'), 0, 0.02, 0.2, w * 0.55 - 0.4, 3.0, 0.1, 0.1, 2)
    tf_pop()
    tf_push(-w * 0.32, 0.2, h + 0.14, 20)
    rbox(c, MT('red'), 0, 0, 0.0, 1.1, 0.5, 0.8, 0.12, 2)
    tf_pop()
    tf_push(w * 0.28, 0.35, h + 0.14, 0)
    bottle(c, 'pink', 'brass', 0.8, 0.2)
    tf_pop()
    tf_push(w * 0.4, 0.2, h + 0.14, 0)
    bottle(c, 'blue', 'white', 0.65, 0.17)
    tf_pop()


def wardrobe(c, w=8.0, d=3.5, h=8.6, open_doors=True):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, -w / 2 + 0.2, 0, 0.0, 0.4, h, d, 0.06, 2)
    rbox(c, w2, w / 2 - 0.2, 0, 0.0, 0.4, h, d, 0.06, 2)
    rbox(c, w2, 0, 0, h - 0.4, w, 0.45, d, 0.06, 2)
    rbox(c, w2, 0, 0, 0.0, w, 0.4, d, 0.05, 2)
    rbox(c, wd, 0, -d / 2 + 0.1, 0.3, w - 0.5, h - 0.7, 0.18, 0.04, 1)
    tube(c, MT('metal'), [(-w / 2 + 0.5, h - 2.4, 0.0), (w / 2 - 0.5, h - 2.4, 0.0)], 0.07, 8)
    rbox(c, w2, 0, 0, h - 1.6, w - 0.8, 0.14, d - 0.5, 0.04, 1)
    for k, cc in enumerate(('cream', 'red', 'blue')):
        rbox(c, MT(cc), -2.6 + k * 1.4, 0.0, h - 1.46, 1.2, 0.55, 1.1, 0.14, 2)    # shelf items stay on the left; the right third is free for hiding
    cols = ('red', 'blue', 'yellow', 'teal', 'white', 'purple', 'orange', 'navy', 'pink')
    for k in range(4):
        x = -w / 2 + 0.9 + k * (w - 1.8) / 8.0
        tube(c, MT('metal'), [(x, h - 2.4, 0), (x, h - 2.7, 0), (x + 0.45, h - 3.0, 0), (x - 0.45, h - 3.0, 0), (x, h - 2.7, 0)], 0.025, 5)
        rbox(c, MT(cols[k]), x, 0.0, h - 5.7, 0.55, 2.7 + (k % 3) * 0.2, 1.1, 0.2, 2)
    for k, cc in enumerate(('red', 'dark', 'blue')):
        tf_push(-w / 2 + 1.1 + k * 1.1, 0.5, 0.4, 15 * (k % 2 * 2 - 1))
        shoe(c, cc)
        tf_pop()
    if open_doors:
        for sx in (-1, 1):
            tf_push(sx * (w / 2 - 0.05), d / 2, 0.0, 0)
            tf_push(0, 0.0, 0.0, -sx * 75)
            rbox(c, w2, sx * (w / 4), 0.0, 0.2, w / 2 - 0.1, h - 0.4, 0.22, 0.06, 2)
            rbox(c, wd, sx * (w / 4), 0.14, 0.7, w / 2 - 0.9, h - 1.4, 0.07, 0.04, 1)
            sphere(c, MT('brass'), sx * 0.4 + 0.0, 0.2, h * 0.5, 0.12, 0.12, 0.12, 8, 6)
            tf_pop()
            tf_pop()


def teddy(c, col='orange'):
    g = MT(col)
    sphere(c, g, 0, 0, 0.55, 0.55, 0.6, 0.5, 12, 8)
    sphere(c, g, 0, 0.05, 1.45, 0.42, 0.4, 0.4, 12, 8)
    for sx in (-1, 1):
        sphere(c, g, sx * 0.33, 0, 1.78, 0.14, 0.14, 0.1, 8, 6)
        sphere(c, g, sx * 0.72, 0.1, 0.8, 0.2, 0.3, 0.2, 8, 6)
        sphere(c, g, sx * 0.35, 0.15, 0.1, 0.25, 0.22, 0.32, 8, 6)
    sphere(c, MT('cream'), 0, 0.33, 1.38, 0.18, 0.14, 0.12, 8, 6)
    sphere(c, MT('black'), 0, 0.45, 1.42, 0.06, 0.05, 0.05, 6, 4)
    for sx in (-1, 1):
        sphere(c, MT('black'), sx * 0.14, 0.32, 1.52, 0.05, 0.05, 0.04, 6, 4)


def bunk_bed(c, w=3.8, l=8.0):
    wd = MT('blue')
    for sx in (-1, 1):
        for sz in (-1, 1):
            rbox(c, wd, sx * (w / 2 - 0.2), sz * (l / 2 - 0.2), 0.0, 0.4, 5.2, 0.4, 0.12, 2)
    for y, sc, pc in ((0.6, 'white', 'yellow'), (3.0, 'white', 'red')):
        rbox(c, MT('wood2'), 0, 0, y, w - 0.4, 0.3, l - 0.4, 0.06, 2)
        rbox(c, MT(sc), 0, 0.1, y + 0.3, w - 0.5, 0.7, l - 0.8, 0.28, 3)
        rbox(c, MT(pc), 0, 1.0, y + 0.85, w - 0.45, 0.4, l * 0.6, 0.18, 3)
        rbox(c, MT('white'), 0, -l / 2 + 1.0, y + 0.95, 2.4, 0.5, 1.1, 0.2, 3)
    for z in (-1.6, 0.0, 1.6):
        tube(c, MT('blue'), [(-w / 2 + 0.2, 4.1, z), (-w / 2 + 0.2, 5.0, z)], 0.07, 6)
        tube(c, MT('blue'), [(w / 2 - 0.2, 4.1, z), (w / 2 - 0.2, 5.0, z)], 0.07, 6)
    tube(c, MT('blue'), [(-w / 2 + 0.2, 5.0, -l / 2 + 0.2), (-w / 2 + 0.2, 5.0, l / 2 - 0.2)], 0.1, 6)
    tube(c, MT('blue'), [(w / 2 - 0.2, 5.0, -l / 2 + 0.2), (w / 2 - 0.2, 5.0, l / 2 - 0.2)], 0.1, 6)
    for sx in (-w / 2 + 0.2, w / 2 - 0.2):
        pass
    # ladder on the west side
    for z in (1.9, 3.1):
        tube(c, MT('wood2'), [(-w / 2 - 0.1, 0.0, z), (-w / 2 - 0.1, 3.9, z)], 0.07, 6)
    for k in range(5):
        tube(c, MT('wood2'), [(-w / 2 - 0.1, 0.5 + k * 0.78, 1.9), (-w / 2 - 0.1, 0.5 + k * 0.78, 3.1)], 0.07, 6)
    tf_push(0.3, l * 0.1, 4.2, 0)
    teddy(c, 'orange')
    tf_pop()


def toy_chest(c):
    rbox(c, MT('red'), 0, 0, 0.0, 3.2, 1.6, 1.8, 0.14, 3)
    rbox(c, MT('yellow'), 0, 0.1, 1.55, 3.3, 0.3, 1.9, 0.14, 3)
    for k in range(3):
        sphere(c, MT('yellow'), -0.9 + k * 0.9, 0.95, 0.9, 0.16, 0.16, 0.04, 8, 5)
    tf_push(-0.7, 0, 1.85, 18)
    rbox(c, MT('blue'), 0, 0, 0.0, 0.7, 0.7, 0.7, 0.1, 2)
    tf_pop()
    tf_push(0.6, 0.1, 1.85, -10)
    rbox(c, MT('teal'), 0, 0, 0.0, 0.7, 0.7, 0.7, 0.1, 2)
    tf_pop()


def desk(c, w=5.6, d=2.4, h=2.9):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.22, w, 0.22, d, 0.08, 2)
    rbox(c, wd, -w / 2 + 0.9, 0, 0.0, 1.6, h - 0.22, d - 0.2, 0.06, 2)
    for k in range(3):
        rbox(c, w2, -w / 2 + 0.9, d / 2 - 0.08, 0.25 + k * 0.85, 1.4, 0.7, 0.07, 0.04, 1)
        sphere(c, MT('brass'), -w / 2 + 0.9, d / 2 + 0.03, 0.6 + k * 0.85, 0.09, 0.09, 0.09, 8, 6)
    for sz in (-1, 1):
        lathe(c, wd, [(0.16, 0), (0.1, 0.9), (0.14, h - 0.22)], w / 2 - 0.35, sz * (d / 2 - 0.3), 0, 10)


def kid_chair(c, col='blue'):
    wd = MT('wood')
    for sx in (-1, 1):
        for sz in (-1, 1):
            tube(c, wd, [(sx * 0.65, 0.0, sz * 0.65), (sx * 0.6, 1.6, sz * 0.6)], 0.07, 6)
    lathe(c, MT(col), [(0.0, 1.55), (0.95, 1.55), (1.0, 1.7), (0.95, 1.85), (0.0, 1.88)], 0, 0, 0, 20)
    for sx in (-1, 1):
        tube(c, wd, [(sx * 0.6, 1.6, -0.62), (sx * 0.6, 3.4, -0.62)], 0.07, 6)
    rbox(c, MT(col), 0, -0.64, 2.6, 1.5, 0.7, 0.14, 0.06, 2)


def globe(c):
    lathe(c, MT('metal'), [(0.0, 0), (0.4, 0.0), (0.3, 0.1), (0.08, 0.2), (0.06, 0.5)], 0, 0, 0, 12)
    sphere(c, MT('blue'), 0, 0, 1.05, 0.6, 0.6, 0.6, 16, 10)
    sphere(c, MT('leaf'), 0.18, 0.2, 1.2, 0.32, 0.25, 0.22, 10, 6)


def trophy(c, col='brass', h=1.0):
    lathe(c, MT('dark'), [(0.0, 0), (0.4, 0.0), (0.4, 0.18), (0.0, 0.18)], 0, 0, 0, 12)
    lathe(c, MT(col), [(0.0, 0.18), (0.1, 0.2), (0.1, h * 0.5), (0.25, h * 0.62), (0.4, h * 0.95), (0.34, h), (0.0, h * 0.5)], 0, 0, 0, 14, caps=False)
    for sx in (-1, 1):
        tube(c, MT(col), [(sx * 0.38, h * 0.88, 0.0), (sx * 0.58, h * 0.78, 0.0), (sx * 0.4, h * 0.65, 0.0)], 0.04, 5)


def dartboard(c, r=1.4):
    lathe(c, MT('black'), [(0.0, 0.0), (r + 0.1, 0.0), (r + 0.1, 0.12), (0.0, 0.12)], 0, 0, 0, 36)
    cols = ('red', 'cream', 'red', 'cream')
    for k, rr in enumerate((r, r * 0.78, r * 0.34, r * 0.16)):
        lathe(c, MT(('leaf', 'cream', 'red', 'cream')[k] if k < 2 else ('red', 'leaf')[k - 2]), [(0.0, 0.13 + k * 0.01), (rr, 0.13 + k * 0.01)], 0, 0, 0, 36, caps=False)


def bar_cart(c):
    for sx in (-1, 1):
        for sz in (-1, 1):
            tube(c, MT('brass'), [(sx * 0.8, 0.3, sz * 0.5), (sx * 0.8, 3.0, sz * 0.5)], 0.06, 6)
    for y in (1.0, 3.0):
        rbox(c, MT('wood2'), 0, 0, y - 0.1, 1.9, 0.14, 1.3, 0.05, 1)
    for sx in (-1, 1):
        cylinder(c, MT('dark'), sx * 0.8, 0.5, 0.0, 0.3, 0.17, 10)
    tf_push(-0.55, 0.0, 3.04, 0)
    bottle(c, 'leaf', 'brass', 1.4, 0.24)
    tf_pop()
    tf_push(0.0, 0.1, 3.04, 0)
    bottle(c, 'orange', 'dark', 1.2, 0.22)
    tf_pop()
    tf_push(0.55, 0.0, 3.04, 0)
    bottle(c, 'red', 'brass', 1.0, 0.2)
    tf_pop()
    tf_push(0.3, -0.3, 1.0, 0)
    glass_cup(c, 0.7, 0.2)
    tf_pop()


def recliner(c):
    armchair(c, 'orange', 'orange', 4.4, 4.0)
    tf_push(0.0, 3.1, 0.0, 0)
    rbox(c, MT('orange'), 0, 0, 0.55, 3.2, 1.0, 2.0, 0.4, 3)
    tf_pop()


def round_table(c, r=1.7, h=2.7, col='white'):
    lathe(c, MT(col), [(r, h - 0.2), (r, h), (0, h)], 0, 0, 0, 24)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        tube(c, MT('dark'), [(0.85 * math.cos(a), 0.0, 0.85 * math.sin(a)), (0.2 * math.cos(a), h - 0.2, 0.2 * math.sin(a))], 0.07, 6)


def folding_chair(c):
    for sx in (-1, 1):
        tube(c, MT('dark'), [(sx * 0.7, 0.0, -0.6), (sx * 0.7, 1.7, 0.6)], 0.05, 6)
        tube(c, MT('dark'), [(sx * 0.7, 0.0, 0.6), (sx * 0.7, 1.7, -0.6)], 0.05, 6)
        tube(c, MT('dark'), [(sx * 0.7, 1.7, -0.7), (sx * 0.7, 3.4, -0.9)], 0.05, 6)
    rbox(c, MT('white'), 0, 0.0, 1.7, 1.6, 0.14, 1.5, 0.05, 1)
    rbox(c, MT('white'), 0, -0.85, 2.7, 1.5, 0.8, 0.08, 0.04, 1)


def hq_upper_hall_bath():
    P_(9.5, 20.0, F1, 0)
    rug(FUc, 4.2, 14.0, 'teal', 'cream', 'yellow', True)
    tf_pop()
    P_(12.65, 31.0, F1, 90)
    console_table(FUc, 4.4, 1.5, 3.0)
    tf_push(-0.9, 0.0, 3.0, 0)
    table_lamp(FUc, base='red')
    tf_pop()
    tf_push(1.2, 0.0, 3.0, 0)
    potted_plant(FUc, 0.7, 'teal', False, 9)
    tf_pop()
    tf_pop()
    P_(13.35, 31.0, F1 + 7.7, 90)
    mirror_round(FUc, 1.4)
    tf_pop()
    for (v, w_, h_, col) in ((17.5, 2.6, 2.8, 'orange'), (27.4, 2.6, 3.0, 'purple')):
        P_(13.4, v, F1 + 6.4, 90)
        picture(FUc, w_, h_, col, 'trim', 'art')
        tf_pop()
    P_(3.3, 13.0, F1, 0)
    potted_plant(FUc, 0.9, 'terra', True, 13)
    tf_pop()
    P_(3.3, 24.2, F1, 0)
    potted_plant(FUc, 0.9, 'navy', True, 12)
    tf_pop()
    curtain_pair(FUc, HX + 9.5, 5.4, F1 + 8.2, 5.4, HZ + 41.9, 'x', 'pink')
    # bathroom
    P_(3.7, 5.7, F1, 0)
    bathtub(FUc)
    tf_pop()
    P_(12.1, 7.2, F1, 90)
    toilet(FUc)
    tf_pop()
    P_(10.6, 3.1, F1, 0)
    pedestal_sink(FUc)
    tf_pop()
    P_(10.6, 1.95, F1 + 5.2, 0)
    rbox(FUc, MT('brass'), 0, 0, -1.4, 2.8, 3.0, 0.14, 0.12, 3)
    rbox(FUc, MT('mirror'), 0, 0.05, -1.25, 2.5, 2.7, 0.06, 0.1, 2)
    tf_pop()
    P_(11.0, 4.4, F1, 0)
    rug(FUc, 3.0, 2.0, 'cream', 'pink', 'teal', False)
    tf_pop()
    P_(13.1, 3.0, F1 + 4.2, 90)
    tube(FUc, MT('metal'), [(-1.0, 0, 0.0), (1.0, 0, 0.0)], 0.06, 6)
    rbox(FUc, MT('red'), -0.2, 0.18, -1.7, 1.4, 1.9, 0.18, 0.1, 3)
    rbox(FUc, MT('blue'), 0.7, 0.18, -1.5, 0.9, 1.6, 0.18, 0.1, 3)
    tf_pop()
    P_(11.9, 3.7, F1, 0)
    potted_plant(FUc, 0.6, 'white', False, 8)
    tf_pop()


def hq_master():
    G_(21.0, 31.0, F1)
    P_(21.0, 35.4, F1, 0)
    rug(FUc, 10.0, 10.5, 'cream', 'pink', 'coral', True)
    tf_pop()
    P_(21.0, 35.7, F1, 0)
    bed(FUc, 6.4, 9.2, 'coral', 'cream', 'wood2', ('white', 'cream'), 'white')
    tf_pop()
    for u in (16.5, 25.5):
        P_(u, 31.9, F1, 0)
        nightstand(FUc)
        tf_push(-0.45, 0.0, 2.44, 0)
        table_lamp(FUc, base='pink')
        tf_pop()
        tf_push(0.5, 0.35, 2.44, 10)
        rbox(FUc, MT('blue'), 0, 0, 0.0, 0.9, 0.2, 0.65, 0.04, 1)
        rbox(FUc, MT('yellow'), 0.05, 0, 0.2, 0.85, 0.16, 0.6, 0.04, 1)
        tf_pop()
        tf_pop()
    G_end()
    P_(25.0, 41.4, F1, 180)
    dresser(FUc, 3.3, 1.5, 3.7)
    tf_pop()
    P_(32.0, 36.7, F1, 90)
    wardrobe(FUc, 8.0, 3.5, 8.6, False)
    anchor('wardrobe_front', 0.0, 0.0, 1.75)
    anchor('wardrobe_hide', 1.7, 0.0, 0.0)
    tf_pop()
    P_(15.8, 41.0, F1, 0)
    floor_lamp(FUc)
    tf_pop()
    G_(21.0, 31.0, F1)
    for (u, w_, h_, col) in ((19.0, 2.8, 2.2, 'blue'), (23.0, 2.2, 3.0, 'yellow')):
        P_(u, 30.9, F1 + 7.0, 0)
        picture(FUc, w_, h_, col, 'brass', 'art')
        tf_pop()
    G_end()
    curtain_pair(FUc, HX + 20, 6.0, F1 + 8.3, 5.8, HZ + 41.7, 'x', 'pink')
    curtain_pair(FUc, HX + 30, 6.0, F1 + 8.3, 5.8, HZ + 41.7, 'x', 'pink')
    P_(28.9, 40.3, F1, 0)
    basket(FUc, 'wood2', True)
    tf_pop()


def hq_child():
    G_(24.0, 23.0, F1)
    P_(24.0, 23.0, F1, 0)
    rug(FUc, 10.0, 8.5, 'yellow', 'blue', 'red', False)
    tf_pop()
    G_end()
    P_(32.2, 22.2, F1, 0)
    bunk_bed(FUc, 3.8, 8.0)
    tf_pop()
    P_(17.5, 28.0, F1, 0)
    toy_chest(FUc)
    tf_pop()
    G_(26.6, 18.1, F1)
    P_(26.6, 18.1, F1, 0)
    desk(FUc, 5.6, 2.4, 2.9)
    tf_push(-0.3, 0.0, 2.9, 0)
    globe(FUc)
    tf_pop()
    tf_push(1.4, 0.2, 2.9, 0)
    table_lamp(FUc, base='yellow')
    tf_pop()
    for k, cc in enumerate(('red', 'blue', 'teal')):
        tf_push(-2.1, 0.3 + k * 0.0, 2.9 + k * 0.28, 5 * k)
        book(FUc, MT(cc), 0, 0, 0.0, 1.5, 0.26, 1.0)
        tf_pop()
    tf_pop()
    P_(26.4, 20.4, F1, 190)
    kid_chair(FUc, 'blue')
    tf_pop()
    # whiteboard + posters
    P_(26.8, 16.7, F1 + 6.5, 0)
    rbox(FUc, MT('trim'), 0, 0, -1.6, 7.0, 3.2, 0.2, 0.08, 2)
    rbox(FUc, MT('white'), 0, 0.08, -1.45, 6.7, 2.9, 0.08, 0.04, 1)
    rbox(FUc, MT('red'), -1.4, 0.15, -0.6, 2.4, 0.12, 0.05, 0.02, 1)
    rbox(FUc, MT('blue'), 1.0, 0.15, -1.1, 2.8, 0.12, 0.05, 0.02, 1)
    sphere(FUc, MT('yellow'), 2.5, 0.15, -0.3, 0.45, 0.45, 0.05, 12, 6)
    rbox(FUc, MT('trim'), 0, 0.25, -1.75, 3.0, 0.14, 0.34, 0.05, 1)
    tf_pop()
    G_end()
    for (v, w_, h_, col) in ((26.9, 2.4, 3.0, 'yellow'),):
        P_(14.65, v, F1 + 6.0, 90)
        picture(FUc, w_, h_, col, 'white', 'art')
        tf_pop()
    G_(24.0, 23.0, F1)
    ball_ = None
    for (u, v, r_, col) in ((21.0, 21.4, 0.85, 'red'), (22.6, 25.4, 0.55, 'blue')):
        X_, Z_ = pos_(u, v, F1)
        sphere(FUc, MT(col), X_, Z_, FH(F1) + r_, r_, r_, r_, 14, 9)
    for k, (u, v, col, rot_) in enumerate(((19.5, 24.4, 'blue', 20), (20.7, 24.0, 'yellow', -10), (20.0, 25.5, 'teal', 40), (21.0, 25.2, 'red', 5))):
        P_(u, v, F1, rot_)
        rbox(FUc, MT(col), 0, 0, 0.0, 1.1, 1.1, 1.1, 0.14, 2)
        tf_pop()
    G_end()
    curtain_pair(FUc, HZ + 23, 6.0, F1 + 8.2, 1.7, HX + 33.65, 'z', 'yellow')


def place_father():
    import os as _os
    glb = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', '..', 'characters', 'RegularDad_GLB', 'RegularDad_LowPoly.glb')
    glb = _os.path.normpath(glb)
    if not _os.path.exists(glb):
        return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    from mathutils import Matrix as _M
    _fx, _fz = pos_(21.0, 6.6, F1)
    ANCH['father'] = (_fx, FH(F1), _fz, 0.0, -1.0)
    T = _M.Translation((_fx, -_fz, FH(F1))) @ _M.Rotation(math.radians(180), 4, 'Z')
    for o in new:
        if o.parent is None:
            o.matrix_world = T @ o.matrix_world
    for o in new:
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        coll('Furn_U').objects.link(o)


def hq_lounge():
    G_(23.5, 7.0, F1)
    P_(23.5, 7.0, F1, 0)
    rug(FUc, 12.0, 9.5, 'orange', 'navy', 'yellow', True)
    tf_pop()
    P_(21.0, 3.9, F1, 0)
    round_table(FUc, 1.45, 2.7, 'wood2')
    tf_push(0.35, 0.1, 2.7, 0)
    mug(FUc, 'teal')
    tf_pop()
    tf_push(-0.5, -0.3, 2.7, 0)
    book(FUc, MT('red'), 0, 0, 0.0, 1.0, 0.2, 0.75)
    tf_pop()
    tf_pop()
    P_(17.4, 9.6, F1, -80)
    recliner(FUc)
    tf_pop()
    G_end()
    P_(28.5, 11.4, F1, 180)
    bookshelf(FUc, 6.0, 9.0, 1.5, 7, 5)
    tf_pop()
    P_(28.5, 14.0, F1, 0)
    anchor('niche', 0.0, 0.0, 0.0)
    tf_pop()
    P_(15.0, 5.5, F1 + 5.4, -90)
    rbox(FUc, MT('wood2'), 0, 0, 0.0, 6.2, 0.2, 1.0, 0.06, 2)
    for sx in (-2.4, 2.4):
        rbox(FUc, MT('metal'), sx, -0.1, -0.7, 0.14, 0.7, 0.7, 0.04, 1)
    for k, (cc, hh) in enumerate((('brass', 1.0), ('metal', 1.3), ('brass', 0.8), ('metal', 1.1), ('brass', 1.0))):
        tf_push(-2.4 + k * 1.2, 0.0, 0.2, 0)
        trophy(FUc, cc, hh)
        tf_pop()
    tf_pop()
    P_(32.5, 1.9, F1 + 5.9, 0)
    dartboard(FUc, 1.35)
    tf_pop()
    P_(33.1, 3.6, F1, 0)
    bar_cart(FUc)
    tf_pop()
    P_(15.6, 13.8, F1, 0)
    floor_lamp(FUc)
    tf_pop()
    P_(33.0, 8.4, F1, 0)
    potted_plant(FUc, 1.0, 'terra', True, 13)
    tf_pop()
    P_(34.4, 8.0, F1 + 5.5, -90)
    picture(FUc, 4.2, 3.4, 'purple', 'trim', 'art')
    tf_pop()
    G_(23.5, 7.0, F1)
    place_father()
    G_end()
    curtain_pair(FUc, HX + 21, 6.0, F1 + 8.3, 5.8, HZ + 2.3, 'x', 'orange')
    # balcony: table, two chairs, pots
    G_(25.0, -2.6, F1)
    P_(22.0, -2.6, F1, 0)
    round_table(FUc, 1.35, 2.6, 'white')
    tf_push(0.0, 0.0, 2.6, 0)
    vase_flowers(FUc, 'red', 5, 0.7)
    tf_pop()
    tf_pop()
    for (u, rot_) in ((19.3, 90), (24.7, -90)):
        P_(u, -2.6, F1, rot_)
        folding_chair(FUc)
        tf_pop()
    for (u, col) in ((29.6, 'red'), (31.0, 'teal')):
        P_(u, -3.6 if col == 'red' else -1.4, F1, 0)
        potted_plant(FUc, 0.7, col, False, 10)
        tf_pop()
    G_end()


exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yard_hq.py'), encoding='utf-8').read(), 'yard_hq.py', 'exec'))
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fill_hq.py'), encoding='utf-8').read(), 'fill_hq.py', 'exec'))
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rooms_extra.py'), encoding='utf-8').read(), 'rooms_extra.py', 'exec'))


def hq_furniture():
    hq_hall_stairs()
    hq_living()
    hq_dining()
    hq_kitchen()
    hq_laundry()
    hq_wc()
    hq_upper_hall_bath()
    hq_master()
    hq_child()
    hq_lounge()


def relink(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll('Yard').objects.link(o)


def tree(x, z, s):
    x, z = FX(x), FZ(z)
    for (cx, cz, r, h, col) in ((x, z, 1.0 * s, 0.0, 'leaf'), ):
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.9 * s, depth=9.0 * s, location=(cx, -cz, 4.5 * s))
        t = bpy.context.object
        t.data.materials.append(MT('trunk'))
        relink(t)
        for (dx, dy, dz, rad, c2) in ((0, 0, 11.5, 5.8, 'leaf'), (-2.2, 1.0, 9.6, 4.2, 'leaf2'), (2.4, -1.2, 10.4, 4.0, 'leaf2'), (0.4, 0.4, 14.2, 3.6, 'leaf')):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rad * s, location=(cx + dx * s, -cz + dy * s, dz * s))
            o = bpy.context.object
            o.data.materials.append(MT(c2))
            for p in o.data.polygons:
                p.use_smooth = True
            relink(o)


# ================================================================== scene, lights, cameras, render
def setup_scene():
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.render.image_settings.color_mode = 'RGB'
    try:
        sc.render.engine = 'BLENDER_EEVEE' if ENGINE == 'EEVEE' else 'CYCLES'
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    if ENGINE == 'EEVEE':
        try:
            sc.eevee.taa_render_samples = SAMPLES
            sc.eevee.use_shadows = True
            sc.eevee.use_raytracing = True
            for sz in ('4096', '2048'):
                try:
                    sc.eevee.shadow_pool_size = sz
                    break
                except Exception:
                    pass
        except Exception as e:
            print('eevee opts', e)
    else:
        sc.cycles.samples = SAMPLES
        sc.cycles.max_bounces = 6
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.sample_clamp_indirect = 8.0
        sc.cycles.use_denoising = True
        sc.cycles.device = 'CPU'
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
    except Exception:
        pass
    sc.view_settings.exposure = -0.2
    # world: sky
    w = bpy.data.worlds.new('World')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0.55, 0.82, 1.0, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (0.06, 0.40, 1.0, 1)
    cn = nt.nodes.new('ShaderNodeTexNoise')
    cn.inputs['Scale'].default_value = 2.2
    cn.inputs['Detail'].default_value = 7.0
    nt.links.new(tc.outputs['Generated'], cn.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.52
    cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(cn.outputs['Fac'], cr.inputs['Fac'])
    up = nt.nodes.new('ShaderNodeMath')
    up.operation = 'MULTIPLY'
    up.inputs[1].default_value = 2.5
    nt.links.new(sep.outputs['Z'], up.inputs[0])
    cl = nt.nodes.new('ShaderNodeMath')
    cl.operation = 'MULTIPLY'
    nt.links.new(cr.outputs['Color'], cl.inputs[0])
    nt.links.new(up.outputs['Value'], cl.inputs[1])
    cmx = nt.nodes.new('ShaderNodeMixRGB')
    cmx.inputs['Color2'].default_value = (1, 1, 1, 1)
    nt.links.new(cl.outputs['Value'], cmx.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], cmx.inputs['Color1'])
    nt.links.new(cmx.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.2
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    # sun from south-east, high
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 2.6
    sun.angle = math.radians(2.5)
    so = bpy.data.objects.new('Sun', sun)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(52), 0, math.radians(35))


def add_room_lights():
    # warm area lights below the ceiling of each room (plot coordinates u,v,h)
    spots = [('hall', 7.5, 33, F0 + 8.4, 800), ('living', 24.5, 32.5, F0 + 8.4, 1000), ('dining', 24.5, 11.5, F0 + 8.4, 900), ('kitchen', 7.5, 16, F0 + 8.4, 760),
             ('laundry', 10.5, 5.5, F0 + 8.4, 440), ('closet', 4, 5.5, F0 + 8.4, 240), ('uphall', 7.5, 24, F1 + 8.4, 800), ('uphall2', 7.5, 38, F1 + 8.4, 600), ('bed', 24.5, 36, F1 + 8.4, 840),
             ('kid', 24.5, 23, F1 + 8.4, 840), ('lounge', 24.5, 8.5, F1 + 8.4, 900), ('bath', 7, 5.5, F1 + 8.4, 440), ('wc', 31.5, 4.5, F0 + 8.4, 200)]
    for n, u, v, h, e in spots:
        li = bpy.data.lights.new(n, 'POINT')
        li.energy = e * 0.45 * KSX * KSZ
        li.color = (1.0, 0.97, 0.92)
        li.shadow_soft_size = 2.0
        ob = bpy.data.objects.new(n, li)
        ob.location = (FX(HX + u), -FZ(HZ + v), FH(h))
        bpy.context.scene.collection.objects.link(ob)
        ob.hide_render = False
        colls.setdefault('RoomLights', None)


CAM = None


def shot(name, loc, target=None, rot=None, lens=28, hide=(), fov_deg=None, exp=-0.2):
    sc = bpy.context.scene
    global CAM
    if CAM is None:
        cd = bpy.data.cameras.new('cam')
        CAM = bpy.data.objects.new('cam', cd)
        sc.collection.objects.link(CAM)
    sc.camera = CAM
    CAM.data.sensor_width = 36
    CAM.data.clip_start = 0.05
    CAM.data.clip_end = 600
    CAM.data.lens = lens if fov_deg is None else (18.0 / math.tan(math.radians(fov_deg / 2)))
    CAM.location = (loc[0], -loc[2], loc[1]) if False else loc
    if target is not None:
        d = Vector(target) - Vector(loc)
        CAM.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    else:
        CAM.rotation_euler = rot
    for cn in ('Roof', 'Upper', 'Furn_U', 'Ground', 'Furn_G', 'Lamps', 'Lamps_U'):
        if cn in colls and colls[cn]:
            colls[cn].hide_render = cn in hide
    sc.view_settings.exposure = exp
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 90
    sc.render.filepath = os.path.join(OUT, name + '.jpg')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)


def P3(x, z, h):
    """plot coords (x, z south, height) -> blender location"""
    return (FX(x), -FZ(z), FH(h))


def eye(u, v, floor, look):
    h = floor + 4.5
    loc = P3(HX + u, HZ + v, h)
    rot = {'N': (math.radians(90), 0, 0), 'E': (math.radians(90), 0, math.radians(-90)), 'S': (math.radians(90), 0, math.radians(180)), 'W': (math.radians(90), 0, math.radians(90))}[look]
    return loc, rot


def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    setup_scene()
    build()
    build_meshes()
    add_room_lights()
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'RegularDadHouse_V2_Concept.blend'))
    def PF(x, z, h):          # lot-relative camera point (follows the lot)
        return (x, -(z + DZ), h)

    def PS(x, z, h):          # fixed street / map point
        return (x, -z, h)

    shots = {
        'front': dict(loc=PF(128, 168, 40), target=PF(45, 80, 12), lens=26),
        'rear': dict(loc=PF(-34, -34, 42), target=PF(55, 50, 10), lens=24),
        'cut_ground': dict(loc=P3(98, 120, 98), target=P3(40, 38, 4), lens=30, hide=('Roof', 'Upper', 'Furn_U', 'Lamps_U')),
        'cut_upper': dict(loc=P3(98, 120, 98), target=P3(40, 38, 10), lens=30, hide=('Roof',)),
        'street': dict(loc=PS(58, 124, 6.0), target=PF(46, 80, 11), fov_deg=70),
        'porch': dict(loc=PF(50, 108, 8.5), target=PF(36, 88, 6.5), lens=30),
        'backyard': dict(loc=PF(84, 5, 9), target=PF(40, 12, 3.5), lens=24),
        'eastyard': dict(loc=PF(79, 6, 10), target=PF(92, 45, 3.5), lens=24),
        'westyard': dict(loc=PF(-6, 104, 30), target=PF(10, 38, 2), fov_deg=65),
        'balcony': dict(loc=PF(55, -17, 38), target=PF(55, 17, 18), fov_deg=70),
        'aerial': dict(loc=PS(52, 190, 150), target=PF(50, 40, 4), lens=26),
        'aerial2': dict(loc=PS(135, 60, 95), target=PF(45, 60, 4), lens=28),
    }
    def iv(u, v, fl, tu, tv, th, fov=95):
        return dict(loc=(FX(HX + u), -FZ(HZ + v), FH(fl) + 4.5), target=(FX(HX + tu), -FZ(HZ + tv), FH(th)), fov_deg=fov, exp=-0.28)

    shots.update({
        'hall': iv(9.5, 42, F0, 8.5, 12, F0 + 4.3),
        'living': iv(15.8, 33.5, F0, 34, 33, F0 + 3.6),
        'kitchen': iv(9.6, 20.9, F0, 4.5, 12.5, F0 + 3.4),
        'laundry': iv(10.5, 11.9, F0, 9.5, 2.0, F0 + 4.2, 92),
        'dining': iv(25, 20.5, F0, 25, 10, F0 + 3.4),
        'uphall': iv(9.5, 30, F1, 9.5, 12, F1 + 4.3),
        'bedroom': iv(28.5, 33.5, F1, 17.0, 38.0, F1 + 2.8, 95),
        'bedroom2': iv(16.0, 36.0, F1, 31.5, 37.0, F1 + 4.0, 95),
        'living2': iv(30.5, 35.0, F0, 14.8, 28.0, F0 + 3.5, 95),
        'kitchen2': iv(9.0, 20.8, F0, 4.6, 11.5, F0 + 3.4, 95),
        'bath': iv(7.0, 13.5, F1, 7.0, 3.0, F1 + 4.0, 95),
        'stairs': iv(3.8, 25.5, F1, 3.8, 42.0, F0 + 1.5, 95),
        'child2': iv(21.5, 28.5, F1, 33.0, 22.0, F1 + 3.0, 100),
        'lounge2': iv(26.0, 13.2, F1, 15.5, 6.0, F1 + 3.5, 100),
        'lounge3': iv(23.5, 14.2, F1, 33.2, 3.0, F1 + 4.0, 100),
        'child': iv(16.5, 28.0, F1, 30, 19.5, F1 + 3.5, 100),
        'lounge': iv(28, 12.5, F1, 21, 6, F1 + 3.4, 100),
    })
    for name, kw in shots.items():
        if WANT and name not in WANT:
            continue
        shot(name, **kw)


main()
