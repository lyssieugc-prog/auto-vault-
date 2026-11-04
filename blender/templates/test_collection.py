"""
Style test collection v4 (style-guides/3D_STYLE_BIBLE.md — DRAFT until the owner approves).

Owner feedback applied:
- L-04: studs are TEXTURE, never geometry.            - L-05: studs on ALL sides of every block.
- L-06: studs at true Roblox size (1 stud) — models are built at real Roblox scale (player = 5
  studs, buildings/trees dwarf the player like the references) so studs read small; shapes are
  not limited to cubes (cylinders, cones, balls, rounded boxes, wedges); EVERYTHING is studded,
  pets/brainrots included; "too bricky" = stair-step block SHAPES -> collectibles use smooth
  round primitives + a crisp cartoon face.

Five ORIGINAL models (nothing copied from the references): tree, rock, "Smoothie Shack",
conveyor machine, brainrot "Frappo Froggini". Plus an R6 dummy (5 studs) and a studded baseplate.

Usage: python blender/templates/test_collection.py <out_dir>   (bpy module)
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402

C = {
    "leaf": "#4CC24A", "leaf_dark": "#2E9A3E", "leaf_light": "#86E05A",
    "bark": "#8A5530", "bark_dark": "#6B3F22",
    "stone": "#8E96A3", "stone_dark": "#6E7683", "moss": "#5FC24A",
    "wall": "#FFF6EA", "frame": "#22C3A6", "frame_dark": "#159C85", "accent": "#FF6B6B",
    "glass": "#9BE1FF", "door": "#8A5A34", "sign": "#FFD93B", "light": "#FFE7B0",
    "steel": "#5B6B82", "steel_dark": "#3E4A5C", "belt": "#2B2F36", "belt_line": "#1E2126",
    "hazard": "#FFC21A", "black": "#1A1A1A", "machine": "#FF8A1F", "scan": "#3EF0FF",
    "ground": "#4FC33A", "pedestal": "#9AA3AF", "pad": "#36E05A",
}

# Real-Roblox scale per model (built at a compact authoring size, then scaled; studs re-mapped).
SCALE = {"Tree": 2.0, "Rock": 1.6, "Building": 2.0, "Conveyor": 1.6, "Brainrot": 1.0, "Dummy": 1.0}


def offset(objs, dx, dy, dz=0.0):
    for o in objs:
        if o.parent is None:
            o.location = (o.location[0] + dx, o.location[1] + dy, o.location[2] + dz)
    return objs


def S(*a, **k):
    return vb.solid(*a, **k)


def face(o):
    """Face pieces stay smooth (no studs) so expressions read cleanly."""
    o["vault_face"] = True
    return o


# 1. Tree -------------------------------------------------------------------------------------
def tree():
    rnd = random.Random(11)
    P = [
        vb.cyl("Trunk", 1.0, 0.65, 7.6, (0, 0, 0), C["bark"], sides=10),
        vb.cyl("RootA", 0.5, 0.3, 0.9, (0.9, 0.3, 0), C["bark_dark"], sides=8, rot=(0, math.radians(35), 0)),
        vb.cyl("RootB", 0.45, 0.3, 0.8, (-0.7, -0.6, 0), C["bark_dark"], sides=8, rot=(math.radians(30), math.radians(-25), 0)),
        vb.cyl("BranchA", 0.35, 0.25, 2.6, (0.3, 0.1, 4.4), C["bark"], sides=8, rot=(0, math.radians(40), 0)),
        vb.cyl("BranchB", 0.32, 0.22, 2.2, (-0.3, -0.1, 5.0), C["bark_dark"], sides=8, rot=(math.radians(-15), math.radians(-38), 0)),
    ]
    clumps = (
        (0, 0, 7.0, 4.4, "leaf"), (2.6, 0.6, 6.6, 3.4, "leaf_dark"), (-2.5, -0.4, 7.0, 3.4, "leaf"),
        (0.4, 2.5, 6.8, 3.2, "leaf_dark"), (-0.3, -2.5, 6.9, 3.0, "leaf"), (1.2, 0.8, 9.6, 3.4, "leaf_light"),
        (-1.4, -0.6, 9.4, 3.0, "leaf"), (2.9, -1.9, 8.6, 2.4, "leaf_light"), (-2.6, 2.0, 8.4, 2.4, "leaf_light"),
        (0.1, 0.0, 11.6, 2.4, "leaf_light"), (3.6, 1.8, 5.8, 1.8, "leaf"), (-3.4, -2.2, 6.2, 1.8, "leaf_dark"),
    )
    for i, (x, y, z, s, col) in enumerate(clumps):
        rot = (math.radians(rnd.uniform(-8, 8)), math.radians(rnd.uniform(-8, 8)), math.radians(rnd.uniform(-20, 20)))
        P.append(vb.rounded(f"Leaves{i}", (s, s, s * 0.85), (x, y, z), C[col], radius=s * 0.16, rot=rot))
    for i, (x, y, z) in enumerate(((3.9, -0.6, 7.6), (-3.2, 2.6, 7.8), (1.8, -3.0, 8.2))):
        P.append(vb.ball(f"Fruit{i}", (0.4, 0.4, 0.4), (x, y, z), "#FF4D4D", segments=10, rings=6))
    return P


# 2. Rock -------------------------------------------------------------------------------------
def rock():
    R = vb.rounded
    return [
        R("RockBase", (6, 4, 1.4), (0, 0, 0), C["stone_dark"], radius=0.35),
        R("RockMid", (4, 3, 1.3), (-0.5, 0.4, 1.25), C["stone"], radius=0.35, rot=(0, 0, math.radians(8))),
        R("RockSide", (2.2, 2, 1.1), (2.1, -0.4, 1.25), C["stone_dark"], radius=0.3, rot=(0, 0, math.radians(-12))),
        R("RockTop", (2.2, 2, 1.1), (-0.9, 0.5, 2.45), C["stone"], radius=0.3, rot=(0, 0, math.radians(20))),
        R("RockChunk", (1.8, 1.4, 1.0), (3.6, 1.4, 0), C["stone"], radius=0.3),
        R("Moss", (2.2, 2.0, 0.35), (-0.9, 0.5, 3.5), C["moss"], radius=0.12, rot=(0, 0, math.radians(20))),
        vb.ball("Pebble0", (0.5, 0.45, 0.3), (-3.8, -1.5, 0.2), C["stone"], segments=10, rings=6),
        vb.ball("Pebble1", (0.4, 0.4, 0.25), (4.4, -1.8, 0.15), C["stone_dark"], segments=10, rings=6),
    ]


# 3. Building — "Smoothie Shack" --------------------------------------------------------------
def building():
    W, D, H1, H2 = 14, 10, 7.0, 6.0
    fy = D / 2
    P = [S("Plinth", (W + 3, D + 3, 0.6), (0, 0, 0), C["stone"])]
    z0 = 0.6
    P += [
        S("Back1", (W, 0.8, H1), (0, -D / 2 + 0.4, z0), C["wall"]),
        S("Left1", (0.8, D - 1.6, H1), (-W / 2 + 0.4, 0, z0), C["wall"]),
        S("Right1", (0.8, D - 1.6, H1), (W / 2 - 0.4, 0, z0), C["wall"]),
        S("FrontSill", (8.0, 0.8, 1.4), (-1.5, fy - 0.4, z0), C["wall"]),
        S("FrontLintel", (W, 0.8, 1.4), (0, fy - 0.4, z0 + H1 - 1.4), C["wall"]),
        S("FrontPierL", (1.5, 0.8, H1 - 1.4), (-W / 2 + 0.75, fy - 0.4, z0), C["wall"]),
        S("FrontPierM", (1.0, 0.8, H1 - 1.4), (3.0, fy - 0.4, z0), C["wall"]),
        S("FrontPierR", (1.0, 0.8, H1 - 1.4), (W / 2 - 0.5, fy - 0.4, z0), C["wall"]),
        S("ShopGlass", (8.0, 0.15, H1 - 2.8), (-1.5, fy - 0.45, z0 + 1.4), C["glass"], studs="none", bevel=0.01),
        S("Door", (2.5, 0.25, 4.6), (4.75, fy - 0.5, z0), C["door"]),
        S("DoorWindow", (1.4, 0.1, 1.2), (4.75, fy - 0.35, z0 + 2.9), C["glass"], studs="none", bevel=0.01),
        S("CounterLedge", (8.6, 1.4, 0.35), (-1.5, fy + 0.3, z0 + 1.4), C["frame"]),
    ]
    P.append(vb.block("InteriorLight1", (11, 7, 0.15), (0, 0, z0 + H1 - 0.3), C["light"], bevel=0.0, emission=3.5))
    for i in range(8):
        P.append(S(f"Awning{i}", (1.08, 2.4, 0.22), (-5.6 + i * 1.1, fy + 1.0, z0 + H1 - 1.6),
                   C["accent"] if i % 2 == 0 else "#FFFFFF", bevel=0.02, rot=(math.radians(-22), 0, 0)))
    for i, (x, y) in enumerate(((-W / 2, fy), (W / 2, fy), (-W / 2, -D / 2), (W / 2, -D / 2))):
        P.append(S(f"Pillar{i}", (1.6, 1.6, H1 + H2 + 1.0), (x, y, z0), C["frame"]))
    P += [
        S("BeamFront", (W, 1.4, 1.0), (0, fy, z0 + H1), C["frame"]),
        S("BeamBack", (W, 1.4, 1.0), (0, -D / 2, z0 + H1), C["frame"]),
        S("BeamL", (1.4, D, 1.0), (-W / 2, 0, z0 + H1), C["frame"]),
        S("BeamR", (1.4, D, 1.0), (W / 2, 0, z0 + H1), C["frame"]),
    ]
    z1 = z0 + H1 + 1.0
    P += [
        S("Back2", (W, 0.8, H2), (0, -D / 2 + 0.4, z1), C["wall"]),
        S("Left2", (0.8, D - 1.6, H2), (-W / 2 + 0.4, 0, z1), C["wall"]),
        S("Right2", (0.8, D - 1.6, H2), (W / 2 - 0.4, 0, z1), C["wall"]),
        S("Front2Low", (W, 0.8, 1.2), (0, fy - 0.4, z1), C["wall"]),
        S("Front2High", (W, 0.8, 1.2), (0, fy - 0.4, z1 + H2 - 1.2), C["wall"]),
        S("Front2L", (3.0, 0.8, H2 - 2.4), (-W / 2 + 1.5, fy - 0.4, z1 + 1.2), C["wall"]),
        S("Front2R", (3.0, 0.8, H2 - 2.4), (W / 2 - 1.5, fy - 0.4, z1 + 1.2), C["wall"]),
        S("UpperGlass", (8.0, 0.15, H2 - 2.4), (0, fy - 0.45, z1 + 1.2), C["glass"], studs="none", bevel=0.01),
        S("UpperSill", (8.8, 1.2, 0.3), (0, fy + 0.1, z1 + 1.2), C["frame_dark"]),
        S("Mullion", (0.3, 0.2, H2 - 2.4), (0, fy - 0.3, z1 + 1.2), "#FFFFFF"),
    ]
    P.append(vb.block("InteriorLight2", (11, 7, 0.15), (0, 0, z1 + H2 - 0.3), C["light"], bevel=0.0, emission=3.0))
    zr = z1 + H2
    P += [
        S("Roof", (W + 2.6, D + 2.6, 0.9), (0, 0, zr), C["accent"]),
        S("RoofTrim", (W + 3.0, D + 3.0, 0.3), (0, 0, zr - 0.3), "#FFFFFF"),
        S("SignBack", (10, 0.6, 2.6), (0, fy + 0.6, zr + 0.9), C["accent"]),
        S("SignFace", (9.2, 0.15, 2.0), (0, fy + 0.95, zr + 1.2), C["sign"], bevel=0.01),
        # rooftop smoothie cup: round shapes
        vb.cyl("CupBody", 1.1, 1.45, 3.0, (-3.8, -1.5, zr + 0.9), "#FF6FAE", sides=16),
        vb.cyl("CupBand", 1.4, 1.5, 0.7, (-3.8, -1.5, zr + 2.0), "#FFFFFF", sides=16),
        vb.cyl("CupLid", 1.65, 1.65, 0.35, (-3.8, -1.5, zr + 3.9), "#FFFFFF", sides=16),
        vb.ball("CupDome", (1.1, 1.1, 0.6), (-3.8, -1.5, zr + 4.25), "#FFFFFF", segments=14, rings=8),
        vb.cyl("Straw", 0.22, 0.22, 2.8, (-3.5, -1.3, zr + 4.3), C["accent"], sides=10, rot=(0, math.radians(18), 0)),
    ]
    for i, x in enumerate((2.0, 7.6)):
        P.append(vb.cyl(f"Planter{i}", 0.6, 0.7, 0.9, (x, fy + 1.4, z0), C["frame_dark"], sides=12))
        P.append(vb.ball(f"Bush{i}", (0.7, 0.7, 0.6), (x, fy + 1.4, z0 + 1.3), C["leaf"], segments=12, rings=8))
    P += building_details(W, D, H1, H2, z0, z1, zr, fy)
    return P


def building_details(W, D, H1, H2, z0, z1, zr, fy):
    """Detail pass (owner: buildings need detail on par with collectibles — not more)."""
    P = []
    WH, WOOD, DARK = "#FFFFFF", "#D9A066", "#2E3440"
    fruit = ("#FF9F1C", "#FF3B5C", "#8BE04E", "#FFD93B")
    # shop window frame + mullions (3 panes)
    P += [S("ShopFrameTop", (8.4, 0.3, 0.3), (-1.5, fy + 0.05, z0 + H1 - 1.7), WH),
          S("ShopFrameL", (0.3, 0.3, 4.4), (-5.55, fy + 0.05, z0 + 1.75), WH),
          S("ShopFrameR", (0.3, 0.3, 4.4), (2.55, fy + 0.05, z0 + 1.75), WH)]
    for i, x in enumerate((-2.83, -0.17)):
        P.append(S(f"ShopMullion{i}", (0.2, 0.2, 4.2), (x, fy - 0.3, z0 + 1.4), WH))
    # scalloped awning valance
    for i in range(16):
        P.append(vb.ball(f"Scallop{i}", (0.3, 0.14, 0.26), (-5.85 + i * 0.55, fy + 2.1, z0 + H1 - 2.05),
                         C["accent"] if i % 2 == 0 else WH, segments=10, rings=6))
    # door frame, knob, lamps, step, mat
    P += [S("DoorFrameTop", (3.0, 0.3, 0.3), (4.75, fy + 0.05, z0 + 4.6), WH),
          S("DoorFrameL", (0.25, 0.3, 4.6), (3.4, fy + 0.05, z0), WH),
          S("DoorFrameR", (0.25, 0.3, 4.6), (6.1, fy + 0.05, z0), WH),
          vb.ball("DoorKnob", (0.16, 0.12, 0.16), (5.6, fy - 0.2, z0 + 2.3), C["sign"], segments=8, rings=5),
          S("DoorStep", (3.4, 1.2, 0.3), (4.75, fy + 2.1, 0), C["stone_dark"]),
          S("Mat", (2.4, 1.0, 0.06), (4.75, fy + 1.0, z0), "#FF6FAE", bevel=0.01)]
    for i, x in enumerate((3.0, 6.6)):
        P.append(S(f"LampBack{i}", (0.5, 0.2, 0.8), (x, fy + 0.1, z0 + 3.2), DARK))
        P.append(vb.ball(f"Lamp{i}", (0.22, 0.22, 0.3), (x, fy + 0.35, z0 + 3.7), C["light"], segments=10, rings=6, emission=4))
    # baseboard + cornice bands
    P += [S("BaseBack", (W, 0.2, 0.5), (0, -D / 2 - 0.1, z0), C["frame_dark"]),
          S("BaseL", (0.2, D - 1.6, 0.5), (-W / 2 - 0.1, 0, z0), C["frame_dark"]),
          S("BaseR", (0.2, D - 1.6, 0.5), (W / 2 + 0.1, 0, z0), C["frame_dark"]),
          S("Cornice", (W + 1.4, D + 1.4, 0.4), (0, 0, zr - 0.7), C["frame_dark"])]
    # side windows with frames + flower boxes (both floors)
    for sx in (-1, 1):
        xo = sx * (W / 2 + 0.04)
        for k, zw in enumerate((z0 + 2.0, z1 + 1.6)):
            tag = f"{'L' if sx < 0 else 'R'}{k}"
            P += [S(f"SideGlass{tag}", (0.1, 3.0, 2.4), (xo, 0, zw), C["glass"], studs="none", bevel=0.01),
                  S(f"SideFrameT{tag}", (0.25, 3.5, 0.3), (xo + sx * 0.05, 0, zw + 2.4), WH),
                  S(f"SideFrameB{tag}", (0.25, 3.5, 0.3), (xo + sx * 0.05, 0, zw - 0.3), WH),
                  S(f"SideFrameF{tag}", (0.25, 0.3, 2.4), (xo + sx * 0.05, 1.6, zw), WH),
                  S(f"SideFrameK{tag}", (0.25, 0.3, 2.4), (xo + sx * 0.05, -1.6, zw), WH),
                  S(f"FlowerBox{tag}", (0.6, 3.2, 0.5), (xo + sx * 0.3, 0, zw - 0.8), C["frame_dark"])]
            for j in range(5):
                P.append(vb.ball(f"Flower{tag}_{j}", (0.22, 0.22, 0.2), (xo + sx * 0.3, -1.2 + j * 0.6, zw - 0.2),
                                 fruit[j % 4], segments=8, rings=5))
    # string lights under the floor beam
    P.append(S("LightWire", (W - 1.0, 0.06, 0.06), (0, fy + 0.75, z0 + H1 - 0.15), DARK, bevel=0.0))
    for i in range(12):
        P.append(vb.ball(f"Bulb{i}", (0.14, 0.14, 0.18), (-6.0 + i * 1.09, fy + 0.78, z0 + H1 - 0.45),
                         ("#FFE066", "#FF8FC8", "#7FF0FF")[i % 3], segments=8, rings=5, emission=3))
    # sign border + fruit icons
    P += [S("SignBorderT", (9.6, 0.25, 0.25), (0, fy + 1.0, zr + 3.2), WH),
          S("SignBorderB", (9.6, 0.25, 0.25), (0, fy + 1.0, zr + 1.0), WH)]
    for i, x in enumerate((-3.2, 0.0, 3.2)):
        P.append(vb.ball(f"SignFruit{i}", (0.55, 0.2, 0.55), (x, fy + 1.12, zr + 2.2), fruit[i], segments=12, rings=8))
        P.append(S(f"SignLeaf{i}", (0.35, 0.12, 0.25), (x + 0.2, fy + 1.15, zr + 2.7), C["leaf"], bevel=0.05))
    # roof: parapet, AC unit, vent, cup toppings
    zt = zr + 0.9
    P += [S("ParapetB", (W + 2.6, 0.5, 0.6), (0, -D / 2 - 1.05, zt), C["accent"]),
          S("ParapetL", (0.5, D + 1.6, 0.6), (-W / 2 - 1.05, -0.25, zt), C["accent"]),
          S("ParapetR", (0.5, D + 1.6, 0.6), (W / 2 + 1.05, -0.25, zt), C["accent"]),
          vb.rounded("ACUnit", (2.2, 1.6, 1.3), (3.5, -2.5, zt), C["steel"], radius=0.12),
          vb.cyl("ACFan", 0.55, 0.55, 0.06, (3.5, -2.5, zt + 1.3), DARK, sides=14),
          vb.cyl("Vent", 0.25, 0.25, 1.4, (5.8, 1.5, zt), C["steel_dark"], sides=10),
          vb.cyl("VentCap", 0.38, 0.38, 0.15, (5.8, 1.5, zt + 1.4), C["steel_dark"], sides=10),
          vb.ball("Whip", (1.0, 1.0, 0.55), (-3.8, -1.5, zr + 4.9), WH, segments=14, rings=8),
          vb.ball("Cherry", (0.28, 0.28, 0.28), (-3.6, -1.4, zr + 5.55), "#FF3B5C", segments=10, rings=6),
          vb.cyl("OrangeSlice", 0.75, 0.75, 0.15, (-2.35, -1.0, zr + 3.9), fruit[0], sides=16, rot=(math.pi / 2, 0, 0.3))]
    for i in range(4):
        P.append(S(f"ACGrille{i}", (1.8, 0.06, 0.12), (3.5, -1.68, zt + 0.25 + i * 0.25), DARK, bevel=0.0))
    # interior seen through the glass: counter, blenders, cups, menu board
    P.append(S("InnerCounter", (7.5, 1.0, 1.6), (-1.5, fy - 2.2, z0), WOOD))
    for i, x in enumerate((-4.2, -2.4, -0.6, 1.2)):
        P.append(S(f"BlenderBase{i}", (0.6, 0.6, 0.35), (x, fy - 2.2, z0 + 1.6), DARK))
        P.append(vb.cyl(f"BlenderJar{i}", 0.22, 0.3, 0.8, (x, fy - 2.2, z0 + 1.95), fruit[i], sides=10))
    P.append(S("MenuBoard", (6.0, 0.15, 2.0), (-1.5, -D / 2 + 0.9, z0 + 3.5), DARK))
    for r in range(3):
        P.append(S(f"MenuLine{r}", (4.8, 0.06, 0.18), (-1.5, -D / 2 + 1.0, z0 + 3.9 + r * 0.5), fruit[r], bevel=0.0))
    # outdoor seating + A-frame menu + crates + drainpipe
    tx, ty = -4.5, fy + 3.6
    P += [vb.cyl("TableLeg", 0.15, 0.15, 1.2, (tx, ty, 0), DARK, sides=8),
          vb.cyl("TableTop", 1.0, 1.0, 0.15, (tx, ty, 1.2), WH, sides=16),
          vb.cyl("UmbrellaPole", 0.08, 0.08, 2.6, (tx, ty, 1.35), WH, sides=8),
          vb.cyl("Umbrella", 1.9, 0.12, 0.8, (tx, ty, 3.6), C["accent"], sides=8),
          vb.ball("UmbrellaTop", (0.15, 0.15, 0.15), (tx, ty, 4.45), WH, segments=8, rings=5)]
    for i, dx in enumerate((-1.5, 1.5)):
        P.append(vb.cyl(f"Stool{i}", 0.42, 0.42, 0.75, (tx + dx, ty, 0), C["frame"], sides=12))
    for i, tilt in enumerate((12, -12)):
        P.append(S(f"AFrame{i}", (1.4, 0.12, 2.0), (0.6, fy + 3.2 + (0.25 if i else -0.25), 0), DARK,
                   rot=(math.radians(tilt), 0, 0)))
    for r in range(3):
        P.append(S(f"AFrameLine{r}", (1.0, 0.05, 0.15), (0.6, fy + 3.48, 0.6 + r * 0.4), fruit[r], bevel=0.0,
                   rot=(math.radians(-12), 0, 0)))
    for i, z in enumerate((0, 0.8)):
        P.append(vb.rounded(f"Crate{i}", (1.3, 1.0, 0.8), (W / 2 + 1.6, fy + 1.6, z), WOOD, radius=0.08))
    for j in range(3):
        P.append(vb.ball(f"CrateFruit{j}", (0.25, 0.25, 0.25), (W / 2 + 1.25 + j * 0.35, fy + 1.6, 1.85), fruit[j],
                         segments=8, rings=5))
    P.append(vb.cyl("Drainpipe", 0.18, 0.18, H1 + H2 + 1.0, (W / 2 + 0.95, -D / 2 - 0.95, z0), C["steel"], sides=8))
    return P


# 4. Conveyor machine --------------------------------------------------------------------------
def conveyor():
    L, Wd, zt = 14, 3.4, 2.6
    P = []
    for i, x in enumerate((-6.2, -1.5, 3.0)):
        for j, y in enumerate((-1.3, 1.3)):
            P.append(S(f"Leg{i}{j}", (0.7, 0.7, zt - 0.8), (x, y, 0), C["steel_dark"]))
        P.append(S(f"Brace{i}", (0.4, 2.6, 0.4), (x, 0, 0.6), C["steel_dark"]))
    P.append(S("Frame", (L, Wd, 0.8), (0, 0, zt - 0.8), C["steel"]))
    P.append(S("Belt", (L - 0.4, Wd - 0.9, 0.2), (0, 0, zt), C["belt"], bevel=0.01))
    for side in (-1, 1):
        P.append(S(f"Guard{side}", (L, 0.35, 0.8), (0, side * (Wd / 2 - 0.1), zt), C["hazard"]))
        for i in range(7):
            P.append(S(f"Stripe{side}_{i}", (0.35, 0.05, 1.0), (-6.0 + i * 2.0, side * (Wd / 2 + 0.08), zt - 0.1),
                       C["black"], bevel=0.0, rot=(0, math.radians(35), 0)))
    for i, x in enumerate((-L / 2, L / 2 - 4.2)):
        P.append(vb.cyl(f"Roller{i}", 0.45, 0.45, Wd - 0.6, (x, (Wd - 0.6) / 2, zt - 0.35), C["steel_dark"], sides=14,
                        rot=(math.pi / 2, 0, 0)))
    P.append(vb.cyl("Hopper", 1.3, 2.0, 2.0, (-5.6, 0, zt + 0.2), C["machine"], sides=8))  # funnel
    P.append(vb.cyl("HopperHole", 1.75, 1.75, 0.05, (-5.6, 0, zt + 2.2), C["black"], sides=8))
    bx = L / 2 - 2.1
    P += [
        vb.rounded("Machine", (4.2, Wd + 1.2, 3.8), (bx, 0, zt - 0.8), C["machine"], radius=0.35),
        S("MachineTop", (3.4, Wd + 0.4, 0.6), (bx, 0, zt + 3.0), C["steel"]),
        S("Tunnel", (0.2, Wd - 1.0, 1.4), (bx - 2.12, 0, zt), C["black"], bevel=0.0),
        vb.cyl("Pipe0", 0.32, 0.32, 1.6, (bx + 0.8, -1.0, zt + 3.6), C["steel_dark"], sides=12),
        vb.cyl("Pipe1", 0.32, 0.32, 1.1, (bx - 0.5, 1.1, zt + 3.6), C["steel_dark"], sides=12),
    ]
    P.append(vb.block("MachineWindow", (2.4, 0.1, 1.4), (bx, Wd / 2 + 0.65, zt + 0.9), C["scan"], bevel=0.0, emission=4))
    P.append(vb.ball("WarnLight", (0.4, 0.4, 0.35), (bx + 1.2, 1.2, zt + 3.9), "#FF3B3B", segments=10, rings=6, emission=5))
    for i, (x, col) in enumerate(((-2.8, "#B678EA"), (0.8, "#2590D1"))):
        P.append(vb.rounded(f"Crate{i}", (1.3, 1.3, 1.3), (x, 0, zt + 0.2), col, radius=0.15))
    return P


# 5. Brainrot collectible — "Frappo Froggini" v3 ------------------------------------------------
def frappo():
    """Chunky MERGED blocks (fine design -> downsampled to 0.5-stud blocks, no colour noise)
    plus a clean cartoon face built from crisp pieces on the head front."""
    V = vb.VoxelCanvas()
    G, GL = "#4FD13A", "#B8F07A"
    CUP, SLEEVE, LID = "#F7F4EC", "#B5743A", "#4A2E1A"
    WHITE, RED, SOLE = "#FFFFFF", "#FF3B3B", "#2E3440"
    for sx in (-1, 1):  # sneakers
        x0, x1 = (2, 7) if sx > 0 else (-8, -3)
        V.box(x0, x1, -3, 5, 0, 1, SOLE)
        V.box(x0, x1, -3, 5, 2, 3, WHITE)
        V.box(x0, x1, 4, 5, 2, 3, RED)
        V.box(x0 + 1, x1 - 1, -1, 1, 4, 5, G)
    V.cylinder(0, 0, 6, 17, 5.5, 6.5, CUP)
    V.paint(lambda x, y, z: 10 <= z <= 13, SLEEVE)
    V.cylinder(0, 0, 18, 19, 7.0, 7.0, LID)
    V.ellipsoid(0, 0.5, 26.5, 11, 8.5, 8.0, G)
    V.paint(lambda x, y, z: z <= 23 and y >= 2 and V.v.get((x, y, z)) == G, GL)
    for sx in (-1, 1):
        V.ellipsoid(sx * 5, 1.5, 33, 3.8, 3.4, 3.6, G)
    for i in range(24):  # thick striped straw
        x, y, z = 6 + i // 6, -6, 18 + i
        for dx in (0, 1):
            for dy in (0, 1):
                V.v[(x + dx, y + dy, z)] = RED if (i // 4) % 2 == 0 else WHITE
    V.box(7, 9, -1, 1, 11, 14, G)  # thumbs-up arm
    V.box(8, 10, -1, 1, 15, 18, G)
    V.box(8, 11, -1, 1, 19, 21, GL)
    V.box(10, 11, -1, 0, 22, 24, GL)
    V.box(-9, -7, -1, 1, 11, 14, G)  # resting arm
    V.box(-10, -7, 0, 3, 10, 11, GL)
    coarse = V.downsample(2, min_fill=3)
    vs = 0.5
    body = vb.voxel_mesh("Frappo_Body", coarse.v, voxel=vs, jitter=0.0, seed=3)
    vb.stud_surface(body, "all")  # EVERYTHING gets stud texture, pets included (owner)
    P = [body]

    def face_y(x_studs, z_studs, half_w=0.0):
        """Front surface (studs) of the merged head at an x/z, max across the feature width."""
        best = None
        for xx in (x_studs - half_w, x_studs, x_studs + half_w):
            fy = coarse.front_y(int(math.floor(xx / vs)), int(math.floor(z_studs / vs)))
            if fy is not None:
                best = max(best, (fy + 1) * vs) if best is not None else (fy + 1) * vs
        return best if best is not None else 2.0

    def feat(name, size, x, z, col, dy=0.0, emission=0.0, rot=None):
        y = face_y(x, z + size[2] / 2, size[0] / 2) + size[1] / 2 - 0.02 + dy
        o = vb.block(name, size, (x, y, z), col, bevel=0.03, segments=1, emission=emission)
        o["vault_face"] = True
        if rot:
            o.rotation_euler = rot
        P.append(o)
        return o

    for sx, side in ((-1, "L"), (1, "R")):  # big eyes on the eye domes, smug half-lids
        ex = sx * 1.25
        feat(f"Eye{side}", (1.5, 0.16, 1.5), ex, 7.55, WHITE)
        feat(f"Pupil{side}", (0.62, 0.14, 0.8), ex - sx * 0.25, 7.7, "#141414", dy=0.08)
        feat(f"Sparkle{side}", (0.24, 0.1, 0.24), ex - sx * 0.05, 8.25, WHITE, dy=0.16, emission=1.0)
        feat(f"Lid{side}", (1.62, 0.2, 0.5), ex, 8.6, "#2F9A22", dy=0.1, rot=(0, math.radians(sx * -8), 0))
        feat(f"Blush{side}", (0.7, 0.12, 0.32), sx * 2.15, 6.05, "#FF8FB1")
    feat("Mouth", (3.0, 0.16, 0.9), 0.2, 4.95, "#141414", rot=(0, math.radians(-6), 0))  # open smirk
    feat("Tongue", (1.3, 0.14, 0.42), -0.2, 5.0, "#FF6F9B", dy=0.06)
    feat("Emblem", (0.7, 0.12, 0.7), 0.0, 2.75, G)  # leaf logo on the cup sleeve
    for i in range(6):  # glow sparkles
        a = 2 * math.pi * i / 6
        P.append(vb.block(f"Glow{i}", (0.35, 0.35, 0.35), (math.cos(a) * 3.8, math.sin(a) * 3.8, 2.0 + (i % 3) * 1.5),
                          "#FFD93B", bevel=0.0, emission=4))
    return P


def pedestal():
    return [
        vb.rounded("Pedestal", (6.5, 6.5, 1.0), (0, 0, 0), C["pedestal"], radius=0.2),
        vb.rounded("PedestalTop", (5.6, 5.6, 0.4), (0, 0, 1.0), C["pedestal"], radius=0.12),
        vb.block("CollectPad", (6.6, 1.2, 0.12), (0, 4.0, 0), C["pad"], bevel=0.0, emission=1.2),
    ]


def r6_dummy():
    g, gd = "#C8CCD2", "#A3A9B1"
    return [
        S("Dummy_LegL", (1, 1, 2), (-0.5, 0, 0), gd, bevel=0.05),
        S("Dummy_LegR", (1, 1, 2), (0.5, 0, 0), gd, bevel=0.05),
        S("Dummy_Torso", (2, 1, 2), (0, 0, 2), g, bevel=0.05),
        S("Dummy_ArmL", (1, 1, 2), (-1.5, 0, 2), gd, bevel=0.05),
        S("Dummy_ArmR", (1, 1, 2), (1.5, 0, 2), gd, bevel=0.05),
        vb.rounded("Dummy_Head", (1.2, 1.2, 1.0), (0, 0, 4), g, radius=0.3),
    ]  # 5 studs tall = Roblox R6 character


LAYOUT = {  # world positions after scaling; every model's FRONT faces +y
    "Tree": (-30, -12), "Rock": (-26, 16), "Building": (6, -20), "Conveyor": (6, 16),
    "Brainrot": (34, 6), "Dummy": (-10, 8),
}


def build_all():
    vb.reset_scene()
    vb.ensure_stud_textures()
    builders = {
        "Tree": tree, "Rock": rock, "Building": building, "Conveyor": conveyor,
        "Brainrot": lambda: pedestal() + offset(frappo(), 0, 0, 1.4), "Dummy": r6_dummy,
    }
    groups = {}
    for name, fn in builders.items():
        objs = fn()
        vb.scale_group(objs, SCALE[name])
        x, y = LAYOUT[name]
        offset(objs, x, y)
        vb.restud(objs)
        groups[name] = objs
    ground = vb.block("Baseplate", (130, 90, 1), (4, 0, -1), C["ground"], bevel=0.0)
    vb.stud_surface(ground, "all")
    return groups, [ground]


def main(out_dir):
    groups, _ = build_all()
    os.makedirs(out_dir, exist_ok=True)
    return {name: vb.poly_report(objs) for name, objs in groups.items()}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    for k, v in main(argv[0] if argv else "out").items():
        print(k, v)
