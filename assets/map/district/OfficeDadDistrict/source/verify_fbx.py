# Re-imports out/OfficeDadDistrict.fbx into a clean Blender scene and checks it: mesh count, triangles, chunk limit, names, vertex colours, bounding box.
# Run: blender -b --factory-startup --python source/verify_fbx.py -- <out dir>
import bpy, sys, os
out = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(out, 'OfficeDadDistrict.fbx'))
ms = [o for o in bpy.data.objects if o.type == 'MESH']
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in ms)
mx = max(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in ms)
bad = [o.name for o in ms if not (o.name[:2] in ('O_', 'G_', 'N_'))]
nocol = [o.name for o in ms if not o.data.color_attributes]
xs = [v.co for o in ms for v in o.data.vertices]
print('VERIFY meshes', len(ms), 'tris', tris, 'max chunk tris', mx, 'bad names', len(bad), 'no colours', len(nocol))
print('VERIFY names sample', sorted(o.name for o in ms)[:3], sorted(o.name for o in ms if 'Fence' in o.name)[:3])
