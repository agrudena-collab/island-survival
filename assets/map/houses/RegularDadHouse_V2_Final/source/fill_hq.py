# Free-lawn fill (executed inside build_house_v5.py after yard_hq.py): park in front of the lot, play area, fountain, scattered trees.
# Final plot coordinates; the lot itself was pushed to z -60..39.4, sidewalk starts at z 101.4.


def fountain(c):
    COLL.append(('cyl',) + _wpos() + (5.6, 1.6))
    st = MT('plinth')
    lathe(c, st, [(0.0, 0.0), (5.6, 0.0), (5.6, 1.5), (5.2, 1.5), (5.2, 0.5), (0.0, 0.5)], 0, 0, 0, 28)
    lathe(c, MT('glass'), [(0.0, 1.2), (5.1, 1.2)], 0, 0, 0, 28, caps=False)
    lathe(c, st, [(0.0, 0.5), (1.1, 0.5), (0.8, 1.6), (0.7, 3.6), (1.0, 4.0), (0.0, 4.0)], 0, 0, 0, 16)
    lathe(c, st, [(0.0, 3.9), (2.9, 4.1), (3.1, 4.7), (2.8, 4.7), (0.0, 4.3)], 0, 0, 0, 22, caps=False)
    lathe(c, MT('glass'), [(0.0, 4.5), (2.7, 4.5)], 0, 0, 0, 22, caps=False)
    tube(c, st, [(0, 4.3, 0), (0, 6.2, 0)], 0.3, 10)
    sphere(c, st, 0, 0, 6.4, 0.55, 0.55, 0.55, 12, 8)
    for k in range(8):
        a = 2 * math.pi * k / 8
        pts = [(0, 6.6, 0), (math.cos(a) * 1.2, 7.4, math.sin(a) * 1.2), (math.cos(a) * 2.3, 6.2, math.sin(a) * 2.3), (math.cos(a) * 2.6, 4.7, math.sin(a) * 2.6)]
        tube(c, MT('glass'), pts, 0.07, 5)


def plaza(c, r=10.0):
    lathe(c, MT('walk'), [(0.0, 0.0), (r, 0.0), (r, 0.18), (0.0, 0.18)], 0, 0, 0, 36)
    torus(c, MT('plinth'), 0, 0, 0.18, r - 0.2, 0.18, 'xz', 36, 6)


def slide(c):
    for sx in (-1, 1):
        _wcyl(sx * 1.0, -2.0, 0.25, 6.4)
        _wcyl(sx * 1.0, 0.6, 0.25, 6.4)
    _wbox(0.0, 4.4, 2.2, 7.0, 3.0)
    r = MT('red')
    for sx in (-1, 1):
        tube(c, r, [(sx * 1.0, 0.0, -2.0), (sx * 1.0, 6.2, -2.0)], 0.14, 6)
        tube(c, r, [(sx * 1.0, 0.0, 0.6), (sx * 1.0, 6.2, 0.6)], 0.14, 6)
    rbox(c, MT('yellow'), 0, -0.7, 6.0, 2.4, 0.3, 3.2, 0.06, 1)
    for k in range(7):
        tube(c, MT('metal'), [(-1.0, 0.7 + k * 0.8, -2.1), (1.0, 0.7 + k * 0.8, -2.1)], 0.06, 5)
    for sx in (-1, 1):
        tube(c, MT('metal'), [(sx * 1.0, 6.2, -2.0), (sx * 1.0, 7.8, -2.0), (sx * 1.0, 7.8, 0.4), (sx * 1.0, 6.4, 0.6)], 0.07, 5)
    n = 14
    verts, faces = [], []
    for i in range(n + 1):
        t = i / n
        z = 0.9 + t * 7.0
        y = max(6.0 - 5.5 * (1 - (1 - t) ** 2) - 0.5 * t, 0.35)
        verts.append((-0.95, y, z))
        verts.append((0.95, y, z))
    for i in range(n):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    emit(c, MT('blue'), verts, faces, True)
    for sx in (-1, 1):
        pts = [(sx * 1.0, max(6.0 - 5.5 * (1 - (1 - i / n) ** 2) - 0.5 * i / n, 0.35) + 0.5, 0.9 + i / n * 7.0) for i in range(n + 1)]
        tube(c, MT('blue'), pts, 0.1, 5)


def seesaw(c):
    for sx in (-0.4, 0.4):
        tube(c, MT('metal'), [(sx, 0.0, -0.9), (sx * 0.2, 1.5, 0.0), (sx, 0.0, 0.9)], 0.07, 5)
    tube(c, MT('yellow'), [(-4.2, 2.6, 0), (0, 1.6, 0), (4.2, 0.6, 0)], 0.3, 4)
    for sx, y in ((-3.6, 3.0), (3.6, 1.0)):
        tube(c, MT('dark'), [(sx, y, 0.0), (sx, y + 0.9, 0.0)], 0.05, 4)
        tube(c, MT('dark'), [(sx - 0.4, y + 0.9, 0.0), (sx + 0.4, y + 0.9, 0.0)], 0.05, 4)


def merry_go_round(c):
    lathe(c, MT('blue'), [(0.0, 0.7), (3.2, 0.7), (3.2, 0.95), (0.0, 0.95)], 0, 0, 0, 24)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        tube(c, MT('metal'), [(0, 0.95, 0), (math.cos(a) * 3.0, 0.95, math.sin(a) * 3.0)], 0.07, 5)
        tube(c, MT('metal'), [(math.cos(a) * 3.0, 0.95, math.sin(a) * 3.0), (math.cos(a) * 3.0, 2.6, math.sin(a) * 3.0), (math.cos(a + 0.4) * 2.2, 2.9, math.sin(a + 0.4) * 2.2)], 0.07, 5)
    torus(c, MT('metal'), 0, 0, 2.8, 2.1, 0.07, 'xz', 24, 5)
    cylinder(c, MT('metal'), 0, 0, 0.0, 0.7, 0.35, 10)
    sphere(c, MT('red'), 0, 0, 1.3, 0.4, 0.4, 0.4, 8, 5)


def hoop(c):
    tube(c, MT('dark'), [(0, 0.0, 0), (0, 10.0, 0)], 0.22, 8)
    tube(c, MT('dark'), [(0, 9.4, 0), (0, 9.6, 0.8), (0, 9.6, 2.0)], 0.1, 6)
    rbox(c, MT('white'), 0, 2.2, 9.5, 0.2, 3.2, 4.2, 0.08, 1)
    rbox(c, MT('red'), 0, 2.31, 9.6, 0.05, 1.4, 1.9, 0.02, 1)
    torus(c, MT('orange'), 0, 3.15, 9.6, 0.85, 0.06, 'xz', 20, 5)
    for k in range(10):
        a = 2 * math.pi * k / 10
        tube(c, MT('white'), [(math.cos(a) * 0.85, 9.55, 3.15 + math.sin(a) * 0.85), (math.cos(a) * 0.4, 8.4, 3.15 + math.sin(a) * 0.4)], 0.02, 3)
    sphere(c, MT('orange'), 3.0, 0.5, 0.6, 0.6, 0.6, 0.6, 12, 8)


def soccer_goal(c):
    m = MT('white')
    for sx in (-1, 1):
        tube(c, m, [(sx * 4.2, 0.0, 0), (sx * 4.2, 4.2, 0), (sx * 4.2, 4.2, -2.6), (sx * 4.2, 0.0, -2.6)], 0.14, 6)
    tube(c, m, [(-4.2, 4.2, 0), (4.2, 4.2, 0)], 0.14, 6)
    for k in range(9):
        x = -4.0 + k
        tube(c, m, [(x, 4.2, 0), (x, 4.2, -2.6), (x, 0.0, -2.6)], 0.015, 3)
    for k in range(6):
        y = 0.6 + k * 0.7
        tube(c, m, [(-4.2, y, -2.6), (4.2, y, -2.6)], 0.015, 3)
    sphere(c, MT('white'), 2.0, 3.0, 0.55, 0.55, 0.55, 0.55, 10, 7)


def hq_fill():
    S = FY
    rnd = _random.Random(11)

    def at0(x, z, rot=0.0, y=0.0):
        tf_push(x, z, y, rot)

    # ---- front park: plaza + fountain on the path, flower rings, benches, lamps along the path
    at0(36.0, 72.0)
    plaza(S, 10.0)
    fountain(S)
    tf_pop()
    for (x, z) in ((26.5, 62.5), (45.5, 62.5), (26.5, 81.5), (45.5, 81.5)):
        at0(x, z)
        flower_patch(S, 5.0, 2.5, int(x + z))
        tf_pop()
    for (x, z, r) in ((24.0, 72.0, 90), (48.0, 72.0, -90)):
        at0(x, z, r)
        bench(S, 6.0)
        tf_pop()
    for z in (47.0, 55.0, 89.0, 96.0):
        for x in (31.0, 41.0):
            at0(x, z)
            lamp_post(S)
            tf_pop()
    for k in range(10):
        x = 8.0 + k * 9.5
        if 27.0 < x < 45.0:
            continue
        at0(x, 42.3)
        flower_patch(S, 8.0, 2.4, 100 + k)
        tf_pop()
    # ---- west: picnic grove
    for (x, z, sd) in ((8.0, 52.0, 41), (14.0, 90.0, 42)):
        at0(x, z)
        tree_oak(S, 1.2, sd, 'oak' if sd % 2 else 'cherry')
        tf_pop()
    at0(21.5, 50.0)
    tree_oak(S, 1.0, 43, 'apple')
    tf_pop()
    for z in (64.0, 78.0):
        at0(11.0, z, 90)
        picnic_table(S, True)
        tf_pop()
    at0(20.0, 71.0)
    trash_can(S, 'teal')
    tf_pop()
    at0(5.5, 71.0)
    bush(S, 1.2, 44, 'pink')
    tf_pop()
    # ---- east: playground and sports
    at0(60.0, 58.0, 180)
    slide(S)
    tf_pop()
    at0(80.0, 56.0, 90)
    swing_set(S)
    tf_pop()
    at0(92.0, 62.0, 90)
    seesaw(S)
    tf_pop()
    at0(62.0, 78.0)
    merry_go_round(S)
    tf_pop()
    at0(80.0, 76.0)
    sandbox(S)
    tf_pop()
    at0(89.0, 90.0, 0)
    hoop(S)
    tf_pop()
    at0(58.0, 93.0, 180)
    soccer_goal(S)
    tf_pop()
    for (x, z, r) in ((70.0, 66.0, 180), (72.0, 86.0, 0)):
        at0(x, z, r)
        bench(S, 6.0)
        tf_pop()
    for (x, z, sd, kd) in ((52.0, 48.0, 45, 'cherry'), (94.0, 48.0, 46, 'oak'), (70.0, 50.0, 47, 'apple')):
        at0(x, z)
        tree_oak(S, 1.1, sd, kd)
        tf_pop()
    at0(95.0, 84.0)
    trash_can(S, 'blue')
    tf_pop()
    # ---- scattered trees / bushes / flower patches on the remaining lawn
    houses = [(-34.0, 62.0, 26.0, 22.0), (-34.0, 22.0, 22.0, 18.0), (126.0, 62.0, 28.0, 24.0), (126.0, 22.0, 22.0, 18.0)]
    keep_out = [(-4.0, 103.0, -64.0, 46.0), (27.0, 45.0, 38.0, 103.0), (0.0, 27.0, 46.0, 98.0), (46.0, 100.0, 46.0, 100.0)]
    keep_out.append((-80.0, 190.0, 92.0, 106.0))     # street trees / sidewalk strip
    for (x, z, w, d) in houses:
        keep_out.append((x - w / 2 - 12.0, x + w / 2 + 12.0, z - d / 2 - 11.0, z + d / 2 + 11.0))
    placed = []

    def free(x, z, r):
        if any(x0 - r < x < x1 + r and z0 - r < z < z1 + r for (x0, x1, z0, z1) in keep_out):
            return False
        return all((x - px) ** 2 + (z - pz) ** 2 > (r + pr) ** 2 for (px, pz, pr) in placed)

    kinds = ['oak', 'apple', 'cherry', 'autumn', 'pine']
    n_tr = 0
    for _ in range(900):
        x, z = rnd.uniform(-66.0, 172.0), rnd.uniform(-56.0, 96.0)
        s = rnd.uniform(1.0, 1.5)
        r = 6.2 * s
        if n_tr < 46 and free(x, z, r):
            k = rnd.choice(kinds)
            at0(x, z)
            if k == 'pine':
                tree_pine(S, s * 0.9, rnd.randrange(999))
            else:
                tree_oak(S, s, rnd.randrange(999), k)
            tf_pop()
            placed.append((x, z, r))
            n_tr += 1
    n_b = 0
    for _ in range(900):
        x, z = rnd.uniform(-66.0, 172.0), rnd.uniform(-56.0, 98.0)
        if n_b < 70 and free(x, z, 2.2):
            at0(x, z)
            if n_b % 3 == 0:
                flower_patch(S, rnd.uniform(4.0, 7.0), rnd.uniform(2.0, 3.5), rnd.randrange(999))
            else:
                bush(S, rnd.uniform(0.9, 1.4), rnd.randrange(999), rnd.choice(['pink', 'yellow', 'white', 'red', None]))
            tf_pop()
            placed.append((x, z, 2.6))
            n_b += 1
