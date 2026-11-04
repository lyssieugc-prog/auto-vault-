"""
Underwater Research Facility — "Coralreach Station" (original art test, no references).

Builds the whole environment with Blender Python, then saves underwater_facility.blend.
    python art-tests/underwater-research-facility/scripts/build_facility.py   (bpy module)
    blender -b -P art-tests/underwater-research-facility/scripts/build_facility.py

Shared visual language: chunky layered geometry, texture studs (normal map, 0.5-stud spacing) on
solid surfaces, smooth glass/water/glow, 2+ shades per material, exaggerated playful proportions.
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path[:0] = [HERE, os.path.join(ROOT, "blender", "lib")]

import bpy  # noqa: E402

import uw_kit as uw  # noqa: E402
import vault_blocky as vb  # noqa: E402
import vault_kit as kit  # noqa: E402

# Facility palette: sunny yellow + lagoon teal + deep navy, coral accent; seabed sand + slate rock.
YEL, TEAL, NAVY, CORAL = "#FFC83D", "#1FB5B0", "#24385B", "#FF6B57"
STEEL, SAND, ROCK, LIGHT = "#C9D3DD", "#F0C47C", "#4F6A8A", "#FFE7A8"
Y, T, N = kit.shades(YEL), kit.shades(TEAL), kit.shades(NAVY)

S, R, C, B = vb.solid, vb.rounded, vb.cyl, vb.ball
OCT = math.radians(22.5)  # octagon parts rotated so one flat face points at +y

GROUND = (-80, 92, -60, 70)
TERRACES = [  # stepped slate-rock seabed shelves hugging the facility (x0, x1, y0, y1, h)
    (-80, 92, -60, -44, 6), (-80, -28, -60, -36, 11), (-80, -52, -60, -26, 16), (24, 92, -60, -38, 9), (56, 92, -60, -28, 14),
    (-80, -62, -26, 70, 4), (-80, -71, -12, 48, 8), (78, 92, -28, 44, 5), (85, 92, -14, 30, 10), (-74, -36, 20, 62, 2.5),
]


PADS = [  # flat building/gameplay pads (x0, x1, y0, y1, h) — override everything else
    (-22, 22, -36, 6, 0), (22, 58, -26, -2, 0), (-52, -24, -28, -2, 0), (-30, 14, 8, 50, 0), (44, 80, 6, 46, 0),
    (-46, 4, -2, 28, 0), (-10, 46, -4, 10, 0), (-74, -36, 20, 62, 2.5), (14, 46, 44, 50, 0), (20, 42, -38, -26, 0),
]
TRENCH = (16, 92, 50, 64)  # x0, x1, y0, y1: two-step trench across the front
CELL = 6.0


def _raw_height(x, y):
    for x0, x1, y0, y1, h in PADS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return h
    tx0, tx1, ty0, ty1 = TRENCH
    if tx0 <= x <= tx1 and ty0 <= y <= ty1:
        return -6.0 if ty0 + 3 <= y <= ty1 - 3 else -3.0
    h = 0.0
    for x0, x1, y0, y1, th in TERRACES:
        if x0 <= x <= x1 and y0 <= y <= y1:
            h = max(h, th)
    if h == 0.0:  # structured rolling mounds (stepped, not noise): 0 / 0.9 / 1.8 / 2.7
        k = math.sin(x * 0.09) + math.cos(y * 0.11) + 0.6 * math.sin((x + y) * 0.05)
        h = 0.9 * max(0, min(3, int(round(k + 0.4))))
    return h


def theight(x, y):
    """Height of the terrain cell containing (x, y)."""
    gx0, _, gy0, _ = GROUND
    cx = gx0 + (math.floor((x - gx0) / CELL) + 0.5) * CELL
    cy = gy0 + (math.floor((y - gy0) / CELL) + 0.5) * CELL
    return _raw_height(cx, cy)


def terrain_blocks():
    """Blocky seabed: CELL-sized columns (run-length merged along x) with rock body, a darker ledge
    band and a sand/moss cap. Height changes read as stepped, layered cliffs."""
    gx0, gx1, gy0, gy1 = GROUND
    nx, ny = int((gx1 - gx0) / CELL), int((gy1 - gy0) / CELL)
    rk, sd = kit.shades(ROCK), kit.shades(SAND)
    P = [S("SeabedFloor", (gx1 - gx0, gy1 - gy0, 1.0), ((gx0 + gx1) / 2, (gy0 + gy1) / 2, -9.0), rk["deep"], bevel=0.0)]
    for j in range(ny):
        cy = gy0 + (j + 0.5) * CELL
        i = 0
        while i < nx:
            cx0 = gx0 + i * CELL
            h = _raw_height(cx0 + CELL / 2, cy)
            k = i
            while k + 1 < nx and _raw_height(gx0 + (k + 1.5) * CELL, cy) == h:
                k += 1
            w = (k - i + 1) * CELL
            x = cx0 + w / 2
            base = -8.0
            P.append(S(f"TBody{j}_{i}", (w, CELL, h - 0.6 - base), (x, cy, base), rk["base" if (i + j) % 2 else "dark"], bevel=0.04))
            cap = sd["base"] if h <= 1.0 else (sd["dark"] if h < 6 else "#6FAE6A")
            if h < -1:
                cap = "#2F5E7A"  # trench floor: deep blue-grey silt
            P.append(S(f"TCap{j}_{i}", (w + 0.2, CELL + 0.2, 0.6), (x, cy, h - 0.6), cap, bevel=0.05))
            if h >= 3 or h <= -3:
                P.append(S(f"TLedge{j}_{i}", (w + 0.45, CELL + 0.45, 0.4), (x, cy, h - 2.2), rk["light"] if h > 0 else rk["dark"], bevel=0.04))
            i = k + 1
    return P


def move(objs, dx, dy, dz=0.0):
    for o in objs:
        if o.parent is None:
            o.location = (o.location[0] + dx, o.location[1] + dy, o.location[2] + dz)
    vb.restud(objs)
    return objs


# ---- 1. Central research hub -------------------------------------------------------------------
def hub(cx=0.0, cy=-15.0):
    P = []
    rot = (0, 0, OCT)
    P += [C("HubFoundation", 17.5, 17.5, 1.4, (cx, cy, 0), N["deep"], sides=8, rot=rot),
          C("HubPlinth", 16.0, 15.6, 1.2, (cx, cy, 1.4), N["base"], sides=8, rot=rot),
          C("HubWall", 14.0, 14.0, 9.0, (cx, cy, 2.6), Y["base"], sides=8, rot=rot),
          uw.ring("HubBandLow", 14.45, 13.9, 0.7, (cx, cy, 2.6), N["base"], sides=8, rot=rot),
          uw.ring("HubBandMid", 14.35, 13.9, 0.45, (cx, cy, 7.6), T["base"], sides=8, rot=rot),
          uw.ring("HubBandTop", 14.45, 13.9, 0.7, (cx, cy, 10.9), N["base"], sides=8, rot=rot)]
    face_d = 14.0 * math.cos(math.radians(22.5))
    for k in range(8):  # corner struts with bolt plates
        a = math.radians(22.5 + 45 * k)
        x, y = cx + math.cos(a) * 14.1, cy + math.sin(a) * 14.1
        P.append(S(f"HubStrut{k}", (1.5, 1.5, 9.6), (x, y, 2.4), N["dark"], rot=(0, 0, a)))
        for j, z in enumerate((4.0, 9.2)):
            P.append(S(f"HubStrutPlate{k}_{j}", (1.9, 1.9, 0.5), (x, y, z), Y["dark"], rot=(0, 0, a)))
    for k in range(8):  # portholes on free faces (0/135/180° faces carry tunnels, 90° the airlock)
        th = math.radians(45 * k)
        if k in (0, 2, 3, 4):
            continue
        nx, ny = math.cos(th), math.sin(th)
        for j, off in enumerate((-2.9, 2.9)):
            px, py = cx + nx * face_d - ny * off, cy + ny * face_d + nx * off
            P += uw.porthole(f"HubPort{k}_{j}_", (px, py, 5.4), th, r=1.15)
        P.append(S(f"HubPanel{k}", (8.4, 0.25, 1.2), (cx + nx * face_d, cy + ny * face_d, 8.25), T["dark"], rot=(0, 0, th + math.pi / 2)))
    # airlock door on the front face
    fy = cy + face_d
    P += [S("AirlockFrame", (6.4, 1.0, 7.0), (cx, fy + 0.3, 2.6), N["base"]),
          S("AirlockDoor", (4.6, 0.5, 5.6), (cx, fy + 0.85, 2.9), STEEL),
          S("AirlockStep", (8.0, 2.6, 0.6), (cx, fy + 2.0, 2.0), N["dark"]),
          S("AirlockStep2", (9.0, 3.4, 0.6), (cx, fy + 2.6, 1.4), N["base"])]
    for i in range(7):  # hazard stripes on the lintel
        P.append(S(f"AirlockHazard{i}", (0.8, 0.12, 1.0), (cx - 2.7 + i * 0.9, fy + 0.86, 8.7), YEL if i % 2 else "#1A1A1A",
                   bevel=0.01, rot=(0, math.radians(30), 0)))
    P.append(uw.ring("AirlockWheel", 1.0, 0.7, 0.3, (cx, fy + 1.1, 5.6), CORAL, sides=16, rot=uw.face_rot(math.pi / 2)))
    for i in range(4):
        P.append(S(f"AirlockSpoke{i}", (1.6, 0.2, 0.2), (cx, fy + 1.25, 5.5), CORAL, rot=(0, math.radians(45 * i), 0)))
    for sx in (-1, 1):
        P.append(R(f"AirlockLampBox{sx}", (0.8, 0.6, 0.8), (cx + sx * 3.9, fy + 0.6, 7.4), N["deep"], radius=0.12))
        P.append(B(f"AirlockLamp{sx}", (0.3, 0.3, 0.3), (cx + sx * 3.9, fy + 1.0, 7.8), "#7CFF9C", segments=8, rings=5, emission=5))
    # sign with a blocky fish icon
    P += [S("HubSign", (9.0, 0.5, 2.0), (cx, fy + 0.4, 9.4), T["base"]),
          S("HubSignFrame", (9.6, 0.4, 0.3), (cx, fy + 0.45, 11.3), Y["light"]),
          R("HubSignFish", (2.0, 0.3, 1.1), (cx - 2.6, fy + 0.75, 9.85), CORAL, radius=0.2),
          S("HubSignFishTail", (0.7, 0.3, 1.0), (cx - 4.0, fy + 0.75, 9.9), CORAL, rot=(0, math.radians(15), 0)),
          S("HubSignBar0", (4.0, 0.3, 0.3), (cx + 1.6, fy + 0.75, 10.5), Y["light"]),
          S("HubSignBar1", (3.0, 0.3, 0.3), (cx + 1.1, fy + 0.75, 9.9), Y["light"])]
    # observation deck + glass ring
    P += [C("HubDeck", 16.2, 16.2, 1.0, (cx, cy, 11.6), N["base"], sides=8, rot=rot),
          C("HubDeckTrim", 16.6, 16.6, 0.3, (cx, cy, 11.3), T["base"], sides=8, rot=rot)]
    for k in range(16):
        a = 2 * math.pi * k / 16
        P.append(S(f"HubRailPost{k}", (0.35, 0.35, 1.8), (cx + math.cos(a) * 15.6, cy + math.sin(a) * 15.6, 12.6), Y["base"]))
    P.append(uw.ring("HubRail", 15.85, 15.35, 0.3, (cx, cy, 14.3), Y["light"], sides=16))
    P.append(uw.glass(C("HubObsGlass", 11.5, 11.5, 4.2, (cx, cy, 12.6), "#BFF3FF", sides=16, studs="none")))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        P.append(S(f"HubMullion{k}", (0.7, 0.7, 4.2), (cx + math.cos(a) * 11.5, cy + math.sin(a) * 11.5, 12.6), N["dark"], rot=(0, 0, a)))
    P.append(vb.block("HubObsLight", (16, 16, 0.2), (cx, cy, 16.4), LIGHT, bevel=0.0, emission=2.5))
    P[-1].rotation_euler = (0, 0, OCT)
    for k in range(4):  # consoles inside the glass ring
        a = math.radians(45 + 90 * k)
        x, y = cx + math.cos(a) * 8.5, cy + math.sin(a) * 8.5
        P.append(S(f"HubConsole{k}", (2.6, 1.4, 1.4), (x, y, 12.6), STEEL, rot=(0, 0, a + math.pi / 2)))
        P.append(vb.block(f"HubScreen{k}", (2.2, 0.1, 0.9), (x - math.cos(a) * 0.2, y - math.sin(a) * 0.2, 14.0), "#5CF2FF",
                          bevel=0.0, emission=3.5))
        P[-1].rotation_euler = (math.radians(-15), 0, a + math.pi / 2)
    # stepped roof, vents, radar mast + beacon
    P += [C("HubRoof", 13.0, 13.0, 0.8, (cx, cy, 16.8), Y["base"], sides=8, rot=rot),
          C("HubRoofCone", 11.5, 6.2, 3.0, (cx, cy, 17.6), Y["light"], sides=8, rot=rot),
          C("HubRoofCap", 6.6, 6.6, 0.8, (cx, cy, 20.6), N["base"], sides=8, rot=rot),
          C("HubMast", 0.45, 0.3, 9.0, (cx, cy, 21.4), STEEL, sides=10),
          S("HubMastBar", (4.0, 0.35, 0.35), (cx, cy, 26.5), STEEL),
          B("HubBeacon", (0.6, 0.6, 0.6), (cx, cy, 30.8), "#FF3B3B", segments=12, rings=7, emission=6),
          S("HubRadarArm", (4.2, 0.5, 0.5), (cx + 2.0, cy, 24.0), N["dark"]),
          B("HubRadarDish", (2.3, 2.3, 0.55), (cx + 4.4, cy, 24.9), "#E8EEF5", segments=16, rings=8, rot=(0, math.radians(-35), 0)),
          C("HubRadarFeed", 0.15, 0.1, 1.6, (cx + 4.4, cy, 24.9), CORAL, sides=6, rot=(0, math.radians(-35), 0))]
    for k in range(3):
        a = math.radians(30 + 120 * k)
        vx, vy = cx + math.cos(a) * 8.5, cy + math.sin(a) * 8.5
        P.append(C(f"HubVent{k}", 0.6, 0.6, 1.8, (vx, vy, 18.4), N["dark"], sides=10))
        P.append(uw.ring(f"HubVentLip{k}", 0.8, 0.45, 0.25, (vx, vy, 20.1), T["base"], sides=10))
        P += uw.bubbles(f"HubVentB{k}", (vx, vy, 21.0), height=14, count=8, rnd=random.Random(k))
    for k in range(4):  # external pipes with clamps + elbows
        a = math.radians(22.5 + 90 * k + 12)
        x, y = cx + math.cos(a) * 14.9, cy + math.sin(a) * 14.9
        P.append(C(f"HubPipe{k}", 0.42, 0.42, 9.0, (x, y, 2.6), T["dark"], sides=10))
        P.append(B(f"HubPipeElbow{k}", (0.55, 0.55, 0.55), (x, y, 11.6), T["base"], segments=10, rings=6))
        for j in range(3):
            P.append(uw.ring(f"HubPipeClamp{k}_{j}", 0.6, 0.38, 0.3, (x, y, 4 + j * 2.6), STEEL, sides=10))
    return P


# ---- 2. Laboratory wing (lab visible through big windows) --------------------------------------
def lab(cx=40.0, cy=-14.0):
    W, D, H = 28, 17, 9.0
    fy = cy + D / 2
    P = [S("LabPlatform", (W + 2, D + 2, 1.5), (cx, cy, 0), N["deep"]),
         S("LabFloor", (W - 1, D - 1, 0.4), (cx, cy, 1.5), "#DCE3EA"),
         S("LabBack", (W, 1, H), (cx, cy - D / 2 + 0.5, 1.5), Y["base"]),
         S("LabSideW", (1, D - 2, H), (cx - W / 2 + 0.5, cy, 1.5), Y["base"]),
         S("LabSideE", (1, D - 2, H), (cx + W / 2 - 0.5, cy, 1.5), Y["base"]),
         S("LabFrontLow", (W, 1, 1.6), (cx, fy - 0.5, 1.5), Y["dark"]),
         S("LabFrontHigh", (W, 1, 1.4), (cx, fy - 0.5, 1.5 + H - 1.4), Y["dark"]),
         uw.glass(S("LabWindow", (W - 2, 0.2, H - 3.0), (cx, fy - 0.5, 3.1), "#BFF3FF", studs="none", bevel=0.0))]
    for i, x in enumerate((-W / 2 + 0.8, -7, 0, 7, W / 2 - 0.8)):  # mullions + transom + corner columns
        big = i in (0, 4)
        P.append(S(f"LabMullion{i}", (1.6 if big else 0.55, 1.4 if big else 0.6, H + (1.2 if big else 0)), (cx + x, fy - 0.3, 1.5),
                   T["base"] if big else T["dark"]))
    P.append(S("LabTransom", (W - 2, 0.6, 0.45), (cx, fy - 0.3, 7.6), T["dark"]))
    P += [S("LabRoof", (W + 2.4, D + 2.4, 1.0), (cx, cy, 1.5 + H), N["base"]),
          S("LabRoofStep", (W - 3, D - 4, 0.8), (cx, cy, 2.5 + H), T["base"]),
          S("LabSignBack", (12, 0.6, 2.2), (cx, fy + 0.6, 2.6 + H), CORAL),
          S("LabSignFace", (11, 0.2, 1.6), (cx, fy + 0.95, 2.9 + H), "#FFF6EA", bevel=0.01),
          R("LabSignFlask", (1.2, 0.3, 1.4), (cx - 4.0, fy + 1.1, 2.95 + H), "#7CFF9C", radius=0.3),
          S("LabSignFlaskNeck", (0.45, 0.3, 0.6), (cx - 4.0, fy + 1.1, 4.3 + H), "#7CFF9C")]
    for i in range(3):
        P.append(S(f"LabSignStripe{i}", (5.0 - i, 0.25, 0.25), (cx + 1.2 - i * 0.4, fy + 1.1, 3.1 + i * 0.45 + H), N["base"]))
    P.append(uw.glass(S("LabSkylight", (9, 5, 0.3), (cx + 5, cy - 1, 3.3 + H), "#BFF3FF", studs="none", bevel=0.0)))
    P.append(S("LabSkyFrame", (9.8, 5.8, 0.25), (cx + 5, cy - 1, 3.2 + H), Y["base"]))
    for i, (x, y) in enumerate(((-9, -3), (-5.5, -4), (-2, -3))):  # sensor dish array
        P.append(C(f"LabDishPole{i}", 0.25, 0.2, 2.0, (cx + x, cy + y, 3.3 + H), STEEL, sides=8))
        P.append(B(f"LabDish{i}", (1.2, 1.2, 0.35), (cx + x, cy + y, 5.4 + H), "#E8EEF5", segments=14, rings=7,
                   rot=(math.radians(-30), 0, math.radians(20 * i))))
    # interior: lights, benches, monitors, specimen tanks, racks, whiteboard
    for i in range(3):
        P.append(vb.block(f"LabCeilLight{i}", (6.5, 2.2, 0.15), (cx - 8 + i * 8, cy, 1.5 + H - 0.35), LIGHT, bevel=0.0, emission=4.0))
    for i, x in enumerate((-8.5, 0.0, 8.5)):
        P += [S(f"LabBench{i}", (6.4, 2.4, 1.5), (cx + x, cy + 2.0, 1.9), "#F4F7FA"),
              S(f"LabBenchTop{i}", (6.8, 2.8, 0.25), (cx + x, cy + 2.0, 3.4), T["base"]),
              S(f"LabMonitor{i}", (2.0, 0.3, 1.4), (cx + x - 1.6, cy + 1.6, 3.65), N["deep"]),
              S(f"LabMicroBase{i}", (0.9, 0.9, 0.3), (cx + x + 1.4, cy + 2.2, 3.65), STEEL),
              S(f"LabMicroArm{i}", (0.3, 0.3, 1.2), (cx + x + 1.6, cy + 2.0, 3.95), STEEL),
              C(f"LabMicroEye{i}", 0.2, 0.2, 0.7, (cx + x + 1.4, cy + 2.2, 4.6), N["dark"], sides=8)]
        P.append(vb.block(f"LabScreen{i}", (1.8, 0.05, 1.2), (cx + x - 1.6, cy + 1.78, 3.75), "#5CF2FF", bevel=0.0, emission=3.5))
        for j, col in enumerate(("#FF6FAE", "#7CFF9C", "#FFD93B")):
            P.append(uw.glass(C(f"LabJar{i}_{j}", 0.22, 0.22, 0.6, (cx + x + 0.1 + j * 0.5, cy + 2.6, 3.65), col, sides=10, studs="none"),
                              tint=col))
    for i, (x, col) in enumerate(((-11.5, "#7CFF9C"), (11.5, "#FF8FE0"))):  # specimen tanks with glowing liquid
        P += [C(f"LabTankBase{i}", 1.4, 1.4, 0.6, (cx + x, cy - 4.5, 1.9), N["base"], sides=12),
              uw.glass(C(f"LabTank{i}", 1.1, 1.1, 4.2, (cx + x, cy - 4.5, 2.5), "#DFFBFF", sides=16, studs="none")),
              C(f"LabTankLiquid{i}", 1.0, 1.0, 3.0, (cx + x, cy - 4.5, 2.55), col, sides=16, studs="none", emission=2.2),
              C(f"LabTankCap{i}", 1.3, 1.3, 0.5, (cx + x, cy - 4.5, 6.7), N["base"], sides=12)]
    for i in range(4):  # server racks against the back wall
        P.append(S(f"LabRack{i}", (2.2, 1.4, 6.0), (cx - 6 + i * 2.6, cy - D / 2 + 1.7, 1.9), N["dark"]))
        for j in range(5):
            P.append(vb.block(f"LabLED{i}_{j}", (0.25, 0.06, 0.25), (cx - 6.6 + i * 2.6 + (j % 2) * 0.6, cy - D / 2 + 2.42, 2.6 + j * 1.0),
                              ("#7CFF9C", "#5CF2FF", "#FFD93B")[j % 3], bevel=0.0, emission=4))
    P.append(S("LabBoard", (6.0, 0.2, 3.0), (cx + 6, cy - D / 2 + 1.05, 4.0), "#FFFFFF"))
    for i, col in enumerate((CORAL, TEAL, "#B678EA")):
        P.append(S(f"LabBoardLine{i}", (4.0 - i, 0.06, 0.2), (cx + 5.8, cy - D / 2 + 1.18, 4.7 + i * 0.7), col, bevel=0.0))
    return P


# ---- 3. Habitat pod with rooftop greenhouse ------------------------------------------------------
def habitat(cx=-38.0, cy=-15.0):
    P = [C("PodBase", 10.5, 10.5, 1.6, (cx, cy, 0), N["deep"], sides=12),
         C("PodWall", 9.0, 9.0, 7.0, (cx, cy, 1.6), T["base"], sides=12),
         uw.ring("PodBand", 9.4, 8.9, 0.6, (cx, cy, 5.0), Y["base"], sides=12),
         C("PodRoof", 9.9, 9.9, 0.7, (cx, cy, 8.6), Y["base"], sides=12),
         C("PodRoofCone", 9.2, 4.6, 2.6, (cx, cy, 9.3), Y["light"], sides=12),
         C("PodRoofRing", 4.9, 4.9, 0.6, (cx, cy, 11.9), N["base"], sides=12)]
    fd = 9.0 * math.cos(math.radians(15))
    for k in range(12):
        th = math.radians(15 + 30 * k)
        if k in (11, 0):  # tunnel side
            continue
        if k % 2 == 0:
            P += uw.porthole(f"PodPort{k}_", (cx + math.cos(th) * fd, cy + math.sin(th) * fd, 3.4), th, r=0.95, frame=Y["dark"])
        P.append(S(f"PodRib{k}", (0.8, 0.8, 7.2), (cx + math.cos(th + math.radians(15)) * 9.05, cy + math.sin(th + math.radians(15)) * 9.05, 1.5),
                   N["base"], rot=(0, 0, th)))
    P.append(uw.glass(B("PodGreenhouse", (4.2, 4.2, 3.2), (cx, cy, 12.5), "#DFFBFF", segments=18, rings=9, studs="none")))
    for i in range(6):  # hydroponic plants inside the greenhouse
        a = 2 * math.pi * i / 6
        P.append(R(f"PodPlant{i}", (1.0, 1.0, 1.2), (cx + math.cos(a) * 2.2, cy + math.sin(a) * 2.2, 12.5), ("#4CC24A", "#86E05A")[i % 2],
                   radius=0.2, rot=(0, 0, a)))
        P.append(B(f"PodTomato{i}", (0.25, 0.25, 0.25), (cx + math.cos(a) * 2.2, cy + math.sin(a) * 2.2 + 0.5, 13.5), "#FF4D4D",
                   segments=8, rings=5))
    P.append(vb.block("PodGrowLight", (3.0, 3.0, 0.15), (cx, cy, 15.2), "#FF8FE0", bevel=0.0, emission=3))
    P += [C("PodAntenna", 0.2, 0.15, 5.0, (cx + 3.5, cy - 3.0, 11.0), STEEL, sides=8),
          B("PodAntennaTip", (0.3, 0.3, 0.3), (cx + 3.5, cy - 3.0, 16.0), "#7CFF9C", segments=8, rings=5, emission=5)]
    for i in range(7):  # ladder rungs
        P.append(S(f"PodLadderRung{i}", (1.4, 0.25, 0.2), (cx - 1.5, cy + 9.3, 1.8 + i * 1.0), STEEL))
    for sx in (-1, 1):
        P.append(S(f"PodLadderRail{sx}", (0.25, 0.25, 7.2), (cx - 1.5 + sx * 0.7, cy + 9.3, 1.6), STEEL))
    return P


# ---- 4. Aquarium dome + original creature "Bubblemunch" -------------------------------------------
def bubblemunch(cx, cy, cz):
    """Original chunky lure-fish: magenta body, layered fins, scale plates (plausible on a fish),
    gill slits, giant eyes, toothy grin, glowing lure on an arched stalk."""
    BODY, BELLY, FIN = kit.shades("#E84A9C"), "#FFC7E6", kit.shades("#FFC83D")
    P = [R("BmBody", (6.2, 5.0, 5.0), (cx, cy, cz - 2.5), BODY["base"], radius=1.3),
         R("BmBelly", (4.6, 1.2, 2.8), (cx, cy + 2.2, cz - 2.3), BELLY, radius=0.5),
         R("BmBrow", (5.0, 1.2, 1.0), (cx, cy + 1.9, cz + 1.4), BODY["dark"], radius=0.35)]
    for sx, side in ((-1, "L"), (1, "R")):  # giant eyes
        ex = cx + sx * 1.45
        P += [R(f"BmEye{side}", (2.2, 0.4, 2.3), (ex, cy + 2.55, cz - 0.6), "#FFFFFF", radius=0.5, studs="none"),
              R(f"BmPupil{side}", (1.0, 0.3, 1.25), (ex - sx * 0.25, cy + 2.78, cz - 0.45), "#141414", radius=0.3, studs="none"),
              B(f"BmSparkle{side}", (0.22, 0.12, 0.22), (ex + sx * 0.05, cy + 2.95, cz + 0.45), "#FFFFFF", segments=8, rings=5,
                studs="none", emission=1.2),
              R(f"BmCheek{side}", (0.8, 0.2, 0.45), (cx + sx * 2.45, cy + 2.4, cz - 1.7), "#FF9CC9", radius=0.12, studs="none")]
    P.append(R("BmMouth", (3.4, 0.35, 1.0), (cx, cy + 2.72, cz - 2.15), "#3A1026", radius=0.35, studs="none"))
    for i in range(5):
        P.append(S(f"BmTooth{i}", (0.32, 0.2, 0.36), (cx - 1.2 + i * 0.6, cy + 2.95, cz - 1.45), "#FFFFFF", bevel=0.05, studs="none",
                   rot=(0, 0, 0)))
    for sx in (-1, 1):
        for row in range(3):  # scale plates along the flanks (2 shades)
            for col in range(3):
                P.append(R(f"BmScale{sx}_{row}{col}", (0.25, 0.95, 0.8), (cx + sx * 3.13, cy - 1.3 + col * 1.1 + row * 0.2, cz - 1.8 + row * 0.95),
                           BODY["dark" if (row + col) % 2 else "light"], radius=0.12))
        for g in range(3):  # gill slits
            P.append(S(f"BmGill{sx}_{g}", (0.12, 0.2, 1.4), (cx + sx * 3.1, cy + 1.6 - g * 0.4, cz - 2.0), "#7A1E4F", bevel=0.02,
                       studs="none"))
        P.append(S(f"BmPecFin{sx}", (0.3, 2.4, 1.6), (cx + sx * 3.4, cy + 0.2, cz - 2.6), FIN["base"], rot=(0, math.radians(sx * 35), 0)))
        P.append(S(f"BmPecFinRay{sx}", (0.32, 1.8, 0.25), (cx + sx * 3.7, cy + 0.2, cz - 1.8), FIN["dark"], rot=(0, math.radians(sx * 35), 0)))
    for i in range(3):  # layered dorsal fin
        P.append(S(f"BmDorsal{i}", (0.4, 2.6 - i * 0.6, 1.6 + i * 0.5), (cx, cy - 0.4 - i * 0.3, cz + 2.2), FIN["base" if i != 1 else "light"],
                   rot=(math.radians(-18 - i * 8), 0, 0)))
    for i, (yaw, col) in enumerate(((-28, "base"), (0, "light"), (28, "dark"))):  # fanned tail fin layers
        P.append(S(f"BmTail{i}", (0.4, 2.6, 3.0), (cx, cy - 3.4, cz - 2.6), FIN[col], rot=(math.radians(yaw), 0, 0)))
    for i in range(5):  # spots on the back
        P.append(B(f"BmSpot{i}", (0.35, 0.35, 0.18), (cx - 1.8 + i * 0.9, cy - 0.8 - (i % 2) * 0.8, cz + 2.45), BODY["light"],
                   segments=8, rings=5))
    pts = [(0, 1.0, 2.4), (0, 1.8, 3.6), (0, 2.9, 4.2), (0, 3.9, 3.8)]  # arched lure stalk
    for i in range(len(pts) - 1):
        (x0, y0, z0), (x1, y1, z1) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        tilt = math.atan2(y1 - y0, z1 - z0)
        P.append(C(f"BmLureStalk{i}", 0.2, 0.17, L + 0.1, (cx + x0, cy + y0, cz + z0), BODY["dark"], sides=8, rot=(-tilt, 0, 0)))
    P.append(B("BmLure", (0.6, 0.6, 0.6), (cx, cy + 3.95, cz + 3.4), "#7CF7FF", segments=12, rings=7, emission=6))
    P.append(uw.ring("BmLureRing", 0.75, 0.5, 0.2, (cx, cy + 3.95, cz + 3.7), "#FFFFFF", sides=12, studs="none"))
    return P


def dome(cx=-8.0, cy=30.0):
    Rd, base_h = 16.0, 2.6
    P = [C("DomeBase", 18.0, 18.0, base_h, (cx, cy, 0), N["base"], sides=24),
         uw.ring("DomeBaseTrim", 18.4, 17.6, 0.6, (cx, cy, base_h - 0.6), T["base"], sides=24),
         C("DomeSandFloor", 15.6, 15.6, 0.6, (cx, cy, base_h), SAND, sides=24)]
    for i in range(12):  # uplights
        a = 2 * math.pi * i / 12
        P.append(S(f"DomeUplightBox{i}", (1.2, 0.8, 0.8), (cx + math.cos(a) * 18.2, cy + math.sin(a) * 18.2, 0.6), N["deep"], rot=(0, 0, a)))
        P.append(vb.block(f"DomeUplight{i}", (0.8, 0.1, 0.4), (cx + math.cos(a) * 18.62, cy + math.sin(a) * 18.62, 0.8), "#7CF7FF",
                          bevel=0.0, emission=5))
        P[-1].rotation_euler = (0, 0, a + math.pi / 2)
    P.append(uw.glass(B("DomeGlass", (Rd, Rd, Rd), (cx, cy, base_h), "#CFF7FF", segments=32, rings=16, studs="none")))
    for z in (5.0, 10.0, 13.6):  # latitude frame rings
        r = math.sqrt(Rd * Rd - z * z)
        P.append(uw.ring(f"DomeLat{int(z)}", r + 0.35, r - 0.05, 0.5, (cx, cy, base_h + z - 0.25), Y["base"], sides=32))
    for k in range(10):  # meridian ribs (segmented arcs)
        th = 2 * math.pi * k / 10
        for j in range(8):
            a0, a1 = math.pi / 2 * j / 8, math.pi / 2 * (j + 1) / 8
            m = (a0 + a1) / 2
            L = 2 * Rd * math.sin((a1 - a0) / 2)
            P.append(S(f"DomeRib{k}_{j}", (0.5, 0.5, L + 0.05),
                       (cx + Rd * math.cos(a0) * math.cos(th), cy + Rd * math.cos(a0) * math.sin(th), base_h + Rd * math.sin(a0)),
                       Y["dark"] if k % 2 else Y["base"], rot=(0, -m, th)))
    P += [C("DomeCrown", 2.4, 1.6, 1.0, (cx, cy, base_h + Rd - 0.2), N["base"], sides=12),
          B("DomeCrownLight", (0.7, 0.7, 0.7), (cx, cy, base_h + Rd + 1.2), "#7CF7FF", segments=12, rings=6, emission=6)]
    rnd = random.Random(33)
    z0 = base_h + 0.6
    P += uw.branch_coral("DomeCoralA", (cx - 7, cy - 5, z0), "#FF6B57", rnd, height=5)
    P += uw.table_coral("DomeTable", (cx + 7, cy - 6, z0), "#B678EA", r=2.4)
    P += uw.anemone("DomeAnemone", (cx + 6, cy + 6, z0), "#FFD93B", "#FF6FAE", rnd)
    P += uw.tube_sponge("DomeSponge", (cx - 6, cy + 7, z0), "#22C3A6", rnd)
    P += uw.starfish("DomeStar", (cx + 2, cy + 9, z0), "#FF9F1C", yaw=0.4)
    P += uw.bubbles("DomeBubbles", (cx + 3, cy - 2, z0), height=10, count=10, rnd=rnd)
    fish = bubblemunch(0, 0, 0)
    vb.scale_group(fish, 1.35)
    P += move(fish, cx, cy + 1, z0 + 7.5)
    # info plaque out front
    P += [S("DomePlaqueStand", (1.0, 1.0, 3.0), (cx + 13, cy + 18, 0), N["base"]),
          S("DomePlaque", (4.4, 0.4, 2.4), (cx + 13, cy + 18.3, 3.0), T["base"], rot=(math.radians(-20), 0, 0)),
          R("DomePlaqueFish", (1.4, 0.2, 0.8), (cx + 12.0, cy + 18.65, 3.9), "#E84A9C", radius=0.2, rot=(math.radians(-20), 0, 0))]
    return P


# ---- 5. Submarine dock + "Snorkel-9" ------------------------------------------------------------
def submarine(cx, cy, cz):
    HULL = kit.shades("#FF8A1F")
    P = [R("SubHull", (15.0, 5.2, 5.2), (cx, cy, cz - 2.6), HULL["base"], radius=1.6),
         R("SubKeel", (12.0, 3.0, 1.0), (cx, cy, cz - 3.1), N["base"], radius=0.4),
         R("SubNose", (3.0, 4.4, 4.4), (cx + 7.6, cy, cz - 2.2), HULL["light"], radius=1.2),
         uw.glass(B("SubBubble", (2.0, 2.0, 2.1), (cx + 9.1, cy, cz - 0.1), "#CFF7FF", segments=18, rings=10, studs="none"))]
    for i, x in enumerate((-4.5, 0.0, 4.5)):  # hull bands
        P.append(R(f"SubBand{i}", (0.8, 5.5, 5.5), (cx + x, cy, cz - 2.75), T["base"], radius=1.5))
    for side in (-1, 1):
        for i, x in enumerate((-2.2, 2.2)):
            P += uw.porthole(f"SubPort{side}_{i}_", (cx + x, cy + side * 2.62, cz + 0.2), math.pi / 2 * side, r=0.8, frame=N["base"])
        P.append(R(f"SubBallast{side}", (8.0, 1.4, 1.4), (cx - 1, cy + side * 3.1, cz - 2.9), N["dark"], radius=0.6))
        P.append(C(f"SubLampHouse{side}", 0.6, 0.6, 0.6, (cx + 8.2, cy + side * 1.7, cz - 1.0), N["base"], sides=12,
                   rot=(0, math.pi / 2, 0)))
        P.append(C(f"SubLamp{side}", 0.45, 0.45, 0.1, (cx + 8.8, cy + side * 1.7, cz - 1.0), "#FFF6C8", sides=12, studs="none",
                   rot=(0, math.pi / 2, 0), emission=6))
        P.append(S(f"SubStabilizer{side}", (2.4, 2.6, 0.4), (cx - 6.6, cy + side * 3.6, cz - 0.4), Y["base"], rot=(0, 0, side * 0.2)))
    P += [R("SubTower", (4.4, 3.0, 3.2), (cx - 0.6, cy, cz + 2.1), HULL["dark"], radius=0.6),
          R("SubTowerCap", (3.4, 2.4, 0.6), (cx - 0.6, cy, cz + 5.2), N["base"], radius=0.2),
          uw.ring("SubHatch", 0.9, 0.55, 0.25, (cx - 1.4, cy, cz + 5.8), Y["base"], sides=14),
          C("SubPeriscope", 0.25, 0.25, 3.0, (cx + 0.6, cy, cz + 5.6), STEEL, sides=8),
          S("SubPeriscopeHead", (1.2, 0.6, 0.6), (cx + 0.9, cy, cz + 8.6), STEEL),
          C("SubWhip", 0.07, 0.05, 3.5, (cx - 1.9, cy + 0.7, cz + 5.8), STEEL, sides=5),
          B("SubWhipTip", (0.18, 0.18, 0.18), (cx - 1.9, cy + 0.7, cz + 9.3), "#FF3B3B", segments=6, rings=4, emission=5),
          S("SubRudder", (2.6, 0.4, 3.0), (cx - 7.6, cy, cz - 0.3), Y["base"]),
          C("SubPropHub", 0.8, 0.4, 1.4, (cx - 7.6, cy, cz - 2.6), STEEL, sides=12, rot=(0, -math.pi / 2, 0)),
          uw.ring("SubPropShroud", 2.4, 2.0, 1.2, (cx - 9.3, cy, cz - 2.6), N["base"], sides=20, rot=(0, -math.pi / 2, 0))]
    for i in range(4):
        P.append(S(f"SubBlade{i}", (0.3, 0.6, 1.9), (cx - 8.6, cy, cz - 2.6), Y["light"], rot=(math.radians(45 + 90 * i), 0, 0)))
    for i, (x, z, ang) in enumerate(((7.0, -4.2, -20), (8.4, -4.8, 15))):  # claw arm
        P.append(S(f"SubClawArm{i}", (2.2, 0.6, 0.6), (cx + x, cy, cz + z), STEEL, rot=(0, math.radians(ang), 0)))
    for sx in (-1, 1):
        P.append(S(f"SubPincer{sx}", (0.9, 0.3, 0.3), (cx + 9.4, cy + sx * 0.35, cz - 5.1), CORAL, rot=(0, 0, sx * 0.5)))
    for i in range(9):  # rivets along the top seam
        P.append(B(f"SubRivet{i}", (0.12, 0.12, 0.12), (cx - 6 + i * 1.5, cy + 2.2, cz + 1.65), "#FFE0B0", segments=6, rings=4, studs="none"))
    return P


def dock(cx=62.0, cy=24.0):
    deck_z = 4.5
    P = [S("DockDeck", (26, 11, 1.0), (cx, cy, deck_z), "#4A5873"),
         S("DockDeckTrim", (26.6, 11.6, 0.35), (cx, cy, deck_z - 0.35), N["dark"])]
    for i in range(13):  # hazard edge along the berth side
        P.append(S(f"DockHazard{i}", (2.0, 0.6, 0.3), (cx - 12 + i * 2.0, cy + 5.2, deck_z + 1.0), YEL if i % 2 else "#1A1A1A", bevel=0.02))
    for i, x in enumerate((-11, -5.5, 0, 5.5, 11)):  # pilings with footings
        for y in (-4.2, 4.2):
            P.append(C(f"DockPile{i}_{y}", 0.7, 0.7, deck_z, (cx + x, cy + y, 0), N["base"], sides=10))
            P.append(C(f"DockPileFoot{i}_{y}", 1.3, 1.5, 0.6, (cx + x, cy + y, 0), N["deep"], sides=10))
            P.append(uw.ring(f"DockPileBand{i}_{y}", 0.9, 0.65, 0.35, (cx + x, cy + y, deck_z * 0.5), Y["base"], sides=10))
    for i, x in enumerate((-9, -3, 3, 9)):  # bollards + mooring lines
        P.append(C(f"DockBollard{i}", 0.55, 0.45, 1.0, (cx + x, cy + 4.0, deck_z + 1.0), STEEL, sides=10))
        P.append(C(f"DockBollardCap{i}", 0.75, 0.75, 0.3, (cx + x, cy + 4.0, deck_z + 2.0), STEEL, sides=10))
    P += [C("DockCraneBase", 1.6, 1.6, 1.2, (cx + 8, cy - 2, deck_z + 1.0), Y["dark"], sides=12),
          S("DockCraneColumn", (1.2, 1.2, 8.0), (cx + 8, cy - 2, deck_z + 2.2), Y["base"]),
          S("DockCraneArm", (10.0, 0.9, 0.9), (cx + 4, cy - 2, deck_z + 10.0), Y["base"], rot=(0, math.radians(-8), 0)),
          S("DockCraneCab", (2.2, 2.0, 1.8), (cx + 8.5, cy - 2, deck_z + 8.4), N["base"]),
          C("DockCraneCable", 0.08, 0.08, 4.5, (cx - 0.6, cy - 2, deck_z + 6.0), "#1A1A1A", sides=5),
          S("DockCraneHook", (0.8, 0.5, 0.9), (cx - 0.6, cy - 2, deck_z + 5.2), CORAL)]
    P.append(vb.block("DockCabWindow", (1.6, 0.1, 0.8), (cx + 8.5, cy - 0.95, deck_z + 9.2), "#5CF2FF", bevel=0.0, emission=2.5))
    for i, (x, y, z, col) in enumerate(((-9, -3, 0, CORAL), (-7.4, -3, 0, TEAL), (-8.2, -3, 1.6, YEL), (-4.5, -3.2, 0, "#B678EA"))):
        P.append(R(f"DockCrate{i}", (1.5, 1.5, 1.5), (cx + x, cy + y, deck_z + 1.0 + z), col, radius=0.12))
        P.append(S(f"DockCrateStrap{i}", (1.56, 0.25, 1.56), (cx + x, cy + y, deck_z + 1.0 + z - 0.03), N["dark"], bevel=0.02))
    # control hut where the tunnel arrives
    P += [S("DockHut", (7, 6, 6), (cx - 3, cy - 9, 0), Y["base"]),
          S("DockHutRoof", (8, 7, 0.8), (cx - 3, cy - 9, 6.0), N["base"]),
          vb.block("DockHutLight", (0.6, 0.6, 0.6), (cx - 3, cy - 9, 6.8), "#FF3B3B", bevel=0.1, emission=5)]
    P += kit.framed_window("DockHutWin", (cx - 3, cy - 6.0, 2.2), 4.0, 2.4, normal="+y", frame=T["base"], glass="#5CF2FF", sill=N["base"])
    for i in range(6):  # ladder down to the seabed
        P.append(S(f"DockLadderRung{i}", (1.4, 0.25, 0.2), (cx - 13.6, cy + 2, 0.5 + i * 0.7), STEEL))
    P += [S("DockLadderRailA", (0.25, 0.25, 4.6), (cx - 14.3, cy + 2, 0), STEEL),
          S("DockLadderRailB", (0.25, 0.25, 4.6), (cx - 12.9, cy + 2, 0), STEEL)]
    hose = [(cx + 1, cy + 3, deck_z + 1.2), (cx + 1.5, cy + 5.5, deck_z + 0.6), (cx + 1.8, cy + 7.6, deck_z + 1.6)]
    for i in range(len(hose) - 1):  # fuel hose to the sub
        (x0, y0, z0), (x1, y1, z1) = hose[i], hose[i + 1]
        L = math.dist(hose[i], hose[i + 1])
        P.append(C(f"DockHose{i}", 0.3, 0.3, L, (x0, y0, z0), "#1A1A1A", sides=8, rot=(-math.atan2(y1 - y0, z1 - z0), 0, 0)))
    for i, x in enumerate((-6, 6)):  # docking clamp arms
        P.append(S(f"DockClamp{i}", (1.2, 3.4, 1.0), (cx + x, cy + 6.6, deck_z + 0.3), STEEL))
        P.append(S(f"DockClampPad{i}", (1.6, 0.6, 1.6), (cx + x, cy + 8.4, deck_z - 0.1), CORAL))
    for i, x in enumerate((-12.5, 12.5)):
        P += uw_lamp(f"DockLamp{i}", (cx + x, cy + 4.6, deck_z + 1.0))
    P += submarine(cx, cy + 11.2, deck_z + 1.4)
    return P


def uw_lamp(prefix, base, glow="#7CF7FF"):
    x, y, z = base
    return [C(f"{prefix}Pole", 0.2, 0.16, 3.6, (x, y, z), N["base"], sides=8),
            R(f"{prefix}Head", (0.8, 0.8, 0.7), (x, y, z + 3.6), N["base"], radius=0.1),
            B(f"{prefix}Glow", (0.3, 0.3, 0.3), (x, y, z + 3.95), glow, segments=8, rings=5, emission=5)]


# ---- 6. Ruins / exploration dig site -----------------------------------------------------------
def ruins(cx=-55.0, cy=40.0, z=2.5):
    STONE = kit.shades("#9FB3B0")
    GLOW = "#5CF2FF"
    rnd = random.Random(44)
    P = []
    for i, (w, d, h) in enumerate(((26, 22, 1.2), (20, 16, 1.0), (13, 10, 1.0))):  # stepped platform with a missing corner
        P.append(S(f"RuinStep{i}", (w, d, h), (cx, cy, z + i * 1.1), STONE["base" if i % 2 == 0 else "dark"]))
    P.append(S("RuinStepChunk", (4, 3, 1.0), (cx + 11, cy + 9, z), STONE["dark"], rot=(0.08, 0.05, 0.3)))
    top = z + 3.2
    for i in range(6):  # ring of columns: intact, broken, fallen
        a = 2 * math.pi * i / 6
        x, y = cx + math.cos(a) * 8.5, cy + math.sin(a) * 6.8
        P.append(S(f"RuinColBase{i}", (2.2, 2.2, 0.6), (x, y, z + 2.2), STONE["dark"]))
        drums = (5, 2, 5, 3, 5, 1)[i]
        for d in range(drums):
            P.append(C(f"RuinDrum{i}_{d}", 0.85, 0.85, 1.25, (x, y, z + 2.8 + d * 1.27), STONE["base" if d % 2 else "light"], sides=8,
                       rot=(0, 0, rnd.uniform(0, 0.4))))
        if drums == 5:
            P.append(S(f"RuinCapital{i}", (2.4, 2.4, 0.7), (x, y, z + 2.8 + 5 * 1.27), STONE["light"]))
        else:
            for k in range(3):
                P.append(S(f"RuinJag{i}_{k}", (0.6, 0.6, 0.7), (x + rnd.uniform(-0.4, 0.4), y + rnd.uniform(-0.4, 0.4), z + 2.8 + drums * 1.27),
                           STONE["light"], rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0, 1))))
    for d in range(3):  # fallen drums
        P.append(C(f"RuinFallen{d}", 0.85, 0.85, 1.25, (cx + 12 + d * 1.35, cy - 9 + d * 0.3, z + 0.85), STONE["base"], sides=8,
                   rot=(0, math.pi / 2, 0.2)))
    # archway with glowing keystone rune
    P += [S("RuinArchL", (2.0, 2.0, 7.0), (cx - 3.2, cy - 6, top), STONE["base"]),
          S("RuinArchR", (2.0, 2.0, 7.0), (cx + 3.2, cy - 6, top), STONE["base"]),
          S("RuinLintel", (9.0, 2.4, 1.4), (cx, cy - 6, top + 7.0), STONE["light"]),
          S("RuinKeystone", (1.8, 2.6, 1.8), (cx, cy - 6, top + 7.8), STONE["dark"])]
    P.append(vb.block("RuinKeyRune", (1.0, 0.1, 1.0), (cx, cy - 4.68, top + 8.2), GLOW, bevel=0.0, emission=6))
    for i, (dx, dz) in enumerate(((-0.4, 0.0), (0.4, 0.0), (0.0, 0.5))):
        P.append(vb.block(f"RuinArchRune{i}", (0.35, 0.08, 0.35), (cx - 3.2 + dx, cy - 4.98, top + 3 + dz), GLOW, bevel=0.0, emission=5))
    # carved guardian totem (original): stacked stone heads with glowing eyes
    for i, (w, h) in enumerate(((4.0, 2.4), (3.4, 2.2), (2.8, 2.0))):
        zz = top + sum(hh for _, hh in ((4.0, 2.4), (3.4, 2.2), (2.8, 2.0))[:i])
        P.append(S(f"RuinTotem{i}", (w, w * 0.9, h), (cx, cy + 3, zz), STONE["base" if i != 1 else "dark"]))
        for sx in (-1, 1):
            P.append(vb.block(f"RuinTotemEye{i}{sx}", (0.5, 0.1, 0.35), (cx + sx * w * 0.22, cy + 3 + w * 0.45 + 0.02, zz + h * 0.55), GLOW,
                              bevel=0.0, emission=5))
        P.append(S(f"RuinTotemFin{i}", (w + 1.4, 0.5, 0.6), (cx, cy + 3, zz + h - 0.6), STONE["light"]))
    # glowing crystal clusters + rune tablets + floating orbs
    for i, (x, y) in enumerate(((-10, 3), (9, 4), (-6, -10))):
        for k in range(4):
            h = rnd.uniform(1.6, 3.6)
            col = ("#B678EA", GLOW)[k % 2]
            P.append(C(f"RuinCrystal{i}_{k}", 0.55, 0.05, h, (cx + x + rnd.uniform(-0.6, 0.6), cy + y + rnd.uniform(-0.6, 0.6), z + 1.2),
                       col, sides=5, studs="none", rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0), emission=3.5))
        P.append(R(f"RuinCrystalRock{i}", (2.0, 1.6, 0.8), (cx + x, cy + y, z + 1.0), STONE["dark"], radius=0.2))
    for i, (x, y, yaw) in enumerate(((-9.5, -8, 0.3), (9.5, -7, -0.4))):
        P.append(S(f"RuinTablet{i}", (2.6, 0.7, 3.4), (cx + x, cy + y, z + 1.2), STONE["base"], rot=(0.12, 0, yaw)))
        for k in range(3):
            P.append(vb.block(f"RuinTabletRune{i}_{k}", (1.4 - k * 0.3, 0.08, 0.25), (cx + x, cy + y + 0.38, z + 2.2 + k * 0.7), GLOW,
                              bevel=0.0, emission=4))
            P[-1].rotation_euler = (0.12, 0, yaw)
    for i in range(5):
        P.append(B(f"RuinOrb{i}", (0.45, 0.45, 0.45), (cx + rnd.uniform(-9, 9), cy + rnd.uniform(-7, 7), top + rnd.uniform(4, 9)), GLOW,
                   segments=10, rings=6, emission=5))
    # the research dig: survey stakes + tape, tool crate, work lamp, open treasure chest
    stakes = [(-12, -10), (-4, -12), (4, -12), (12, -10)]
    for i, (x, y) in enumerate(stakes):
        P.append(S(f"DigStake{i}", (0.3, 0.3, 1.8), (cx + x, cy + y, z + 1.2), "#FFFFFF"))
        P.append(S(f"DigStakeFlag{i}", (0.6, 0.06, 0.4), (cx + x + 0.35, cy + y, z + 2.6), CORAL, bevel=0.01))
        if i < len(stakes) - 1:
            (x1, y1) = stakes[i + 1]
            L = math.hypot(x1 - x, y1 - y)
            P.append(S(f"DigTape{i}", (L, 0.08, 0.12), ((cx + x + cx + x1) / 2, (cy + y + cy + y1) / 2, z + 2.4), YEL, bevel=0.0,
                       rot=(0, 0, math.atan2(y1 - y, x1 - x))))
    P += [R("DigToolCrate", (2.2, 1.4, 1.2), (cx + 14, cy - 4, z), "#C98A4B", radius=0.12),
          S("DigShovelHandle", (0.2, 0.2, 2.6), (cx + 14.6, cy - 3.6, z + 1.2), "#8A5530", rot=(0.3, 0, 0)),
          S("DigShovelBlade", (0.8, 0.12, 0.9), (cx + 14.6, cy - 3.0, z + 3.5), STEEL, rot=(0.3, 0, 0))]
    P += uw_lamp("DigLamp", (cx + 15, cy + 1, z), glow=LIGHT)
    P += [R("ChestBase", (2.4, 1.6, 1.2), (cx - 13, cy + 6, z + 1.2), "#8A5530", radius=0.15),
          S("ChestBand", (2.5, 1.7, 0.3), (cx - 13, cy + 6, z + 1.6), YEL),
          R("ChestLid", (2.4, 1.6, 0.7), (cx - 13, cy + 5.0, z + 2.6), "#8A5530", radius=0.2, rot=(math.radians(-60), 0, 0))]
    for i in range(6):
        P.append(C(f"ChestCoin{i}", 0.3, 0.3, 0.12, (cx - 13.6 + (i % 3) * 0.6, cy + 6.2 + (i // 3) * 0.4, z + 2.4 + (i % 2) * 0.12),
                   "#FFD93B", sides=10, studs="none", emission=1.5))
    return P


# ---- 7. Landscape, reefs, life & small details ---------------------------------------------------
def landscape():
    gx0, gx1, gy0, gy1 = GROUND
    P = terrain_blocks()
    rnd = random.Random(12)
    # dress terrace tops so no shelf is a blank plane (placed groups, varied per shelf)
    tr = random.Random(77)
    for i, (x0, x1, y0, y1, h) in enumerate(TERRACES):
        n = max(2, int((x1 - x0) * (y1 - y0) / 260))
        for j in range(n):
            x, y = tr.uniform(x0 + 3, x1 - 3), tr.uniform(y0 + 3, y1 - 3)
            z = theight(x, y)
            if z < 3:
                continue
            kind = (i + j) % 5
            tag = f"Shelf{i}_{j}"
            if kind == 0:
                P += uw.brain_coral(tag, (x, y, z), ("#FF6FAE", "#B678EA", "#FF9F1C")[j % 3], r=tr.uniform(1.2, 1.9))
            elif kind == 1:
                P += uw.seagrass(tag, (x, y, z), tr, radius=2.4, n=12)
            elif kind == 2:
                P += uw.tube_sponge(tag, (x, y, z), ("#22C3A6", "#FFD93B", "#FF6B57")[j % 3], tr, n=3)
            elif kind == 3:
                P.append(R(f"{tag}Boulder", (tr.uniform(2, 3.5), tr.uniform(1.6, 3), tr.uniform(1, 2)), (x, y, z), kit.shades(ROCK)["light"],
                           radius=0.3, rot=(0, 0, tr.uniform(0, 1))))
                P += uw.starfish(f"{tag}Star", (x + 1.6, y + 0.4, z), "#FF9F1C", yaw=tr.uniform(0, 1))
            else:
                P += uw.glow_plant(tag, (x, y, z), tr, color=("#7CF7FF", "#FF8FE0")[j % 2])
    # research trail from the hub to the dig site
    P += kit.path_network([[(0, 2.5), (-14, 8), (-28, 14), (-40, 22)]], colors=("#B8C4CF", "#A3B1BE"), edge="#7F8EA0",
                          rnd=random.Random(13))
    for i, (x, y) in enumerate(((-10, 6.5), (-24, 12.5), (-36, 20.5))):
        P += uw_lamp(f"TrailLamp{i}", (x, y + 3.5, 0))
    # coral reef vignettes
    reefs = [("ReefA", (26, 54), ("#FF6B57", "#B678EA", "#FFD93B")), ("ReefB", (-24, 58), ("#22C3A6", "#FF6FAE", "#FF9F1C")),
             ("ReefC", (68, -18), ("#FF6FAE", "#FFC83D", "#7CF7FF")), ("ReefD", (16, 40), ("#B678EA", "#FF6B57", "#22C3A6")),
             ("ReefE", (-56, -18), ("#FF9F1C", "#22C3A6", "#FF6FAE")), ("ReefF", (-18, -30), ("#FF6FAE", "#7CF7FF", "#FFD93B")),
             ("ReefG", (46, 60), ("#22C3A6", "#FFD93B", "#B678EA")), ("ReefH", (84, 52), ("#FF6B57", "#FF6FAE", "#22C3A6"))]
    for name, (x, y), cols in reefs:
        def z(dx, dy):
            return theight(x + dx, y + dy)
        P += uw.branch_coral(f"{name}Branch", (x, y, z(0, 0)), cols[0], rnd, height=6)
        P += uw.branch_coral(f"{name}Branch2", (x + 3.5, y - 1.5, z(3.5, -1.5)), cols[1], rnd, height=4.5)
        P += uw.brain_coral(f"{name}Brain", (x - 3.5, y + 1.0, z(-3.5, 1)), cols[2], r=1.8)
        P += uw.table_coral(f"{name}Table", (x + 1.0, y + 4.0, z(1, 4)), cols[1], r=2.2)
        P += uw.sea_fan(f"{name}Fan", (x - 5.5, y - 2.5, z(-5.5, -2.5)), cols[0], rnd, yaw=rnd.uniform(0, 1))
        P += uw.tube_sponge(f"{name}Sponge", (x + 6.0, y + 2.5, z(6, 2.5)), cols[2], rnd)
        P += uw.anemone(f"{name}Anem", (x - 1.5, y - 4.0, z(-1.5, -4)), cols[1], "#FFFFFF", rnd)
        P += uw.starfish(f"{name}Star", (x + 4.5, y - 4.5, z(4.5, -4.5)), "#FF9F1C", yaw=rnd.uniform(0, 1))
        P += uw.urchin(f"{name}Urchin", (x - 6.5, y + 3.5, z(-6.5, 3.5)))
        P.append(R(f"{name}Rock", (3.0, 2.4, 1.4), (x + 0.5, y - 0.5, z(0.5, -0.5)), ROCK, radius=0.3))
    # kelp forests at the edges + glow plants near the ruins + rock arch + pillar stacks
    for i, (x, y) in enumerate(((-66, -30), (-62, -33), (-69, -2), (-67, 6), (80, 32), (82, 40), (76, -24), (28, -36), (34, -37),
                                (-72, 52), (-76, 58), (60, -34), (88, 60))):
        P += uw.kelp(f"Kelp{i}", (x, y, theight(x, y)), rnd, height=rnd.uniform(12, 22))
    for i, (x, y) in enumerate(((-38, 52), (-34, 47), (-70, 24), (-62, 10), (-40, 30))):
        P += uw.glow_plant(f"GlowPlant{i}", (x, y, theight(x, y)), rnd, color=("#7CF7FF", "#FF8FE0")[i % 2])
    arch = [(0, 0, 0, 3.2, 3.0, 2.4), (0.3, 0, 2.4, 2.8, 2.6, 2.2), (0.8, 0, 4.6, 2.4, 2.4, 2.0), (2.6, 0, 6.2, 3.0, 2.4, 1.8),
            (5.0, 0, 6.3, 3.0, 2.6, 1.8), (7.0, 0, 4.6, 2.4, 2.4, 2.0), (7.4, 0, 2.4, 2.8, 2.6, 2.2), (7.6, 0, 0, 3.2, 3.0, 2.4)]
    for i, (dx, dy, z, w, d, h) in enumerate(arch):  # rock arch (environmental landmark)
        P.append(R(f"RockArch{i}", (w, d, h), (4 + dx, 58 + dy, z + theight(4, 58)), (ROCK, kit.shades(ROCK)["light"])[i % 2], radius=0.35,
                   rot=(0, 0, rnd.uniform(-0.15, 0.15))))
    for j, (x, y, n) in enumerate(((82, 8, 5), (-40, -46, 4), (36, 66, 3))):
        for i in range(n):  # balancing rock pillars
            s = 3.2 - i * 0.45
            P.append(R(f"RockPillar{j}_{i}", (s, s * 0.9, 1.8), (x + rnd.uniform(-0.3, 0.3), y, theight(x, y) + i * 1.75),
                       (ROCK, kit.shades(ROCK)["dark"])[i % 2], radius=0.3, rot=(0, 0, rnd.uniform(-0.4, 0.4))))
    # sunken boat bow near the ruins (storytelling)
    for i in range(5):
        P.append(S(f"WreckRib{i}", (0.5, 6.0 - i * 0.6, 0.5), (-58 + i * 1.6, 60, 2.5 + 2.2), "#7A4E2E", rot=(math.radians(70), 0, 0)))
        P.append(S(f"WreckPlank{i}", (7.0, 0.4, 0.8), (-55, 58.6 + i * 0.3, 2.5 + i * 0.9), ("#8A5530", "#6B3F22")[i % 2],
                   rot=(0, 0, 0.1)))
    P += [S("WreckMast", (0.5, 0.5, 8.0), (-52, 61, 2.5), "#6B3F22", rot=(0.5, 0.3, 0)),
          S("AnchorShank", (0.5, 0.5, 3.4), (-46, 54, 2.5), "#5B6B82", rot=(0.4, 0, 0.6)),
          S("AnchorArm", (2.6, 0.5, 0.5), (-46, 54, 2.5), "#5B6B82", rot=(0, 0, 0.6))]
    for i in range(3):  # barrels
        P.append(C(f"Barrel{i}", 0.8, 0.8, 1.6, (-62 + i * 1.9, 52, 2.5), "#8A5530", sides=12))
        P.append(uw.ring(f"BarrelHoop{i}", 0.86, 0.78, 0.2, (-62 + i * 1.9, 52, 3.2), "#5B6B82", sides=12))
    # seabed cables between modules
    for name, pts in (("CableLab", [(14, -10), (20, -9.2), (26, -9.6)]), ("CableDome", [(-5, -2), (-6, 6), (-7, 13)])):
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            L = math.hypot(x1 - x0, y1 - y0)
            P.append(C(f"{name}{i}", 0.28, 0.28, L, (x0, y0, 0.28), "#1A1A1A", sides=8, rot=(0, math.pi / 2, math.atan2(y1 - y0, x1 - x0))))
    # marine life: fish schools, jellyfish, bubble vents, divers
    for g, (x, y, z, col, yaw) in enumerate(((20, 18, 18, "#FFC83D", 0.4), (-50, 6, 22, "#7CF7FF", -0.6), (72, -32, 20, "#FF6FAE", 2.2))):
        for i in range(7):
            P += uw.tiny_fish(f"School{g}_{i}_", (x + (i % 3) * 2.2 + rnd.uniform(-0.4, 0.4), y + (i // 3) * 1.8, z + rnd.uniform(-1, 1)), col,
                              yaw=yaw, s=rnd.uniform(0.8, 1.2))
    for i, (x, y, z) in enumerate(((-60, 40, 16), (-84, 26, 18), (-30, 44, 20), (30, 10, 24))):
        P += uw.jellyfish(f"Jelly{i}", (x, y, z), ("#FF8FE0", "#B678EA", "#7CF7FF", "#FF8FE0")[i], rnd)
    for i, (x, y) in enumerate(((50, 46), (-14, 50), (70, 2))):
        P.append(R(f"VentRock{i}", (1.8, 1.8, 0.8), (x, y, theight(x, y)), kit.shades(ROCK)["dark"], radius=0.25))
        P += uw.bubbles(f"Vent{i}", (x, y, theight(x, y) + 1.0), height=16, count=10, rnd=rnd)
    P += uw.diver("DiverA", (-44, 24, 2.5), suit="#FF8A1F")
    P += uw.diver("DiverB", (52, 30, 0), suit="#22C3A6")
    P += uw.diver("DiverC", (-6, 44, 0), suit="#B678EA")
    return P


def build_all():
    vb.reset_scene()
    uw.install()
    groups = {
        "Hub": hub(),
        "Lab": lab(),
        "Habitat": habitat(),
        "Dome": dome(),
        "Dock": dock(),
        "Ruins": ruins(),
        "Tunnels": (uw.tunnel("TunLab", (12.9, -15), (26.5, -15), 6.5) + uw.tunnel("TunPod", (-12.9, -15), (-29.3, -15), 5.5)
                    + uw.tunnel("TunDome", (-9.15, -5.85), (-8.3, 12.6), 5.5) + uw.tunnel("TunDock", (54.2, -8.5), (58.0, 15.0), 4.2)),
        "Landscape": landscape(),
        "HubDetail": hub_detail(), "LabDetail": lab_detail(), "PodDetail": pod_detail(),
        "DockDetail": dock_detail() + sub_detail(),
        "Environment": environment_v2(),
    }
    return groups


def main(save=True):
    groups = build_all()
    if save:
        path = os.path.join(HERE, "..", "underwater_facility.blend")
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path))
    return {k: vb.poly_report(v) for k, v in groups.items()}




# ================================================================================================
# DETAIL PASS v2 (owner: more layered components, panels, trims, supports, bolts, silhouettes)
# ================================================================================================
def bolt_grid(prefix, pts, color="#D9DEE6", r=0.12):
    return [B(f"{prefix}{i}", (r, r, r), p, color, segments=6, rings=4, studs="none") for i, p in enumerate(pts)]


def hub_detail(cx=0.0, cy=-15.0):
    P = []
    face_d = 14.0 * math.cos(math.radians(22.5))
    for k in range(8):
        th = math.radians(45 * k)
        nx, ny = math.cos(th), math.sin(th)
        tx, ty = -ny, nx
        fx, fy = cx + nx * face_d, cy + ny * face_d
        if k not in (0, 2, 3, 4):  # vertical panel strip between portholes + bolts
            P.append(S(f"HubStrip{k}", (1.6, 0.35, 4.4), (fx + nx * 0.15, fy + ny * 0.15, 3.4), T["dark"], rot=(0, 0, th + math.pi / 2)))
            P += bolt_grid(f"HubStripBolt{k}_", [(fx + nx * 0.4 + tx * o, fy + ny * 0.4 + ty * o, z) for o in (-0.5, 0.5) for z in (3.7, 7.5)])
        P += bolt_grid(f"HubBandBolt{k}_", [(fx + nx * 0.62 + tx * o, fy + ny * 0.62 + ty * o, 2.95) for o in (-4, -2.4, -0.8, 0.8, 2.4, 4)])
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        x, y = cx + math.cos(a) * 15.0, cy + math.sin(a) * 15.0
        P.append(S(f"HubButtress{k}", (2.4, 1.2, 3.4), (x, y, 2.6), N["base"], rot=(0, -0.35, a)))
        P.append(S(f"HubButtressCap{k}", (1.4, 1.4, 0.5), (cx + math.cos(a) * 14.3, cy + math.sin(a) * 14.3, 5.6), Y["dark"], rot=(0, 0, a)))
        P.append(S(f"HubBracket{k}", (2.6, 0.8, 1.6), (cx + math.cos(a) * 14.6, cy + math.sin(a) * 14.6, 10.1), N["dark"], rot=(0, 0.55, a)))
        P.append(S(f"HubRoofFin{k}", (2.4, 0.6, 1.5), (cx + math.cos(a) * 12.0, cy + math.sin(a) * 12.0, 17.6), CORAL, rot=(0, 0, a)))
    for k in range(16):  # deck edge marker lights
        a = 2 * math.pi * (k + 0.5) / 16
        P.append(vb.block(f"HubDeckLight{k}", (0.5, 0.3, 0.3), (cx + math.cos(a) * 16.25, cy + math.sin(a) * 16.25, 12.0),
                          ("#7CFF9C", "#FFD93B")[k % 2], bevel=0.0, emission=4))
        P[-1].rotation_euler = (0, 0, a + math.pi / 2)
    for k in range(12):  # railed roof cap deck with equipment
        a = 2 * math.pi * k / 12
        P.append(S(f"HubCapPost{k}", (0.25, 0.25, 1.2), (cx + math.cos(a) * 6.2, cy + math.sin(a) * 6.2, 21.4), Y["base"]))
    P.append(uw.ring("HubCapRail", 6.35, 6.05, 0.2, (cx, cy, 22.5), Y["light"], sides=12))
    P += [R("HubCapGen", (2.6, 1.8, 1.3), (cx - 3.2, cy + 1.6, 21.4), STEEL, radius=0.15),
          uw.ring("HubCapGenFan", 0.7, 0.45, 0.15, (cx - 3.2, cy + 1.6, 22.7), N["dark"], sides=12),
          R("HubCapBox", (1.6, 1.6, 1.0), (cx - 2.6, cy - 2.8, 21.4), CORAL, radius=0.12)]
    for i in range(14):  # tethered sensor buoy above the hub (silhouette)
        P.append(uw.ring(f"HubTether{i}", 0.25, 0.12, 0.35, (cx + 3.2, cy - 2.4, 21.6 + i * 0.7), "#5B6B82", sides=8,
                         rot=(0, (i % 2) * math.pi / 2, 0)))
    P += [B("HubBuoy", (1.5, 1.5, 1.3), (cx + 3.2, cy - 2.4, 32.4), Y["base"], segments=16, rings=8),
          uw.ring("HubBuoyBand", 1.55, 1.3, 0.4, (cx + 3.2, cy - 2.4, 32.2), CORAL, sides=16),
          vb.block("HubBuoyLight", (0.5, 0.5, 0.5), (cx + 3.2, cy - 2.4, 33.6), "#7CF7FF", bevel=0.1, emission=6)]
    return P


def lab_detail(cx=40.0, cy=-14.0, W=28, D=17, H=9.0):
    P = []
    fy = cy + D / 2
    for i, (x, y) in enumerate(((cx - W / 2 - 1, fy + 1), (cx + W / 2 + 1, fy + 1), (cx - W / 2 - 1, cy - D / 2 - 1),
                                (cx + W / 2 + 1, cy - D / 2 - 1))):  # corner frame pillars
        P += [S(f"LabPillar{i}", (2.2, 2.2, H + 3.0), (x, y, 0), T["base"]),
              S(f"LabPillarCap{i}", (2.8, 2.8, 0.6), (x, y, H + 3.0), N["base"]),
              S(f"LabPillarPlate{i}", (2.6, 2.6, 0.5), (x, y, 2.0), Y["dark"])]
    for side, x in (("W", cx - W / 2 - 0.15), ("E", cx + W / 2 + 0.15)):  # bolted side panels
        for j, y in enumerate((cy - 5, cy, cy + 5)):
            P.append(S(f"LabPanel{side}{j}", (0.35, 3.8, 5.2), (x, y, 3.0), Y["dark"] if j != 1 else T["dark"]))
            dx = -0.25 if side == "W" else 0.25
            P += bolt_grid(f"LabPanelBolt{side}{j}_", [(x + dx, y + o, z) for o in (-1.6, 1.6) for z in (3.3, 7.9)])
    by = cy - D / 2 - 0.4
    for i, z in enumerate((3.0, 4.3, 5.6)):  # pipe runs along the back wall
        P.append(C(f"LabBackPipe{i}", 0.35, 0.35, W - 2, (cx - W / 2 + 1, by - 0.4 - i * 0.05, z), (T["base"], CORAL, Y["base"])[i], sides=10,
                   rot=(0, math.pi / 2, 0)))
    for j in range(5):
        P.append(S(f"LabPipeClamp{j}", (0.5, 1.1, 3.3), (cx - 11 + j * 5.5, by - 0.45, 2.6), N["dark"]))
    P += [S("LabHood", (W - 1, 1.8, 0.45), (cx, fy + 0.4, 1.5 + H - 0.3), N["base"]),
          vb.block("LabLightBar", (W - 3, 0.25, 0.25), (cx, fy + 1.2, 1.5 + H - 0.55), "#BFF6FF", bevel=0.0, emission=4)]
    for i, x in enumerate((-10, -4)):  # roof fans
        P += [S(f"LabFanBox{i}", (3.4, 3.4, 1.0), (cx + x, cy + 3.5, 12.3), STEEL),
              uw.ring(f"LabFanRing{i}", 1.5, 1.2, 0.3, (cx + x, cy + 3.5, 13.3), N["base"], sides=16)]
        for b in range(4):
            P.append(S(f"LabFanBlade{i}_{b}", (2.2, 0.35, 0.12), (cx + x, cy + 3.5, 13.2), N["dark"], bevel=0.02,
                       rot=(0.2, 0, math.radians(45 * b + 10))))
    for i in range(14):  # roof parapet crenels
        P.append(S(f"LabCrenel{i}", (1.0, 0.8, 0.8), (cx - W / 2 + 1 + i * 2.0, fy + 1.0, 1.5 + H + 1.0), CORAL if i % 2 else Y["base"]))
    for i in range(9):  # east ladder to the roof
        P.append(S(f"LabLadderRung{i}", (0.25, 1.4, 0.2), (cx + W / 2 + 0.6, cy - 3, 1.0 + i * 1.1), STEEL))
    for s_ in (-1, 1):
        P.append(S(f"LabLadderRail{s_}", (0.25, 0.25, 10.5), (cx + W / 2 + 0.6, cy - 3 + s_ * 0.7, 0.8), STEEL))
    return P


def pod_detail(cx=-38.0, cy=-15.0):
    P = []
    for k in range(4):  # angled landing legs + feet
        a = math.radians(45 + 90 * k)
        x, y = cx + math.cos(a) * 10.8, cy + math.sin(a) * 10.8
        P += [S(f"PodLeg{k}", (1.0, 1.0, 5.4), (x, y, 0.3), N["dark"], rot=(0, 0.45, a + math.pi)),
              S(f"PodFoot{k}", (2.4, 2.4, 0.5), (x, y, 0), Y["dark"], rot=(0, 0, a))]
    for k in range(24):
        a = 2 * math.pi * k / 24
        P.append(B(f"PodBandBolt{k}", (0.12, 0.12, 0.12), (cx + math.cos(a) * 9.45, cy + math.sin(a) * 9.45, 5.3), "#D9DEE6",
                   segments=6, rings=4, studs="none"))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        P.append(S(f"PodAccent{k}", (2.0, 0.3, 0.8), (cx + math.cos(a) * 9.1, cy + math.sin(a) * 9.1, 7.2), CORAL, rot=(0, 0, a + math.pi / 2)))
    return P


def dock_detail(cx=62.0, cy=24.0, deck_z=4.5):
    P = []
    for i in range(12):
        P.append(S(f"DockPlankLine{i}", (0.12, 10.6, 0.05), (cx - 11.6 + i * 2.1, cy, deck_z + 1.0), N["dark"], bevel=0.0))
    for i, x in enumerate((-11, -5.5, 0, 5.5)):  # cross bracing between pilings
        for y in (-4.2, 4.2):
            P.append(S(f"DockBrace{i}_{y}", (6.0, 0.4, 0.4), (cx + x + 0.2, cy + y, 1.0), STEEL, rot=(0, -0.62, 0)))
    for i in range(14):  # back railing
        P.append(S(f"DockRailPost{i}", (0.25, 0.25, 1.4), (cx - 12.6 + i * 1.95, cy - 5.2, deck_z + 1.0), Y["base"]))
    P.append(S("DockRail", (26, 0.25, 0.25), (cx, cy - 5.2, deck_z + 2.3), Y["light"]))
    for i, x in enumerate((-12.5, -9.5)):  # fuel tanks with bands
        P.append(C(f"DockFuel{i}", 1.1, 1.1, 4.0, (cx + x, cy - 2.0, deck_z + 2.1), "#E84A4A", sides=14, rot=(math.pi / 2, 0, 0)))
        for j in range(2):
            P.append(uw.ring(f"DockFuelBand{i}_{j}", 1.18, 1.0, 0.3, (cx + x, cy - 2.6 - j * 1.6, deck_z + 2.1), N["dark"], sides=14,
                             rot=(math.pi / 2, 0, 0)))
    P += [S("DockCounterweight", (2.0, 1.6, 1.6), (cx + 13.2, cy - 2, deck_z + 9.4), N["dark"]),
          S("DockCraneBrace", (0.5, 0.5, 6.0), (cx + 9.5, cy - 2, deck_z + 3.4), Y["dark"], rot=(0, -0.45, 0))]
    return P


def sub_detail(cx=62.0, cy=35.2, cz=5.9):
    P = []
    for side in (-1, 1):
        y = cy + side * 2.68
        for i, x in enumerate((-5.6, -2.8, 0.0, 2.8, 5.4)):  # bolted armor plates under the portholes
            P.append(S(f"SubPlate{side}_{i}", (2.5, 0.3, 1.3), (cx + x, y, cz - 2.4), kit.shades("#FF8A1F")["dark"]))
            P += bolt_grid(f"SubPlateBolt{side}_{i}_", [(cx + x + o, y + side * 0.18, cz - 2.4 + z) for o in (-1.0, 1.0) for z in (0.2, 1.1)])
        P += [S(f"SubStripe{side}", (13.0, 0.25, 0.4), (cx - 0.5, y, cz - 0.95), CORAL),
              C(f"SubThruster{side}", 0.8, 0.8, 2.6, (cx - 5.2, cy + side * 3.5, cz + 0.6), N["base"], sides=14, rot=(0, math.pi / 2, 0)),
              uw.ring(f"SubThrusterGrille{side}", 0.85, 0.5, 0.3, (cx - 5.3, cy + side * 3.5, cz + 0.6), STEEL, sides=14,
                      rot=(0, -math.pi / 2, 0)),
              C(f"SubThrusterGlow{side}", 0.5, 0.5, 0.1, (cx - 5.35, cy + side * 3.5, cz + 0.6), "#5CF2FF", sides=12, studs="none",
                rot=(0, -math.pi / 2, 0), emission=5),
              B(f"SubNavLight{side}", (0.22, 0.22, 0.22), (cx - 6.6, cy + side * 4.9, cz - 0.2), "#FF3B3B" if side < 0 else "#3BFF7A",
                segments=8, rings=5, emission=6),
              S(f"SubKeelFin{side}", (2.0, 0.3, 1.0), (cx - 3, cy + side * 1.2, cz - 4.0), Y["dark"], rot=(side * 0.3, 0, 0))]
        for g in range(4):  # intake grille bars on the nose
            P.append(S(f"SubGrille{side}_{g}", (0.15, 0.2, 1.4), (cx + 6.4 + g * 0.35, cy + side * 2.25, cz - 3.0), N["dark"], bevel=0.02))
    P += [uw.ring("SubBubbleFrame", 2.35, 1.9, 0.45, (cx + 8.2, cy, cz - 0.1), N["base"], sides=20, rot=(0, math.pi / 2, 0)),
          S("SubSearchArm", (1.6, 0.4, 0.4), (cx + 2.0, cy, cz + 4.4), STEEL),
          C("SubSearchLamp", 0.45, 0.6, 0.8, (cx + 2.8, cy, cz + 4.6), N["base"], sides=12, rot=(0, math.pi / 2, 0)),
          C("SubSearchGlow", 0.5, 0.5, 0.05, (cx + 3.62, cy, cz + 4.6), "#FFF6C8", sides=12, studs="none", rot=(0, math.pi / 2, 0), emission=6),
          uw.ring("SubTowRing", 0.7, 0.45, 0.3, (cx - 9.8, cy, cz - 3.6), STEEL, sides=12, rot=(math.pi / 2, 0, 0)),
          S("SubRudder2", (1.6, 0.45, 2.0), (cx - 8.0, cy, cz + 0.6), CORAL)]
    for i in range(7):  # dorsal handrail
        P.append(S(f"SubRailPost{i}", (0.18, 0.18, 0.8), (cx - 6.5 + i * 1.1 + (2.2 if i > 3 else 0), cy + 1.6, cz + 2.55), STEEL))
    P.append(S("SubRail", (10.0, 0.18, 0.18), (cx - 2.0, cy + 1.6, cz + 3.35), STEEL))
    return P


def cable(prefix, pts, z=0.25, color="#1A1A1A"):
    P = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        P.append(C(f"{prefix}{i}", 0.26, 0.26, L, (x0, y0, z + theight(x0, y0)), color, sides=8, rot=(0, math.pi / 2, math.atan2(y1 - y0, x1 - x0))))
    for i, (x, y) in enumerate(pts[1:-1]):  # junction boxes at the bends
        P += [R(f"{prefix}Junction{i}", (1.4, 1.1, 0.9), (x, y, theight(x, y)), Y["dark"], radius=0.12),
              vb.block(f"{prefix}JunctionLED{i}", (0.25, 0.08, 0.25), (x, y + 0.58, theight(x, y) + 0.55), "#7CFF9C", bevel=0.0, emission=4)]
    return P


def environment_v2():
    """Intentional density: machinery, cables, paths, bridge, buoys, planted clusters, props."""
    P = []
    rnd = random.Random(55)
    # pump station behind the lab
    px, py = 31, -32
    P += [S("PumpPad", (18, 9, 0.5), (px, py, 0), N["base"]),
          S("PumpHouse", (5, 4, 4), (px - 4, py, 0.5), Y["base"]),
          S("PumpHouseRoof", (5.8, 4.8, 0.5), (px - 4, py, 4.5), N["dark"]),
          uw.ring("PumpFan", 1.2, 0.9, 0.3, (px - 4, py, 5.0), T["dark"], sides=14)]
    for i, x in enumerate((2, 6)):
        P += [C(f"PumpTank{i}", 2.0, 2.0, 5.5, (px + x, py, 0.5), (TEAL, CORAL)[i], sides=16),
              B(f"PumpTankDome{i}", (2.0, 2.0, 1.0), (px + x, py, 6.0), kit.shades((TEAL, CORAL)[i])["light"], segments=16, rings=8)]
        for j, z in enumerate((1.6, 4.0)):
            P.append(uw.ring(f"PumpTankBand{i}_{j}", 2.1, 1.95, 0.4, (px + x, py, z), N["dark"], sides=16))
        P += [uw.ring(f"PumpValve{i}", 0.6, 0.4, 0.15, (px + x, py + 2.05, 3.2), "#E84A4A", sides=12, rot=uw.face_rot(math.pi / 2)),
              vb.block(f"PumpGauge{i}", (0.6, 0.1, 0.6), (px + x + 1.0, py + 1.95, 4.6), "#7CFF9C", bevel=0.0, emission=3)]
    for i, (x0, z0) in enumerate(((px + 2, 5.0), (px + 6, 5.0))):  # pipes up into the lab's back wall
        P += [C(f"PumpRiser{i}", 0.4, 0.4, 2.0, (x0, py + 2.0, z0 - 1.5), T["base"], sides=10),
              C(f"PumpRun{i}", 0.4, 0.4, 9.0, (x0, py + 2.0, z0 + 0.5), T["base"], sides=10, rot=(-math.pi / 2, 0, 0)),
              B(f"PumpElbow{i}", (0.5, 0.5, 0.5), (x0, py + 2.0, z0 + 0.5), T["light"], segments=8, rings=5)]
    # generator in the front plaza, cabled to hub / lab / dock / dome
    gx, gy = 30, 4
    P += [R("Generator", (6, 3.6, 3.4), (gx, gy, 0), Y["base"], radius=0.35),
          S("GeneratorBase", (7, 4.4, 0.5), (gx, gy, 0), N["dark"]),
          C("GeneratorStack", 0.5, 0.45, 3.4, (gx + 2.2, gy - 0.8, 3.4), N["base"], sides=10)]
    for i, x in enumerate((-1.6, 0.4)):
        P += [uw.ring(f"GenFan{i}", 0.85, 0.6, 0.2, (gx + x, gy, 3.4), N["dark"], sides=14),
              S(f"GenFanBlade{i}", (1.4, 0.3, 0.1), (gx + x, gy, 3.45), STEEL, bevel=0.02, rot=(0, 0, 0.6 * i))]
    for i in range(6):
        P.append(S(f"GenHazard{i}", (0.8, 0.15, 0.5), (gx - 2.5 + i * 1.0, gy + 1.85, 0.6), YEL if i % 2 else "#1A1A1A", bevel=0.01,
                   rot=(0, 0.5, 0)))
    P += cable("CableHubG", [(gx - 3, gy), (14, 2), (6, -2)])
    P += cable("CableDockG", [(gx + 3, gy), (46, 6), (56, 14)])
    P += cable("CableDomeG", [(gx - 2, gy + 2), (18, 20), (11, 28)])
    P += cable("CablePumpLab", [(px - 4, py + 2), (px - 6, -24)])
    # path network on the pads
    paths = [[(0, 0.5), (0, 7.5), (22, 7.5), (44, 8.5)], [(44, 8.5), (50, 20)], [(0, 7.5), (8, 22), (10, 40)], [(22, 7.5), (30, 46)]]
    P += kit.path_network(paths, colors=("#B8C4CF", "#A3B1BE"), edge="#7F8EA0", rnd=random.Random(14))
    for i, (x, y) in enumerate(((3.5, 11), (25, 11), (40, 12), (12, 28), (27, 30), (52, 16))):
        P += uw_lamp(f"PathLamp{i}", (x, y, 0))
    P += kit.signpost("SignHubJct", (-3.5, 9.5), arrows=((CORAL, 0), (TEAL, 70), (YEL, 160)))
    P += kit.signpost("SignDockJct", (25.5, 4.0), arrows=((CORAL, 20), (TEAL, 90), (YEL, -150)))
    # bridge over the trench (viewpoint over the deep reef)
    bx = 30
    P += [S("BridgeDeck", (4.0, 16, 0.5), (bx, 57, 0.1), "#8A5530"), S("BridgeEdgeL", (0.4, 16, 0.4), (bx - 1.9, 57, 0.6), "#6B3F22"),
          S("BridgeEdgeR", (0.4, 16, 0.4), (bx + 1.9, 57, 0.6), "#6B3F22")]
    for i in range(5):
        y = 50 + i * 3.5
        for sx in (-1, 1):
            P.append(S(f"BridgePost{i}{sx}", (0.5, 0.5, 2.0 + (6.0 if 52 < y < 62 else 0)), (bx + sx * 1.9, y, -6.0 if 52 < y < 62 else 0.1),
                       "#6B3F22"))
        P.append(S(f"BridgePlankGap{i}", (4.1, 0.15, 0.06), (bx, y + 1.7, 0.6), "#5A3A22", bevel=0.0))
    for sx in (-1, 1):
        P.append(C(f"BridgeRope{sx}", 0.1, 0.1, 16, (bx + sx * 1.9, 49, 1.9), "#E8D7B0", sides=6, rot=(-math.pi / 2, 0, 0)))
    for i, (x, y) in enumerate(((50, 49), (70, 49), (86, 65))):  # tethered sensor buoys on the trench rim
        z0 = theight(x, y)
        for j in range(8):
            P.append(uw.ring(f"Buoy{i}Chain{j}", 0.22, 0.1, 0.32, (x, y, z0 + j * 0.62), "#5B6B82", sides=8, rot=(0, (j % 2) * math.pi / 2, 0)))
        P += [B(f"Buoy{i}", (1.0, 1.0, 0.9), (x, y, z0 + 5.8), (CORAL, YEL, TEAL)[i], segments=14, rings=8),
              vb.block(f"Buoy{i}Light", (0.4, 0.4, 0.4), (x, y, z0 + 6.7), "#FFFFFF", bevel=0.1, emission=6)]
    # planted clusters at building bases + meadows
    for i, (x, y) in enumerate(((-18, 6), (19, -2), (-26, -4), (14, 12), (-28, 46), (46, 44), (58, -4), (-50, -30))):
        z = theight(x, y)
        P += uw.brain_coral(f"BaseCoral{i}", (x, y, z), ("#FF6FAE", "#B678EA", "#FF9F1C")[i % 3], r=1.3)
        P += uw.seagrass(f"BaseGrass{i}", (x + 2.2, y + 0.6, z), random.Random(200 + i), radius=1.8, n=12)
        P += uw.glow_plant(f"BaseGlow{i}", (x - 2.0, y + 1.0, z), random.Random(300 + i), color=("#7CF7FF", "#FF8FE0")[i % 2])
    for i, (x, y) in enumerate(((-6, 52), (36, 30), (-44, 4), (8, -36), (54, -6), (-22, 34), (70, 30), (-66, 30), (60, 66), (-10, 64))):
        P += uw.seagrass(f"Meadow{i}", (x, y, theight(x, y)), random.Random(90 + i), radius=3.4, n=26)
    # small themed props along the paths
    for i, (x, y) in enumerate(((36, 12), (48, 4), (-6, 20))):
        for j in range(3):
            P.append(R(f"PropCrate{i}_{j}", (1.4, 1.4, 1.4), (x + (j % 2) * 1.5, y, (j // 2) * 1.45), (CORAL, TEAL, YEL)[j], radius=0.12))
        P.append(S(f"PropCrateStrap{i}", (1.46, 0.3, 1.46), (x, y, 0), N["dark"], bevel=0.02))
    P += [S("FishTrapBase", (2.4, 2.4, 0.3), (16, 34, 0), STEEL), S("FishTrapTop", (2.4, 2.4, 0.3), (16, 34, 2.0), STEEL)]
    for i in range(4):
        P.append(S(f"FishTrapBar{i}", (0.2, 0.2, 2.0), (16 + (i % 2 - 0.5) * 2.2, 34 + (i // 2 - 0.5) * 2.2, 0.3), STEEL))
    P += uw.tiny_fish("FishTrapFish", (16, 34, 1.2), "#FFD93B", yaw=0.6, s=0.8)
    return P


if __name__ == "__main__":
    for k, v in main(save="--no-save" not in sys.argv).items():
        print(k, v)
