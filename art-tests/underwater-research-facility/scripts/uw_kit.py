"""
uw_kit — techniques for the Underwater Research Facility art test (original designs only).

Studs are TEXTURE-BASED: a seamless 256 px stud tile is generated (height + tangent-space normal
map) and applied through a Normal Map node on world-space box UVs (0.5-stud spacing, owner
approved). Glass, water and glow materials stay smooth. Geometry detail is never replaced by studs.
"""

import math
import os
import random

import bpy
import bmesh

import vault_blocky as vb
import vault_kit as kit

HERE = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(HERE, "..", "textures")
STUD_PX = 256


# ---- Stud texture + normal-map material --------------------------------------------------------

def make_stud_textures(force=False):
    """Seamless 1-stud tile: height map + OpenGL tangent normal map (wrap-around gradients)."""
    hpath = os.path.join(TEX_DIR, "stud_tile_height.png")
    npath = os.path.join(TEX_DIR, "stud_tile_normal.png")
    if os.path.exists(hpath) and os.path.exists(npath) and not force:
        return hpath, npath
    os.makedirs(TEX_DIR, exist_ok=True)
    n, R, E = STUD_PX, 0.27, 0.03

    def h(u, v):
        r = math.hypot(u - 0.5, v - 0.5)
        if r >= R + E:
            return 0.0
        if r <= R:
            return 0.55 + 0.45 * (1 - (r / R) ** 2)
        t = (R + E - r) / E
        return 0.55 * t * t * (3 - 2 * t)

    H = [[h((x + 0.5) / n, (y + 0.5) / n) for x in range(n)] for y in range(n)]
    hp, np_ = [], []
    for y in range(n):
        for x in range(n):
            v = H[y][x]
            hp += [v, v, v, 1.0]
            dx = (H[y][(x + 1) % n] - H[y][(x - 1) % n]) * n / 2
            dy = (H[(y + 1) % n][x] - H[(y - 1) % n][x]) * n / 2
            k = 0.06  # bump height in tile units
            nx, ny, nz = -dx * k, -dy * k, 1.0
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            np_ += [nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5, 1.0]
    for path, px, name in ((hpath, hp, "uw_stud_height"), (npath, np_, "uw_stud_normal")):
        img = bpy.data.images.new(name, n, n, alpha=False)
        img.pixels = px
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
    return hpath, npath


def studded_material_normal(base):
    """Replacement for vault_blocky.studded_material: Normal Map node with the stud normal tile."""
    name = base.name + "_StudN"
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = base.copy()
    mat.name = name
    _, npath = make_stud_textures()
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.45  # glossy plastic
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.get("uw_stud_normal_tile") or bpy.data.images.load(npath)
    img.name = "uw_stud_normal_tile"
    img.colorspace_settings.name = "Non-Color"
    tex.image = img
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = "TANGENT"
    nmap.uv_map = "UVMap"
    nmap.inputs["Strength"].default_value = 1.0
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    mat["vault_studs"] = True
    return mat


def install():
    """Use the normal-map stud shader for this test (does not change the shared library files)."""
    make_stud_textures()
    vb.studded_material = studded_material_normal
    vb.STUD_PITCH = 0.5


# ---- Smooth materials --------------------------------------------------------------------------

def _set(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return


def glass(obj, tint="#BFF3FF", rough=0.03):
    """Transparent glass (no studs)."""
    key = f"M_Glass_{tint}"
    mat = bpy.data.materials.get(key)
    if not mat:
        mat = bpy.data.materials.new(key)
        mat.use_nodes = True
        b = mat.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = vb.hex_to_rgba(tint)
        b.inputs["Roughness"].default_value = rough
        _set(b, ("Transmission Weight", "Transmission"), 1.0)
        _set(b, ("IOR",), 1.15)
        mat["roblox_glass"] = True
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj["vault_stud_mode"] = "none"
    return obj


# ---- Geometry helpers --------------------------------------------------------------------------

def ring(name, r_out, r_in, h, location, color, sides=24, studs="all", rot=None, emission=0.0):
    """Hollow ring/collar (frames portholes, tunnel ribs, dome latitude bands)."""
    bm = bmesh.new()
    ob, ot, ib, it = [], [], [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        c, s = math.cos(a), math.sin(a)
        ob.append(bm.verts.new((c * r_out, s * r_out, 0)))
        ot.append(bm.verts.new((c * r_out, s * r_out, h)))
        ib.append(bm.verts.new((c * r_in, s * r_in, 0)))
        it.append(bm.verts.new((c * r_in, s * r_in, h)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))
    obj = vb._new_mesh_object(name, bm)
    obj.location = location
    return vb._finish(obj, color, emission, studs, rot)


def face_rot(theta):
    """Rotation that points an object's local +Z along the horizontal direction theta."""
    return (-math.pi / 2, 0, theta - math.pi / 2)


def porthole(prefix, wall_point, theta, r=1.1, frame="#1FB5B0", glow="#FFE7A8", bolts=6):
    """Round window: studded frame ring + lit glass disk + bolt heads."""
    x, y, z = wall_point
    rot = face_rot(theta)
    P = [ring(f"{prefix}Frame", r + 0.45, r - 0.05, 0.45, (x, y, z), frame, sides=20, rot=rot),
         vb.cyl(f"{prefix}Glass", r, r, 0.12, (x, y, z), glow, sides=20, studs="none", rot=rot, emission=1.6)]
    nx, ny = math.cos(theta), math.sin(theta)
    tx, ty = -ny, nx
    for b in range(bolts):
        a = 2 * math.pi * b / bolts
        ox, oz = math.cos(a) * (r + 0.22), math.sin(a) * (r + 0.22)
        P.append(vb.ball(f"{prefix}Bolt{b}", (0.11, 0.11, 0.11), (x + tx * ox + nx * 0.47, y + ty * ox + ny * 0.47, z + oz),
                         "#D9DEE6", segments=6, rings=4, studs="none"))
    return P


def tunnel(prefix, a, b, z, R=2.8, rib="#FFC83D", floor="#C9D3DD", light="#BFF6FF", supports=True, rib_step=3.0):
    """Glass observation tunnel: smooth glass tube + studded rib rings + walkway + light strip + legs."""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    ang = math.atan2(by - ay, bx - ax)
    rot = (0, math.pi / 2, ang)
    P = [glass(vb.cyl(f"{prefix}Tube", R, R, L, (ax, ay, z), "#BFF3FF", sides=24, studs="none", rot=rot))]
    n = max(2, int(L / rib_step))
    for i in range(n + 1):
        t = i / n
        P.append(ring(f"{prefix}Rib{i}", R + 0.5, R - 0.08, 0.7 if i in (0, n) else 0.45,
                      (ax + (bx - ax) * t - math.cos(ang) * (0.35 if i == n else 0), ay + (by - ay) * t - math.sin(ang) * (0.35 if i == n else 0), z),
                      rib if i % 2 == 0 else kit.shades(rib)["dark"], sides=24, rot=rot))
    mx, my = (ax + bx) / 2, (ay + by) / 2
    P.append(vb.solid(f"{prefix}Walk", (L, R * 1.2, 0.3), (mx, my, z - R * 0.72), floor, rot=(0, 0, ang)))
    P.append(vb.block(f"{prefix}Light", (L * 0.92, 0.35, 0.1), (mx, my, z + R * 0.78), light, bevel=0.0, emission=3.0))
    P[-1].rotation_euler = (0, 0, ang)
    if supports and z - R > 0.5:
        for i in range(1, n, 2):
            t = i / n
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            P.append(vb.solid(f"{prefix}Leg{i}", (0.9, 0.9, z - R - 0.3), (px, py, 0), "#24385B", rot=(0, 0, ang)))
            P.append(vb.solid(f"{prefix}Foot{i}", (2.0, 2.0, 0.4), (px, py, 0), "#3A5378", rot=(0, 0, ang)))
            P.append(vb.solid(f"{prefix}Cradle{i}", (0.8, R * 1.8, 0.5), (px, py, z - R - 0.4), "#24385B", rot=(0, 0, ang)))
    return P


def bubbles(prefix, base, height=12, count=9, rnd=None, size=0.28):
    """Rising bubble column (smooth glass spheres, varied sizes, slight drift)."""
    rnd = rnd or random.Random(7)
    x, y, z = base
    out = []
    for i in range(count):
        s = size * rnd.uniform(0.6, 1.4) * (1 + i / count * 0.6)
        out.append(glass(vb.ball(f"{prefix}Bubble{i}", (s, s, s), (x + rnd.uniform(-0.6, 0.6), y + rnd.uniform(-0.6, 0.6),
                                                                      z + height * i / count), "#E8FCFF", segments=10, rings=6,
                                 studs="none"), tint="#EFFFFF", rough=0.0))
    return out


# ---- Reef & seabed life (all original, plausible underwater details) -----------------------------

def branch_coral(prefix, base, color, rnd, height=4.0, depth=0):
    """Angular branching coral: stacked chunky segments that fork and tilt."""
    x, y, z = base
    P = []
    seg = height / 3
    sh = kit.shades(color)
    cx, cy, cz = x, y, z
    for i in range(3):
        w = 0.7 - i * 0.12
        tilt = (math.radians(rnd.uniform(-14, 14)), math.radians(rnd.uniform(-14, 14)), 0)
        P.append(vb.rounded(f"{prefix}Seg{depth}_{i}", (w, w, seg), (cx, cy, cz), sh["base"] if i % 2 == 0 else sh["light"],
                            radius=w * 0.25, rot=tilt))
        cz += seg * 0.92
        cx += math.sin(tilt[1]) * seg * 0.9
        cy -= math.sin(tilt[0]) * seg * 0.9
        if depth < 1 and i == 1:
            for k in (-1, 1):
                a = rnd.uniform(0, math.pi)
                P += branch_coral(f"{prefix}B{k}", (cx + math.cos(a) * 0.6 * k, cy + math.sin(a) * 0.6 * k, cz - seg * 0.5),
                                  color, rnd, height * 0.55, depth + 1)
    P.append(vb.ball(f"{prefix}Tip{depth}", (0.32, 0.32, 0.32), (cx, cy, cz), sh["light"], segments=8, rings=5))
    return P


def brain_coral(prefix, base, color, r=1.6):
    x, y, z = base
    sh = kit.shades(color)
    P = [vb.ball(f"{prefix}Dome", (r, r, r * 0.7), (x, y, z + r * 0.3), sh["base"], segments=16, rings=8)]
    for i in range(3):  # ridges
        rr = r * (0.95 - i * 0.28)
        P.append(ring(f"{prefix}Ridge{i}", rr + 0.12, rr - 0.12, 0.22, (x, y, z + r * 0.3 + r * 0.7 * math.sqrt(max(0, 1 - (rr / r) ** 2)) - 0.1),
                      sh["dark"], sides=16))
    return P


def table_coral(prefix, base, color, r=2.2, tiers=2):
    x, y, z = base
    sh = kit.shades(color)
    P = [vb.cyl(f"{prefix}Stalk", 0.4, 0.3, 1.6, (x, y, z), sh["dark"], sides=8)]
    for t in range(tiers):
        rr = r * (1 - t * 0.35)
        P.append(vb.cyl(f"{prefix}Plate{t}", rr, rr * 0.92, 0.35, (x + t * 0.4, y, z + 1.6 + t * 0.9), sh["base" if t % 2 == 0 else "light"],
                        sides=10))
        P.append(ring(f"{prefix}Rim{t}", rr + 0.1, rr - 0.25, 0.25, (x + t * 0.4, y, z + 1.95 + t * 0.9), sh["light"], sides=10))
    return P


def tube_sponge(prefix, base, color, rnd, n=4):
    x, y, z = base
    sh = kit.shades(color)
    P = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.3, 0.3)
        h = rnd.uniform(1.6, 3.4)
        r = rnd.uniform(0.35, 0.6)
        px, py = x + math.cos(a) * 0.7, y + math.sin(a) * 0.7
        P.append(vb.cyl(f"{prefix}Tube{i}", r * 0.9, r, h, (px, py, z), sh["base"], sides=10,
                        rot=(math.radians(rnd.uniform(-10, 10)), math.radians(rnd.uniform(-10, 10)), 0)))
        P.append(ring(f"{prefix}Lip{i}", r + 0.08, r - 0.16, 0.2, (px, py, z + h - 0.05), sh["light"], sides=10))
        P.append(vb.cyl(f"{prefix}Hole{i}", r - 0.15, r - 0.15, 0.06, (px, py, z + h - 0.25), sh["deep"], sides=10, studs="none"))
    return P


def sea_fan(prefix, base, color, rnd, w=3.0, h=3.2, yaw=0.0):
    """Flat lattice fan built from thin angled ribs (layered, not a flat textured card)."""
    x, y, z = base
    sh = kit.shades(color)
    P = [vb.cyl(f"{prefix}Stem", 0.18, 0.15, 0.8, (x, y, z), sh["dark"], sides=6)]
    for i in range(7):
        a = math.radians(-60 + i * 20)
        P.append(vb.solid(f"{prefix}Rib{i}", (0.16, 0.16, h), (x, y, z + 0.7), sh["base" if i % 2 else "light"], bevel=0.03,
                          rot=(0, a, yaw)))
    for j in range(3):
        rr = h * (0.45 + j * 0.25)
        P.append(vb.solid(f"{prefix}Cross{j}", (w * (0.4 + j * 0.25), 0.14, 0.14), (x, y, z + 0.7 + rr * 0.85), sh["light"],
                          bevel=0.03, rot=(0, 0, yaw)))
    return P


def anemone(prefix, base, color, tip, rnd, n=10):
    x, y, z = base
    P = [vb.cyl(f"{prefix}Base", 0.9, 0.7, 0.8, (x, y, z), kit.shades(color)["dark"], sides=12)]
    for i in range(n):
        a = 2 * math.pi * i / n
        tilt = math.radians(rnd.uniform(25, 45))
        P.append(vb.cyl(f"{prefix}Tent{i}", 0.16, 0.1, 1.5, (x + math.cos(a) * 0.55, y + math.sin(a) * 0.55, z + 0.7), color, sides=6,
                        rot=(-math.sin(a) * tilt, math.cos(a) * tilt, 0)))
        P.append(vb.ball(f"{prefix}Tip{i}", (0.15, 0.15, 0.15), (x + math.cos(a) * (0.55 + 1.5 * math.sin(tilt)),
                                                                  y + math.sin(a) * (0.55 + 1.5 * math.sin(tilt)),
                                                                  z + 0.7 + 1.5 * math.cos(tilt)), tip, segments=6, rings=4, emission=1.5))
    return P


def starfish(prefix, base, color, yaw=0.0):
    x, y, z = base
    P = [vb.cyl(f"{prefix}Core", 0.45, 0.4, 0.25, (x, y, z), color, sides=10)]
    for i in range(5):
        a = yaw + 2 * math.pi * i / 5
        P.append(vb.rounded(f"{prefix}Arm{i}", (1.3, 0.42, 0.22), (x + math.cos(a) * 0.7, y + math.sin(a) * 0.7, z), color, radius=0.1,
                            rot=(0, 0, a)))
    return P


def urchin(prefix, base, color="#5B2A86", spikes=14):
    """Spiky sea urchin — spikes are plausible here."""
    x, y, z = base
    P = [vb.ball(f"{prefix}Body", (0.6, 0.6, 0.5), (x, y, z + 0.4), color, segments=12, rings=8)]
    for i in range(spikes):
        a = 2 * math.pi * i / spikes
        el = math.radians(20 + (i % 3) * 25)
        P.append(vb.cyl(f"{prefix}Spike{i}", 0.07, 0.01, 0.9, (x, y, z + 0.4), kit.shades(color)["light"], sides=4,
                        rot=(-math.sin(a) * (math.pi / 2 - el), math.cos(a) * (math.pi / 2 - el), 0)))
    return P


def kelp(prefix, base, rnd, height=16, color="#3FAE4A"):
    """Tall segmented kelp: drifting stalk segments + alternating blade leaves + float bulbs."""
    x, y, z = base
    sh = kit.shades(color)
    P = []
    n = int(height / 1.6)
    dx = dy = 0.0
    for i in range(n):
        dx += rnd.uniform(-0.15, 0.15)
        dy += rnd.uniform(-0.15, 0.15)
        zz = z + i * 1.6
        P.append(vb.rounded(f"{prefix}Stalk{i}", (0.35, 0.35, 1.7), (x + dx, y + dy, zz), sh["dark"], radius=0.1))
        if i > 0:
            side = 1 if i % 2 else -1
            P.append(vb.rounded(f"{prefix}Blade{i}", (1.6, 0.12, 0.7), (x + dx + side * 0.8, y + dy, zz + 0.5),
                                sh["base" if i % 3 else "light"], radius=0.05, rot=(0, math.radians(side * -28), rnd.uniform(-0.4, 0.4))))
        if i % 3 == 2:
            P.append(vb.ball(f"{prefix}Float{i}", (0.28, 0.28, 0.34), (x + dx - 0.3, y + dy, zz + 1.2), "#C9E86A", segments=8, rings=5))
    return P


def glow_plant(prefix, base, rnd, color="#7CF7FF"):
    x, y, z = base
    P = []
    for i in range(3):
        h = rnd.uniform(1.2, 2.6)
        a = rnd.uniform(0, 2 * math.pi)
        px, py = x + math.cos(a) * 0.5, y + math.sin(a) * 0.5
        P.append(vb.cyl(f"{prefix}Stalk{i}", 0.12, 0.08, h, (px, py, z), "#1E6B6B", sides=6, rot=(0.15 * math.cos(a), 0.15 * math.sin(a), 0)))
        P.append(vb.ball(f"{prefix}Bulb{i}", (0.34, 0.34, 0.42), (px + 0.15 * math.sin(a) * h * 0.1, py, z + h), color, segments=10,
                         rings=6, emission=4.0))
    P.append(vb.rounded(f"{prefix}Root", (1.4, 1.2, 0.4), (x, y, z), "#2D4A5E", radius=0.12))
    return P


def tiny_fish(prefix, center, color, yaw=0.0, s=1.0):
    """Little blocky fish for schools (body + tail fin + fin + eye)."""
    x, y, z = center
    ca, sa = math.cos(yaw), math.sin(yaw)
    P = [vb.rounded(f"{prefix}Body", (1.2 * s, 0.6 * s, 0.7 * s), (x, y, z), color, radius=0.18 * s, rot=(0, 0, yaw)),
         vb.solid(f"{prefix}Tail", (0.25 * s, 0.12 * s, 0.7 * s), (x - ca * 0.75 * s, y - sa * 0.75 * s, z), kit.shades(color)["dark"],
                  bevel=0.03, rot=(0, 0, yaw)),
         vb.solid(f"{prefix}Fin", (0.4 * s, 0.1 * s, 0.25 * s), (x, y, z + 0.65 * s), kit.shades(color)["light"], bevel=0.02, rot=(0, 0, yaw)),
         vb.ball(f"{prefix}Eye", (0.1 * s, 0.1 * s, 0.1 * s), (x + ca * 0.45 * s - sa * 0.3 * s, y + sa * 0.45 * s + ca * 0.3 * s, z + 0.42 * s),
                 "#141414", segments=6, rings=4, studs="none")]
    return P


def jellyfish(prefix, center, color="#FF8FE0", rnd=None):
    rnd = rnd or random.Random(9)
    x, y, z = center
    P = [vb.ball(f"{prefix}Bell", (1.2, 1.2, 0.8), (x, y, z), color, segments=14, rings=7, emission=0.8),
         ring(f"{prefix}Skirt", 1.25, 0.95, 0.25, (x, y, z - 0.2), kit.shades(color)["dark"], sides=14)]
    for i in range(6):
        a = 2 * math.pi * i / 6
        P.append(vb.cyl(f"{prefix}Tent{i}", 0.06, 0.04, rnd.uniform(1.8, 3.0), (x + math.cos(a) * 0.7, y + math.sin(a) * 0.7, z - 3.0),
                        "#FFD1F2", sides=5, studs="none", emission=1.2))
    return P


def diver(prefix, base, suit="#FF8A1F", yaw=0.0):
    """R6-scale diver (5 studs) for scale: suit, glass helmet, air tank, flippers."""
    x, y, z = base
    P = [vb.solid(f"{prefix}LegL", (1, 1, 2), (x - 0.5, y, z), kit.shades(suit)["dark"]),
         vb.solid(f"{prefix}LegR", (1, 1, 2), (x + 0.5, y, z), kit.shades(suit)["dark"]),
         vb.solid(f"{prefix}FinL", (1.0, 1.6, 0.25), (x - 0.5, y + 0.4, z), "#FFD93B"),
         vb.solid(f"{prefix}FinR", (1.0, 1.6, 0.25), (x + 0.5, y + 0.4, z), "#FFD93B"),
         vb.solid(f"{prefix}Torso", (2, 1, 2), (x, y, z + 2), suit),
         vb.solid(f"{prefix}Belt", (2.1, 1.1, 0.35), (x, y, z + 2.1), "#24385B"),
         vb.solid(f"{prefix}ArmL", (1, 1, 2), (x - 1.5, y, z + 2), kit.shades(suit)["dark"]),
         vb.solid(f"{prefix}ArmR", (1, 1, 2), (x + 1.5, y, z + 2), kit.shades(suit)["dark"]),
         vb.cyl(f"{prefix}Tank", 0.45, 0.45, 2.0, (x, y - 0.9, z + 2.1), "#D9DEE6", sides=10),
         vb.solid(f"{prefix}Head", (1.0, 1.0, 1.0), (x, y, z + 4.05), "#F2C9A0"),
         glass(vb.ball(f"{prefix}Helmet", (0.9, 0.9, 0.85), (x, y, z + 4.55), "#BFF3FF", segments=14, rings=8, studs="none")),
         ring(f"{prefix}Collar", 0.95, 0.6, 0.3, (x, y, z + 3.95), "#FFC83D", sides=14)]
    return P


def seagrass(prefix, center, rnd, radius=3.0, n=18, greens=("#3FAE4A", "#5FCB55", "#2E8C3C", "#9BD84E")):
    """Sea-grass meadow: tilted angular blades of varied height in several greens."""
    x, y, z = center
    P = []
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r = radius * math.sqrt(rnd.random())
        h = rnd.uniform(0.9, 2.4)
        P.append(vb.solid(f"{prefix}Blade{i}", (0.2, 0.1, h), (x + math.cos(a) * r, y + math.sin(a) * r, z), greens[i % len(greens)],
                          bevel=0.02, rot=(rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), rnd.uniform(0, 3.14))))
    return P
