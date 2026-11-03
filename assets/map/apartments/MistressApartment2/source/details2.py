# Decor of flat 2 (exec'd at the end of rooms2.py): small objects that make the rooms lived in — books, vases, photo frames, shoes, towels, kitchen things,
# wall panelling, cove light, window-sill pots.  Everything stands on a surface (no floating details); floor items get colliders.
def vase(x, y, z, col, h=1.6, r=0.45, seg=14, neck=0.22):
    D.lathe(x, z, y, [(0.0, 0), (r * 0.7, 0), (r, h * 0.3), (r * 0.95, h * 0.55), (neck, h * 0.85), (neck * 1.3, h), (0.0, h)], col, seg=seg)


def bowl(x, y, z, col, r=0.9, h=0.5, seg=16):
    D.lathe(x, z, y, [(0.0, 0), (r * 0.45, 0), (r, h), (r * 0.94, h), (r * 0.4, 0.1), (0.0, 0.1)], col, seg=seg)


def cup(x, y, z, col, r=0.28, h=0.5):
    D.lathe(x, z, y, [(0.0, 0), (r, 0), (r * 1.1, h), (r * 0.9, h), (r * 0.9, 0.06), (0.0, 0.06)], col, seg=10)


def book_stack(x, y, z, n=3, seed=0, w=1.4, d=1.0, rot=0):
    r = rnd_of(seed)
    cols = [P['red'], P['navy'], P['mustard'], P['teal'], P['coral'], P['cream'], P['blue']]
    yy = y
    for k in range(n):
        t = r.uniform(0.18, 0.3)
        ww = w * r.uniform(0.85, 1.0)
        dd = d * r.uniform(0.85, 1.0)
        cbox(x + r.uniform(-0.08, 0.08), yy + t / 2, z + r.uniform(-0.08, 0.08), ww, t, dd, cols[(seed + k) % len(cols)], rot=rot + r.uniform(-8, 8))
        yy += t
    return yy


def photo_frame(x, y, z, face='S', w=0.9, h=1.2, seed=0, col=None):
    """small standing frame (the picture faces `face`)"""
    f = F(face, x, z)
    col = col or P['brass']
    f.b(-w / 2, w / 2, y, y + h, -0.06, 0.06, col)
    f.b(-w / 2 + 0.1, w / 2 - 0.1, y + 0.1, y + h - 0.1, 0.06, 0.1, rnd_of(seed).choice([P['sky'], P['coral'], P['mustard'], P['teal'], P['blue']]))
    f.b(-0.08, 0.08, y, y + h * 0.75, -0.4, -0.06, shade(col, -0.2))


def candle(x, y, z, col=None, h=0.8):
    cyl(x, z, y, y + h, 0.14, col or P['cream'], seg=8)
    D.sphere(x, y + h + 0.1, z, 0.07, 0.15, 0.07, '#FFD58A', seg=5, rings=4, kind='N')


def shoe_pair(x, z, face, col):
    f = F(face, x, z)
    for u in (-0.45, 0.45):
        f.b(u - 0.3, u + 0.3, FY, FY + 0.35, -0.9, 0.9, P['white'])
        f.b(u - 0.3, u + 0.3, FY + 0.35, FY + 0.8, -0.9, 0.2, col)
        f.b(u - 0.28, u + 0.28, FY + 0.35, FY + 0.6, 0.2, 0.9, shade(col, -0.1))


def towel(x0, x1, y0, y1, z0, z1, col):
    box(x0, x1, y0, y1, z0, z1, col)
    box(x0, x1, y0 - 0.03, y0 + 0.08, z0 - 0.02, z1 + 0.02, shade(col, -0.2))


# ---------------------------------------------------------------------------------------------------------------------------------------- cove light + panelling
def cove(x0, x1, z0, z1, col='#FFE9B0'):
    """warm light strip below the crown moulding on the four walls of a room (clear x0..x1, z0..z1)"""
    y = CY - 0.9
    box(x0, x1, y, y + 0.14, z0, z0 + 0.14, col, 'N')
    box(x0, x1, y, y + 0.14, z1 - 0.14, z1, col, 'N')
    box(x0, x0 + 0.14, y, y + 0.14, z0 + 0.14, z1 - 0.14, col, 'N')
    box(x1 - 0.14, x1, y, y + 0.14, z0 + 0.14, z1 - 0.14, col, 'N')


cove(-23.7, 23.7, -16.7, 16.7)
cove(25.3, 44.7, -16.7, 1.7)
cove(25.3, 44.7, 3.3, 16.7)


def panel_frame(n, px, y0, pz, w, h, col=None):
    """picture-frame moulding panel on a wall: four 0.3-wide strips, 0.12 proud"""
    col = col or P['white']
    t = 0.3
    if n in 'NS':
        wb(n, px, y0, pz, w, t, 0.12, col)
        wb(n, px, y0 + h - t, pz, w, t, 0.12, col)
        wb(n, px - w / 2 + t / 2, y0 + t, pz, t, h - 2 * t, 0.12, col)
        wb(n, px + w / 2 - t / 2, y0 + t, pz, t, h - 2 * t, 0.12, col)
    else:
        wb(n, px, y0, pz, t, t, 0.12, col) if False else None
        for (dz, ww) in ((0.0, w), (0.0, w)):
            pass
        wb(n, px, y0, pz, w, t, 0.12, col)
        wb(n, px, y0 + h - t, pz, w, t, 0.12, col)
        wb(n, px, y0 + t, pz - w / 2 + t / 2, t, h - 2 * t, 0.12, col)
        wb(n, px, y0 + t, pz + w / 2 - t / 2, t, h - 2 * t, 0.12, col)


for (ux, ww) in ((-5.0, 5.5), (20.5, 5.0)):                                                        # navy TV wall (south): panels left and right of the TV
    panel_frame('N', ux, FY + 1.6, 17.0, ww, 7.6)
for (zc_) in (-13.0, -1.0):                                                                          # north/south ends of the bedroom headboard wall
    pass
panel_frame('E', -24.0, FY + 1.6, -1.0, 5.0, 6.0) if False else None


# ---------------------------------------------------------------------------------------------------------------------------------------- desk zone
f = F('S', DX, DZ)
ty = FY + 3.1
f.b(-5.6, -3.7, ty, ty + 0.14, 0.5, 1.9, P['charcoal'])                                            # closed laptop
f.b(-5.55, -3.75, ty + 0.14, ty + 0.2, 0.55, 1.85, P['metal'])
f.cyl(-4.65, 1.2, ty + 0.2, ty + 0.24, 0.16, P['brass'], seg=8)
yy = book_stack(*f.p(4.9, 1.0)[:1], ty, f.p(4.9, 1.0)[1], n=4, seed=3, w=1.5, d=1.0)
f.cyl(-3.0, -0.4, ty, ty + 0.75, 0.3, P['teal'], seg=10)                                            # pen holder with pens
for k in range(4):
    f.b(-3.2 + k * 0.12, -3.14 + k * 0.12, ty + 0.75, ty + 1.3 + (k % 2) * 0.2, -0.45, -0.39, [P['red'], P['navy'], P['mustard'], P['black']][k])
f.b(3.6, 4.6, ty, ty + 0.7, -1.4, -1.3, P['white'])                                                  # standing calendar
f.b(3.65, 4.55, ty + 0.1, ty + 0.65, -1.3, -1.28, P['cream'])
f.b(3.9, 4.3, ty + 0.1, ty + 0.5, -1.28, -1.26, P['red'])
cbox(*(list(f.p(2.0, 0.9))[:1] + [ty + 0.12] + list(f.p(2.0, 0.9))[1:]), 1.0, 0.24, 0.7, P['mustard'], rot=0)    # desk tray / folder
CY_add(13.5, FY + 0.9, -12.6, 1.5, 1.8, 'wastebasket')
D.lathe(13.5, -12.6, FY, [(0.0, 0), (0.6, 0), (0.75, 1.7), (0.0, 1.7)], P['charcoal'], seg=12)
D.lathe(13.5, -12.6, FY + 1.7, [(0.75, 0), (0.7, 0.1)], P['metal'], seg=12)
# credenza decor: frames, decanter + glasses, trophy, books
fc = F('S', 15.5, -17.0)
for k, u in enumerate((1.3, 2.4, 3.5)):
    photo_frame(*fc.p(u, 1.5)[:1], FY + 3.2, fc.p(u, 1.5)[1], face='S', w=0.9 + 0.2 * (k % 2), h=1.2 + 0.2 * (k % 2), seed=k)
vase(*fc.p(-1.2, 1.1)[:1], FY + 3.2, fc.p(-1.2, 1.1)[1], P['coral'], 1.8, 0.5)
D.lathe(fc.p(-2.0, 1.2)[0], fc.p(-2.0, 1.2)[1], FY + 3.2, [(0.0, 0), (0.5, 0), (0.55, 0.9), (0.2, 1.3), (0.2, 1.8), (0.28, 1.9), (0.0, 1.9)], P['sky'], seg=12)
for k in range(2):
    cup(fc.p(-0.8 - k * 0.6, 0.6)[0], FY + 3.2, fc.p(-0.8 - k * 0.6, 0.6)[1], P['sky'], 0.22, 0.5)
D.lathe(fc.p(0.2, 1.3)[0], fc.p(0.2, 1.3)[1], FY + 3.2, [(0.0, 0), (0.5, 0), (0.5, 0.2), (0.15, 0.3), (0.15, 1.3), (0.5, 1.6), (0.35, 1.9), (0.0, 1.9)], P['brass'], seg=10)     # trophy
book_stack(fc.p(-3.6, 1.0)[0], FY + 3.2, fc.p(-3.6, 1.0)[1], n=3, seed=7, w=1.5, d=1.0)
# window-sill pots (behind the desk) and on the kitchen window
for k, u in enumerate((-3.0, 1.0, 9.0, 13.0, 18.0)):
    x = u
    cyl(x, -16.4, FY + 3.4, FY + 3.9, 0.3, [P['pot'], P['pot2'], P['mustard'], P['white'], P['coral']][k], seg=8)
    D.sphere(x, FY + 4.35, -16.4, 0.38, 0.4, 0.38, P['leaf'], seg=7, rings=5)
cyl(-23.5, -10.0, FY + 4.4, FY + 4.9, 0.32, P['pot2'], seg=8)
D.sphere(-23.5, FY + 5.35, -10.0, 0.4, 0.4, 0.4, P['green2'], seg=7, rings=5)
cyl(-23.5, -6.0, FY + 4.4, FY + 4.9, 0.32, P['pot'], seg=8)
D.sphere(-23.5, FY + 5.35, -6.0, 0.4, 0.4, 0.4, P['leaf'], seg=7, rings=5)

# ---------------------------------------------------------------------------------------------------------------------------------------- kitchen
# utensil rail with hanging tools over the north-run backsplash, spice shelf, pots on the hob, cutting board with bread, dish rack, fridge magnets
box(-19.2, -16.4, FY + 5.9, FY + 6.0, -16.9, -16.8, P['brass'])
for k, (u, c) in enumerate(((-18.9, P['metal']), (-18.4, P['wood2']), (-17.9, P['metal']), (-17.4, P['red']), (-16.9, P['wood']))):
    box(u - 0.05, u + 0.05, FY + 4.2, FY + 5.9, -16.9, -16.78, c)
    D.sphere(u, FY + 4.15, -16.84, 0.2, 0.25, 0.1, c, seg=6, rings=4)
box(-11.5, -7.0, FY + 5.0, FY + 5.15, -16.95, -16.2, P['walnut2'])
for k in range(5):
    cyl(-11.0 + k * 0.9, -16.6, FY + 5.15, FY + 5.9, 0.28, [P['white'], P['mustard'], P['red'], P['cream'], P['teal']][k], seg=8)
    cyl(-11.0 + k * 0.9, -16.6, FY + 5.9, FY + 6.0, 0.3, P['black'], seg=8)
D.lathe(-15.0, -16.1, FY + 3.26, [(0.0, 0), (0.9, 0), (0.95, 1.0), (0.0, 1.0)], P['red'], seg=14)
D.lathe(-15.0, -16.1, FY + 4.26, [(0.0, 0.0), (0.95, 0.0), (0.4, 0.3), (0.0, 0.4)], P['red2'], seg=14)
D.lathe(-12.9, -15.8, FY + 3.26, [(0.0, 0), (0.7, 0), (0.7, 0.6), (0.0, 0.6)], P['charcoal'], seg=12)
box(-12.3, -9.8, FY + 3.2, FY + 3.3, -16.4, -15.0, P['oak'])
D.sphere(-11.0, FY + 3.7, -15.7, 0.9, 0.35, 0.4, '#E8C08A', seg=9, rings=6)
box(-23.7, -22.2, FY + 3.2, FY + 3.34, -3.8, -1.4, P['metal'])
for k in range(5):
    box(-23.6 + 0.0, -22.3, FY + 3.34, FY + 3.4 + (k % 2) * 0.01, -3.7 + k * 0.5, -3.65 + k * 0.5, P['white'])
for k, c in enumerate((P['red'], P['mustard'], P['blue'], P['green'])):                              # magnets and a note on the fridge
    box(-21.0 - 0.0, -20.9 + 0.0, FY + 6.2 + k * 0.5, FY + 6.5 + k * 0.5, -16.2 + (k % 2) * 0.8, -15.9 + (k % 2) * 0.8, c) if False else None
for k, c in enumerate((P['red'], P['mustard'], P['teal'], P['coral'])):
    box(-20.9, -20.8, FY + 6.1 + k * 0.55, FY + 6.4 + k * 0.55, -16.4 + (k % 2) * 0.9, -16.1 + (k % 2) * 0.9, c)
# kitchen runner rug, dish towel on the oven handle, hanging pots over the island
rug(-21.0, -17.4, -12.5, -1.0, P['navy'], P['white'], P['cream'])
box(-21.7, -21.55, FY + 1.6, FY + 2.8, -0.5, 0.3, P['white'])
for k in range(3):
    bx = -13.6 + (k - 1) * 0.0
D.lathe(-13.6, -9.0 + 0.0, CY - 3.0, [(0.0, 0), (0.5, 0), (0.4, 0.3)], P['metal'], seg=8) if False else None

# ---------------------------------------------------------------------------------------------------------------------------------------- lounge
fl = F('S', 12.0, 8.8)
cx_, cz_ = 9.6, 11.8
box(cx_ - 0.9, cx_ + 0.9, FY + 1.9, FY + 1.95, cz_ - 0.5, cz_ + 0.5, P['navy']) if False else None
book_stack(cx_ - 0.9, FY + 1.9, cz_ - 0.6, n=3, seed=11, w=1.6, d=1.1, rot=10)
vase(cx_ + 0.7, FY + 1.9, cz_ + 0.4, P['teal'], 1.4, 0.4)
D.sphere(cx_ + 0.7, FY + 3.55, cz_ + 0.4, 0.5, 0.45, 0.5, P['coral'], seg=8, rings=5)
D.sphere(cx_ + 0.95, FY + 3.5, cz_ + 0.25, 0.35, 0.3, 0.35, P['mustard'], seg=7, rings=4)
candle(cx_ - 0.4, FY + 1.9, cz_ + 0.9, P['cream'], 0.6)
candle(cx_ - 0.1, FY + 1.9, cz_ + 1.0, P['red'], 0.9)
# throw blanket on the chaise and on the armchair, floor basket
f2 = F('S', 12.0, 8.8)
cbox(f2.p(-3.9, 2.8)[0], FY + 2.72, f2.p(-3.9, 2.8)[1], 3.2, 0.25, 4.4, P['mustard'], rot=0)
box(*sorted((f2.p(-5.6, 3.0)[0] - 1.6, f2.p(-5.6, 3.0)[0] + 1.6)), FY + 2.55, FY + 2.6, f2.p(-5.6, 3.0)[1] - 2.3, f2.p(-5.6, 3.0)[1] + 2.3, P['white']) if False else None
D.lathe(22.2, 16.0, FY, [(0.0, 0), (0.85, 0), (0.95, 0.15), (1.0, 2.0), (0.0, 2.0)], '#C9A06E', seg=14)
for k in range(4):
    D.sphere(22.2 + math.cos(k * 1.7) * 0.3, FY + 2.2, 16.0 + math.sin(k * 1.7) * 0.3, 0.55, 0.3, 0.55, [P['coral'], P['cream'], P['navy'], P['mustard']][k], seg=7, rings=4)
CY_add(22.2, FY + 1.1, 16.0, 2.1, 2.2, 'basket')
# TV unit decor and floating shelves on the south wall
for (x, c) in ((6.4, P['coral']), (17.6, P['teal'])):
    vase(x, FY + 2.8, 16.0, c, 1.8, 0.5)
photo_frame(7.2, FY + 2.8, 16.4, 'N', 1.1, 1.4, seed=21)
photo_frame(16.8, FY + 2.8, 16.4, 'N', 1.1, 1.4, seed=22)
for (sx, sy) in ((2.5, 5.0), (2.5, 7.0), (21.5, 5.0), (21.5, 7.0)):
    box(sx - 1.6, sx + 1.6, FY + sy, FY + sy + 0.25, 16.0, 17.0, P['walnut2'])
box(1.4, 3.4, FY + 5.25, FY + 6.0, 16.4, 16.9, P['navy'])
vase(3.0, FY + 7.25, 16.4, P['mustard'], 1.2, 0.35)
book_stack(2.0, FY + 7.25, 16.4, 3, 31, 1.3, 0.8)
box(20.6, 21.7, FY + 5.25, FY + 6.2, 16.4, 16.9, P['red'])
cyl(22.2, 16.5, FY + 5.25, FY + 5.75, 0.3, P['pot2'], seg=8)
D.sphere(22.2, FY + 6.15, 16.5, 0.4, 0.4, 0.4, P['leaf'], seg=7, rings=5)
cyl(21.0, 16.4, FY + 7.25, FY + 7.7, 0.3, P['white'], seg=8)
D.sphere(21.0, FY + 8.1, 16.4, 0.4, 0.4, 0.4, P['green2'], seg=7, rings=5)

# ---------------------------------------------------------------------------------------------------------------------------------------- hall
box(-18.5, -13.5, FY, FY + 0.08, 15.2, 16.8, P['navy'])                                              # door mat
box(-18.3, -13.7, FY + 0.08, FY + 0.1, 15.4, 16.6, P['mustard'])
shoe_pair(-21.2, 14.55, 'N', P['red'])
shoe_pair(-22.9, 14.55, 'N', P['navy'])
shoe_pair(-21.6, 15.2 + 0.0, 'N', P['coral']) if False else None
box(-23.4, -21.6, FY + 1.9, FY + 2.7, 14.3, 15.0, P['coral'])                                         # handbag on the bench
box(-23.2, -21.8, FY + 2.7, FY + 2.8, 14.45, 14.85, P['brass'])
vase(-23.2, FY + 3.12, 7.8, P['coral'], 1.6, 0.4)
book_stack(-23.2, FY + 3.12, 11.0, 2, 41, 1.2, 0.8)
D.sphere(-23.2, FY + 5.15, 7.8, 0.4, 0.4, 0.4, P['coral'], seg=7, rings=5)
box(-23.7, -22.5, FY + 6.7, FY + 6.9, 16.6, 16.95, P['mustard']) if False else None

# ---------------------------------------------------------------------------------------------------------------------------------------- bedroom
bd = F('W', 45.0, -9.6)
for s in (-1, 1):                                                                                      # nightstand things: clock, book, small plant
    nn = F('W', 45.0, -9.6 + s * 6.4)
    nn.b(-0.5, 0.2, FY + 2.4, FY + 2.9, 0.2, 0.9, P['coral'] if s < 0 else P['teal'])
    nn.b(0.1, 0.8, FY + 2.4, FY + 2.55, 1.0, 1.7, P['paper'])
    nn.b(0.15, 0.75, FY + 2.55, FY + 2.65, 1.05, 1.6, P['navy'])
for k in range(3):                                                                                     # bed runner stripes
    bd.b(-4.9, 4.9, FY + 3.3 + 0.0, FY + 3.36, 5.0 + k * 0.7, 5.35 + k * 0.7, [P['teal'], P['white'], P['coral']][k])
bd.b(-4.7, 4.7, FY + 3.4, FY + 3.45, 3.6, 4.0, P['navy']) if False else None
box(26.0, 27.4, FY, FY + 0.12, -1.2, -0.2, P['coral']) if False else None
D.lathe(26.9, 0.5, FY, [(0.0, 0), (0.9, 0), (1.0, 0.15), (1.05, 2.4), (0.0, 2.4)], '#C9A06E', seg=14)                    # hamper
D.lathe(26.9, 0.5, FY + 2.4, [(1.1, 0), (1.1, 0.12), (0.0, 0.12)], P['cream'], seg=14)
CY_add(26.9, FY + 1.3, 0.5, 2.1, 2.6, 'hamper')
for (x, z, c) in ((31.0, -1.6, P['coral']), (32.0, -1.8, P['coral'])):                               # slippers
    box(x - 0.3, x + 0.3, FY, FY + 0.25, z - 0.7, z + 0.7, c)
pf = F('S', 28.0, -17.0)                                                                               # vanity: jewellery box, perfume, brush
pf.b(-1.9, -0.7, FY + 3.0, FY + 3.5, 0.5, 1.4, P['navy'])
pf.b(-1.85, -0.75, FY + 3.5, FY + 3.6, 0.55, 1.35, P['brass'])
vase(*pf.p(0.6, 0.8)[:1], FY + 3.0, pf.p(0.6, 0.8)[1], P['sky'], 1.0, 0.3)
vase(*pf.p(1.4, 1.1)[:1], FY + 3.0, pf.p(1.4, 1.1)[1], P['coral'], 0.8, 0.25)
# wall sconces above the nightstands
for s in (-1, 1):
    zz = -9.6 + s * 6.4
    box(44.6, 45.0, FY + 6.0, FY + 6.5, zz - 0.4, zz + 0.4, P['brass'])
    D.lathe(44.5, zz, FY + 6.3, [(0.0, 0), (0.45, 0.2), (0.5, 0.9), (0.0, 0.9)], P['cream'], seg=10)
    spot(44.4, FY + 6.8, zz, 10, 0.5)

# ---------------------------------------------------------------------------------------------------------------------------------------- bathroom
for k in range(2):                                                                                     # towel ladder on the bedroom/bath partition (bath side z = 3)
    box(28.3 + k * 3.4, 28.6 + k * 3.4, FY + 0.5, FY + 6.4, 3.0, 3.35, P['brass'])
for k in range(5):
    box(28.3, 31.9, FY + 1.4 + k * 1.0, FY + 1.5 + k * 1.0, 3.0, 3.3, P['brass'])
towel(28.7, 31.5, FY + 3.9, FY + 5.4, 3.3, 3.55, P['coral'])
towel(28.7, 31.5, FY + 2.0, FY + 3.5, 3.3, 3.55, P['white'])
towel(28.7, 31.5, FY + 5.4 - 0.0, FY + 5.9, 3.3, 3.55, P['teal'])
box(44.2, 45.0, FY + 5.6, FY + 5.8, 12.0, 14.0, P['walnut2']) if False else None
box(44.0, 45.0, FY + 7.2, FY + 7.45, 7.4, 10.0, P['walnut2'])                                           # shelf over the toilet
vase(44.5, FY + 7.45, 8.2, P['teal'], 1.3, 0.35)
book_stack(44.4, FY + 7.45, 9.3, 2, 51, 1.1, 0.8)
box(44.6, 45.0, FY + 4.0, FY + 4.4, 8.4, 8.8, P['metal'])                                              # paper-roll holder
cyl(44.4, 8.6, FY + 4.0, FY + 4.5, 0.3, P['white'], seg=10) if False else None
for k, c in enumerate((P['coral'], P['white'], P['teal'])):
    vn_ = F('N', 33.5, 17.0)
cup(31.2, FY + 3.2, 16.0, P['white'], 0.3, 0.6)
for k in range(3):
    box(31.1 + k * 0.1, 31.17 + k * 0.1, FY + 3.8, FY + 4.3, 15.95, 16.05, [P['red'], P['blue'], P['mustard']][k])
D.lathe(35.6, 16.0, FY + 3.2, [(0.0, 0), (0.3, 0), (0.3, 0.8), (0.12, 1.0), (0.12, 1.3), (0.0, 1.3)], P['teal'], seg=10)
box(36.5, 38.0, FY, FY + 0.08, 8.0, 11.0, P['sky'])                                                      # bath mat
box(36.7, 37.8, FY + 0.08, FY + 0.1, 8.2, 10.8, P['white'])
D.lathe(27.2, 15.6, FY, [(0.0, 0), (0.9, 0), (1.0, 0.15), (1.0, 2.3), (0.0, 2.3)], '#C9A06E', seg=14)
CY_add(27.2, FY + 1.15, 15.6, 2.0, 2.3, 'laundry')
