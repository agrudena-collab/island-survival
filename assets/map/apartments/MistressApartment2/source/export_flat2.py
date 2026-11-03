# Chunking, FBX export, json, mesh integrity and review renders of flat 2 (exec'd by build_flat2.py).
MAXT = 9000
CELL = 24.0


def lin(h):
    c = [v / 255.0 for v in D.hexc(h)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = bpy.data.collections.new('FLAT2')
scene.collection.children.link(coll)
made = []
tris_total = 0
INVERTED, OPEN_ITEMS = [], [0]
for kind in D.KINDS:
    cells = {}
    for it in D.ITEMS[kind]:
        if -26 < it[0] < 47 and -19 < it[1] < 19:
            cells.setdefault((int(it[0] // CELL), int(it[1] // CELL)), []).append(it)
        else:
            cells.setdefault((int(it[0] // 150.0) + 40, int(it[1] // 150.0) + 40), []).append(it)
    for (ci, cj), items in sorted(cells.items()):
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
            name = '%s_%d_%d_%d' % (kind, ci + 20, cj + 20, gi)
            me = bpy.data.meshes.new(name)
            me.from_pydata([(x, -z, y) for (x, y, z) in verts], [], polys)
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
            pl = list(me.polygons)
            vc = [vv.co for vv in me.vertices]
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
                if all(c == 2 for c in ec.values()):
                    if vol < -1e-6:
                        INVERTED.append('%s polys %d..%d vol %.3f' % (name, a_, b_, vol))
                else:
                    OPEN_ITEMS[0] += 1
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            made.append(ob)
            tris_total += sum(len(p.vertices) - 2 for p in me.polygons)
print('CHUNKS', len(made), 'TRIS', tris_total, 'kinds', D.tri_count(), 'colliders', len(D.STATS['colliders']), 'lights', len(LIGHTS), 'elapsed %.1fs' % (time.time() - T0))

zero_faces = nan_verts = over = loose = 0
bad_names = []
for o in made:
    me = o.data
    if sum(len(p.vertices) - 2 for p in me.polygons) > MAXT:
        over += 1
    if not o.name[:2] in ('O_', 'G_', 'N_'):
        bad_names.append(o.name)
    zero_faces += sum(1 for p in me.polygons if p.area < 1e-9)
    nan_verts += sum(1 for v in me.vertices if any(c != c or abs(c) > 1e5 for c in v.co))
    used = set()
    for p in me.polygons:
        used.update(p.vertices)
    loose += len(me.vertices) - len(used)
with open(os.path.join(OUT, 'audit.txt'), 'a', encoding='utf-8') as fh:
    fh.write('NORMALS: inverted closed items %d, open (single-sided) items %d' % (len(INVERTED), OPEN_ITEMS[0]) + chr(10))
    for ln in INVERTED[:20]:
        fh.write('   ' + ln + chr(10))
    fh.write('MESH INTEGRITY: chunks %d, zero-area faces %d, NaN vertices %d, loose vertices %d, over-limit chunks %d, bad names %d' % (len(made), zero_faces, nan_verts, loose, over, len(bad_names)) + chr(10))
print('MESH INTEGRITY', len(made), 'zero', zero_faces, 'nan', nan_verts, 'loose', loose, 'over', over, 'inverted', len(INVERTED))

bpy.ops.object.select_all(action='DESELECT')
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = made[0]
FBX = os.path.join(OUT, 'MistressFlat2.fbx')
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                         mesh_smooth_type='FACE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False, path_mode='AUTO', embed_textures=False,
                         object_types={'MESH'}, colors_type='SRGB')
json.dump({'colliders': D.STATS['colliders'], 'cyl_colliders': [list(map(lambda v: round(v, 3) if not isinstance(v, str) else v, c)) for c in CYLC], 'anchors': D.STATS['anchors'],
           'signs': [dict(text=s[0], x=s[1], y=s[2], z=s[3], w=s[4], h=s[5], face=s[6]) for s in SIGNS],
           'lights': [list(map(lambda v: round(v, 2), l)) for l in LIGHTS], 'floor_top': FY, 'ceiling': CY, 'tris': tris_total, 'chunks': len(made)},
          open(os.path.join(OUT, 'flat.json'), 'w'), indent=1)
print('EXPORTED', FBX)

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
    cam.data.clip_end = 4000
    os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)

    def shot(name, loc, target, lens=24, ortho=None, clip=0.1, res=None):
        cam.location = Vector((loc[0], -loc[2], loc[1]))
        tgt = Vector((target[0], -target[2], target[1]))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.clip_start = clip
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
        ('plan', (10.5, 90, 0.001), (10.5, 0, 0), 35, 82, 78.6, (1500, 700)),
        ('hall', (-12, 8, 15.5), (4, 3.5, -4), 22, None, 0.1, None),
        ('desk_guest_view', (6, 6.2, -1.0), (6, 5.5, -13), 28, None, 0.1, None),
        ('desk_from_door', (-14, 6.5, 14), (6, 4.5, -10), 24, None, 0.1, None),
        ('kitchen', (-6, 8, 14), (-19, 4, -7), 22, None, 0.1, None),
        ('lounge', (-4, 7.5, 0), (16, 3.5, 11), 24, None, 0.1, None),
        ('window_view', (14.5, 7.2, -12.5), (4, -8.0, -90), 24, None, 0.1, None),
        ('bedroom', (26.5, 9, -1.5), (40, 3.5, -9), 22, None, 0.1, None),
        ('bath', (26, 8.5, 6), (38, 3, 14), 22, None, 0.1, None),
        ('entrance_door', (-16, 6.2, 5), (-16, 5, 17), 28, None, 0.1, None),
        ('plant_check', (-7.5, 8.0, 13.5), (-11.6, 7.2, 8.4), 30, None, 0.1, None),
        ('plant_check2', (8.0, 8.0, 10.0), (4.4, 7.0, 14.6), 30, None, 0.1, None),
        ('main_wide', (-21, 10.6, 14), (10, 3, -6), 16, None, 0.1, None),
    ]
    for (nm, loc, tgt, lens, ortho, clip, res) in SHOTS:
        if ONLY and nm not in ONLY:
            continue
        gl = [o for o in made if o.name.startswith('G_')] if nm == 'window_view' else []
        for o in gl:
            o.hide_render = True
        shot(nm, loc, tgt, lens=lens, ortho=ortho, clip=clip, res=res)
        for o in gl:
            o.hide_render = False
    print('RENDERED elapsed %.1fs' % (time.time() - T0))
