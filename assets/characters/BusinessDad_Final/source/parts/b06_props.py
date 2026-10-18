# ----------------------------------------------------------------------------------------------
# phone (separate rigid prop in the left hand): near-black slab, rounded corners, two lenses + flash, no UI / text / logo
# ----------------------------------------------------------------------------------------------
PHONE_LOGICAL = (2.15, 1.52, 4.60)
PHONE_C = Bl(*PHONE_LOGICAL)
PHONE_YAW = 28.0                              # screen turned towards his face
PHONE_ROLL = 10.0                             # top leans outward (towards +X) as in the reference
_yaw, _roll = rot_xf(PHONE_C, PHONE_YAW, "Z"), rot_xf(PHONE_C, PHONE_ROLL, "Y")
PW, PT_, PH = .62, .12, 1.12                    # width X, thickness F, height H (revision 2: larger, as in the reference where the phone is ~0.7 of the fist width)
ph = PM("Phone", PHONE_C, geo="Phone_Geo", xf=lambda p: _yaw(_roll(p)))
PX, PY, PZ = PHONE_C.x, PHONE_C.y, PHONE_C.z
PR = .17


def phone_ring(y, grow=0.0):
    """rounded rectangle outline, 4 arcs x 4 points (revision 4: rounder corners as in the turnaround close-up)"""
    a, hh = PW / 2 + grow, PH / 2 + grow
    r = PR + grow
    pts = []
    for cxq, czq, a0 in ((a - r, hh - r, 0), (-a + r, hh - r, 90), (-a + r, -hh + r, 180), (a - r, -hh + r, 270)):
        for k in range(4):
            th = math.radians(a0 + 90 * k / 3)
            pts.append((cxq + r * math.cos(th), czq + r * math.sin(th)))
    return [V((PX + x, y, PZ + z)) for x, z in pts]


# body: front/back half-thickness PT_/2; edge frame slightly lighter, back dark; screen side faces -F (towards his face)
loft(ph, "PH_body", [phone_ring(PY - PT_ / 2 + .012, -.012), phone_ring(PY - PT_ / 2 + .02), phone_ring(PY + PT_ / 2 - .02), phone_ring(PY + PT_ / 2 - .012, -.012)], sh_const("PhoneBody"), band_tiles={1: "PhoneEdge"},
     meta={"recipe": "slab .50 x .09 x .92, corner radius .11 (octagon), edge band lighter", "class": "observed"})
back = PY - PT_ / 2                              # logical back of the phone faces +F = Blender -Y
for k, (lx, lz, r_) in enumerate(((-.15, .38, .075), (-.15, .22, .070))):
    cyl_y(ph, "PH_lens_ring_%d" % (k + 1), PX + lx, PZ + lz, back + .02, back - .034, r_ + .018, 10, sh_const("LensRing"), {"recipe": "lens ring", "class": "observed"})
    cyl_y(ph, "PH_lens_%d" % (k + 1), PX + lx, PZ + lz, back + .02, back - .042, r_, 10, sh_const("Lens"), {"recipe": "dark lens", "class": "observed"})
cyl_y(ph, "PH_flash", PX - .06, PZ + .45, back + .02, back - .030, .026, 8, sh_const("Flash"), {"recipe": "tiny flash", "class": "observed"})
# revision 3: raised camera island behind the lenses, two side buttons, thin glass inset on the back (all separate shells embedded in the slab, no coplanar faces)
solid_box(ph, "PH_camera_island", PX - .29, PX - .01, back - .020, back + .030, PZ + .13, PZ + .51, "PhoneEdge", {"recipe": "raised camera island .28 x .38, proud .02", "class": "observed"})
solid_box(ph, "PH_side_button_1", PX + PW / 2 - .01, PX + PW / 2 + .028, PY - .035, PY + .020, PZ + .12, PZ + .30, "PhoneEdge", {"recipe": "side button", "class": "extrapolated"})
solid_box(ph, "PH_side_button_2", PX + PW / 2 - .01, PX + PW / 2 + .028, PY - .035, PY + .020, PZ - .12, PZ + .02, "PhoneEdge", {"recipe": "side button", "class": "extrapolated"})
solid_box(ph, "PH_back_inset", PX - .22, PX + .22, back - .006, back + .030, PZ - .46, PZ + .06, "PhoneEdge", {"recipe": "slightly lighter back glass panel, proud .006", "class": "extrapolated"})
