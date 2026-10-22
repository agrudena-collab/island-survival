HQ_ROOMS_2 = '''
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
    P_(2.9, 15.2, F0, -90)
    sink_unit(FGc, 4.0, 2.1, 3.1)
    tf_pop()
    P_(2.9, 19.2, F0, -90)
    cabinet(FGc, 4.0, 2.1, 3.1, 2, 'cab', 'teal')
    tf_push(0.0, 0.1, 3.1, 0)
    microwave(FGc)
    tf_pop()
    tf_pop()
    # north run (front faces south): cabinet with toaster, stove, hood
    P_(4.0, 11.7, F0, 0)
    cabinet(FGc, 3.0, 2.1, 3.1, 2, 'cab', 'teal')
    tf_push(0.0, 0.0, 3.1, 0)
    toaster(FGc)
    tf_pop()
    tf_pop()
    P_(6.9, 11.7, F0, 0)
    stove(FGc)
    tf_push(-0.65, -0.55, 3.26, 0)
    cooking_pot(FGc, 'metal', 1.0)
    tf_pop()
    tf_push(0.65, 0.55, 3.26, 20)
    pan(FGc)
    tf_pop()
    tf_push(0.65, -0.55, 3.26, 0)
    kettle(FGc, 'red')
    tf_pop()
    tf_pop()
    P_(6.9, 11.6, F0 + 6.4, 0)
    range_hood(FGc)
    tf_pop()
    P_(4.0, 11.2, F0 + 6.1, 0)
    upper_cabinet(FGc, 3.0, 1.1, 3.1, 2)
    tf_pop()
    P_(2.35, 19.9, F0 + 6.0, -90)
    upper_cabinet(FGc, 2.8, 1.1, 3.3, 2)
    tf_pop()
    # fridge in the south-east corner (front faces west) and the island with stools
    P_(12.2, 19.6, F0, 90)
    fridge(FGc, 2.8, 2.5, 7.1)
    tf_pop()
    P_(7.6, 15.8, F0, 0)
    cabinet(FGc, 5.4, 3.0, 3.5, 3, 'cab', 'teal')
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
    curtain_pair(FGc, HZ + 16, 5.2, F0 + 8.0, 3.9, HX + 2.0, 'z', 'red')


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
    P_(9.0, 3.4, F0, 0)
    drying_rack(FGc)
    tf_pop()
    P_(8.9, 8.3, F0, 0)
    basket(FGc)
    tf_pop()
    P_(8.1, 5.7, F0, 90)
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
    P_(2.7, 5.5, F0, -90)
    for k in range(5):
        rbox(FGc, MT('wood2'), 0, 0, 1.2 + k * 1.5, 7.0, 0.16, 1.2, 0.04, 1)
    rbox(FGc, MT('wood'), 0, -0.55, 0.0, 7.0, 7.8, 0.12, 0.03, 1)
    tf_pop()
    rnd = _random.Random(11)
    for k in range(5):
        for j in range(3):
            P_(2.7, 2.6 + j * 2.1, F0 + 1.36 + k * 1.5, -90)
            col = ('cardboard', 'blue', 'cream', 'red', 'yellow', 'teal')[(k + j) % 6]
            rbox(FGc, MT(col), 0, 0, 0.0, 1.7, 0.95, 0.9, 0.12, 2)
            rbox(FGc, MT('white'), 0, 0.46, 0.35, 0.7, 0.3, 0.02, 0.01, 1)
            tf_pop()
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
    P_(33.0, 3.0, F0, 90)
    toilet(FGc)
    tf_pop()
    P_(30.3, 6.7, F0, 180)
    pedestal_sink(FGc)
    tf_pop()
    P_(30.3, 7.4, F0 + 5.2, 180)
    rbox(FGc, MT('brass'), 0, 0, -1.4, 2.6, 2.8, 0.12, 0.06, 2)
    rbox(FGc, MT('mirror'), 0, -0.05, -1.25, 2.3, 2.5, 0.06, 0.03, 1)
    tf_pop()
    P_(31.5, 4.5, F0, 0)
    rug(FGc, 2.8, 1.8, 'teal', 'cream', 'yellow', False)
    tf_pop()
'''
