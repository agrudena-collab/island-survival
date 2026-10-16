

# ----------------------------------------------------------------------------------------------
# GrillTongs (sections 24..27): two wooden handles, two steel stems, two paddles, lower bridge
# ----------------------------------------------------------------------------------------------
tg = PM("GrillTongs", GRIP_C)
BLADE_PROFILE = [(-.055, 5.03), (-.18, 5.30), (-.19, 5.67), (-.07, 5.92), (.10, 5.82), (.18, 5.50), (.11, 5.20), (.055, 5.03)]


def blade_u(h):
    return .265 + (.325 - .265) * (h - 5.03) / (5.92 - 5.03)


for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    wood_h = [2.56, 3.10, 3.50, 3.90, 4.25]
    P = [V((GRIP_C.x + s * branch_u(h), GRIP_C.y, h)) for h in wood_h]
    sweep(tg, "TG_wood_" + nm, P, [.13, .15, .15, .155, .16], [.16, .17, .17, .175, .18], sh_wood, up=V((0, -1, 0)), n=8, c=.02,
          meta_=meta("wooden handle H2.56..4.25, section .13x.16 -> .16x.18, centre u=+/-.055..+.145", dims={"levels": wood_h}))
    box_c(tg, "TG_cap_" + nm, (GRIP_C.x + s * .055, GRIP_C.y, 2.53), (.13, .16, .06), sh_const("WOOD_DARK"), ch=.012, meta_=meta("dark end cap H2.50..2.56 W.13 D.16", "observed+prescribed"))
    st_h = [4.17, 4.30, 4.72, 5.05, 5.11]
    P = [V((GRIP_C.x + s * branch_u(h), GRIP_C.y, h)) for h in st_h]
    sweep(tg, "TG_stem_" + nm, P, [.075, .075, .08, .105, .105], [.085] * 5, sh_steel, up=V((0, -1, 0)), n=8, c=.012,
          meta_=meta("steel stem H4.17..5.11 (enters the wood .08 and the paddle .06), .075..105 x .085", dims={"levels": st_h}))
    pts = []
    for px, h in BLADE_PROFILE:
        pts.append((GRIP_C.x + s * (blade_u(h) + px), h))
    if s < 0:
        pts = pts[::-1]
    xs = [p[0] for p in pts]
    xmin, xmax = min(xs), max(xs)

    def front_fn(x, h, _xmin=xmin, _xmax=xmax, _s=s):
        t = (x - _xmin) / (_xmax - _xmin)
        if _s < 0:
            t = 1 - t
        return GRIP_C.y - .0425 + (.02 * (t - .35) / .65 if t > .35 else 0.0)

    def btile(n, c, _xmin=xmin, _xmax=xmax, _s=s):
        if abs(n.y) < .35:
            return "STEEL_EDGE" if n.z > .3 else "STEEL_LIGHT"
        if n.y < -.5:
            t = (c.x - _xmin) / (_xmax - _xmin)
            if _s < 0:
                t = 1 - t
            return "STEEL_DARK" if t > .35 else "STEEL"
        return "STEEL_DARK"

    plate(tg, "TG_blade_" + nm, pts, lambda x, h: GRIP_C.y + .0425, front_fn, btile, ch=.012, meta_=meta("steel paddle thickness .085, profile of section 27, one plane break at 35% width (dD .02)", dims={"profile": BLADE_PROFILE}))
box_c(tg, "TG_bridge", (GRIP_C.x, GRIP_C.y, 2.58), (.12, .07, .08), sh_const("STEEL"), ch=.012, meta_=meta("lower bridge W.12 D.07 H.08", "prescribed"))
