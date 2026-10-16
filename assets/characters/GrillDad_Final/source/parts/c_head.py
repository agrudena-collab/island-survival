

# ----------------------------------------------------------------------------------------------
# containers + shading rules + generators specific to Fisherman Dad
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_GrillDad")
SCENE.collection.children.link(EXP_COLL)
_H = {n: h for n, h, _ in PAL}
HEXOF = _H
OBS = {"class": "observed+prescribed"}
PRE = {"class": "prescribed"}


def meta(recipe, cls="observed+prescribed", **kw):
    d = {"recipe": recipe, "class": cls}
    d.update(kw)
    return d
