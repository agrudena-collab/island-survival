"""Stage-1 plan of OfficeDadDistrict (proposal, nothing is built yet).
Coordinates are Blender XY in studs: +X east, +Y north, centre of the district = (0, 0).  Roblox z = -Y (after the usual 180 deg turn the file notes it).
The same data feeds the SVG plan and the Blender block renders, so the plan and the renders always agree."""

HALF = 250                     # district 500 x 500
FLOOR_H = 11.0                 # studs per floor (matched to district 1 RegularDadDistrict: fh=11)
GROUND_H = 13.0                # ground-floor height (district 1: 13, towers 14)
TOWER_GROUND_H = 14.0          # tower ground floor (district 1 tower uses 14)
# building height = GROUND_H + (floors-1)*FLOOR_H  ->  tower 10 floors = 14 + 9*11 = 113 studs

# streets: (name, axis, centre, half asphalt, half street incl. sidewalks, connector?)
STREETS = [
    ('Avenue A', 'x', -30, 12, 21, True),     # runs east-west at y = -30
    ('Avenue B', 'y', 40, 12, 21, True),      # runs north-south at x = 40
    ('Street C', 'y', -130, 8, 15, False),    # side street, north-south, closed by the fence at both ends
    ('Street D', 'x', 120, 8, 15, False),     # side street, east-west, closed by the fence at both ends
]

# facade palette (Office Dad vivid): key -> hex
PAL = {
    'blue':   '#A9CBEA',   # blue-grey stucco (Office Dad signature)
    'steel':  '#9CB8EC',
    'sand':   '#F8DCA6',
    'cream':  '#F6F4EC',
    'brick':  '#C4633F',
    'teal':   '#9AD9DA',
    'stone':  '#DCD0BB',
    'red':    '#CF4A3C',   # tower facade (Ivan: red, to stand out against the biome)
}
ROOF = '#2D58B0'

# buildings: id, x0, x1, y0, y1, floors, kind, facade, front side (where the door/shopfront looks)
B = [
    ('TOWER', 100, 136, 31, 59, 10, 'башня любовницы 2', 'red', 'W'),
    # south-west block
    ('B01', -245, -175, -110, -60, 3, 'торговое', 'brick', 'N'),
    ('B02', -170, -148, -100, -60, 2, 'торговое', 'sand', 'N'),
    # south-middle block
    ('B03', -108, -62, -120, -60, 6, 'деловое', 'steel', 'N'),
    ('B04', -52, 12, -110, -60, 5, 'деловое', 'cream', 'N'),
    ('B05', -105, -55, -200, -140, 5, 'деловое', 'blue', 'W'),
    # south-east block
    ('B06', 75, 125, -125, -70, 7, 'деловое', 'blue', 'N'),
    ('B07', 140, 200, -120, -70, 6, 'деловое', 'steel', 'N'),
    ('B08', 75, 140, -230, -170, 4, 'деловое', 'cream', 'W'),
    # west-middle block
    ('B09', -245, -180, 0, 50, 3, 'торговое', 'sand', 'E'),
    ('B10', -245, -185, 60, 100, 2, 'торговое', 'teal', 'E'),
    ('B11', -175, -152, 55, 100, 2, 'торговое', 'brick', 'E'),
    # east-middle block (behind the tower)
    ('B12', 150, 240, 62, 100, 3, 'торговое', 'stone', 'S'),
    # north-west block
    ('B13', -240, -185, 145, 190, 6, 'жилое', 'sand', 'S'),
    ('B14', -240, -185, 200, 245, 5, 'жилое', 'teal', 'S'),
    # north-middle block
    ('B15', -108, -55, 142, 200, 5, 'смешанное', 'steel', 'S'),
    ('B16', -45, 12, 142, 195, 5, 'деловое', 'blue', 'S'),
    ('B17', -100, -55, 210, 245, 2, 'торговое', 'cream', 'S'),
    # north-east block
    ('B18', 70, 125, 150, 215, 7, 'деловое', 'blue', 'W'),
    ('B19', 140, 200, 145, 200, 6, 'деловое', 'steel', 'S'),
    ('B20', 210, 245, 145, 190, 3, 'торговое', 'brick', 'S'),
]

# open areas: id, x0, x1, y0, y1, label, colour
AREAS = [
    ('PARK',  -115, 19, -9, 105, 'сквер: фонтан, площадка, скамейки, киоск', '#8FD07A'),
    ('PLAZA',  61, 100, 8, 82, 'площадь башни (вход с козырьком)', '#DAD7CE'),
    ('P1',   -245, -150, -245, -120, 'парковка P1 с разметкой', '#9AA0AA'),
    ('P2',    150, 240, -4, 50, 'парковка P2 (за башней)', '#9AA0AA'),
    ('P3',    150, 240, -240, -150, 'парковка P3', '#9AA0AA'),
    ('GARD1', -45, 12, -200, -130, 'дворик-сквер', '#8FD07A'),
    ('GARD2', 135, 245, 205, 245, 'двор-сад, детская площадка', '#8FD07A'),
]

# small forms with sign (the only signs allowed: APARTMENTS on the tower, BUS)
SMALL = [
    ('BUS', 57, 15, 'автобусная остановка (вывеска BUS)'),
    ('KIOSK', -30, -3, 'газетный киоск (без вывески)'),
    ('FOUNTAIN', -48, 48, 'фонтан'),
]

# anchors: name -> (x, y, dirX, dirY)   direction in Blender XY, facing where the player looks
ANCHORS = {
    'tower_entrance':      (95, 45, 1, 0),      # in front of the door, door faces west, the player comes from the west and looks east
    'tower_exit_arrival':  (82, 45, -1, 0),     # appears on the plaza, faces the street (west)
    'connector_E': (250, -30, 1, 0),
    'connector_W': (-250, -30, -1, 0),
    'connector_N': (40, 250, 0, 1),
    'connector_S': (40, -250, 0, -1),
}
GAP = 22                       # fence gap half width at connectors (as in district 1)
