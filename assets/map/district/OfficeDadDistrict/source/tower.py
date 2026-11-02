# The red mistress tower (10 storeys) and its plaza.  Plan: x 100..136, plan-y 31..59 (z -59..-31), door on the west face toward the plaza.
META = []                                      # (name, rect, front side, door position u, wall colour, door width) for the entrance paths and fillers
TW = rect_bl(100, 136, 31, 59)
TW_DOOR_U = 14.0
H_T = building(TW, 10, PAL['tower'], PAL['white'], fh=PD.FLOOR_H, front='W', ground_h=PD.TOWER_GROUND_H, win_w=3.8, balconies=True, name='tower', seed=11, tank=True, tall=True,
               band=PAL['navy'], band_h=1.0, door_w=7.2, door_h=9.2, canopy=PAL['roof'], door_depth=5.0, entrance_u=TW_DOOR_U,
               storefronts=[(2.5, 9.0, None), (19.0, 25.5, None)], front_bulk=PAL['navy'], ac_prob=0.1, flowers_prob=0.0)
front_face_sign('APARTMENTS', TW, 'W', TW_DOOR_U, PD.TOWER_GROUND_H, 20, PAL['navy'])
occ('bld', TW.x0 - 1.5, TW.x1 + 1.5, TW.z0 - 1.5, TW.z1 + 1.5)
_tcz = (TW.z0 + TW.z1) / 2                      # door centre line z = -45
anchor('tower_entrance', 93.5, SWY, _tcz, 1, 0)         # in front of the door, looking at it (the door faces west)
anchor('tower_exit_arrival', 84.0, SWY, _tcz, -1, 0)    # on the plaza, looking out to the avenue (west)

# ---- plaza: z -82..9 so it joins the avenue crossing; a 10-wide corridor on the door axis stays clear
PLZ = (61.0, 100.0, -82.0, 9.0)
paved(PLZ[0], PLZ[1], PLZ[2], PLZ[3], name='plaza', zone='p', tag='plaza')
for (x, z) in ((70, -72), (92, -72), (70, -18), (92, -18)):
    planter(x, z, 4.8, 4.8, y=SWY, col=PAL['brick2'])
for (x, z) in ((66, -78), (93, -78), (66, 3), (93, 3), (66, -62), (93, -62), (66, -28), (93, -28)):
    tree(x, z, seed=int(x + z), h=10, r=4.4, y=SWY)
for (x, z, r_) in ((76, -57.5, 180), (86, -57.5, 180), (76, -32.5, 0), (86, -32.5, 0)):
    bench(x, z, rot=r_, y=SWY)
for (x, z) in ((64, -35), (64, -55), (84, -68), (98, -24), (80, -78), (80, 4)):
    street_lamp(x, z, facing=math.pi / 2 if z > -45 else -math.pi / 2, y=SWY)
bike_rack(80, -70, 0, y=SWY)
bike_rack(80, -12, 0, y=SWY)
trash_bin(74, -45 - 8.5, y=SWY)
trash_bin(74, -45 + 8.5, y=SWY)

# ---- bus stop on the east sidewalk of Avenue B (shelter along z, back toward the plaza; the only other sign: BUS)
BSX, BSZ = 59.2, -15.0                           # (x across the sidewalk 52..61, z along the avenue)


def sb(u0, u1, y0, y1, v0, v1, col, kind='O'):
    box(BSX + v0, BSX + v1, y0, y1, BSZ + u0, BSZ + u1, col, kind)


sb(-5.2, 5.2, SWY, SWY + 0.12, -1.9, 1.9, PAL['walk3'])
for u in (-4.8, 4.8):
    sb(u - 0.14, u + 0.14, SWY + 0.12, SWY + 8.5, 1.45, 1.75, PAL['dark'])
    sb(u - 0.14, u + 0.14, SWY + 0.12, SWY + 8.5, -1.75, -1.45, PAL['dark'])
sb(-5.4, 5.4, SWY + 8.5, SWY + 9.2, -2.2, 2.2, PAL['teal'])
sb(-5.1, 5.1, SWY + 9.2, SWY + 9.5, -1.9, 1.9, PAL['white'])
sb(-4.7, 4.7, SWY + 2.8, SWY + 8.3, 1.55, 1.7, PAL['glass'], 'G')                 # back glass (toward the plaza)
sb(4.55, 4.75, SWY + 2.8, SWY + 8.3, -1.6, 1.55, PAL['glass'], 'G')               # south end glass
sb(-4.75, -4.55, SWY + 2.8, SWY + 8.3, -1.6, 1.55, PAL['glass'], 'G')            # north end glass
sb(-2.2, 2.2, SWY + 1.0, SWY + 1.15, 0.5, 1.3, PAL['wood'])                      # seat
sb(-2.0, -1.8, SWY + 0.12, SWY + 1.0, 0.6, 1.2, PAL['dark'])
sb(1.8, 2.0, SWY + 0.12, SWY + 1.0, 0.6, 1.2, PAL['dark'])
collider(BSX - 2.2, BSX + 2.2, SWY, SWY + 9.5, BSZ - 5.4, BSZ + 5.4, 'busstop')
# BUS post with a blue board facing the road (west)
sb(-7.1, -6.9, SWY + 0.12, SWY + 12.5, -0.1, 0.1, PAL['dark'])
box(BSX - 0.25, BSX + 0.25, SWY + 10.0, SWY + 12.5, BSZ - 8.4, BSZ - 5.6, PAL['blue'])
SIGNS.append(('BUS', BSX - 0.25, SWY + 11.25, BSZ - 7.0, 2.6, 2.1, 'W'))      # sign position = front face plane of the board
collider(BSX - 0.25, BSX + 0.25, SWY, SWY + 12.5, BSZ - 7.1, BSZ - 6.9, 'buspost')
occ('bus', BSX - 2.4, BSX + 2.4, BSZ - 8.5, BSZ + 5.6)
