"""Mesh overlap audit of the built model. For every pair of the 16 meshes (BVH on the evaluated meshes):
  - coplanar_candidates: faces of A whose centre lies within 2 mm (0.002 stud) of the surface of B with an (anti)parallel normal  -> potential z-fighting
  - overlapping_triangle_pairs: triangle pairs that intersect (expected only at joints / hidden embeds)
blender -b <package>/source/BusinessDad_Review.blend --python overlap_audit.py -- <package_dir> [out.json]"""
import bpy, bmesh, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PKG = sys.argv[sys.argv.index("--") + 1]
dg = bpy.context.evaluated_depsgraph_get()
obs = [o for o in bpy.data.objects if o.type == 'MESH']
data = {}
for o in obs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ev.matrix_world); bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    data[o.name] = {"bvh": BVHTree.FromBMesh(bm), "faces": [(f.calc_center_median(), f.normal.copy(), f.calc_area()) for f in bm.faces]}
    ev.to_mesh_clear(); bm.free()
names = sorted(data)
rows = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        ov = len(data[a]["bvh"].overlap(data[b]["bvh"]))
        cop = 0
        area = 0.0
        for src, dst in ((a, b), (b, a)):
            for c, n, ar in data[src]["faces"]:
                loc, nn, idx, dist = data[dst]["bvh"].find_nearest(c, 0.01)
                if loc is not None and dist < 0.002 and abs(n.dot(nn)) > 0.98:
                    cop += 1
                    area += ar
        if ov or cop:
            rows.append({"a": a, "b": b, "overlapping_triangle_pairs": ov, "coplanar_candidate_faces": cop, "coplanar_area": round(area, 4)})
rows.sort(key=lambda r: -r["coplanar_area"])
out = sys.argv[sys.argv.index("--") + 2] if len(sys.argv) > sys.argv.index("--") + 2 else PKG + "/data/overlap_audit.json"
json.dump({"pairs_with_overlap_or_coplanar": rows, "n_meshes": len(names)}, open(out, "w"), indent=1)
print("AUDIT pairs", len(rows))
for r in rows[:14]:
    print("AUDIT", r)
