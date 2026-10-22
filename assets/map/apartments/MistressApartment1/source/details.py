# More detail (exec'd at the end of rooms.py): wicker baskets, candles, photo frames, plate wall, globes, sculptures, rug fringes.
def basket(x, z, r=1.0, h=1.4, col='#C9A06E', blanket=None, y=FY, collide=True):
    lathe(x, z, y, [(0.0, 0), (r * 0.85, 0), (r, 0.15), (r * 1.05, h * 0.9), (r * 1.1, h), (r * 0.95, h), (r * 0.95, h - 0.12), (0.0, h - 0.12)], col, seg=18)
    for k in range(5):
        ring(x, y + 0.25 + k * (h - 0.4) / 4, z, r * (0.95 + 0.04 * k / 4) + 0.04, 0.045, 'xz', shade(col, -0.18), seg=24, tseg=4)
    if blanket:
        for k in range(5):
            D.sphere(x + math.cos(k * 1.3) * r * 0.45, y + h + 0.1, z + math.sin(k * 1.3) * r * 0.45, 0.55, 0.32, 0.55, blanket, seg=8, rings=5)
    if collide:
        CYLC.append((x, y + h / 2, z, 2.1 * r, h, 'basket'))


def candles(x, y, z, seed=0, n=3):
    r_ = rnd_of(seed)
    for k in range(n):
        a = k * 2.1
        cx, cz = x + math.cos(a) * 0.28, z + math.sin(a) * 0.28
        h = r_.uniform(0.5, 1.1)
        cyl(cx, cz, y, y + h, 0.12, P['cream'], seg=8)
        D.sphere(cx, y + h + 0.12, cz, 0.06, 0.14, 0.06, '#FFD58A', seg=5, rings=4, kind='N')


def standing_photo(f, x, y, z, w=0.9, h=1.2, seed=1, frame=None):
    frame = frame or P['brass']
    f.b(x - w / 2, x + w / 2, y, y + h, z, z + 0.1, frame)
    f.b(x - w / 2 + 0.1, x + w / 2 - 0.1, y + 0.1, y + h - 0.1, z + 0.1, z + 0.14, rnd_of(seed).choice([P['sky'], P['blush'], P['sage'], P['lilac'], P['mustard']]))
    f.b(x - 0.08, x + 0.08, y, y + h * 0.8, z - 0.35, z, shade(frame, -0.2))


def plate_wall(px, pz, y, seed=3):
    """Plates on the north wall (wall faces +z)."""
    r_ = rnd_of(seed)
    spots = [(0.0, 0.0, 1.5), (-2.0, 0.9, 1.0), (2.0, 0.7, 1.1), (-1.1, -1.7, 0.9), (1.2, -1.6, 1.0), (-3.0, -0.8, 0.8), (3.1, -0.9, 0.8)]
    cols = [P['white'], P['teal2'], P['rose'], P['navy'], P['cream']]
    for (du, dv, rr) in spots:
        hcyl(px + du, y + dv, pz + 0.15, 'z', 0.18, rr, cols[r_.randrange(5)], seg=24)
        hcyl(px + du, y + dv, pz + 0.26, 'z', 0.06, rr * 0.62, P['gold'], seg=24)


def globe(x, z, y=FY):
    lathe(x, z, y, [(0.0, 0), (0.9, 0), (0.9, 0.15), (0.2, 0.4), (0.15, 2.4)], P['walnut'], seg=16)
    ring(x, y + 3.3, z, 0.95, 0.07, 'xy', P['brass'], seg=24, tseg=5)
    D.sphere(x, y + 3.3, z, 0.85, 0.85, 0.85, P['sky'], seg=20, rings=12)
    for k in range(6):
        a = k * 1.1
        D.sphere(x + math.cos(a) * 0.62, y + 3.3 + math.sin(a * 1.3) * 0.5, z + math.sin(a) * 0.62, 0.3, 0.2, 0.3, P['sage'], seg=6, rings=4)
    CYLC.append((x, y + 1.7, z, 1.8, 3.4, 'globe'))


def sculpture(x, y, z, col=None):
    col = col or P['white']
    D.sphere(x, y + 0.5, z, 0.5, 0.5, 0.5, col, seg=14, rings=9)
    D.sphere(x + 0.15, y + 1.25, z, 0.38, 0.38, 0.38, shade(col, -0.05), seg=12, rings=8)
    D.sphere(x - 0.1, y + 1.85, z, 0.26, 0.26, 0.26, shade(col, -0.1), seg=10, rings=7)


# sideboard under the window: photos, candles, a sculpture
fz = F(2, -15.0, 'S')
standing_photo(fz, 3.0, FY + 2.55, -0.3, seed=1)
standing_photo(fz, 1.9, FY + 2.55, -0.5, w=0.7, h=0.9, seed=2)
candles(-0.4, FY + 2.55, -15.2, seed=4)
sculpture(-1.8, FY + 2.55, -15.0, P['cream'])
# kitchen: fruit basket at the far end of the island
basket(-12.4, -4.6, r=0.6, h=0.6, y=FY + 3.5, collide=False)
for k, c in enumerate((P['red'], P['mustard'], P['green2'])):
    D.sphere(-12.4 + (k - 1) * 0.3, FY + 4.2, -4.6 + (k % 2) * 0.2, 0.25, 0.25, 0.25, c, seg=8, rings=6)
# living: wicker basket with a throw, candles on the TV console, plate wall over the reading armchair
basket(5.3, 1.8, r=0.95, h=1.3, blanket=P['blush'])
candles(7.4, FY + 2.55, 14.9, seed=7)
plate_wall(18.2, -16.0, FY + 6.4, seed=3)
# bedroom: candles on the nightstands, a basket with a throw
candles(45.0, FY + 2.75, -1.2, seed=12)
candles(44.7, FY + 2.75, -11.2, seed=13)
basket(26.2, -3.0, r=0.8, h=1.1, blanket=P['lilac'])
# bathroom: candles on the tub edge
candles(34.5, FY + 2.1, 14.4, seed=14, n=4)
# globe in the hall
globe(-18.5, 6.4)
# rug fringes
for (cx, cz, w, d) in ((2, -5, 13.0, 13.0), (14.5, 10, 13.0, 9.6), (39.8, -6.5, 13.0, 11.0)):
    for k in range(int(w // 0.55)):
        for z in (cz - d / 2 - 0.28, cz + d / 2 + 0.28):
            _box_sharp(cx - w / 2 + 0.2 + k * 0.55, cx - w / 2 + 0.3 + k * 0.55, FY, FY + 0.05, z - 0.28, z + 0.28, P['cream'])
