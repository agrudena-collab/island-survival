"""Writes plan.svg (2D plan with dimensions) and palette.svg from plan_data.py.  Run: py make_plan_svg.py <out dir>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_data as P

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
S = 1.9
M = 60
W = int(2 * P.HALF * S + 2 * M + 330)
H = int(2 * P.HALF * S + 2 * M)


def X(x):
    return M + (x + P.HALF) * S


def Y(y):
    return M + (P.HALF - y) * S


def rect(x0, x1, y0, y1, fill, stroke='none', sw=1, op=1.0, extra=''):
    return (f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{(x1 - x0) * S:.1f}" height="{(y1 - y0) * S:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}" {extra}/>')


def text(x, y, s, size=11, fill='#1B2A41', anchor='middle', weight='normal'):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,sans-serif" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'


o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
     f'<rect width="{W}" height="{H}" fill="#F4F6F8"/>']
o.append(rect(-P.HALF, P.HALF, -P.HALF, P.HALF, '#CFE8C0'))                      # grass base

# streets (sidewalk, asphalt)
for (nm, ax, c, ha, hs, conn) in P.STREETS:
    if ax == 'x':
        o.append(rect(-P.HALF, P.HALF, c - hs, c + hs, '#DAD7CE'))
    else:
        o.append(rect(c - hs, c + hs, -P.HALF, P.HALF, '#DAD7CE'))
for (nm, ax, c, ha, hs, conn) in P.STREETS:
    if ax == 'x':
        o.append(rect(-P.HALF, P.HALF, c - ha, c + ha, '#464B58'))
    else:
        o.append(rect(c - ha, c + ha, -P.HALF, P.HALF, '#464B58'))
# centre lines
for (nm, ax, c, ha, hs, conn) in P.STREETS:
    if ax == 'x':
        o.append(f'<line x1="{X(-P.HALF)}" y1="{Y(c):.1f}" x2="{X(P.HALF)}" y2="{Y(c):.1f}" stroke="#F8D030" stroke-width="1.4" stroke-dasharray="8 6"/>')
    else:
        o.append(f'<line x1="{X(c):.1f}" y1="{Y(-P.HALF)}" x2="{X(c):.1f}" y2="{Y(P.HALF)}" stroke="#F8D030" stroke-width="1.4" stroke-dasharray="8 6"/>')

for (i, x0, x1, y0, y1, lab, col) in P.AREAS:
    o.append(rect(x0, x1, y0, y1, col, '#6E7480', 0.8, 0.95))
    o.append(text(X((x0 + x1) / 2), Y(y1) + 14, i, 12, '#1B2A41', weight='bold'))

for (i, x0, x1, y0, y1, fl, kind, fac, front) in P.B:
    col = P.PAL[fac]
    o.append(rect(x0, x1, y0, y1, col, '#2D58B0', 1.4 if i != 'TOWER' else 3))
    o.append(rect(x0 + 2, x1 - 2, y0 + 2, y1 - 2, P.ROOF, 'none', 0, 0.28))
    cx, cy = X((x0 + x1) / 2), Y((y0 + y1) / 2)
    if i == 'TOWER':
        o.append(text(cx, Y(y1) - 7, f'БАШНЯ · {fl} эт', 12, '#10213B', weight='bold'))
    else:
        narrow = (x1 - x0) < 30
        o.append(text(cx, cy - 2, i, 12, '#10213B', weight='bold'))
        o.append(text(cx, cy + 11, f'{fl} эт' if narrow else f'{fl} эт · {kind}', 9.5, '#10213B'))
    fx = {'N': ((x0 + x1) / 2, y1), 'S': ((x0 + x1) / 2, y0), 'E': (x1, (y0 + y1) / 2), 'W': (x0, (y0 + y1) / 2)}[front]
    o.append(f'<circle cx="{X(fx[0]):.1f}" cy="{Y(fx[1]):.1f}" r="3.4" fill="#E43A2E"/>')

for (n, x, y, lab) in P.SMALL:
    o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="6" fill="#F4BA3A" stroke="#1B2A41" stroke-width="1"/>')
    o.append(text(X(x) + 9, Y(y) + 4, n, 10, '#1B2A41', 'start', 'bold'))

# perimeter fence with gaps
for (name, (x, y, dx, dy)) in P.ANCHORS.items():
    if name.startswith('connector'):
        if dx:
            o.append(f'<rect x="{X(x) - 5:.1f}" y="{Y(y + P.GAP):.1f}" width="10" height="{2 * P.GAP * S:.1f}" fill="#F4F6F8" stroke="#E43A2E" stroke-width="1.5"/>')
        else:
            o.append(f'<rect x="{X(x - P.GAP):.1f}" y="{Y(y) - 5:.1f}" width="{2 * P.GAP * S:.1f}" height="10" fill="#F4F6F8" stroke="#E43A2E" stroke-width="1.5"/>')
o.append(f'<rect x="{X(-P.HALF):.1f}" y="{Y(P.HALF):.1f}" width="{2 * P.HALF * S:.1f}" height="{2 * P.HALF * S:.1f}" fill="none" stroke="#1F7A4D" stroke-width="3" stroke-dasharray="14 5"/>')

# anchors
for (name, (x, y, dx, dy)) in P.ANCHORS.items():
    c = '#E43A2E' if not name.startswith('connector') else '#7B3FE4'
    o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="5" fill="{c}"/>')
    o.append(f'<line x1="{X(x):.1f}" y1="{Y(y):.1f}" x2="{X(x) + dx * 20:.1f}" y2="{Y(y) - dy * 20:.1f}" stroke="{c}" stroke-width="2"/>')
    lx = X(x) + (-6 if dx > 0 else 6 if dx < 0 else 8)
    ly = Y(y) + (-8 if name.startswith('tower_exit') else 14 if dy <= 0 else -12)
    anc = 'end' if dx > 0 else 'start'
    if name == 'tower_entrance':
        lx, ly, anc = X(x) - 8, Y(y) + 16, 'end'
    if name == 'tower_exit_arrival':
        lx, ly, anc = X(x) - 8, Y(y) - 10, 'end'
    o.append(text(lx, ly, name, 10, c, anc, 'bold'))

# street names and dimensions
o.append(text(X(-105), Y(-30) - 5, 'Avenue A: асфальт 24, тротуары по 9 (общая 42)', 11, '#FFFFFF'))
o.append(text(X(40) + 14, Y(-150), 'Avenue B', 12, '#FFFFFF', 'start', 'bold'))
o.append(text(X(-130) + 18, Y(235), 'Street C: асфальт 16', 10, '#1B2A41', 'start'))
o.append(text(X(150), Y(120) - 3, 'Street D: асфальт 16, тротуары по 7', 10, '#FFFFFF'))
o.append(text(M + P.HALF * S, 22, 'OfficeDadDistrict · план на согласование · 500 × 500 студ (север вверху, +X восток, +Y север в Blender)', 14, '#1B2A41', weight='bold'))
o.append(text(M + P.HALF * S, H - 18, 'красная точка на здании = вход/витрина; фиолетовые точки = коннекторы (разрыв в изгороди ±22); красные = якоря башни', 11, '#3D4A5C'))

# north arrow and scale bar
o.append(f'<path d="M {W - 345} 70 l 10 -26 l 10 26 l -10 -6 z" fill="#1B2A41"/>' + text(W - 335, 90, 'N', 13, '#1B2A41', weight='bold'))
o.append(f'<rect x="{M}" y="{H - 40}" width="{100 * S:.1f}" height="6" fill="#1B2A41"/>' + text(M + 50 * S, H - 46, '100 студ', 10))

# legend
lx = 2 * P.HALF * S + 2 * M + 10
ly = M + 10
o.append(text(lx, ly, 'ЛЕГЕНДА', 13, '#1B2A41', 'start', 'bold'))
leg = [('#464B58', 'асфальт'), ('#DAD7CE', 'тротуар'), ('#F8D030', 'разметка'), ('#8FD07A', 'сквер / сад'), ('#9AA0AA', 'парковка')]
for k, (c, t) in enumerate(leg):
    o.append(f'<rect x="{lx}" y="{ly + 14 + k * 20}" width="22" height="13" fill="{c}" stroke="#6E7480"/>' + text(lx + 30, ly + 25 + k * 20, t, 11, '#1B2A41', 'start'))
ly2 = ly + 14 + len(leg) * 20 + 14
o.append(text(lx, ly2, 'ФАСАДЫ (стены)', 12, '#1B2A41', 'start', 'bold'))
for k, (key, c) in enumerate(P.PAL.items()):
    o.append(f'<rect x="{lx}" y="{ly2 + 10 + k * 20}" width="22" height="13" fill="{c}" stroke="#6E7480"/>' + text(lx + 30, ly2 + 21 + k * 20, f'{key}  {c}', 11, '#1B2A41', 'start'))
ly3 = ly2 + 10 + len(P.PAL) * 20 + 8
o.append(f'<rect x="{lx}" y="{ly3}" width="22" height="13" fill="{P.ROOF}"/>' + text(lx + 30, ly3 + 11, f'крыши  {P.ROOF}', 11, '#1B2A41', 'start'))
bt = [b for b in P.B]
o.append(text(lx, ly3 + 40, f'Зданий: {len(bt)}  (башня + {len(bt) - 1})', 11, '#1B2A41', 'start'))
o.append('</svg>')
with open(os.path.join(OUT, 'plan.svg'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(o))
print('plan.svg written', W, H)
