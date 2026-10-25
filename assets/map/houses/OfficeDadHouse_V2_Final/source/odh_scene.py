"""Blender scene helpers: turn the geometry accumulator into objects, light the scene, take render shots (Cycles on CPU or Workbench)."""
import os
import math
import bpy
import bmesh
from mathutils import Vector

import odh_core as K
from odh_core import P, acc, finish_mesh, hexrgb, GLASS_COLORS, NEON_COLORS

ROOM_LIGHTS = []      # (name, x, h, z, energy)
_mats = {}
_colls = {}


def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(h):
    return tuple(srgb2lin(c) for c in hexrgb(h)) + (1.0,)


def hex_of(name):
    return P[name] if name in P else name


def material(name):
    if name in _mats:
        return _mats[name]
    hx = hex_of(name)
    m = bpy.data.materials.new('M_' + str(name))
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(hx)
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Specular IOR Level'].default_value = 0.25
    if name in GLASS_COLORS:
        b.inputs['Alpha'].default_value = 0.28
        b.inputs['Roughness'].default_value = 0.08
        m.surface_render_method = 'BLENDED'
    if name in NEON_COLORS:
        b.inputs['Emission Color'].default_value = lin(hx)
        b.inputs['Emission Strength'].default_value = 3.0
    m.diffuse_color = lin(hx)
    _mats[name] = m
    return m


def coll(name):
    if name not in _colls:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        _colls[name] = c
    return _colls[name]


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    _colls.clear()
    _mats.clear()


def materialize(skip=()):
    for (c, m), (vs, fs) in acc.items():
        if c in skip or not fs:
            continue
        me = bpy.data.meshes.new('%s_%s' % (c, m))
        me.from_pydata(vs, [], fs)
        me.update()
        finish_mesh(me, flat=c in ('Ground', 'Upper', 'Roof', 'Site', 'Biome'))   # flat shading: no gradient bands across wall panels
        ob = bpy.data.objects.new('%s_%s' % (c, m), me)
        ob.data.materials.append(material(m))
        coll(c).objects.link(ob)


def setup_scene(res=(1280, 800), samples=24, engine='CYCLES', sky=((0.36, 0.62, 0.95), 1.3), sun_energy=3.2):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.engine = engine
    if engine == 'CYCLES':
        sc.cycles.samples = samples
        sc.cycles.device = 'CPU'
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.cycles.diffuse_bounces = 3
    w = bpy.data.worlds.new('W') if not sc.world else sc.world
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (sky[0][0], sky[0][1], sky[0][2], 1.0)
    bg.inputs['Strength'].default_value = sky[1]
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = sun_energy
    sun.angle = math.radians(6)
    so = bpy.data.objects.new('Sun', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(52), math.radians(8), math.radians(-35))
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    return sc


def add_room_lights(on=True, scale=1.0):
    for (n, x, h, z, e) in ROOM_LIGHTS:
        L = bpy.data.lights.new('L_' + n, 'POINT')
        L.energy = e * scale
        L.shadow_soft_size = 1.0
        L.color = (1.0, 0.92, 0.78)
        o = bpy.data.objects.new('L_' + n, L)
        o.location = (x, -z, h)
        bpy.context.scene.collection.objects.link(o)
        o.hide_render = not on


def shot(path, loc, target, lens=26, hide=(), sun_hide=False, exp=0.0, res=None):
    """loc / target in PLOT coordinates (x, h, z)"""
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('cam')
    cam.lens = lens
    cam.clip_start = 0.1
    cam.clip_end = 2000
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    co.location = (loc[0], -loc[2], loc[1])
    d = Vector((target[0], -target[2], target[1])) - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.exposure = exp
    states = {}
    for name in hide:
        if name in _colls:
            states[name] = (_colls[name].hide_render, _colls[name].hide_viewport)
            _colls[name].hide_render = True
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for name, (hr, hv) in states.items():
        _colls[name].hide_render = hr
    bpy.data.objects.remove(co, do_unlink=True)
