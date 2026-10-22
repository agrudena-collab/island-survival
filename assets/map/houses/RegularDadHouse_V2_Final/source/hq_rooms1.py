HQ_ROOMS_1 = '''
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
    P_(12.9, 26.0, F0, 90)
    console_table(FGc)
    tf_push(-0.9, 0.0, 3.0, 0)
    table_lamp(FGc, base='teal')
    tf_pop()
    tf_push(1.2, 0.1, 3.0, 0)
    vase_flowers(FGc, 'blue', 6, 1.0)
    tf_pop()
    tf_pop()
    P_(13.35, 26.0, F0 + 6.6, 90)
    mirror_round(FGc, 1.7)
    tf_pop()
    # family pictures
    for k, (v, w_, h_, kind, col) in enumerate(((29.4, 2.6, 3.2, 'family', 'orange'), (36.6, 3.0, 2.4, 'art', 'blue'), (39.6, 2.2, 2.8, 'art', 'purple'))):
        P_(13.4, v, F0 + 6.4, 90)
        picture(FGc, w_, h_, col, 'trim', kind)
        tf_pop()
    # coat rack with coats and hat shelf
    P_(13.3, 40.2, F0 + 6.8, 90)
    rbox(FGc, MT('wood2'), 0, 0, -0.5, 4.4, 1.2, 0.3, 0.1, 2)
    for k in range(4):
        x = -1.5 + k * 1.0
        sphere(FGc, MT('brass'), x, 0.28, 0.0, 0.14, 0.14, 0.14, 8, 6)
        tf_push(x, 0.3, 0.0, 0)
        coat_on_hook(FGc, ('red', 'blue', 'yellow', 'teal')[k])
        tf_pop()
    tf_pop()
    # shoe rack and shoes, umbrella stand, door mat
    P_(12.3, 36.9, F0, 0)
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
    P_(12.3, 41.6, F0, 0)
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
        P_(3.75, (v0 + v1) / 2, F0 + rise * i, 0)
        rbox(FGc, MT('red'), 0, 0, 0.0, 2.9, 0.06, run - 0.1, 0.02, 1)
        rbox(FGc, MT('cream'), 0, 0, 0.06, 2.9, 0.02, 0.12, 0.01, 1)
        tf_pop()
    P_(6.0, 42.1, F0, 0)
    newel(FGc)
    tf_pop()
    P_(6.0, 26.9, F1, 0)
    newel(FUc)
    tf_pop()
    def yf(v):
        return F0 + rise * (42.5 - v) / run
    for k in range(0, 14):
        v = 41.0 - k * run
        P_(6.0, v, yf(v), 0)
        baluster(FGc)
        tf_pop()
    tube(FGc, MT('wood'), [(HX + 6.0, yf(42.0) + 3.1, HZ + 42.0), (HX + 6.0, yf(27.0) + 3.1, HZ + 27.0)], 0.2, 10)
    # upper rail turned balusters
    for v in [27.2 + 0.85 * i for i in range(18)]:
        P_(6.0, v, F1, 0)
        baluster(FUc)
        tf_pop()
    tube(FUc, MT('wood'), [(HX + 6.0, F1 + 3.1, HZ + 26.8), (HX + 6.0, F1 + 3.1, HZ + 42.3)], 0.2, 10)


def hq_living():
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
    P_(15.7, 28.0, F0, -90)
    tv_unit(FGc)
    tf_pop()
    P_(15.4, 23.5, F0, 0)
    floor_lamp(FGc)
    tf_pop()
    P_(15.6, 41.4, F0, 0)
    potted_plant(FGc, 1.5, 'terra', True, 14)
    tf_pop()
    P_(33.2, 39.6, F0, 90)
    bookshelf(FGc, 6.4, 7.0, 1.5, 5, 3)
    tf_pop()
    for k, (u, w_, h_, kind, col) in enumerate(((28.4, 2.8, 3.4, 'art', 'blue'), (31.4, 3.4, 2.6, 'art', 'orange'), (33.4, 1.9, 2.9, 'art', 'teal'))):
        P_(u, 22.7, F0 + 6.6, 0)
        picture(FGc, w_, h_, col, 'trim', kind)
        tf_pop()
    # curtains: south windows and east window
    for ac in (HX + 20, HX + 30):
        curtain_pair(FGc, ac, 6.0, F0 + 8.3, 5.8, HZ + 41.7, 'x', 'coral')
    curtain_pair(FGc, HZ + 33, 6.0, F0 + 8.3, 5.8, HX + 33.9, 'z', 'coral')


def hq_dining():
    P_(24.0, 10.2, F0, 0)
    rug(FGc, 14.5, 9.6, 'cream', 'red', 'yellow', fringe=True)
    tf_pop()
    P_(24.0, 10.2, F0, 0)
    dining_table(FGc)
    for k in range(3):
        x = -3.3 + k * 3.3
        for (z, rot_) in ((-1.55, 180), (1.55, 0)):
            tf_push(x, z, 2.9, rot_)
            place_setting(FGc, ('teal', 'red', 'blue')[k])
            tf_pop()
    for sx in (-1, 1):
        tf_push(sx * 4.3, 0.0, 2.9, 90 * sx)
        place_setting(FGc, 'yellow')
        tf_pop()
    rbox(FGc, MT('yellow'), 0, 0, 2.9, 8.6, 0.04, 1.1, 0.02, 1)
    tf_push(0.0, 0.0, 2.9, 0)
    vase_flowers(FGc, 'blue', 9, 1.3)
    tf_pop()
    for sx in (-1.8, 1.8):
        tf_push(sx, 0.2, 2.9, 0)
        candle(FGc)
        tf_pop()
    tf_push(3.0, -0.2, 2.9, 0)
    fruit_bowl(FGc)
    tf_pop()
    tf_pop()
    for k in range(3):
        x = 24.0 - 3.3 + k * 3.3
        P_(x - HX + HX - HX, 6.55, F0, 0)
        tf_pop()
    for k in range(3):
        u = 24.0 - 3.3 + k * 3.3
        P_(u, 7.0, F0, 0)
        dining_chair(FGc, 'red', 'cream')
        tf_pop()
        P_(u, 13.4, F0, 180)
        dining_chair(FGc, 'red', 'cream')
        tf_pop()
    P_(17.6, 10.2, F0, -90)
    dining_chair(FGc, 'red', 'cream')
    tf_pop()
    P_(30.4, 10.2, F0, 90)
    dining_chair(FGc, 'red', 'cream')
    tf_pop()
    P_(24.0, 10.2, F0 + 10.0, 0)
    chandelier(FGc)
    tf_pop()
    P_(15.8, 7.0, F0, -90)
    sideboard(FGc)
    tf_push(-1.6, 0.0, 2.8, 0)
    table_lamp(FGc, base='red')
    tf_pop()
    tf_push(1.7, 0.0, 2.8, 0)
    vase_flowers(FGc, 'teal', 6, 1.1)
    tf_pop()
    for k in range(3):
        tf_push(-0.2 + k * 0.0, -0.3 + k * 1.0, 2.8, 0)
        plate(FGc, ('blue', 'white', 'red')[k], 0.5)
        tf_pop()
    tf_pop()
    for k, (u, w_, h_, kind, col) in enumerate(((17.6, 3.2, 2.4, 'art', 'purple'), (31.4, 2.4, 3.0, 'art', 'orange'))):
        P_(u, 21.4, F0 + 6.5, 180)
        picture(FGc, w_, h_, col, 'trim', kind)
        tf_pop()
    for ac in (HX + 22,):
        curtain_pair(FGc, ac, 6.0, F0 + 8.3, 5.8, HZ + 2.3, 'x', 'yellow')
    curtain_pair(FGc, HZ + 11, 6.0, F0 + 8.3, 5.8, HX + 33.9, 'z', 'yellow')
'''
