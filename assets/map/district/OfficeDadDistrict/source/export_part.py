# Second half of build_district.py (exec'd): chunk the python meshes, build Blender objects, export the FBX, json and renders.
MAXT = 9000
CELL = 48.0


def lin(h):
    c = [v / 255.0 for v in D.hexc(h)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


INVERTED = []
OPEN_ITEMS = [0]
OPEN_BY = {}
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = bpy.data.collections.new('ODD')
scene.collection.children.link(coll)
made = []
tris_total = 0


def emit(name, items):
    """build chunk meshes (<= MAXT tris each) from python items; returns the created objects"""
    global tris_total
    out = []
    groups = []
    verts, polys, cols, rng, tris = [], [], [], [], 0
    for (cx, cz, v, f, col) in items:
        t = sum(len(p) - 2 for p in f)
        if tris + t > MAXT and verts:
            groups.append((verts, polys, cols, rng))
            verts, polys, cols, rng, tris = [], [], [], [], 0
        base = len(verts)
        verts.extend(v)
        p0 = len(polys)
        for p in f:
            polys.append(tuple(base + i for i in p))
            cols.append(col)
        rng.append((p0, len(polys)))
        tris += t
    if verts:
        groups.append((verts, polys, cols, rng))
    for gi, (verts, polys, cols, rng) in enumerate(groups):
        nm = '%s_%d' % (name, gi)
        me = bpy.data.meshes.new(nm)
        me.from_pydata([(x, -z, y) for (x, y, z) in verts], [], polys)    # Studio-like (x,y,z) -> Blender (x,-z,y)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        ca = me.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
        li = 0
        for pi, p in enumerate(me.polygons):
            c4 = lin(cols[pi])
            for _ in range(p.loop_total):
                ca.data[li].color = c4
                li += 1
        for p in me.polygons:
            p.use_smooth = False
        # orientation check: a closed item must have a positive signed volume (outward normals), otherwise it is invisible from outside in Studio
        pl = list(me.polygons)
        vc = [v.co for v in me.vertices]
        for (a_, b_) in rng:
            ec = {}
            vol = 0.0
            o_ = vc[list(pl[a_].vertices)[0]]
            for p in pl[a_:b_]:
                ids = list(p.vertices)
                for q in range(len(ids)):
                    key = (min(ids[q], ids[(q + 1) % len(ids)]), max(ids[q], ids[(q + 1) % len(ids)]))
                    ec[key] = ec.get(key, 0) + 1
                for q in range(1, len(ids) - 1):
                    vol += (vc[ids[0]] - o_).dot((vc[ids[q]] - o_).cross(vc[ids[q + 1]] - o_)) / 6.0
            closed = all(c == 2 for c in ec.values())
            if closed and vol < -1e-6:
                INVERTED.append('%s polys %d..%d vol %.3f' % (nm, a_, b_, vol))
            elif not closed:
                OPEN_ITEMS[0] += 1
                OPEN_BY[b_ - a_] = OPEN_BY.get(b_ - a_, 0) + 1
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        out.append(ob)
        tris_total += sum(len(p.vertices) - 2 for p in me.polygons)
    return out


for kind in D.KINDS:
    cells = {}
    for it in D.ITEMS[kind]:
        cells.setdefault((int(it[0] // CELL), int(it[1] // CELL)), []).append(it)
    for (ci, cj), items in sorted(cells.items()):
        made += emit('%s_%d_%d' % (kind, ci + 20, cj + 20), items)
for nm, items in sorted(FENCE.items()):
    made += emit('O_Fence_%s' % nm, items)           # removable perimeter sections (collider edge<nm>)
print('CHUNKS', len(made), 'TRIS', tris_total, 'kinds', D.tri_count(), 'elapsed %.1fs' % (time.time() - T0))

# ---- mesh integrity of every chunk (appended to audit_all.txt)
MESHCHK = []
zero_faces = nan_verts = over = loose = 0
names = set()
for o in made:
    me = o.data
    nt = sum(len(p.vertices) - 2 for p in me.polygons)
    if nt > MAXT:
        over += 1
        MESHCHK.append('chunk %s has %d tris (> %d)' % (o.name, nt, MAXT))
    if o.name in names:
        MESHCHK.append('duplicate chunk name %s' % o.name)
    names.add(o.name)
    if not (o.name.startswith('O_') or o.name.startswith('G_') or o.name.startswith('N_')):
        MESHCHK.append('bad chunk name %s' % o.name)
    for p in me.polygons:
        if p.area < 1e-9:
            zero_faces += 1
    for v in me.vertices:
        if any(c != c or abs(c) > 1e5 for c in v.co):
            nan_verts += 1
    used = set()
    for p in me.polygons:
        used.update(p.vertices)
    loose += len(me.vertices) - len(used)
    if not me.color_attributes:
        MESHCHK.append('chunk %s has no vertex colours' % o.name)
with open(os.path.join(OUT, 'audit_all.txt'), 'a', encoding='utf-8') as fh:
    fh.write('NORMALS: inverted closed items %d, open (single-sided) items %d' % (len(INVERTED), OPEN_ITEMS[0]) + chr(10))
    fh.write('   open items by polygon count: ' + str(sorted(OPEN_BY.items(), key=lambda kv: -kv[1])[:10]) + chr(10))
    for ln in INVERTED[:20]:
        fh.write('   ' + ln + chr(10))
    fh.write('MESH INTEGRITY: chunks %d, zero-area faces %d, NaN/huge vertices %d, loose vertices %d, over-limit chunks %d' % (len(made), zero_faces, nan_verts, loose, over) + chr(10))
    for ln in MESHCHK[:40]:
        fh.write('   ' + ln + chr(10))
print('MESH INTEGRITY', len(made), 'zero', zero_faces, 'nan', nan_verts, 'loose', loose, 'over', over)

# ---- export FBX + json
bpy.ops.object.select_all(action='DESELECT')
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = made[0]
FBX = os.path.join(OUT, 'OfficeDadDistrict.fbx')
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                         mesh_smooth_type='FACE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False, path_mode='AUTO', embed_textures=False,
                         object_types={'MESH'}, colors_type='SRGB')
bb = [[min(v.co[i] for o in made for v in o.data.vertices) for i in range(3)], [max(v.co[i] for o in made for v in o.data.vertices) for i in range(3)]]
fence_tris = sum(sum(len(f) - 2 for f in it[3]) for its in FENCE.values() for it in its)
json.dump({'colliders': D.STATS['colliders'], 'anchors': D.STATS['anchors'], 'signs': [dict(text=s[0], x=round(s[1], 3), y=round(s[2], 3), z=round(s[3], 3), w=round(s[4], 3), h=round(s[5], 3), face=s[6]) for s in SIGNS],
           'lights': [list(map(lambda v: round(v, 2), l)) for l in LIGHTS], 'ground_top': GY, 'tris': tris_total, 'chunks': len(made), 'bbox_blender': bb},
          open(os.path.join(OUT, 'district.json'), 'w'), indent=1)
json.dump({'buildings': [dict(name=n, x0=x0, x1=x1, z0=z0, z1=z1, top=t, wall=w, floors=fl, front=fr) for (n, x0, x1, z0, z1, t, w, fl, fr) in BLD_INFO],
           'trees': [[round(t[0], 1), round(t[1], 1), round(t[2], 1)] for t in TREES], 'streets': [dict(name=s_['name'], ew=s_['ew'], c=s_['c'], ah=s_['ah'], sh=s_['sh'], ext=s_['ext']) for s_ in STREETS],
           'park': list(PK), 'fountain': list(PC), 'gardens': [list(G1), list(G2)], 'lots': [list(l) for l in LOTS], 'plaza': list(PLZ), 'tower': [TW.x0, TW.x1, TW.z0, TW.z1], 'half': HALF,
           'bus': [BSX, BSZ]}, open(os.path.join(OUT, 'skyline.json'), 'w'))
print('EXPORTED', FBX, 'colliders', len(D.STATS['colliders']), 'signs', len(SIGNS), 'lights', len(LIGHTS), 'fence tris', fence_tris)

# ---- renders (Workbench, vertex colours)
if not NORENDER:
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = 1500, 950
    sh = sc.display.shading
    sh.light, sh.color_type, sh.show_cavity = 'STUDIO', 'VERTEX', False
    sh.studio_light = 'paint.sl'
    sc.display_settings.display_device = 'sRGB'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    w.color = (0.62, 0.80, 0.96)
    sc.world = w
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_end = 5000
    os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)

    def shot(name, loc, target, lens=35, ortho=None, res=None):
        cam.location = Vector((loc[0], -loc[2], loc[1]))
        tgt = Vector((target[0], -target[2], target[1]))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        if ortho:
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = ortho
        else:
            cam.data.type = 'PERSP'
            cam.data.lens = lens
        sc.render.resolution_x, sc.render.resolution_y = res or (1500, 950)
        sc.render.filepath = os.path.join(OUT, 'renders', name + '.png')
        bpy.ops.render.render(write_still=True)

    ONLY = [a.split('=')[1] for a in args if a.startswith('--only=')]
    SHOTS = [
        ('aerial_sw', (-400, 300, 400), (30, 20, -10), 32, None),
        ('aerial_ne', (400, 280, -400), (20, 20, 10), 32, None),
        ('plan', (0, 900, 0.001), (0, 0, 0), 35, 520),
        ('tower_avenue', (46, 7, 44), (112, 52, -45), 24, None),
        ('tower_plaza', (66, 6.5, -22), (104, 24, -45), 22, None),
        ('tower_entrance', (86, 6.5, -45), (100, 12, -45), 24, None),
        ('tower_aerial', (30, 150, 70), (112, 65, -45), 30, None),
        ('crossroads', (12, 6.5, 12), (44, 4, 30), 22, None),
        ('park_fountain', (-20, 14, 6), (-48, 4, -48), 26, None),
        ('park_playground', (-50, 14, -55), (-84, 3, -82), 28, None),
        ('street_eye_B', (46, 6, 200), (46, 6, 60), 30, None),
        ('connector_E', (180, 7, 30), (250, 5, 30), 28, None),
        ('retail_row', (-130, 6.5, 40), (-210, 12, 70), 26, None),
        ('parking_P1', (-140, 40, 150), (-200, 2, 185), 28, None),
        ('bus_stop', (50, 8, -2), (59, 6, -15), 28, None),
        ('connector_W', (-190, 7, 30), (-250, 5, 30), 28, None),
        ('connector_N', (40, 7, -190), (40, 5, -250), 28, None),
        ('connector_S', (40, 7, 190), (40, 5, 250), 28, None),
        ('eye_tower_approach', (66, 5.5, -45), (100, 9, -45), 26, None),
        ('eye_park_path', (-100, 5.5, -48), (-48, 5, -48), 26, None),
        ('eye_avenue_A', (-60, 5.5, 22), (60, 6, 22), 30, None),
        ('detail_storefront', (-222, 6, 47), (-210, 7, 60), 30, None),
        ('detail_cornice', (-52, 26, 48), (-62, 17, 60), 35, None),
        ('detail_lobby', (104, 6, 50), (100, 7, 70), 28, None),
        ('detail_tower_corner', (88, 8, -70), (100, 12, -59), 30, None),
        ('detail_curb_corner', (14, 3.5, 14), (30, 1, 26), 40, None),
        ('detail_window', (-80, 14, 40), (-75, 17, 60), 40, None),
        ('tree_check', (-22, 9, -88), (-30, 11, -98), 32, None),
    ]
    for (nm, loc, tgt, lens, ortho) in SHOTS:
        if ONLY and nm not in ONLY:
            continue
        shot(nm, loc, tgt, lens=lens, ortho=ortho, res=(1200, 1200) if nm == 'plan' else None)
    print('RENDERED', 'elapsed %.1fs' % (time.time() - T0))
