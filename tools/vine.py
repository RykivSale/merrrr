"""Рисует тонкую цветочную лозу, обвивающую арку фото -> img/vine.svg.

Координаты: фото 300x400 в (0,0), контур арки на 8 ед. снаружи.
"""
import math, random

random.seed(14112026)
INK = "#6B5646"
PAPER = "#F6F1E8"
OUT = 8
R = 150 + OUT
CX, CY = 150, 150
BOTTOM = 400 + OUT


def outline(s):
    """Точка на контуре, касательная и внешняя нормаль по длине дуги s."""
    side = BOTTOM - CY
    arc = math.pi * R
    if s <= side:  # левая сторона снизу вверх
        return (CX - R, BOTTOM - s), (0, -1), (-1, 0)
    s -= side
    if s <= arc:  # полукруг слева направо через верх
        th = math.pi - s / R
        p = (CX + R * math.cos(th), CY - R * math.sin(th))
        n = (math.cos(th), -math.sin(th))
        t = (math.sin(th), math.cos(th))
        return p, t, n
    s -= arc
    return (CX + R, CY + s), (0, 1), (1, 0)


TOTAL = 2 * (BOTTOM - CY) + math.pi * R


def vine_point(s, amp, wave, phase):
    p, t, n = outline(s)
    k = amp * math.sin(2 * math.pi * s / wave + phase)
    return (p[0] + n[0] * k, p[1] + n[1] * k), t, n, k


def polyline(s0, s1, amp, wave, phase, taper=True):
    pts = []
    steps = int(abs(s1 - s0) / 2) + 2
    for i in range(steps + 1):
        s = s0 + (s1 - s0) * i / steps
        f = i / steps
        a = amp * (math.sin(math.pi * f) ** .5 if taper else 1)
        pts.append(vine_point(s, a, wave, phase)[0])
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return d


def leaf(x, y, ang, L):
    w = L * .32
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})">'
            f'<path fill="{PAPER}" d="M0 0 C{L*.3:.1f} {-w:.1f} {L*.75:.1f} {-w*.9:.1f} {L:.1f} 0 '
            f'C{L*.7:.1f} {w*.6:.1f} {L*.3:.1f} {w*.7:.1f} 0 0 Z"/>'
            f'<path d="M{L*.08:.1f} 0 Q{L*.5:.1f} {-w*.15:.1f} {L*.85:.1f} {-w*.05:.1f}" stroke-width=".5"/></g>')


def petal(Rp, rot):
    a = Rp * .62
    d = (f"M0 0 C{-a:.1f} {-Rp*.25:.1f} {-a*1.05:.1f} {-Rp*.85:.1f} {-a*.35:.1f} {-Rp:.1f} "
         f"Q0 {-Rp*.9:.1f} {a*.35:.1f} {-Rp*1.02:.1f} "
         f"C{a*1.05:.1f} {-Rp*.85:.1f} {a:.1f} {-Rp*.25:.1f} 0 0 Z")
    veins = "".join(
        f'<path d="M0 {-Rp*.12:.1f} Q{dx*.5:.1f} {-Rp*.5:.1f} {dx:.1f} {-Rp*.78:.1f}" stroke-width=".45"/>'
        for dx in (-a * .45, 0, a * .45))
    return f'<g transform="rotate({rot:.1f})"><path fill="{PAPER}" d="{d}"/>{veins}</g>'


def flower(x, y, Rp, rot, tilt=.82):
    petals = "".join(petal(Rp * random.uniform(.9, 1.08), i * 72 + random.uniform(-8, 8)) for i in range(5))
    stamens = ""
    for i in range(9):
        a = math.radians(i * 40 + random.uniform(-10, 10))
        l = Rp * random.uniform(.28, .42)
        sx, sy = math.cos(a) * l, math.sin(a) * l
        stamens += (f'<path d="M0 0 L{sx:.1f} {sy:.1f}" stroke-width=".5"/>'
                    f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r=".9" fill="{INK}" stroke="none"/>')
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot:.1f}) scale(1 {tilt})">'
            f'{petals}<circle fill="{PAPER}" r="{Rp*.12:.1f}"/>{stamens}</g>')


def bud(x, y, ang, L):
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})">'
            f'<path fill="{PAPER}" d="M0 0 C{-L*.35:.1f} {-L*.35:.1f} {-L*.2:.1f} {-L*.85:.1f} 0 {-L:.1f} '
            f'C{L*.2:.1f} {-L*.85:.1f} {L*.35:.1f} {-L*.35:.1f} 0 0 Z"/>'
            f'<path d="M0 0 C{-L*.45:.1f} {-L*.2:.1f} {-L*.5:.1f} {-L*.45:.1f} {-L*.42:.1f} {-L*.6:.1f}" stroke-width=".6"/>'
            f'<path d="M0 0 C{L*.45:.1f} {-L*.2:.1f} {L*.5:.1f} {-L*.45:.1f} {L*.42:.1f} {-L*.6:.1f}" stroke-width=".6"/></g>')


def tendril(x, y, ang, size, turns=1.6):
    pts = []
    for i in range(60):
        f = i / 59
        th = f * turns * 2 * math.pi
        r = size * (1 - f * .85)
        pts.append((f * size * 1.2 + math.sin(th) * r * .4, -(1 - math.cos(th)) * r * .5))
    d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts)
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})"><path d="{d}" stroke-width=".6"/></g>'


parts = []


def stem_along(s0, s1, amp, wave, phase):
    parts.append(f'<path d="{polyline(s0, s1, amp, wave, phase)}" stroke-width=".8"/>')
    parts.append(f'<path d="{polyline(s0 + 6, s1 - 10, amp * .7, wave, phase + math.pi)}" stroke-width=".4"/>')


def deg(v):
    return math.degrees(math.atan2(v[1], v[0]))


def leaves_on(s0, s1, amp, wave, phase, step, flip=1):
    s, side = s0 + step * .6, 1
    while s < s1 - 8:
        (x, y), t, n, _ = vine_point(s, amp, wave, phase)
        base = deg(t) * (1 if s1 > s0 else -1)
        ang = base + flip * side * random.uniform(35, 60)
        parts.append(leaf(x, y, ang, random.uniform(10, 21)))
        s += step * random.uniform(.8, 1.2)
        side = -side


# Лоза 1: от низа левой стороны через верх к правому плечу
A = (30, 640, 6, 70, 0.0)
stem_along(*A)
leaves_on(*A, step=44)
# Лоза 2: коротко снизу по правой стороне вверх (идёт по s назад)
B = (TOTAL - 20, TOTAL - 230, 5, 64, 1.2)
stem_along(*B)
leaves_on(TOTAL - 225, TOTAL - 25, 5, 64, 1.2, step=48, flip=-1)

# Цветы
(p1, t1, n1, _) = vine_point(300, *A[2:])
parts.append(flower(p1[0] - 6, p1[1] - 4, 27, -20))
(p2, _, _, _) = vine_point(TOTAL - 150, *B[2:])
parts.append(flower(p2[0] + 6, p2[1], 18, 30, .75))
(p3, t3, _, _) = vine_point(520, *A[2:])
parts.append(flower(p3[0], p3[1] - 3, 13, 10, .7))
# Бутоны на концах
(pe, te, _, _) = vine_point(640, *A[2:])
parts.append(bud(pe[0], pe[1], deg(te) + 90, 14))
(pb, tb, _, _) = vine_point(TOTAL - 230, *B[2:])
parts.append(bud(pb[0], pb[1], deg(tb) + 120, 12))
(pc, tc, _, _) = vine_point(30, *A[2:])
parts.append(bud(pc[0], pc[1], 200, 10))
# Усики
(q, tq, _, _) = vine_point(170, *A[2:])
parts.append(tendril(q[0], q[1], 200, 12))
(q, tq, _, _) = vine_point(430, *A[2:])
parts.append(tendril(q[0], q[1], -70, 10))
(q, tq, _, _) = vine_point(TOTAL - 100, *B[2:])
parts.append(tendril(q[0], q[1], -10, 10))

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-45 -45 390 500" fill="none" stroke="{INK}" '
       f'stroke-width=".65" stroke-linecap="round" stroke-linejoin="round">' + "".join(parts) + "</svg>")
open("img/vine.svg", "w").write(svg)
print(len(svg))
