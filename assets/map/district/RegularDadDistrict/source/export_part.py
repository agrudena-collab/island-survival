# Second half of build_district.py (exec'd): chunk the python meshes, build Blender objects, export the FBX, json and renders.
MAXT = 9000
CELL = 48.0


def lin(h):
    c = [v / 255.0 for v in D.hexc(h)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
coll = bpy.data.collections.new('RDD')
scene.collection.children.link(coll)
made = []
tris_total = 0
for kind in D.KINDS:
    cells = {}
    for it in D.ITEMS[kind]:
        cells.setdefault((int(it[0] // CELL), int(it[1] // CELL)), []).append(it)
    for (ci, cj), items in sorted(cells.items()):
        part = []
        cur = ([], [], [], 0)
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
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            made.append(ob)
            tris_total += sum(len(p.vertices) - 2 for p in me.polygons)
print('CHUNKS', len(made), 'TRIS', tris_total, 'kinds', D.tri_count(), 'elapsed %.1fs' % (time.time() - T0))

# ---- export FBX + json
bpy.ops.object.select_all(action='DESELECT')
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = made[0]
FBX = os.path.join(OUT, 'RDD_District.fbx')
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                         mesh_smooth_type='FACE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False, path_mode='AUTO', embed_textures=False,
                         object_types={'MESH'}, colors_type='SRGB')
bb = [[min(v.co[i] for o in made for v in o.data.vertices) for i in range(3)], [max(v.co[i] for o in made for v in o.data.vertices) for i in range(3)]]
json.dump({'colliders': D.STATS['colliders'], 'anchors': D.STATS['anchors'], 'signs': [dict(text=s[0], x=s[1], y=s[2], z=s[3], w=s[4], h=s[5], face=s[6]) for s in SIGNS],
           'lights': [list(map(lambda v: round(v, 2), l)) for l in LIGHTS], 'ground_top': GY, 'tris': tris_total, 'chunks': len(made), 'bbox_blender': bb},
          open(os.path.join(OUT, 'district.json'), 'w'), indent=1)
print('EXPORTED', FBX, 'colliders', len(D.STATS['colliders']), 'signs', len(SIGNS), 'lights', len(LIGHTS))

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

    def shot(name, loc, target, lens=35, ortho=None):
        # Studio-like locations -> Blender
        cam.location = Vector((loc[0], -loc[2], loc[1]))
        tgt = Vector((target[0], -target[2], target[1]))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        if ortho:
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = ortho
        else:
            cam.data.type = 'PERSP'
            cam.data.lens = lens
        sc.render.filepath = os.path.join(OUT, 'renders', name + '.png')
        bpy.ops.render.render(write_still=True)

    shot('aerial_sw', (-330, 260, 330), (0, 20, 0), lens=30)
    shot('aerial_ne', (330, 230, -330), (0, 20, 0), lens=30)
    shot('plan', (0, 900, 0.001), (0, 0, 0), ortho=520)
    shot('tower_street', (-100, 12, 25), (-100, 60, -62), lens=24)
    shot('tower_front', (-100, 8, -20), (-100, 14, -62), lens=30)
    shot('hardware', (60, 10, -10), (75, 8, -52), lens=30)
    shot('park', (60, 14, 60), (120, 4, 120), lens=28)
    print('RENDERED', 'elapsed %.1fs' % (time.time() - T0))
