# Chunking, FBX export, json and review renders of the flat (exec'd by build_flat.py).
MAXT = 9000
CELL = 40.0


def lin(h):
    c = [v / 255.0 for v in D.hexc(h)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = bpy.data.collections.new('FLAT')
scene.collection.children.link(coll)
made = []
tris_total = 0
for kind in D.KINDS:
    cells = {}
    for it in D.ITEMS[kind]:
        cells.setdefault((int(it[0] // CELL), int(it[1] // CELL)), []).append(it)
    for (ci, cj), items in sorted(cells.items()):
        groups = []
        verts, polys, cols, tris = [], [], [], 0
        for (cx, cz, v, f, col) in items:
            t = sum(len(p) - 2 for p in f)
            if tris + t > MAXT and verts:
                groups.append((verts, polys, cols))
                verts, polys, cols, tris = [], [], [], 0
            base = len(verts)
            verts.extend(v)
            for p in f:
                polys.append(tuple(base + i for i in p))
                cols.append(col)
            tris += t
        if verts:
            groups.append((verts, polys, cols))
        for gi, (verts, polys, cols) in enumerate(groups):
            name = '%s_%d_%d_%d' % (kind, ci + 20, cj + 20, gi)
            me = bpy.data.meshes.new(name)
            me.from_pydata([(x, -z, y) for (x, y, z) in verts], [], polys)
            me.update()
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            if ROUND:
                for ed in bm.edges:                  # smooth shading on curved surfaces, hard edges where faces meet at > 38 degrees
                    ed.smooth = not (len(ed.link_faces) == 2 and ed.calc_face_angle(0.0) > 0.66)
                for fc in bm.faces:
                    fc.smooth = True
            bm.to_mesh(me)
            bm.free()
            ca = me.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
            li = 0
            for pi, p in enumerate(me.polygons):
                c4 = lin(cols[pi])
                for _ in range(p.loop_total):
                    ca.data[li].color = c4
                    li += 1
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            made.append(ob)
            tris_total += sum(len(p.vertices) - 2 for p in me.polygons)
print('CHUNKS', len(made), 'TRIS', tris_total, 'kinds', D.tri_count(), 'colliders', len(D.STATS['colliders']), 'lights', len(LIGHTS), 'elapsed %.1fs' % (time.time() - T0))

bpy.ops.object.select_all(action='DESELECT')
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = made[0]
FBX = os.path.join(OUT, 'MistressFlat.fbx')
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                         mesh_smooth_type='EDGE' if ROUND else 'FACE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False, path_mode='AUTO', embed_textures=False,
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

    def shot(name, loc, target, lens=24, ortho=None, clip=0.1):
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
        sc.render.filepath = os.path.join(OUT, 'renders', name + '.png')
        bpy.ops.render.render(write_still=True)

    shot('plan', (12, 90, 0.001), (12, 0, 0), ortho=82, clip=78.6)
    shot('hall', (-12, 7.5, 15), (4, 3.5, -4), lens=22)
    shot('dining', (-12, 8, 6), (4, 3, -9), lens=24)
    shot('living', (6, 8, -13), (16, 3, 9), lens=22)
    shot('kitchen', (-6, 8, 14), (-19, 4, -7), lens=22)
    shot('bedroom', (24.2, 9, -1.5), (40, 3, -8), lens=22)
    shot('bath', (24, 8.5, 5), (36, 3, 12), lens=22)
    shot('window', (2, 5.5, 8), (2, 6, -30), lens=26)
    print('RENDERED elapsed %.1fs' % (time.time() - T0))
