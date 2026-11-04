"""
vault_kit — reusable MODELING TECHNIQUES (not assets) for the owner's art direction
(style-guides/3D_STYLE_BIBLE.md ★). Every game composes ORIGINAL models from these tools; nothing
here is a finished object to drop into a game.

    shades(hex)                         -> {"light","base","dark","deep"} multi-shade palette
    canopy(prefix, center, ...)         -> irregular angular leaf-cluster canopy (any tree type)
    terrace_field(rects, ...)           -> stepped, layered terrain with cliff detail + lip trims
    path_network(polylines, ...)        -> tiled paths without coplanar overlaps + edge stones
    framed_window(prefix, ...)          -> glass + frame + mullion + sill (physical trim)
    striped_awning(prefix, ...)         -> awning strips + scalloped valance
    Vignettes (purposeful decoration, tell a small story — never uniform scatter):
    flower_bed, rock_garden, signpost, picnic_spot, lamp_post

All pieces get texture studs via vault_blocky (world-space, owner-approved 0.5-stud spacing).
"""

from __future__ import annotations

import math
import random

import vault_blocky as vb


def _mix(hex_color: str, factor: float) -> str:
    h = vb.PALETTE.get(hex_color, hex_color).lstrip("#")
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    if factor >= 1:
        rgb = [int(c + (255 - c) * (factor - 1)) for c in rgb]
    else:
        rgb = [int(c * factor) for c in rgb]
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, c)) for c in rgb])


def shades(hex_color: str) -> dict:
    """Multiple shades per material (owner rule): light / base / dark / deep."""
    return {"light": _mix(hex_color, 1.22), "base": hex_color, "dark": _mix(hex_color, 0.78), "deep": _mix(hex_color, 0.6)}


def canopy(prefix, center, radius=4.5, height=5.0, clusters=12, leaf="#4CC24A", rnd=None, fruit=None):
    """Irregular silhouette from individually placed angular leaf clusters (varied size/tilt/yaw),
    lighter on top, darker underneath. Works for round, tall, flat or droopy trees via radius/height."""
    rnd = rnd or random.Random(1)
    sh = shades(leaf)
    cx, cy, cz = center
    P = []
    for i in range(clusters):
        a = rnd.uniform(0, 2 * math.pi)
        r = radius * math.sqrt(rnd.uniform(0.05, 1.0))
        z = cz + rnd.uniform(0, height) * (1 - 0.35 * r / radius)
        s = rnd.uniform(0.45, 0.85) * radius * (1.15 - 0.4 * r / radius)
        tone = "light" if z > cz + height * 0.6 else ("dark" if z < cz + height * 0.25 else "base")
        P.append(vb.rounded(f"{prefix}Leaf{i}", (s, s * rnd.uniform(0.85, 1.15), s * 0.8),
                            (cx + math.cos(a) * r, cy + math.sin(a) * r, z), sh[tone], radius=s * 0.14,
                            rot=(math.radians(rnd.uniform(-9, 9)), math.radians(rnd.uniform(-9, 9)),
                                 math.radians(rnd.uniform(-25, 25)))))
    for i in range(rnd.randint(2, 4) if fruit else 0):
        a = rnd.uniform(0, 2 * math.pi)
        P.append(vb.ball(f"{prefix}Fruit{i}", (0.38, 0.38, 0.38),
                         (cx + math.cos(a) * radius * 0.95, cy + math.sin(a) * radius * 0.95, cz + height * 0.35),
                         fruit, segments=10, rings=6))
    return P


def terrace_field(rects, body="#9A6B45", cap="#5BCB3F", rnd=None):
    """Stepped rectangular terrain. Each terrace: dirt body + grass cap + darker lip trim +
    a few exposed stone blocks on the cliff faces (environmental detail, not flat walls)."""
    rnd = rnd or random.Random(2)
    bsh, csh = shades(body), shades(cap)
    P = []
    for i, (x0, x1, y0, y1, h) in enumerate(rects):
        w, d = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        P.append(vb.solid(f"TerraceBody{i}", (w, d, h - 0.6), (cx, cy, 0), bsh["base"], bevel=0.05))
        P.append(vb.solid(f"TerraceCap{i}", (w + 0.3, d + 0.3, 0.6), (cx, cy, h - 0.6), csh["base"], bevel=0.06))
        P.append(vb.solid(f"TerraceLip{i}", (w + 0.5, d + 0.5, 0.18), (cx, cy, h - 0.75), csh["dark"], bevel=0.03))
        for j in range(max(2, int((w + d) / 8))):  # exposed stones on the cliff faces
            if rnd.random() < 0.5:
                x, y = rnd.uniform(x0 + 1, x1 - 1), (y1 if rnd.random() < 0.5 else y0)
            else:
                x, y = (x1 if rnd.random() < 0.5 else x0), rnd.uniform(y0 + 1, y1 - 1)
            s = rnd.uniform(0.8, 1.6)
            P.append(vb.rounded(f"CliffStone{i}_{j}", (s, s, min(s, h - 0.8) * 0.8),
                                (x, y, rnd.uniform(0, max(0.0, h - 0.6 - s))), rnd.choice(("#8E96A3", "#6E7683", bsh["dark"])),
                                radius=0.15))
    return P


def path_network(polylines, tile=2.9, step=3.2, colors=("#E4D3A8", "#D2BE8E"), rnd=None, edge="#B8A47A"):
    """Tiles along polylines; shared corner/branch tiles skipped (no coplanar overlaps)."""
    rnd = rnd or random.Random(3)
    P = []
    for li, line in enumerate(polylines):
        for si in range(len(line) - 1):
            (ax, ay), (bx, by) = line[si], line[si + 1]
            n = max(1, int(math.hypot(bx - ax, by - ay) / step))
            for k in range(0 if (si == 0 and li == 0) else 1, n + 1):
                t = k / n
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                P.append(vb.solid(f"PathTile{li}_{si}_{k}", (tile, tile, 0.25), (x, y, 0), colors[(k + si) % 2],
                                  bevel=0.05, rot=(0, 0, math.radians(rnd.uniform(-6, 6)))))
                if k % 3 == 1:  # occasional edge stone breaks the repetition
                    ang = math.atan2(by - ay, bx - ax) + math.pi / 2
                    side = 1 if rnd.random() < 0.5 else -1
                    P.append(vb.rounded(f"PathEdge{li}_{si}_{k}", (0.8, 0.6, 0.35),
                                        (x + math.cos(ang) * side * (tile / 2 + 0.5), y + math.sin(ang) * side * (tile / 2 + 0.5), 0),
                                        edge, radius=0.12, rot=(0, 0, rnd.uniform(0, math.pi))))
    return P


def framed_window(prefix, center, width, height, normal="+y", frame="#FFFFFF", glass="#9BE1FF", sill=None, mullions=1):
    """Glass + 4 frame bars + mullions + sill on a wall face. center = (x, y, z_bottom) on the wall surface."""
    x, y, z = center
    t = 0.3
    P = []
    if normal in ("+y", "-y"):
        sgn = 1 if normal == "+y" else -1
        P.append(vb.solid(f"{prefix}Glass", (width, 0.12, height), (x, y, z), glass, studs="none", bevel=0.01))
        P += [vb.solid(f"{prefix}FrameT", (width + 2 * t, t, t), (x, y + sgn * 0.1, z + height), frame),
              vb.solid(f"{prefix}FrameB", (width + 2 * t, t, t), (x, y + sgn * 0.1, z - t), frame),
              vb.solid(f"{prefix}FrameL", (t, t, height), (x - width / 2 - t / 2, y + sgn * 0.1, z), frame),
              vb.solid(f"{prefix}FrameR", (t, t, height), (x + width / 2 + t / 2, y + sgn * 0.1, z), frame)]
        for m in range(mullions):
            mx = x - width / 2 + width * (m + 1) / (mullions + 1)
            P.append(vb.solid(f"{prefix}Mullion{m}", (0.18, 0.18, height), (mx, y + sgn * 0.08, z), frame))
        if sill:
            P.append(vb.solid(f"{prefix}Sill", (width + 0.9, 0.7, 0.25), (x, y + sgn * 0.3, z - t - 0.25), sill))
    else:
        sgn = 1 if normal == "+x" else -1
        P.append(vb.solid(f"{prefix}Glass", (0.12, width, height), (x, y, z), glass, studs="none", bevel=0.01))
        P += [vb.solid(f"{prefix}FrameT", (t, width + 2 * t, t), (x + sgn * 0.1, y, z + height), frame),
              vb.solid(f"{prefix}FrameB", (t, width + 2 * t, t), (x + sgn * 0.1, y, z - t), frame),
              vb.solid(f"{prefix}FrameL", (t, t, height), (x + sgn * 0.1, y - width / 2 - t / 2, z), frame),
              vb.solid(f"{prefix}FrameR", (t, t, height), (x + sgn * 0.1, y + width / 2 + t / 2, z), frame)]
        if sill:
            P.append(vb.solid(f"{prefix}Sill", (0.7, width + 0.9, 0.25), (x + sgn * 0.3, y, z - t - 0.25), sill))
    return P


def striped_awning(prefix, x0, x1, y, z, depth=2.4, tilt=22, colors=("#FF6B6B", "#FFFFFF"), valance=True):
    """Awning strips facing +y with a scalloped valance along the front edge."""
    P = []
    n = max(2, int(round((x1 - x0) / 1.1)))
    w = (x1 - x0) / n
    for i in range(n):
        P.append(vb.solid(f"{prefix}Strip{i}", (w * 0.98, depth, 0.22), (x0 + w * (i + 0.5), y + depth / 2 - 0.2, z),
                          colors[i % 2], bevel=0.02, rot=(math.radians(-tilt), 0, 0)))
    if valance:
        fy = y - 0.2 + depth * math.cos(math.radians(tilt))
        fz = z - depth * math.sin(math.radians(tilt)) * 0.5 - 0.2
        for i in range(int((x1 - x0) / 0.55)):
            P.append(vb.ball(f"{prefix}Scallop{i}", (0.3, 0.14, 0.26), (x0 + 0.3 + i * 0.55, fy, fz), colors[i % 2],
                             segments=10, rings=6))
    return P


# ---- Vignettes: purposeful decoration groups ----------------------------------------------------

def flower_bed(prefix, start, end, z=0.0, colors=("#FF5FA2", "#FFD93B", "#B678EA"), rnd=None):
    """A bordered bed running alongside a path edge: timber border + soil + mixed blooms + leaves."""
    rnd = rnd or random.Random(4)
    (ax, ay), (bx, by) = start, end
    L = math.hypot(bx - ax, by - ay)
    ang = math.atan2(by - ay, bx - ax)
    cx, cy = (ax + bx) / 2, (ay + by) / 2
    P = [vb.solid(f"{prefix}Border", (L, 1.6, 0.45), (cx, cy, z), "#8A5530", rot=(0, 0, ang)),
         vb.solid(f"{prefix}Soil", (L - 0.3, 1.2, 0.5), (cx, cy, z + 0.02), "#5A3A22", rot=(0, 0, ang))]
    n = int(L / 0.7)
    for i in range(n):
        t = (i + 0.5) / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        h = rnd.uniform(0.5, 1.0)
        P.append(vb.solid(f"{prefix}Stem{i}", (0.14, 0.14, h), (x, y, z + 0.5), "#2E9A3E", bevel=0.02))
        P.append(vb.solid(f"{prefix}Bloom{i}", (0.5, 0.5, 0.36), (x, y, z + 0.5 + h), colors[i % len(colors)], bevel=0.08,
                          rot=(0, 0, rnd.uniform(0, 0.8))))
        if i % 2 == 0:
            P.append(vb.solid(f"{prefix}LeafPair{i}", (0.6, 0.12, 0.2), (x, y, z + 0.5 + h * 0.5), "#4CC24A", bevel=0.03,
                              rot=(0, 0, ang + 0.6)))
    return P


def rock_garden(prefix, center, z=0.0, rnd=None):
    """Grouped boulders of 3 sizes + moss caps + a small sprout — reads as a placed feature."""
    rnd = rnd or random.Random(5)
    x, y = center
    P = []
    for i, (dx, dy, s) in enumerate(((0, 0, 2.2), (1.8, 0.6, 1.4), (-1.5, 1.0, 1.1), (0.6, -1.6, 0.8))):
        sh = shades("#8E96A3")
        P.append(vb.rounded(f"{prefix}Boulder{i}", (s, s * 0.9, s * 0.75), (x + dx, y + dy, z),
                            sh["base"] if i % 2 == 0 else sh["dark"], radius=s * 0.18, rot=(0, 0, rnd.uniform(0, 1.2))))
        if i < 2:
            P.append(vb.rounded(f"{prefix}Moss{i}", (s * 0.7, s * 0.6, 0.2), (x + dx, y + dy, z + s * 0.75), "#5FC24A",
                                radius=0.06))
    P.append(vb.solid(f"{prefix}Sprout", (0.15, 0.15, 0.9), (x - 0.4, y - 0.9, z), "#2E9A3E", bevel=0.02))
    P.append(vb.solid(f"{prefix}SproutLeaf", (0.6, 0.15, 0.25), (x - 0.4, y - 0.9, z + 0.8), "#86E05A", bevel=0.04))
    return P


def signpost(prefix, center, arrows=(("#FF6B6B", 30), ("#22C3A6", -150), ("#FFD93B", 100)), z=0.0):
    """Post + cap + pointing arrow boards at a path fork (blank: text added in Studio)."""
    x, y = center
    P = [vb.solid(f"{prefix}Post", (0.5, 0.5, 4.2), (x, y, z), "#8A5530"),
         vb.solid(f"{prefix}Cap", (0.8, 0.8, 0.3), (x, y, z + 4.2), "#6B3F22")]
    for i, (col, yaw) in enumerate(arrows):
        a = math.radians(yaw)
        P.append(vb.solid(f"{prefix}Arrow{i}", (2.2, 0.2, 0.6), (x + math.cos(a) * 1.0, y + math.sin(a) * 1.0, z + 3.3 - i * 0.8),
                          col, rot=(0, 0, a)))
    return P


def picnic_spot(prefix, center, z=0.0, cloth=("#FF6B6B", "#FFFFFF")):
    """Checkered blanket + basket + cups — a tiny story beat in an open grass area."""
    x, y = center
    P = []
    for i in range(4):
        for j in range(4):
            P.append(vb.solid(f"{prefix}Cloth{i}{j}", (0.9, 0.9, 0.06), (x - 1.35 + i * 0.9, y - 1.35 + j * 0.9, z),
                              cloth[(i + j) % 2], bevel=0.01))
    P += [vb.rounded(f"{prefix}Basket", (1.2, 0.8, 0.7), (x + 0.6, y + 0.4, z + 0.06), "#C98A4B", radius=0.1),
          vb.solid(f"{prefix}Handle", (1.0, 0.12, 0.12), (x + 0.6, y + 0.4, z + 1.0), "#8A5530", bevel=0.03),
          vb.cyl(f"{prefix}Cup0", 0.18, 0.22, 0.4, (x - 0.6, y - 0.5, z + 0.06), "#FF6FAE", sides=10),
          vb.cyl(f"{prefix}Cup1", 0.18, 0.22, 0.4, (x - 0.1, y - 0.8, z + 0.06), "#22C3A6", sides=10)]
    return P


def lamp_post(prefix, center, z=0.0, light="#FFE7B0"):
    x, y = center
    return [vb.solid(f"{prefix}Base", (0.9, 0.9, 0.4), (x, y, z), "#2E3440"),
            vb.cyl(f"{prefix}Pole", 0.22, 0.18, 4.0, (x, y, z + 0.4), "#2E3440", sides=8),
            vb.rounded(f"{prefix}Head", (0.9, 0.9, 0.8), (x, y, z + 4.4), "#2E3440", radius=0.1),
            vb.ball(f"{prefix}Glow", (0.32, 0.32, 0.3), (x, y, z + 4.8), light, segments=10, rings=6, emission=5),
            vb.solid(f"{prefix}Roof", (1.1, 1.1, 0.2), (x, y, z + 5.2), "#2E3440", bevel=0.05)]
