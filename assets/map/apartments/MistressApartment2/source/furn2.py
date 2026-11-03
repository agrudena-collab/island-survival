# Furniture and decor of flat 2 (exec'd by build_flat2.py).  Every piece is built in its own local frame F(face, x, z) and gets a collider with a name.
def CY_add(x, y, z, d, h, name):
    CYLC.append((x, y, z, d, h, name))


def wb(n, px, y0, pz, w, h, d, col, off=0.0, kind='O'):
    """box on a wall. n = direction the wall faces (into the room); (px, pz) = point on the wall plane; w along the wall, d out of it"""
    if n == 'S':
        box(px - w / 2, px + w / 2, y0, y0 + h, pz + off, pz + off + d, col, kind)
    elif n == 'N':
        box(px - w / 2, px + w / 2, y0, y0 + h, pz - off - d, pz - off, col, kind)
    elif n == 'E':
        box(px + off, px + off + d, y0, y0 + h, pz - w / 2, pz + w / 2, col, kind)
    else:
        box(px - off - d, px - off, y0, y0 + h, pz - w / 2, pz + w / 2, col, kind)


def art(n, px, y0, pz, w, h, seed, frame=None):
    """framed abstract print on a wall (frame, mat, three colour blocks); (px, pz) = wall plane point, w runs along the wall"""
    r = rnd_of(seed)
    frame = frame or P['white']
    alongx = n in 'NS'

    def blk(du, y, ww, hh, d, col, off):
        if alongx:
            wb(n, px + du, y, pz, ww, hh, d, col, off)
        else:
            wb(n, px, y, pz + du, ww, hh, d, col, off)

    blk(0.0, y0, w, h, 0.25, frame, 0.0)
    blk(0.0, y0 + 0.25, w - 0.5, h - 0.5, 0.05, P['cream'], 0.25)
    cols = [P['red'], P['navy'], P['mustard'], P['teal'], P['coral'], P['blue']]
    cu = [r.choice(cols) for _ in range(3)]
    ww, hh = w - 1.4, h - 1.4
    blk(-ww * 0.2, y0 + 0.7, ww * 0.55, hh * 0.9, 0.03, cu[0], 0.30)
    blk(ww * 0.28, y0 + 0.7 + hh * 0.35, ww * 0.42, hh * 0.55, 0.03, cu[1], 0.30)
    blk(ww * 0.28, y0 + 0.7, ww * 0.3, hh * 0.28, 0.06, cu[2], 0.30)


def clock(n, px, y, pz, r=1.4):
    x, z = px, pz
    if n in 'NS':
        hcyl(x, y, z + (0.15 if n == 'S' else -0.15), 'z', 0.3, r, P['white'], seg=24)
        hcyl(x, y, z + (0.34 if n == 'S' else -0.34), 'z', 0.08, r * 0.92, P['cream'], seg=24)
        sgn = 1 if n == 'S' else -1
        box(x - 0.06, x + 0.06, y, y + r * 0.7, z + sgn * 0.4, z + sgn * 0.46, P['black'])
        box(x, x + r * 0.5, y - 0.05, y + 0.05, z + sgn * 0.4, z + sgn * 0.46, P['black'])
    else:
        hcyl(x + (0.15 if n == 'E' else -0.15), y, z, 'x', 0.3, r, P['white'], seg=24)
        hcyl(x + (0.34 if n == 'E' else -0.34), y, z, 'x', 0.08, r * 0.92, P['cream'], seg=24)


# ------------------------------------------------------------------------------------------------------------------------------------- seating
def chair(face, ox, oz, col, seat, name='chair'):
    f = F(face, ox, oz)
    for (u, w) in ((-0.9, -0.9), (0.9, -0.9), (-0.9, 0.9), (0.9, 0.9)):
        f.b(u - 0.14, u + 0.14, FY, FY + 2.0, w - 0.14, w + 0.14, P['walnut'])
    f.b(-1.1, 1.1, FY + 2.0, FY + 2.3, -1.1, 1.1, P['walnut'])
    f.b(-0.95, 0.95, FY + 2.3, FY + 2.55, -0.95, 0.95, seat)
    f.b(-1.1, -0.85, FY + 2.3, FY + 4.7, -1.1, -0.85, P['walnut'])
    f.b(-1.0, 1.0, FY + 2.9, FY + 4.5, -1.05, -0.9, col)
    f.b(1.0, 1.1, FY + 2.3, FY + 4.7, -1.1, -0.85, P['walnut'])
    # colliders: backrest + seat block up to the seat surface (z -0.85..1.1); the GuestSeat anchor sits ON the block top (FY + 2.55), not inside a solid
    # box, so the guest can walk up to the chair from any side and sit on the surface (the old full-height box swallowed the anchor)
    f.col(name, -1.1, 1.1, FY, FY + 4.7, -1.1, -0.85)
    f.col(name + '_seat', -1.1, 1.1, FY, FY + 2.55, -0.85, 1.1)


def office_chair(face, ox, oz, col, name='office_chair'):
    f = F(face, ox, oz)
    for k in range(5):
        a = k * 72.0 + 15
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        x, z = f.p(ca * 0.9, sa * 0.9)
        cbox(x, FY + 0.45, z, 1.8, 0.14, 0.26, P['charcoal'], rot=-a if face in 'NS' else -a + 90)
        xe, ze = f.p(ca * 1.75, sa * 1.75)
        D.sphere(xe, FY + 0.32, ze, 0.32, 0.32, 0.32, P['black'], seg=8, rings=5)
    f.cyl(0, 0, FY + 0.5, FY + 2.2, 0.26, P['metal2'], seg=10)
    f.b(-1.45, 1.45, FY + 2.2, FY + 2.55, -1.45, 1.45, P['charcoal'])
    f.b(-1.35, 1.35, FY + 2.55, FY + 3.05, -1.35, 1.35, col)
    f.b(-1.25, 1.25, FY + 3.05, FY + 3.2, -1.25, 1.25, shade(col, 0.1))
    f.b(-1.3, 1.3, FY + 3.2, FY + 6.3, -1.55, -1.25, col)
    f.b(-1.0, 1.0, FY + 6.3, FY + 7.0, -1.58, -1.28, shade(col, -0.12))
    for s in (-1, 1):
        f.b(s * 1.45 - 0.12, s * 1.45 + 0.12, FY + 3.05, FY + 4.3, -0.9, -0.7, P['metal2'])
        f.b(s * 1.45 - 0.2, s * 1.45 + 0.2, FY + 4.3, FY + 4.55, -1.0, 0.7, P['charcoal'])
    f.col(name, -1.75, 1.75, FY, FY + 7.0, -1.75, 1.75)


def stool(x, z, col, name='stool', h=3.4):
    cyl(x, z, FY + h - 0.35, FY + h, 0.95, col, seg=18)
    cyl(x, z, FY + h - 0.45, FY + h - 0.35, 0.8, P['charcoal'], seg=14)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        hx, hz = x + math.cos(a) * 0.62, z + math.sin(a) * 0.62
        box(hx - 0.1, hx + 0.1, FY, FY + h - 0.45, hz - 0.1, hz + 0.1, P['metal'])
    D.lathe(x, z, FY + 1.3, [(0.62, 0), (0.62, 0.12)], P['metal'], seg=12)
    CY_add(x, FY + h / 2, z, 1.9, h, name)


def sofa(face, ox, oz, seats, col, cush, name='sofa', chaise=False, pillow_cols=None):
    """straight sofa centred on (ox, oz) (oz = front edge when facing); width 3.8 per seat + arms; optional chaise on the right end"""
    f = F(face, ox, oz)
    w_in = 3.9 * seats
    half = w_in / 2 + 1.0
    d = 3.8
    f.b(-half, half, FY + 0.45, FY + 1.5, -d, 0, col)                                 # base
    for s in (-1, 1):
        for w in (-d + 0.5, -0.5):
            f.b(s * (half - 0.4) - 0.2, s * (half - 0.4) + 0.2, FY, FY + 0.45, w - 0.2, w + 0.2, P['walnut'])
    for k in range(seats):
        u0 = -w_in / 2 + k * 3.9
        f.b(u0 + 0.08, u0 + 3.82, FY + 1.5, FY + 2.6, -d + 1.2, -0.04, cush, kind='O')
    f.b(-half + 1.0, half - 1.0, FY + 1.5, FY + 5.1, -d, -d + 1.0, col)                # back
    for k in range(seats):
        u0 = -w_in / 2 + k * 3.9
        f.b(u0 + 0.12, u0 + 3.78, FY + 2.6, FY + 4.9, -d + 1.0, -d + 1.6, shade(cush, 0.06))
    for s in (-1, 1):
        f.b(s * (half - 1.0) if s > 0 else -half, half if s > 0 else -half + 1.0, FY + 0.45, FY + 3.7, -d, 0, col)
        f.b((s * (half - 1.0)) if s > 0 else -half, half if s > 0 else -half + 1.0, FY + 3.7, FY + 3.95, -d + 0.1, -0.1, shade(col, 0.12))
    pc = pillow_cols or [P['mustard'], P['navy'], P['white'], P['teal']]
    for k in range(min(seats * 2, 4)):
        u = -w_in / 2 + 0.9 + k * (w_in - 1.8) / max(1, min(seats * 2, 4) - 1)
        x, z = f.p(u, -d + 1.9)
        cbox(x, FY + 3.4, z, 1.6, 1.6, 0.55, pc[k % len(pc)], rot=(15 if k % 2 else -12) + (0 if face in 'NS' else 90))
    if chaise:
        cs = 1 if chaise is True else (1 if chaise > 0 else -1)
        u0c, u1c = (half - 1.0 - 3.9, half - 1.0) if cs > 0 else (-half + 1.0, -half + 1.0 + 3.9)
        f.b(u0c, u1c, FY + 0.45, FY + 1.5, 0, 5.6, col)
        f.b(u0c + 0.08, u1c - 0.08, FY + 1.5, FY + 2.6, 0, 5.5, cush)
        f.col(name + '_chaise', u0c, u1c, FY, FY + 2.6, 0, 5.6)
    f.col(name, -half, half, FY, FY + 5.1, -d, 0)
    return half


def armchair(face, ox, oz, col, cush, name='armchair'):
    f = F(face, ox, oz)
    f.b(-2.0, 2.0, FY + 0.45, FY + 1.5, -3.4, 0, col)
    for s in (-1, 1):
        for w in (-3.0, -0.4):
            f.b(s * 1.7 - 0.18, s * 1.7 + 0.18, FY, FY + 0.45, w - 0.18, w + 0.18, P['walnut'])
    f.b(-1.2, 1.2, FY + 1.5, FY + 2.6, -2.4, -0.05, cush)
    f.b(-1.9, 1.9, FY + 1.5, FY + 5.0, -3.4, -2.6, col)
    f.b(-1.1, 1.1, FY + 2.6, FY + 4.7, -2.6, -2.1, shade(cush, 0.06))
    for s in (-1, 1):
        f.b((1.2 if s > 0 else -2.0), (2.0 if s > 0 else -1.2), FY + 0.45, FY + 3.4, -3.4, 0, col)
    f.col(name, -2.0, 2.0, FY, FY + 5.0, -3.4, 0)


# ------------------------------------------------------------------------------------------------------------------------------------- tables
def round_table(x, z, r, h, top, leg, name='table'):
    cyl(x, z, FY + h - 0.3, FY + h, r, top, seg=28)
    cyl(x, z, FY + h - 0.45, FY + h - 0.3, r - 0.15, shade(top, -0.2), seg=24)
    for k in range(3):
        a = k * 2.094 + 0.5
        hx, hz = x + math.cos(a) * (r - 0.9), z + math.sin(a) * (r - 0.9)
        box(hx - 0.14, hx + 0.14, FY, FY + h - 0.45, hz - 0.14, hz + 0.14, leg)
    CY_add(x, FY + h / 2, z, 2 * r, h, name)


def rect_table(x0, x1, z0, z1, h, top, leg, name='table'):
    box(x0, x1, FY + h - 0.35, FY + h, z0, z1, top)
    box(x0 + 0.1, x1 - 0.1, FY + h - 0.5, FY + h - 0.35, z0 + 0.1, z1 - 0.1, shade(top, -0.2))
    for (x, z) in ((x0 + 0.3, z0 + 0.3), (x1 - 0.3, z0 + 0.3), (x0 + 0.3, z1 - 0.3), (x1 - 0.3, z1 - 0.3)):
        box(x - 0.14, x + 0.14, FY, FY + h - 0.5, z - 0.14, z + 0.14, leg)
    collider(x0, x1, FY, FY + h, z0, z1, name)


def executive_desk(face, ox, oz):
    """12 x 4.8 desk: two drawer pedestals, a knee space, brass edge, leather pad (forward = the guest side)"""
    f = F(face, ox, oz)
    ty = FY + 3.1
    f.b(-6.1, 6.1, ty - 0.4, ty, -2.5, 2.5, P['walnut2'])
    f.b(-6.2, 6.2, ty - 0.1, ty, -2.6, 2.6, P['brass'])
    for s in (-1, 1):
        u0, u1 = (3.4, 5.9) if s > 0 else (-5.9, -3.4)
        f.b(u0, u1, FY + 0.15, ty - 0.4, -2.2, 2.2, P['walnut'])
        f.b(u0 - 0.05, u1 + 0.05, FY, FY + 0.15, -2.25, 2.25, P['charcoal'])
        for k in range(3):
            y0 = FY + 0.35 + k * 0.82
            f.b(u0 + 0.12, u1 - 0.12, y0, y0 + 0.72, 2.2, 2.26, P['walnut2'])
            f.b((u0 + u1) / 2 - 0.5, (u0 + u1) / 2 + 0.5, y0 + 0.3, y0 + 0.42, 2.26, 2.38, P['brass'])
    f.b(-3.4, 3.4, FY + 0.6, ty - 0.4, -2.2, -2.0, P['walnut'])                         # modesty panel (towards the executive)
    f.b(-3.0, 3.0, ty, ty + 0.04, -1.9, 0.5, P['navy'])                                  # leather pad
    f.col('desk', -6.2, 6.2, FY, ty, -2.6, 2.6)


def desk_things(face, ox, oz):
    f = F(face, ox, oz)
    ty = FY + 3.1
    for u in (-1.7, 1.7):                                                               # two monitors, screens towards the executive
        f.b(u - 0.9, u + 0.9, ty, ty + 0.12, -0.95, -0.35, P['charcoal'])
        f.b(u - 0.16, u + 0.16, ty + 0.12, ty + 1.3, -0.75, -0.55, P['charcoal'])
        f.b(u - 1.65, u + 1.65, ty + 1.3, ty + 3.7, -0.7, -0.45, P['black'])
        f.b(u - 1.55, u + 1.55, ty + 1.4, ty + 3.6, -0.72, -0.7, P['screen2'] if u < 0 else P['screen'])
        f.b(u - 1.0, u + 0.2, ty + 2.2, ty + 3.0, -0.735, -0.72, P['white'] if u < 0 else '#4A7DB5')
    f.b(-1.6, 0.8, ty, ty + 0.12, -2.0, -1.3, P['charcoal'])                           # keyboard
    f.b(-1.5, 0.7, ty + 0.12, ty + 0.16, -1.95, -1.35, P['metal'])
    f.b(1.5, 2.1, ty, ty + 0.14, -1.9, -1.3, P['charcoal'])                              # mouse
    f.cyl(-5.0, 0.2, ty, ty + 0.18, 0.5, P['black'], seg=12)                              # desk lamp
    f.b(-5.04, -4.96, ty + 0.18, ty + 2.4, 0.16, 0.24, P['brass'])
    f.b(-5.04, -4.3, ty + 2.4, ty + 2.5, 0.16, 0.24, P['brass'])
    f.lathe(-4.3, 0.2, ty + 1.9, [(0.0, 0.0), (0.2, 0.0), (0.6, 0.55), (0.0, 0.6)], P['teal'], seg=14)
    f.sphere(-4.3, ty + 1.95, 0.2, 0.2, 0.12, 0.2, '#FFE9B0', seg=8, rings=5, kind='N')
    spot(*(list(f.p(-4.3, 0.2)[:1]) + [ty + 1.7] + list(f.p(-4.3, 0.2)[1:])), rng=14, br=0.8)
    f.cyl(4.6, -1.0, ty, ty + 0.55, 0.38, P['white'], seg=12)                             # mug
    f.cyl(4.6, -1.0, ty + 0.5, ty + 0.56, 0.3, '#5B3A21', seg=12)
    f.b(2.6, 4.0, ty, ty + 0.5, 0.3, 1.8, P['paper'])                                    # papers
    f.b(2.7, 3.9, ty + 0.5, ty + 0.62, 0.35, 1.7, P['cream'])
    f.b(2.9, 3.4, ty + 0.62, ty + 0.7, 0.5, 1.2, P['coral'])
    f.b(-3.6, -2.4, ty, ty + 0.3, 0.7, 1.7, P['charcoal'])                              # phone
    f.b(-3.5, -2.5, ty + 0.3, ty + 0.4, 0.8, 1.2, P['black'])
    f.b(-0.7, 0.7, ty, ty + 0.35, 1.7, 2.1, P['walnut'])                                 # nameplate (no text)
    f.b(-0.6, 0.6, ty + 0.35, ty + 0.75, 1.75, 1.85, P['brass'])
    f.cyl(5.0, 1.4, ty, ty + 0.5, 0.35, P['pot2'], seg=10)                              # tiny plant
    f.sphere(5.0, ty + 0.9, 1.4, 0.45, 0.4, 0.45, P['leaf'], seg=8, rings=5)
    f.sphere(4.75, ty + 1.15, 1.35, 0.3, 0.3, 0.3, P['green2'], seg=8, rings=5)


def briefcase(x, z, face='N'):
    f = F(face, x, z)
    f.b(-1.3, 1.3, FY, FY + 1.9, -0.5, 0.5, P['walnut'])
    f.b(-1.35, 1.35, FY + 0.9, FY + 1.0, -0.55, 0.55, shade(P['walnut'], -0.3))
    f.b(-0.45, 0.45, FY + 1.9, FY + 2.15, -0.1, 0.1, P['brass'])
    f.b(-0.45, -0.35, FY + 1.9, FY + 2.5, -0.1, 0.1, P['brass'])
    f.b(0.35, 0.45, FY + 1.9, FY + 2.5, -0.1, 0.1, P['brass'])
    f.b(-0.45, 0.45, FY + 2.4, FY + 2.5, -0.1, 0.1, P['brass'])
    for s in (-1, 1):
        f.b(s * 0.9 - 0.15, s * 0.9 + 0.15, FY + 1.0, FY + 1.5, 0.5, 0.58, P['brass'])
    f.col('briefcase', -1.35, 1.35, FY, FY + 2.5, -0.55, 0.55)


# ------------------------------------------------------------------------------------------------------------------------------------- storage
def bookshelf(face, ox, oz, width, height, depth, name='bookshelf', seed=1, deco=True):
    """ox, oz = back-centre point on the wall plane; the shelf faces away from the wall"""
    f = F(face, ox, oz)
    r = rnd_of(seed)
    f.b(-width / 2, width / 2, FY, FY + 0.5, 0.0, depth, P['walnut'])
    f.b(-width / 2 + 0.25, width / 2 - 0.25, FY + 0.5, FY + height - 0.25, 0.3, 0.5, shade(P['walnut'], -0.1))
    for s in (-1, 1):
        f.b((width / 2 - 0.25) if s > 0 else -width / 2, width / 2 if s > 0 else (-width / 2 + 0.25), FY + 0.5, FY + height - 0.25, 0.0, depth, P['walnut'])
    f.b(-width / 2 - 0.06, width / 2 + 0.06, FY + height - 0.25, FY + height, 0.0, depth + 0.06, P['walnut2'])
    n = int((height - 1.0) // 2.5)
    bc = [P['red'], P['navy'], P['mustard'], P['teal'], P['white'], P['coral'], P['blue'], P['cream'], P['plum'], P['green']]
    for k in range(n):
        y = FY + 0.5 + k * (height - 0.75) / n
        if k > 0:
            f.b(-width / 2 + 0.25, width / 2 - 0.25, y, y + 0.2, 0.25, depth, P['walnut2'])
        if k == 0:
            continue
        u = -width / 2 + 0.4
        while u < width / 2 - 1.0:
            bw = r.uniform(0.28, 0.55)
            bh = r.uniform(1.4, (height - 0.75) / n - 0.35)
            if r.random() < 0.18 and deco:
                f.b(u, u + 1.1, y + 0.2, y + 1.3, 0.8, 1.9, r.choice([P['white'], P['teal'], P['mustard'], P['coral']]))
                u += 1.3
                continue
            f.b(u, u + bw, y + 0.2, y + 0.2 + bh, 0.45, depth - 0.2, r.choice(bc))
            u += bw + 0.03
    f.col(name, -width / 2, width / 2, FY, FY + height, 0.0, depth)


def plant(x, z, h=6.0, pot=None, kind='fiddle', seed=0, name='plant', y=FY):
    r = rnd_of(seed)
    pot = pot or P['pot']
    rr = 1.1 if h > 4 else 0.7
    D.lathe(x, z, y, [(0.0, 0), (rr * 0.7, 0), (rr * 0.85, 0.2), (rr, 1.9 * rr), (rr * 1.08, 2.0 * rr), (rr * 0.9, 2.0 * rr), (0.0, 2.0 * rr - 0.15)], pot, seg=14)
    cyl(x, z, y + 2.0 * rr - 0.15, y + 2.0 * rr - 0.05, rr * 0.9, '#5A3E2B', seg=12)
    top = y + 2.0 * rr
    if kind == 'fiddle':
        D.lathe(x, z, top, [(0.2, 0), (0.13, h * 0.7)], P['walnut'], seg=6)
        cc_ = top + h * 0.62                                                   # one continuous crown: blobs spiral through an ellipsoid, no gaps between tiers
        for k in range(20):
            t_ = (k + 0.5) / 20
            a_ = k * 2.4 + seed
            rd = 0.95 * math.sqrt(t_)
            D.sphere(x + math.cos(a_) * rd, cc_ + (t_ - 0.5) * h * 0.5, z + math.sin(a_) * rd, 0.95, 0.8, 0.95, [P['leaf'], P['green2'], '#3E9E4A'][k % 3], seg=8, rings=5)
    elif kind == 'snake':
        for k in range(9):
            a = k * 0.7 + seed
            bx, bz = x + math.cos(a) * 0.45, z + math.sin(a) * 0.45
            hh = h * (0.55 + 0.45 * ((k * 7) % 5) / 4)
            D.lathe(bx, bz, top, [(0.0, 0), (0.28, 0.0), (0.22, hh * 0.9), (0.0, hh)], P['leaf'] if k % 2 else '#7BC96F', seg=5)
    else:                                                                              # bushy
        cc_ = top + h * 0.42
        for k in range(20):
            t_ = (k + 0.5) / 20
            a_ = k * 2.2 + seed
            rd = 0.85 * math.sqrt(t_)
            D.sphere(x + math.cos(a_) * rd, cc_ + (t_ - 0.5) * h * 0.55, z + math.sin(a_) * rd, 0.9, 0.8, 0.9, [P['leaf'], P['green2'], '#3E9E4A'][k % 3], seg=8, rings=5)
    ch_ = (top - y) + (h * 0.62 + h * 0.25 + 0.9 if kind != 'snake' else h * 0.5)       # the collider covers the whole crown
    CY_add(x, y + ch_ / 2, z, rr * 2.1, ch_, name)


def floor_lamp(x, z, col=None, name='floor_lamp'):
    col = col or P['cream']
    D.lathe(x, z, FY, [(0.0, 0), (0.7, 0), (0.7, 0.18), (0.14, 0.3), (0.12, 6.4)], P['brass'], seg=12)
    D.lathe(x, z, FY + 6.0, [(0.9, 0), (1.35, 1.7), (1.35, 1.76), (0.9, 0.06)], col, seg=16)
    D.sphere(x, FY + 6.5, z, 0.3, 0.3, 0.3, '#FFE9B0', seg=7, rings=5, kind='N')
    spot(x, FY + 6.4, z, 20, 0.9)
    CY_add(x, FY + 3.9, z, 1.5, 7.8, name)


def pendant(x, z, y_shade, col, seed=0, r=1.5):
    box(x - 0.04, x + 0.04, y_shade + 0.9, CY, z - 0.04, z + 0.04, P['black'])
    D.lathe(x, z, y_shade, [(0.0, 1.0), (r * 0.35, 0.9), (r, 0.0), (r * 0.98, -0.08), (0.0, -0.08)], col, seg=18)
    D.lathe(x, z, y_shade, [(r * 0.97, -0.08), (r * 0.5, -0.04), (0.0, -0.04)], P['cream'], seg=16) if False else None
    D.sphere(x, y_shade - 0.15, z, 0.34, 0.3, 0.34, '#FFE9B0', seg=7, rings=5, kind='N')
    spot(x, y_shade - 0.5, z, 20, 0.9)


def rug(x0, x1, z0, z1, c1, c2, c3=None):
    c3 = c3 or P['cream']
    y = FY + 0.06
    box(x0, x1, y - 0.04, y, z0, z1, c1)
    box(x0 + 0.5, x1 - 0.5, y, y + 0.015, z0 + 0.5, z1 - 0.5, c3)
    n = int((x1 - x0 - 2) // 2.4)
    m = int((z1 - z0 - 2) // 2.4)
    for i in range(n):
        for j in range(m):
            if (i + j) % 2 == 0:
                cx, cz = x0 + 1.4 + i * (x1 - x0 - 2.8) / max(1, n - 1) if n > 1 else (x0 + x1) / 2, z0 + 1.4 + j * (z1 - z0 - 2.8) / max(1, m - 1) if m > 1 else (z0 + z1) / 2
                box(cx - 0.55, cx + 0.55, y + 0.015, y + 0.045, cz - 0.55, cz + 0.55, c2)


def curtain(face, ox, oz, width, y0, y1, col, n=7):
    """curtain panel hanging from a chrome rod: u in [-width/2, width/2] along the wall, standing out of the wall plane"""
    f = F(face, ox, oz)
    f.b(-width / 2 - 0.3, width / 2 + 0.3, y1 - 0.15, y1 + 0.05, 0.3, 0.5, P['metal'])
    for k in range(n):
        u0 = -width / 2 + k * width / n
        w0 = 0.45 + (0.1 if k % 2 else 0.0)
        f.b(u0, u0 + width / n - 0.04, y0, y1 - 0.15, w0, w0 + 0.18, col if k % 2 else shade(col, -0.05))
