HQ_ROOMS_3 = '''
def bed(c, w=6.4, l=9.4, quilt='pink', sheet='cream', wood='wood2', pillows=('white', 'cream'), stripe='white'):
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
        rbox(c, MT(cc), -2.6 + k * 1.4, 0.0, h - 1.46, 1.2, 0.55, 1.1, 0.14, 2)
    cols = ('red', 'blue', 'yellow', 'teal', 'white', 'purple', 'orange', 'navy', 'pink')
    for k in range(9):
        x = -w / 2 + 0.9 + k * (w - 1.8) / 8.0
        tube(c, MT('metal'), [(x, h - 2.4, 0), (x, h - 2.7, 0), (x + 0.45, h - 3.0, 0), (x - 0.45, h - 3.0, 0), (x, h - 2.7, 0)], 0.025, 5)
        rbox(c, MT(cols[k]), x, 0.0, h - 5.7, 0.55, 2.7 + (k % 3) * 0.2, 1.1, 0.2, 2)
    for k, cc in enumerate(('red', 'dark', 'blue', 'cream')):
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
    P_(12.85, 31.0, F1, 90)
    console_table(FUc, 4.4, 1.5, 3.0)
    tf_push(-0.9, 0.0, 3.0, 0)
    table_lamp(FUc, base='red')
    tf_pop()
    tf_push(1.2, 0.0, 3.0, 0)
    potted_plant(FUc, 0.7, 'teal', False, 9)
    tf_pop()
    tf_pop()
    P_(13.35, 31.0, F1 + 6.6, 90)
    mirror_round(FUc, 1.5)
    tf_pop()
    for (v, w_, h_, col) in ((15.5, 2.4, 3.0, 'orange'), (19.0, 3.0, 2.2, 'blue'), (25.8, 2.6, 3.2, 'purple')):
        P_(13.4, v, F1 + 6.4, 90)
        picture(FUc, w_, h_, col, 'trim', 'art')
        tf_pop()
    P_(2.5, 12.5, F1, 0)
    potted_plant(FUc, 1.4, 'terra', True, 13)
    tf_pop()
    P_(2.9, 24.6, F1, 0)
    potted_plant(FUc, 1.1, 'navy', True, 12)
    tf_pop()
    curtain_pair(FUc, HX + 9.5, 5.4, F1 + 8.2, 5.4, HZ + 41.9, 'x', 'pink')
    # bathroom
    P_(3.7, 5.7, F1, 0)
    bathtub(FUc)
    tf_pop()
    P_(12.4, 7.2, F1, 90)
    toilet(FUc)
    tf_pop()
    P_(9.7, 2.5, F1, 0)
    pedestal_sink(FUc)
    tf_pop()
    P_(9.7, 1.95, F1 + 5.2, 0)
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
    P_(12.3, 3.2, F1, 0)
    potted_plant(FUc, 0.7, 'white', False, 8)
    tf_pop()


def hq_master():
    P_(21.0, 35.4, F1, 0)
    rug(FUc, 10.0, 10.5, 'cream', 'pink', 'coral', True)
    tf_pop()
    P_(21.0, 35.7, F1, 0)
    bed(FUc, 6.4, 9.2, 'coral', 'cream', 'wood2', ('white', 'cream'), 'white')
    tf_pop()
    for u in (16.5, 25.5):
        P_(u, 31.9, F1, 0)
        nightstand(FUc)
        tf_push(0.0, 0.0, 2.44, 0)
        table_lamp(FUc, base='pink')
        tf_pop()
        tf_push(0.5, 0.5, 2.44, 10)
        rbox(FUc, MT('blue'), 0, 0, 0.0, 0.9, 0.2, 0.65, 0.04, 1)
        rbox(FUc, MT('yellow'), 0.05, 0, 0.2, 0.85, 0.16, 0.6, 0.04, 1)
        tf_pop()
        tf_pop()
    P_(25.0, 41.0, F1, 180)
    dresser(FUc, 4.2, 2.2, 3.7)
    tf_pop()
    P_(32.4, 38.0, F1, 90)
    wardrobe(FUc, 8.0, 3.5, 8.6, True)
    tf_pop()
    P_(26.4, 31.5, F1, 0)
    potted_plant(FUc, 1.0, 'terra', True, 12)
    tf_pop()
    P_(15.8, 41.0, F1, 0)
    floor_lamp(FUc)
    tf_pop()
    for (u, w_, h_, col) in ((19.0, 2.8, 2.2, 'blue'), (23.0, 2.2, 3.0, 'yellow')):
        P_(u, 30.9, F1 + 7.0, 0)
        picture(FUc, w_, h_, col, 'brass', 'art')
        tf_pop()
    curtain_pair(FUc, HX + 20, 6.0, F1 + 8.3, 5.8, HZ + 41.7, 'x', 'pink')
    curtain_pair(FUc, HX + 30, 6.0, F1 + 8.3, 5.8, HZ + 41.7, 'x', 'pink')
    P_(28.0, 40.0, F1, 0)
    basket(FUc, 'wood2', True)
    tf_pop()


def hq_child():
    P_(24.0, 23.0, F1, 0)
    rug(FUc, 10.0, 8.5, 'yellow', 'blue', 'red', False)
    tf_pop()
    P_(32.2, 22.2, F1, 0)
    bunk_bed(FUc, 3.8, 8.0)
    tf_pop()
    P_(17.5, 28.0, F1, 0)
    toy_chest(FUc)
    tf_pop()
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
    for (v, w_, h_, col) in ((25.4, 2.2, 3.0, 'yellow'), (27.9, 2.6, 2.2, 'pink')):
        P_(14.65, v, F1 + 6.0, 90)
        picture(FUc, w_, h_, col, 'white', 'art')
        tf_pop()
    ball_ = None
    for (u, v, r_, col) in ((21.0, 21.4, 0.85, 'red'), (22.6, 25.4, 0.55, 'blue')):
        sphere(FUc, MT(col), HX + u, HZ + v, F1 + r_, r_, r_, r_, 14, 9)
    for k, (u, v, col, rot_) in enumerate(((19.5, 24.4, 'blue', 20), (20.7, 24.0, 'yellow', -10), (20.0, 25.5, 'teal', 40), (21.0, 25.2, 'red', 5))):
        P_(u, v, F1, rot_)
        rbox(FUc, MT(col), 0, 0, 0.0, 1.1, 1.1, 1.1, 0.14, 2)
        tf_pop()
    curtain_pair(FUc, HZ + 23, 6.0, F1 + 8.2, 5.6, HX + 33.8, 'z', 'yellow')


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
    T = _M.Translation((HX + 21.0, -(HZ + 6.6), F1)) @ _M.Rotation(math.radians(180), 4, 'Z')
    for o in new:
        if o.parent is None:
            o.matrix_world = T @ o.matrix_world
    for o in new:
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        coll('Furn_U').objects.link(o)


def hq_lounge():
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
    P_(30.4, 9.5, F1, 90)
    bookshelf(FUc, 7.2, 9.0, 1.5, 7, 5)
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
    P_(15.4, 3.0, F1, 0)
    floor_lamp(FUc)
    tf_pop()
    P_(34.0, 13.8, F1, 0)
    potted_plant(FUc, 1.2, 'terra', True, 13)
    tf_pop()
    P_(34.4, 8.0, F1 + 5.5, -90)
    picture(FUc, 4.2, 3.4, 'purple', 'trim', 'art')
    tf_pop()
    place_father()
    curtain_pair(FUc, HX + 21, 6.0, F1 + 8.3, 5.8, HZ + 2.3, 'x', 'orange')
    # balcony: table, two chairs, pots
    P_(25.5, -2.6, F1, 0)
    round_table(FUc, 1.35, 2.6, 'white')
    tf_push(0.0, 0.0, 2.6, 0)
    vase_flowers(FUc, 'red', 5, 0.7)
    tf_pop()
    tf_pop()
    for (u, rot_) in ((22.7, 90), (28.3, -90)):
        P_(u, -2.6, F1, rot_)
        folding_chair(FUc)
        tf_pop()
    for (u, col) in ((19.2, 'red'), (30.8, 'teal')):
        P_(u, -4.0, F1, 0)
        potted_plant(FUc, 0.8, col, False, 10)
        tf_pop()
'''
