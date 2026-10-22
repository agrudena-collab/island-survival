"""Architecture layering audit: box-vs-box interpenetration and coplanar same-direction faces (z-fighting) among B() boxes (warped)."""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build_house_v5.py'), encoding='utf-8').read().rstrip()[:-len('main()')]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'audit_tmp')]
ns = {'__name__': 'ba', '__file__': os.path.join(HERE, 'build_house_v5.py')}
exec(compile(src, 'b', 'exec'), ns)
import bpy
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
ns['setup_scene'](); ns['build']()
FX, FZ, FH = ns['FX'], ns['FZ'], ns['FH']
site = lambda c: c == 'Site'
boxes = []
for (c, mn, x0, x1, h0, h1, z0, z1) in ns['BOXLOG']:
    if c == 'Site':
        continue
    boxes.append((c, mn, FX(x0), FX(x1), FH(h0), FH(h1), FZ(z0), FZ(z1)))
print('BOXES', len(boxes))
E = 0.02
inter = []
cop = []
for i in range(len(boxes)):
    a = boxes[i]
    for j in range(i + 1, len(boxes)):
        b = boxes[j]
        ox = min(a[3], b[3]) - max(a[2], b[2])
        oy = min(a[5], b[5]) - max(a[4], b[4])
        oz = min(a[7], b[7]) - max(a[6], b[6])
        if ox > E and oy > E and oz > E:
            inter.append((ox * oy * oz, min(ox, oy, oz), a, b))
        # coplanar faces: boxes touching/overlapping in plane with the same outward normal
        elif ox > -0.001 and oy > -0.001 and oz > -0.001:
            pass
inter.sort(key=lambda t: -t[0])
print('INTERPENETRATING', len(inter))
byp = collections.Counter()
for v, m, a, b in inter:
    byp[tuple(sorted((a[1], b[1])))] += 1
for k, n in byp.most_common(25):
    print('PAIR', k, n)
print('--- biggest overlaps')
for v, m, a, b in inter[:30]:
    print('OVL vol=%.2f min=%.2f %s %s [%.1f..%.1f x %.1f..%.1f x %.1f..%.1f] vs %s %s [%.1f..%.1f x %.1f..%.1f x %.1f..%.1f]' % ((v, m, a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7])))
# coplanar same-direction faces: outward faces at the same coordinate with overlapping area
faces = []   # (axis, coord, sign, (u0,u1,v0,v1), mat, idx)
for k, (c, mn, x0, x1, h0, h1, z0, z1) in enumerate(boxes):
    faces += [(0, x0, -1, (h0, h1, z0, z1), mn, k), (0, x1, 1, (h0, h1, z0, z1), mn, k),
              (1, h0, -1, (x0, x1, z0, z1), mn, k), (1, h1, 1, (x0, x1, z0, z1), mn, k),
              (2, z0, -1, (x0, x1, h0, h1), mn, k), (2, z1, 1, (x0, x1, h0, h1), mn, k)]
byaxis = collections.defaultdict(list)
for f in faces:
    byaxis[(f[0], f[2], round(f[1], 2))].append(f)
zf = collections.Counter()
ex = collections.defaultdict(list)
for key, lst in byaxis.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            a, b = lst[i], lst[j]
            if a[5] == b[5] or a[4] == b[4]:
                continue
            ou = min(a[3][1], b[3][1]) - max(a[3][0], b[3][0])
            ov = min(a[3][3], b[3][3]) - max(a[3][2], b[3][2])
            if ou > 0.05 and ov > 0.05:
                pr = tuple(sorted((a[4], b[4])))
                zf[pr] += 1
                if len(ex[pr]) < 3:
                    ex[pr].append((key, round(ou, 2), round(ov, 2), (round(max(a[3][0], b[3][0]), 1), round(max(a[3][2], b[3][2]), 1))))
print('COPLANAR_DIFFERENT_MATERIAL', sum(zf.values()))
for k, n in zf.most_common(30):
    print('ZF', k, n, ex[k])
