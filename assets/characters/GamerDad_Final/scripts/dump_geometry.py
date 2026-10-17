"""Dumps per-object geometry (world vertices, UV, polygons, material index, transforms) of a .blend or .fbx for a numeric reproducibility comparison.
blender -b [<file.blend>] --python dump_geometry.py -- <out.json> [--fbx <file.fbx> ...]
With --fbx the FBX files are imported into an EMPTY factory scene (importer defaults of the project: axis_forward Z, axis_up Y) and every mesh is dumped."""
import hashlib
import json
import os
import sys

import bpy

A = sys.argv[sys.argv.index("--") + 1:]
OUT = A[0]
fbxs = A[A.index("--fbx") + 1:] if "--fbx" in A else []
if fbxs:
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for f in fbxs:
        bpy.ops.import_scene.fbx(filepath=f, axis_forward='Z', axis_up='Y', use_custom_normals=False)
res = {}
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [tuple(round(c, 5) for c in (mw @ v.co)) for v in me.vertices]
    uv = me.uv_layers.active
    uvs = [tuple(round(c, 5) for c in uv.data[l].uv) for l in range(len(me.loops))] if uv else []
    polys = [tuple(p.vertices) for p in me.polygons]
    name = ob.name.replace("_Geo", "").split(".")[0]
    res[name] = {"verts": len(verts), "polys": len(polys), "tris": sum(len(p) - 2 for p in polys),
                 "vertex_hash": hashlib.sha256(json.dumps(sorted(verts)).encode()).hexdigest(), "uv_hash": hashlib.sha256(json.dumps(sorted(set(uvs))).encode()).hexdigest(),
                 "bbox_min": [min(v[i] for v in verts) for i in range(3)], "bbox_max": [max(v[i] for v in verts) for i in range(3)], "verts_sorted_sample": sorted(verts)[:3],
                 "materials": [m.name for m in ob.data.materials], "location": [round(c, 5) for c in ob.location]}
    ev.to_mesh_clear()
json.dump(res, open(OUT, "w"), indent=1)
print("DUMPED", OUT, len(res))
