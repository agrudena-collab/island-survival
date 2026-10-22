import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build_house_v5.py'), encoding='utf-8').read().rstrip()[:-len('main()')]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'audit_tmp')]
ns = {'__name__': 'cb', '__file__': os.path.join(HERE, 'build_house_v5.py')}
exec(compile(src, 'b', 'exec'), ns)
import bpy
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
ns['setup_scene'](); ns['build']()
FX, FZ, FH = ns['FX'], ns['FZ'], ns['FH']
out = []
for (c, mn, x0, x1, h0, h1, z0, z1) in ns['BOXLOG']:
    if c not in ('Ground', 'Upper'):
        continue
    if mn.startswith(('glass', 'trim')) and False:
        continue
    X0, X1, Z0, Z1, H0, H1 = FX(x0), FX(x1), FZ(z0), FZ(z1), FH(h0), FH(h1)
    dx, dy, dz = X1 - X0, H1 - H0, Z1 - Z0
    if min(dx, dy, dz) < 0.25 and max(dx, dy, dz) < 6:
        continue
    out.append([round((X0 + X1) / 2, 3), round((H0 + H1) / 2, 3), round((Z0 + Z1) / 2, 3), round(dx, 3), round(dy, 3), round(dz, 3), mn])
json.dump(out, open(os.path.join(HERE, 'roblox_export', 'collision_boxes.json'), 'w'))
print('BOXES', len(out), 'of', len(ns['BOXLOG']))
lines = []
for r in ns['COLL']:
    lines.append(r[0] + ',' + ','.join(('%.2f' % v).rstrip('0').rstrip('.') for v in r[1:]))
open(os.path.join(HERE, 'roblox_export', 'yard_colliders.txt'), 'w').write(';'.join(lines))
import collections
print('YARD_COLLIDERS', dict(collections.Counter(r[0] for r in ns['COLL'])))
open(os.path.join(HERE, 'roblox_export', 'boxes.txt'), 'w').write(';'.join(','.join(('%.2f' % v).rstrip('0').rstrip('.') for v in r[:6]) for r in out))

# ---- gameplay anchors and door openings (final, warped coordinates)
FXw, FZw, FHw = ns['FX'], ns['FZ'], ns['FH']
doors = []
for (ax, ctr, w, h0, hh, wall, th, kind) in ns['DOORLOG']:
    if ax == 'x':
        x0, x1 = FXw(ctr - w / 2), FXw(ctr + w / 2)
        doors.append(dict(kind=kind, axis='x', cx=(x0 + x1) / 2, cz=FZw(wall), width=x1 - x0, y0=FHw(h0), height=FHw(h0 + hh) - FHw(h0), thick=th))
    else:
        z0, z1 = FZw(ctr - w / 2), FZw(ctr + w / 2)
        doors.append(dict(kind=kind, axis='z', cx=FXw(wall), cz=(z0 + z1) / 2, width=z1 - z0, y0=FHw(h0), height=FHw(h0 + hh) - FHw(h0), thick=th))
anch = {k: [round(v[0], 3), round(v[1], 3), round(v[2], 3), round(v[3], 3), round(v[4], 3)] for k, v in ns['ANCH'].items()}
# closet (walk-in cupboard of the laundry) centre
anch['closet_centre'] = [round((FXw(ns['HX'] + 1.8) + FXw(ns['HX'] + 6.5)) / 2, 3), round(ns['F0'], 3), round((FZw(ns['HZ'] + 1.8) + FZw(ns['HZ'] + 9.5)) / 2, 3), 1.0, 0.0]
cover = [dict(name=c[0], x=round(c[1], 3), y=round(c[2], 3), z=round(c[3], 3), w=round(c[4], 3), d=round(c[5], 3), h=round(c[6], 3), yaw=round(c[7], 5)) for c in ns['COVER']]
json.dump(dict(doors=doors, anchors=anch, cover=cover), open(os.path.join(HERE, 'roblox_export', 'interactive.json'), 'w'), indent=1)
print('INTERACTIVE', len(doors), 'doors', list(anch))
