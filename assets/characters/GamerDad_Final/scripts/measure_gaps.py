"""Triangle-based clearances between registered components (needs a build made with --keepcomp: the per-face 'comp' attribute).
blender -b <build_keepcomp>/source/GamerDad_Sweatshirt_Review.blend --python measure_gaps.py -- <component_registry.json> <out.json>
distance = min over (vertices of A to the surface of B) and (vertices of B to the surface of A) plus edge-midpoint / face-centre samples; overlaps = BVH triangle pairs."""
import json
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

A = sys.argv[sys.argv.index("--") + 1:]
REG = json.load(open(A[0]))["components"]
OUT = A[1]
objs = {o.name.replace("_Geo", ""): o for o in bpy.data.objects if o.type == "MESH"}
IDS = [r["id"] for r in REG]


def comp_tris(part, ids):
    o = objs[part]
    me = o.data
    attr = me.attributes.get("comp")
    keep = set()
    for pi in range(len(me.polygons)):
        cid = REG[attr.data[pi].value]["id"]
        if any(cid == i or cid.startswith(i) for i in ids):
            keep.add(pi)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    return bm


def samples(bm):
    for f in bm.faces:
        pts = [v.co for v in f.verts]
        yield from pts
        yield f.calc_center_median()
        for i in range(3):
            yield (pts[i] + pts[(i + 1) % 3]) / 2


def pair(a, b):
    ta, tb = BVHTree.FromBMesh(a), BVHTree.FromBMesh(b)
    d = 1e9
    for p in samples(a):
        loc, n, i, dist = tb.find_nearest(p)
        d = min(d, dist)
    for p in samples(b):
        loc, n, i, dist = ta.find_nearest(p)
        d = min(d, dist)
    return {"min_distance": round(d, 4), "overlapping_triangle_pairs": len(ta.overlap(tb))}


G = {
    "beard": ("Head", ["HD_beard"]), "moustache": ("Head", ["HD_moustache"]), "hair": ("Head", ["HD_hair_cap", "HD_lock"]), "head_shell": ("Head", ["HD_shell"]),
    "mic": ("Headset", ["HS_mic", "HS_boom"]), "cups": ("Headset", ["HS_cup_", "HS_pad_"]), "cup_bodies": ("Headset", ["HS_cup_"]), "pads": ("Headset", ["HS_pad_"]), "band": ("Headset", ["HS_band"]),
    "can": ("EnergyCan", ["CAN_body"]), "right_hand": ("RightHand", ["HAND_palm_Right"]), "right_forearm": ("RightLowerArm", ["LA_sleeve_Right"]), "right_cuff": ("RightLowerArm", ["LA_cuff_Right"]),
    "left_hand": ("LeftHand", ["HAND_palm_Left"]), "pelvis": ("LowerTorso", ["LT_pelvis", "LT_waistband"]), "torso": ("UpperTorso", ["UT_shell"]),
}
bms = {k: comp_tris(*v) for k, v in G.items()}
PAIRS = [("beard", "mic"), ("beard", "cups"), ("beard", "cup_bodies"), ("beard", "pads"), ("hair", "cup_bodies"), ("beard", "band"), ("moustache", "mic"), ("hair", "mic"), ("hair", "cups"), ("hair", "band"), ("can", "right_hand"), ("can", "right_forearm"), ("can", "right_cuff"),
         ("right_hand", "right_cuff"), ("left_hand", "pelvis"), ("left_hand", "torso"), ("beard", "head_shell")]
res = {"{}_vs_{}".format(a, b): pair(bms[a], bms[b]) for a, b in PAIRS}
json.dump(res, open(OUT, "w"), indent=1)
for k, v in res.items():
    print("GAP", k, v)


def self_isect(bm):
    b2 = bm.copy()
    bmesh.ops.remove_doubles(b2, verts=b2.verts, dist=1e-5)
    b2.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(b2)
    n = 0
    for i, j in tree.overlap(tree):
        if i >= j:
            continue
        if {v.index for v in b2.faces[i].verts} & {v.index for v in b2.faces[j].verts}:
            continue
        n += 1
    b2.free()
    return n


SI = {}
for name, (part, ids) in {"beard": ("Head", ["HD_beard"]), "hair_cap": ("Head", ["HD_hair_cap"]), "UA_sleeve_Right": ("RightUpperArm", ["UA_sleeve_Right"]), "UA_sleeve_Left": ("LeftUpperArm", ["UA_sleeve_Left"]),
                          "LA_sleeve_Right": ("RightLowerArm", ["LA_sleeve_Right"]), "LA_sleeve_Left": ("LeftLowerArm", ["LA_sleeve_Left"]), "can": ("EnergyCan", ["CAN_body"]),
                          "headset_band": ("Headset", ["HS_band"]), "boom": ("Headset", ["HS_boom"]), "UT_shell": ("UpperTorso", ["UT_shell"]), "HD_shell": ("Head", ["HD_shell"])}.items():
    SI[name] = self_isect(comp_tris(part, ids))
json.dump({"pair_clearances": res, "self_intersections_per_component": SI}, open(OUT, "w"), indent=1)
print("SELF", SI)
