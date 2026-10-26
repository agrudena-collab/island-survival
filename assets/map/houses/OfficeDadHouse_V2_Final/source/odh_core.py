"""OfficeDadHouse_V2_Final -- core library: palette, geometry accumulator, primitives, wall/door helpers, logs.

Coordinates everywhere are PLOT space in studs: x east, h up, z toward the back yard (the street is at z = 0).
Blender space is X = x, Y = -z, Z = h (same convention as RegularDadHouse_V2_Final, so the Roblox export pipeline is unchanged).
Geometry is only accumulated here (acc); build_odh.py turns it into Blender objects (render) and export_roblox.py into FBX chunks.
"""
import bpy
import bmesh
import math
import random
import sys
from mathutils import Vector

# ------------------------------------------------------------------ house frame
HX, HZ = 40.0, 16.0            # house origin (plot): u = x - HX, v = z - HZ
W, D = 54.0, 67.0              # main body footprint (u 0..W, v 0..D)
F1, F2 = 1.0, 14.75            # floor tops: ground floor / upper floor
CH = 12.5                      # clear height of a storey
CEIL1 = F1 + CH                # 13.5  underside of the upper slab
CEIL2 = F2 + CH                # 27.25 underside of the roof slab
SLAB = CEIL1 - 0.0             # slab occupies CEIL1 .. F2-0.5 (floor finish 0.5 on top)
TEXT, TINT = 1.5, 1.0          # exterior / interior wall thickness
DOOR_W, DOOR_H = 5.6, 9.6      # interior door opening (>= 5 studs wide, md: first-person)
EXT_W = 6.4                    # exterior door opening

# ------------------------------------------------------------------ palette (sRGB hex).  Office Dad: grey stucco, navy flat roofs, white trim, brown wood.
# Names are a superset of the RegularDadHouse_V2 palette so the ported furniture / yard models keep working; values are Office Dad's muted look.
P = dict(
    stucco='#CBC7BF', stucco_dk='#B4B0A8', trim='#F0EEE8', roof='#4A5878', roof_dk='#394560', parapet='#E3E0D8', siding='#CBC7BF', siding_dk='#B4B0A8',
    wood='#8B6A4A', wood_dk='#5E4630', wood_lt='#B28D63', wood2='#A27B54', door='#7A5638', door2='#6E4B30', doorin='#9A7650', floor='#B89066', floor2='#A57F57',
    floor_wood='#B89066', floor_wood2='#A57F57',
    tile='#D7D2C6', tile_dk='#9FA8AA', tile_k='#CFC8B6', tile_b='#BFD3D6', tile_l='#C5D2D8', concrete='#A8A8A4', asphalt='#4B4E55', road='#4B4E55', curb='#C4C2BC',
    walk='#CFCBC0', path='#CFCBC0', plinth='#B2AEA4', gravel='#B7B1A3', lawn='#7FA46A', lawn2='#74996A', hedge='#4F7A47', soil='#5A4331', trunk='#6B4E36',
    leaf='#4F8346', leaf2='#6F9F55', foliage='#5B8A4E', foliage2='#7DA85F', cherry='#D9A0B3', cherry2='#E8BFCC', autumn='#C98A3C', autumn2='#B8623A',
    glass='#BFDCE6', ceiling='#F6F4EE', skirt='#ECE9E1', black='#25262B', dark='#3A3C42', metal='#BFC5CA', metal_dk='#7E868C', steel='#9AA3AA',
    wall_hall='#E5DDCF', wall_liv='#D8DCE2', wall_kit='#EADFC4', wall_din='#DFD3C2', wall_lau='#CFDDE2', wall_wc='#D3E3E0', wall_lib='#C9D2C4', wall_gar='#BDBAB2',
    wall_bed='#E3D6D8', wall_bath='#D5E4E6', wall_kid='#CFDDEF', wall_lng='#C8D6D2', wall_gst='#E1DAC8', wall_off='#CBD1DC', wall_uph='#E9E4D8', wall_lounge='#C8D6D2',
    sofa='#40608E', sofa2='#2F4A70', burg='#6B2B35', cream='#EFE6D0', navy='#2B3A5C', teal='#3E8C8A', coral='#C9705E', mustard='#C9A64A', olive='#7C8450',
    white='#F4F3EE', paper='#E6E3D8', screen='#1B1F27', cab='#E8E3D6', cab_dk='#7B6A58', counter='#B7A58D', brass='#C9A24B', red='#A9413A', yellow='#D8B84E',
    orange='#CF7E43', pink='#D8A1B1', purple='#74589B', blue='#4A7DB5', green='#5A9657', lamp='#FFE8B0', lampshade='#F2E2B8', mirror='#CFE3EA', terra='#B5684A',
    skin='#E8B58C', hair='#4A3322', jeans='#3C5E9B', cardboard='#C9A06E', car='#2F4B73', car_dk='#22344F', tire='#1F2024', chrome='#D3D8DC', fence='#E9E6DD',
    fence_dk='#8D8A82', line='#E2CC6A', shutter='#5B6F8E', chimney='#9A6A58', sky='#9CC4E4',
)
# vivid palette in the manner of RegularDadHouse_V2_Final (saturated Roblox colours; office identity kept: blue flat roof, white trim, blue-grey stucco)
P.update(
    walk_b='#E4E7EB', walk_c='#D3D8DE', walk_dk='#AEB5BE', curb_top='#F2F4F6', gutter='#3B3F47', brick='#C4633F', brick_dk='#A44C30', stone='#DCD0BB', stone_dk='#B8AB95',
    flower_r='#F0405A', flower_y='#FFD23A', flower_p='#B568E0', curtain_a='#F6E6C8', curtain_b='#F2C6CE', curtain_c='#C8E0F2', leaf3='#7ED05C', sign_green='#1F7A4D', sign_red='#D8342F', tactile='#F4C430',
    stucco='#A9CBEA', stucco_dk='#8FB5DB', trim='#FFFFFF', roof='#2D58B0', roof_dk='#24479A', parapet='#F6F4EC', siding='#A9CBEA', siding_dk='#8FB5DB',
    wood='#9A6A3A', wood_dk='#6B4524', wood_lt='#C8935A', wood2='#B87C45', door='#8A4E2A', door2='#7C4524', doorin='#B27A45',
    floor='#E0A24E', floor2='#CC8A3C', floor_wood='#E3A653', floor_wood2='#CF8E3E', tile='#F2EBD6', tile_dk='#8FB4C0', tile_k='#F4E4B4', tile_b='#A8DCE6', tile_l='#BBE0EA',
    concrete='#B9BAB6', asphalt='#464B58', road='#464B58', curb='#D6D4CC', walk='#DAD7CE', path='#DAD7CE', plinth='#C6C2B8', gravel='#CDC6B0',
    lawn='#5BC247', lawn2='#4EB23C', hedge='#2C9A3A', soil='#6A4A30', trunk='#7A5232',
    leaf='#2FA84A', leaf2='#4DC252', foliage='#34B04A', foliage2='#5AC65A', cherry='#F28CC0', cherry2='#F8BAD8', autumn='#F59A2C', autumn2='#E2582E',
    glass='#BFE4F4', ceiling='#FBFAF4', skirt='#FFFFFF', floor_a='#C98534', floor_b='#EDB566', tile_a='#E6D6A6',
    wall_hall='#F8DCA6', wall_liv='#F4A98A', wall_kit='#FCE288', wall_din='#F2B58A', wall_lau='#9AD9DA', wall_wc='#A4E0D0', wall_lib='#A9D88C', wall_gar='#C9C6BC',
    wall_bed='#F4B0C4', wall_bath='#98D8EC', wall_kid='#8CC6F4', wall_lng='#A6E0B6', wall_gst='#F6D88A', wall_off='#9CB8EC', wall_uph='#FBE6B0', wall_lounge='#B4E2AE',
    sofa='#2E7FD0', sofa2='#2060B8', burg='#BE2A40', navy='#2C4C94', teal='#12AC9C', coral='#F4705C', mustard='#F4BA3A', olive='#8CBA3A',
    white='#FFFFFF', cab='#F9F2DF', cab_dk='#8A6A4A', counter='#E0B67A', brass='#E0B040', red='#E43A2E', yellow='#F8D030', orange='#F58A2A',
    pink='#F48CB2', purple='#8C60D4', blue='#3A88E4', green='#3CB44E', car='#2F63B8', car_dk='#234A8F', fence='#FFFFFF', shutter='#E0503C', sky='#7DBCF2',
)
GLASS_COLORS = ('glass', 'mirror')
NEON_COLORS = ('lamp',)

# ------------------------------------------------------------------ accumulator
acc = {}            # (collection, colorname) -> ([verts], [faces])   verts in Blender coords
BOXLOG = []         # solid architecture boxes: (coll, color, x0, x1, h0, h1, z0, z1) plot coords
DOORLOG = []        # doors / openings, see door()
WINLOG = []         # windows (for audits and renders)
ANCH = {}           # gameplay anchors: name -> (x, h, z, fx, fz)
COVER = []          # low-cover proxies: (name, x, floor_y, z, w, d, h, yaw)
COLL = []           # yard colliders: (kind, x, z, y0, h, a, b, yaw)  kind box/cyl
ROUTES = []         # family routes: (role, index, x, floor_y, z, pause, activity)
FURN_LOG = []       # placed furniture footprints for audits: (room, name, x0,x1,z0,z1,h0,h1)

_TF = []


def hexrgb(h):
    h = h.lstrip('#')[:6]
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def col(c):
    return P[c] if c in P else c


def coll_for(c, h0):
    """architecture goes to Ground/Upper by height so the render cut-aways can hide whole storeys"""
    if c == 'Arch':
        return 'Upper' if h0 >= CEIL1 - 0.01 else 'Ground'
    return c


BIOME_SOLID_COL = ('plinth', 'stone', 'stone_dk', 'concrete', 'trim', 'brick', 'wood', 'wood2', 'metal', 'metal_dk',
                   'stucco', 'stucco_dk', 'wall_hall', 'wall_uph', 'wall_liv', 'siding')


def B(c, color, x0, x1, h0, h1, z0, z1, solid=None):
    """axis aligned box in plot coordinates"""
    if x1 < x0:
        x0, x1 = x1, x0
    if h1 < h0:
        h0, h1 = h1, h0
    if z1 < z0:
        z0, z1 = z1, z0
    assert x1 - x0 > 1e-6 and h1 - h0 > 1e-6 and z1 - z0 > 1e-6, (c, color, x0, x1, h0, h1, z0, z1)
    c = coll_for(c, h0)
    if solid is None:
        solid = c in ('Ground', 'Upper', 'Roof', 'Site') and color not in ('trim', 'skirt', 'brass', 'lamp', 'parapet_trim')
        if not solid and c == 'Biome' and h0 < 8.0 and h1 - h0 >= 0.3 and color in BIOME_SOLID_COL:
            solid = True    # plinths, porch platforms, steps, columns, window sills of the neighbour buildings: the player must not sink into them
    if solid:
        BOXLOG.append((c, color, x0, x1, h0, h1, z0, z1))
    y0, y1 = -z1, -z0
    v = [(x0, y0, h0), (x1, y0, h0), (x1, y1, h0), (x0, y1, h0), (x0, y0, h1), (x1, y0, h1), (x1, y1, h1), (x0, y1, h1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    vs, fs = acc.setdefault((c, color), ([], []))
    base = len(vs)
    vs.extend(v)
    fs.extend([tuple(base + i for i in face) for face in f])


def HB(c, color, u0, u1, h0, h1, v0, v1, solid=None):
    B(c, color, HX + u0, HX + u1, h0, h1, HZ + v0, HZ + v1, solid)


def prism(c, color, pts, x0, x1, solid=False):
    """triangular/poly prism extruded along x; pts = [(z, h), ...] CCW seen from +x"""
    n = len(pts)
    verts = [(x0, -z, h) for z, h in pts] + [(x1, -z, h) for z, h in pts]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    vs, fs = acc.setdefault((c, color), ([], []))
    base = len(vs)
    vs.extend(verts)
    fs.extend([tuple(base + i for i in f) for f in faces])


# ------------------------------------------------------------------ local frame transform for modelled objects
# yard / street objects that get an auto-fitted collision box from their real geometry: name -> max height counted (None = whole object)
OBJ_COLL = {'bush': None, 'hedge': None, 'bench': 3.5, 'mailbox': None, 'hydrant': None, 'trash_can': None, 'bbq': 5.5, 'raised_bed': None,
            'birdbath': 4.5, 'picnic_table': 3.4, 'doghouse': None, 'planter': None, 'bollard': None, 'lamp_post': 6.0, 'stop_sign': 5.0, 'street_sign': 5.0}
_REC = []           # one entry per open tf_push: None, or [name, [(x, z, h)]] for the outermost frame of a collidable object


def _obj_name():
    f = sys._getframe(2)
    n = f.f_code.co_name
    if n in ('place', 'pl'):
        fn = f.f_locals.get('fn')
        n = getattr(fn, '__name__', n)
    return n


def tf_push(x, z, y0=0.0, rot=0.0):
    """push a local frame (lx right, h up, lz forward); composes with the current one. rot in degrees about vertical"""
    nm = _obj_name() if not _TF else None
    _REC.append([nm, []] if nm in OBJ_COLL else None)
    a = math.radians(rot)
    if _TF:
        px, pz, py, pc, ps = _TF[-1]
        wx = px + x * pc - z * ps
        wz = pz + x * ps + z * pc
        pa = math.atan2(ps, pc) + a
        _TF.append((wx, wz, py + y0, math.cos(pa), math.sin(pa)))
    else:
        _TF.append((x, z, y0, math.cos(a), math.sin(a)))


def tf_pop():
    _TF.pop()
    rec = _REC.pop() if _REC else None
    if rec and rec[1]:
        cap = OBJ_COLL[rec[0]]
        pts = [p for p in rec[1] if cap is None or p[2] <= cap] or []
        if pts:
            x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
            z0, z1 = min(p[1] for p in pts), max(p[1] for p in pts)
            h = max(p[2] for p in pts)
            if h >= 0.8:
                COLL.append(('box', (x0 + x1) / 2, (z0 + z1) / 2, max(x1 - x0, 0.9), max(z1 - z0, 0.9), h))


def tf_top():
    return _TF[-1] if _TF else (0.0, 0.0, 0.0, 1.0, 0.0)


def _t(lx, h, lz):
    if not _TF:
        return (lx, h, lz)
    x, z, y0, c, s = _TF[-1]
    return (x + lx * c - lz * s, h + y0, z + lx * s + lz * c)


def emit(c, color, verts, faces, two_sided=False):
    vs, fs = acc.setdefault((c, color), ([], []))
    base = len(vs)
    rec = _REC[0] if _REC else None
    for (lx, h, lz) in verts:
        px, ph, pz = _t(lx, h, lz)
        vs.append((px, -pz, ph))
        if rec:
            rec[1].append((px, pz, ph))
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


CUR = ['Furn_G']      # current collection for furniture helpers


def rbox(color, cx, cz, y0, sx, sy, sz, r=0.1, seg=2, c=None):
    """rounded box centred on (cx, cz) with base at y0 (local frame)"""
    r = max(0.001, min(r, 0.46 * min(sx, sy, sz)))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = cx + v.co.x * sx
        v.co.y = y0 + sy / 2 + v.co.y * sy
        v.co.z = cz + v.co.z * sz
    bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=r, offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES')
    v, f = _bm_out(bm)
    emit(c or CUR[0], color, v, f)


def box(color, cx, cz, y0, sx, sy, sz, c=None):
    """sharp box centred on (cx, cz) in the local frame (rotation aware)"""
    hx, hz = sx / 2, sz / 2
    v = [(cx - hx, y0, cz - hz), (cx + hx, y0, cz - hz), (cx + hx, y0, cz + hz), (cx - hx, y0, cz + hz),
         (cx - hx, y0 + sy, cz - hz), (cx + hx, y0 + sy, cz - hz), (cx + hx, y0 + sy, cz + hz), (cx - hx, y0 + sy, cz + hz)]
    # emit() maps (lx, h, lz); mirror of B's winding for outward normals after the y flip
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    emit(c or CUR[0], color, v, f)


def lathe(color, prof, cx, cz, y0=0.0, seg=20, sx=1.0, sz=1.0, caps=True, c=None):
    """revolve [(radius, height), ...] about the vertical axis through (cx, cz)"""
    verts, rings = [], []
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
    emit(c or CUR[0], color, verts, faces)


def cyl(color, cx, cz, y0, h, r, seg=18, r2=None, c=None):
    lathe(color, [(r, 0.0), (r if r2 is None else r2, h)], cx, cz, y0, seg, c=c)


def sphere(color, cx, cz, cy, rx, ry=None, rz=None, seg=16, rings=9, c=None):
    ry = ry or rx
    rz = rz or rx
    prof = []
    for k in range(rings + 1):
        a = math.pi * k / rings
        prof.append((math.sin(a), cy - ry * math.cos(a)))
    lathe(color, prof, cx, cz, 0.0, seg, sx=rx, sz=rz, caps=False, c=c)


def tube(color, pts, r, seg=8, closed=False, caps=True, r_end=None, c=None):
    n = len(pts)
    P_ = [Vector(p) for p in pts]
    up = Vector((0, 1, 0))
    rings, verts = [], []
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
    emit(c or CUR[0], color, verts, faces)


def rod(color, x0, y0, z0, x1, y1, z1, r=0.08, seg=6, c=None):
    tube(color, [(x0, y0, z0), (x1, y1, z1)], r, seg, c=c)


def torus(color, cx, cz, cy, R, r, plane='xz', seg=24, tseg=7, c=None):
    pts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        if plane == 'xz':
            pts.append((cx + R * math.cos(a), cy, cz + R * math.sin(a)))
        elif plane == 'xy':
            pts.append((cx + R * math.cos(a), cy + R * math.sin(a), cz))
        else:
            pts.append((cx, cy + R * math.sin(a), cz + R * math.cos(a)))
    tube(color, pts, r, tseg, closed=True, c=c)


def leaf(color, bx, bh, bz, ang, length, width, lift=0.6, droop=0.9, n=5, c=None):
    dx, dz = math.cos(ang), math.sin(ang)
    verts = []
    for i in range(n + 1):
        u = i / n
        w = width * math.sin(math.pi * (u ** 0.75)) * 0.5
        cxp, czp = bx + dx * length * u, bz + dz * length * u
        ch = bh + length * (lift * u - droop * u * u * 0.7)
        for sgn in (-1, 1):
            verts.append((cxp - dz * w * sgn, ch, czp + dx * w * sgn))
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(n)]
    emit(c or CUR[0], color, verts, faces, two_sided=True)


def sheet(color, x0, x1, y0, y1, z, folds=6, amp=0.16, nx=28, axis='x', c=None):
    verts = []
    for i in range(nx + 1):
        u = i / nx
        for j in (0, 1):
            h = y0 + (y1 - y0) * j
            off = amp * math.sin(2 * math.pi * folds * u) * (1 - 0.35 * j)
            verts.append((x0 + (x1 - x0) * u, h, z + off) if axis == 'x' else (z + off, h, x0 + (x1 - x0) * u))
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(nx)]
    emit(c or CUR[0], color, verts, faces, two_sided=True)


def wedge(color, pts_xz, y0, y1, c=None):
    """polygon prism from a footprint polygon [(lx, lz), ...] (CCW seen from above in plot space) between heights y0 and y1"""
    n = len(pts_xz)
    verts = [(x, y0, z) for x, z in pts_xz] + [(x, y1, z) for x, z in pts_xz]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    emit(c or CUR[0], color, verts, faces)


def finish_mesh(me, angle_deg=38.0, flat=False):
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
        p.use_smooth = not flat


# ------------------------------------------------------------------ openings
def _ops(doors, wins, h0):
    return sorted([(d[0] - d[1] / 2, d[0] + d[1] / 2, h0, h0 + d[2]) for d in doors] +
                  [(w[0] - w[1] / 2, w[0] + w[1] / 2, h0 + w[2], h0 + w[3]) for w in wins])


def wall_x(c, ca, cb, x0, x1, zc, th, h0, h1, doors=(), wins=(), split=0.5):
    """wall along x, centred on z = zc.  ca = colour of the z-low face, cb = colour of the z-high face (two layers).
    doors: (xc, w, h);  wins: (xc, w, sill, top) -- heights relative to h0"""
    z0, z1 = zc - th / 2, zc + th / 2
    zm = z0 + th * split
    for (colr, za, zb) in ((ca, z0, zm), (cb, zm, z1)):
        cur = x0
        for a, b, o0, o1 in _ops(doors, wins, h0):
            if a - cur > 0.01:
                B(c, colr, cur, a, h0, h1, za, zb)
            if o1 < h1 - 0.01:
                B(c, colr, a, b, o1, h1, za, zb)
            if o0 > h0 + 0.01:
                B(c, colr, a, b, h0, o0, za, zb)
            cur = b
        if x1 - cur > 0.01:
            B(c, colr, cur, x1, h0, h1, za, zb)


def wall_z(c, ca, cb, z0, z1, xc, th, h0, h1, doors=(), wins=(), split=0.5):
    """wall along z, centred on x = xc.  ca = colour of the x-low face, cb = x-high face"""
    x0, x1 = xc - th / 2, xc + th / 2
    xm = x0 + th * split
    for (colr, xa, xb) in ((ca, x0, xm), (cb, xm, x1)):
        cur = z0
        for a, b, o0, o1 in _ops(doors, wins, h0):
            if a - cur > 0.01:
                B(c, colr, xa, xb, h0, h1, cur, a)
            if o1 < h1 - 0.01:
                B(c, colr, xa, xb, o1, h1, a, b)
            if o0 > h0 + 0.01:
                B(c, colr, xa, xb, h0, o0, a, b)
            cur = b
        if z1 - cur > 0.01:
            B(c, colr, xa, xb, h0, h1, cur, z1)


def frame_x(c, xc, w, h0, hh, zc, th, trim='trim', pad=0.4, depth=0.25, sill=False):
    z0, z1 = zc - th / 2 - depth, zc + th / 2 + depth
    xa, xb = xc - w / 2, xc + w / 2
    B(c, trim, xa - pad, xa, h0, h0 + hh, z0, z1)
    B(c, trim, xb, xb + pad, h0, h0 + hh, z0, z1)
    B(c, trim, xa - pad, xb + pad, h0 + hh, h0 + hh + pad, z0, z1)
    if sill:
        B(c, trim, xa - pad, xb + pad, h0 - pad, h0, z0, z1)


def frame_z(c, zc, w, h0, hh, xc, th, trim='trim', pad=0.4, depth=0.25, sill=False):
    x0, x1 = xc - th / 2 - depth, xc + th / 2 + depth
    za, zb = zc - w / 2, zc + w / 2
    B(c, trim, x0, x1, h0, h0 + hh, za - pad, za)
    B(c, trim, x0, x1, h0, h0 + hh, zb, zb + pad)
    B(c, trim, x0, x1, h0 + hh, h0 + hh + pad, za - pad, zb + pad)
    if sill:
        B(c, trim, x0, x1, h0 - pad, h0, za - pad, zb + pad)


def window_x(c, xc, w, h0, sill, top, zc, th, glass='glass', mullions=2):
    """window in a wall along x: glass pane, frame and mullions"""
    a0, a1 = h0 + sill, h0 + top
    frame_x(c, xc, w, a0, a1 - a0, zc, th, sill=True)
    B(c, glass, xc - w / 2, xc + w / 2, a0, a1, zc - 0.06, zc + 0.06, solid=True)
    for k in range(1, mullions):
        xm = xc - w / 2 + w * k / mullions
        B(c, 'trim', xm - 0.1, xm + 0.1, a0, a1, zc - th / 2 - 0.12, zc + th / 2 + 0.12, solid=False)
    B(c, 'trim', xc - w / 2, xc + w / 2, (a0 + a1) / 2 - 0.1, (a0 + a1) / 2 + 0.1, zc - th / 2 - 0.12, zc + th / 2 + 0.12, solid=False)
    WINLOG.append(('x', xc, w, a0, a1, zc, th))


def window_z(c, zc, w, h0, sill, top, xc, th, glass='glass', mullions=2):
    a0, a1 = h0 + sill, h0 + top
    frame_z(c, zc, w, a0, a1 - a0, xc, th, sill=True)
    B(c, glass, xc - 0.06, xc + 0.06, a0, a1, zc - w / 2, zc + w / 2, solid=True)
    for k in range(1, mullions):
        zm = zc - w / 2 + w * k / mullions
        B(c, 'trim', xc - th / 2 - 0.12, xc + th / 2 + 0.12, a0, a1, zm - 0.1, zm + 0.1, solid=False)
    B(c, 'trim', xc - th / 2 - 0.12, xc + th / 2 + 0.12, (a0 + a1) / 2 - 0.1, (a0 + a1) / 2 + 0.1, zc - w / 2, zc + w / 2, solid=False)
    WINLOG.append(('z', zc, w, a0, a1, xc, th))


def door(did, kind, axis, ctr, w, h0, hh, wall, th, inside, hinge='low', swing=1, locked=False, item=None, leaf_col='door', trim=True, frame_c='Arch'):
    """register a door opening and (optionally) draw its trim.  inside = unit vector (dx, dz) pointing into the house.
    hinge: 'low' hinge at the low coordinate side of the opening, 'high' at the high side.  swing: +1/-1 which way the leaf opens."""
    DOORLOG.append(dict(id=did, kind=kind, axis=axis, ctr=ctr, w=w, y0=h0, h=hh, wall=wall, th=th, inside=list(inside), hinge=hinge,
                        swing=swing, locked=locked, item=item, leaf=leaf_col))
    if trim:
        if axis == 'x':
            frame_x(frame_c, ctr, w, h0, hh, wall, th)
        else:
            frame_z(frame_c, ctr, w, h0, hh, wall, th)


def anchor_w(name, x, h, z, fx=0.0, fz=1.0):
    ANCH[name] = (x, h, z, fx, fz)


def cover(name, w, d, h, lx=0.0, lz=0.0):
    """vision-only proxy box for a low piece of furniture: footprint w x d centred at local (lx, lz), h above the local floor"""
    p = _t(lx, 0.0, lz)
    yaw = math.atan2(_TF[-1][4], _TF[-1][3]) if _TF else 0.0
    COVER.append((name, p[0], p[1], p[2], w, d, h, yaw))


def anchor(name, lx, h, lz):
    p = _t(lx, h, lz)
    f = (-_TF[-1][4], _TF[-1][3]) if _TF else (0.0, 1.0)
    ANCH[name] = (p[0], p[1], p[2], f[0], f[1])


def cbox(x0, x1, h0, h1, z0, z1, name='cbox'):
    """collision-only box (no geometry): big pieces of furniture that must block movement and sight"""
    if x1 < x0:
        x0, x1 = x1, x0
    if z1 < z0:
        z0, z1 = z1, z0
    BOXLOG.append(('Ground' if h0 < CEIL1 - 0.01 else 'Upper', name, x0, x1, h0, h1, z0, z1))


def lcbox(lx, lz, sx, sz, h, name='cbox'):
    """collision-only box from the current local frame (axis aligned only: rotation must be a multiple of 90 degrees)"""
    x, z, y0, c, s = tf_top()
    wx = x + lx * c - lz * s
    wz = z + lx * s + lz * c
    if abs(s) > 0.5:
        sx, sz = sz, sx
    cbox(wx - sx / 2, wx + sx / 2, y0, y0 + h, wz - sz / 2, wz + sz / 2, name)
