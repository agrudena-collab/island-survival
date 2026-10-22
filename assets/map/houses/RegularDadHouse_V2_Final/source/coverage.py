import sys, os, re, inspect, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'build_house_v5.py'), encoding='utf-8').read().rstrip()[:-len('main()')]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'audit_tmp')]
ns = {'__name__': 'cov', '__file__': os.path.join(HERE, 'build_house_v5.py')}
exec(compile(src, 'b', 'exec'), ns)
import bpy
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
names = set()
for fn in ('hq_models1.py', 'hq_rooms1.py', 'hq_rooms2.py', 'hq_rooms3.py'):
    names |= set(re.findall(r'^def (\w+)', open(os.path.join(HERE, fn), encoding='utf-8').read(), re.M))
names = {n for n in names if not n.startswith('hq_') and n in ns and n != 'P_'}
acc = ns['acc']; orig = ns['emit']
groups = []; st = {'d': 0, 'cur': None}
def emit_w(c, m, verts, faces, two_sided=False):
    key = (c, m); vs, fs = acc.setdefault(key, ([], []))
    v0 = len(vs); orig(c, m, verts, faces, two_sided)
    g = st['cur']
    if g is None:
        g = dict(c=c, pts=[]); groups.append(g)
    g['c'] = c
    g['pts'] += vs[v0:]
ns['emit'] = emit_w
def wrap(n):
    fn = ns[n]
    def w(*a, **k):
        top = st['d'] == 0
        if top:
            st['cur'] = dict(c=None, pts=[]); groups.append(st['cur'])
        st['d'] += 1
        try: return fn(*a, **k)
        finally:
            st['d'] -= 1
            if top: st['cur'] = None
    ns[n] = w
for n in names:
    if n not in ('rbox','lathe','cylinder','sphere','tube','torus','leaf','sheet','book','ring_pts','emit'):
        wrap(n)
ns['setup_scene'](); ns['build']()
FX, FZ, FH, HX, HZ = ns['FX'], ns['FZ'], ns['FH'], ns['HX'], ns['HZ']
rooms = {'hall':(0,1.8,13.5,22.5,42.2),'kitchen':(0,1.8,13.5,10.5,21.5),'laundry':(0,7.5,13.5,1.8,9.5),'dining':(0,14.5,34.2,1.8,21.5),'living':(0,14.5,34.2,22.5,42.2),
'bath':(1,1.8,13.5,1.8,9.5),'uphall':(1,1.8,13.5,10.5,42.2),'lounge':(1,14.5,34.2,1.8,15.5),'child':(1,14.5,34.2,16.5,29.5),'master':(1,14.5,34.2,30.5,42.2)}
cov = collections.defaultdict(float); area = {}
for k, (fl, u0, u1, v0, v1) in rooms.items():
    x0, x1, z0, z1 = FX(HX+u0), FX(HX+u1), FZ(HZ+v0), FZ(HZ+v1)
    area[k] = (x1-x0)*(z1-z0)
    ylo = FH(ns['F1'] if fl else ns['F0']); yhi = ylo + 4.0
    for g in groups:
        if not g['pts'] or not g['c'] or not g['c'].startswith('Furn_'): continue
        xs = [p[0] for p in g['pts']]; zs = [-p[1] for p in g['pts']]; hs = [p[2] for p in g['pts']]
        if min(hs) > ylo + 1.0 or max(hs) < ylo: continue   # not a floor-standing item of this storey
        cx, cz = (min(xs)+max(xs))/2, (min(zs)+max(zs))/2
        if x0 <= cx <= x1 and z0 <= cz <= z1:
            w = max(xs)-min(xs); d = max(zs)-min(zs)
            if w*d < area[k]*0.5:
                cov[k] += w*d
for k in rooms:
    print('COV %-8s area=%7.1f furniture_footprint=%6.1f  coverage=%4.1f%%' % (k, area[k], cov[k], 100*cov[k]/area[k]))
