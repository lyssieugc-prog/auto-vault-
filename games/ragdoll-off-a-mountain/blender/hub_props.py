"""
Ragdoll Off a Mountain — BONE ZONE hub props (original models, SOLID language, texture studs).

    python3 games/ragdoll-off-a-mountain/blender/hub_props.py [export_dir] [--samples N] [--only Name]
                                                              [--no-render] [--no-hero]

Models (FRONT = +Y, pivot bottom-centre, 1 unit = 1 stud):
  RebirthStatue  giant cheerful cartoon skeleton in a victory pose holding a gold trophy (~26 tall)
  EggStand       studded stand + roof sign + display ring for a 6-stud egg; recolourable mesh/material "Accent"
  CannonShop     booth: counter, striped awning, sign with cannon icon, rooftop cannon, cannonball stack
  UpgradeStand   round kiosk: striped canopy, tower sign with bone + up-arrow icon, milk bottles, X-ray box
  SeasonBoard    big notice board on posts, snow cap, snowflake crest; blank face mesh "Screen"
  Leaderboard    1-2-3 podium + board, trophy topper; blank face mesh "Screen"
  DailyChest     chunky chest, domed lid, gold trim, bone-shaped lock, glowing seam
Shared helpers live in cannons.py.
"""

from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import cannons as cn  # noqa: E402  (also sets up vault libs + stud textures)
from cannons import (B, C, R, S, SH, T, Rx, Ry, Rz, N, xf, tube, prism, beam, bolts, star_pts, circle_pts,  # noqa: E402
                     bone_icon, cartoon_bone, finish_model, setup_render, render_views, review_ground, shoot,
                     merge_manifest, all_bounds, GAME, EXPORT_DIR, PREVIEW_DIR, BONE, SNAP, GOLD, INK, NAVY, STONE)

import vault_blocky as vb  # noqa: E402
import vault_kit as kit  # noqa: E402

ACCENT_HEX = "#4CC24B"  # egg stand default accent (recoloured per peak in Studio)
WOOD = SH("#C98A4B")
CREAM = SH("#FFF6EA")
ORANGE = SH(SNAP)
GOLDS = SH(GOLD)
BONES = SH(BONE)
ST = SH(STONE)
TEAL = SH("#22C3A6")
CORAL = SH("#FF6B6B")
ICE = SH("#7FD3FF")
SNOW = SH("#F4FBFF")


def rect(w, h, cx=0.0, cy=0.0):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def ellipse(rx, ry, n=16, cx=0.0, cy=0.0):
    return [(cx + math.cos(2 * math.pi * i / n) * rx, cy + math.sin(2 * math.pi * i / n) * ry) for i in range(n)]


def face_piece(name, pts, depth, color, y, z0=0.0, x0=0.0, glow=0.0):
    """Flat piece on a +Y facing surface (outline in X/Z), unstudded (face/decal geometry)."""
    o = prism(name, pts, depth, color, plane="xz", loc=(x0, y + depth / 2, z0), studs="none")
    return N(o, glow) if glow else o


def trophy(prefix, base, s=1.0, gem=SNAP):
    """Gold cup trophy (base -> stem -> cup + handles + rim + gem) standing at `base`."""
    x, y, z = base
    G = GOLDS
    P = [C(f"{prefix}Foot", 1.1 * s, 1.0 * s, 0.4 * s, (x, y, z), G["dark"], sides=12),
         C(f"{prefix}Foot2", 0.8 * s, 0.7 * s, 0.35 * s, (x, y, z + 0.4 * s), G["base"], sides=12),
         C(f"{prefix}Stem", 0.3 * s, 0.35 * s, 0.9 * s, (x, y, z + 0.75 * s), G["dark"], sides=10),
         B(f"{prefix}Knot", (0.5 * s, 0.5 * s, 0.3 * s), (x, y, z + 1.6 * s), G["light"], segments=10, rings=6),
         C(f"{prefix}Cup", 0.7 * s, 1.45 * s, 1.9 * s, (x, y, z + 1.7 * s), G["base"], sides=16),
         tube(f"{prefix}Rim", 1.6 * s, 1.6 * s, 0.3 * s, 0.35 * s, (x, y, z + 3.55 * s), G["light"], sides=16),
         C(f"{prefix}Inside", 1.3 * s, 1.3 * s, 0.1 * s, (x, y, z + 3.4 * s), G["deep"], sides=16, studs="none")]
    for sx in (-1, 1):
        h = tube(f"{prefix}Handle{sx}", 0.75 * s, 0.75 * s, 0.32 * s, 0.28 * s, (0, 0, -0.16 * s), G["base"], sides=12,
                 a0=-90, a1=90)
        xf([h], T(x + sx * 1.25 * s, y, z + 2.8 * s) @ Rx(90) @ Rz(0 if sx > 0 else 180))
        P.append(h)
    P.append(face_piece(f"{prefix}Gem", star_pts(0.55 * s, 0.25 * s), 0.18 * s, gem, y + 1.05 * s, z + 2.55 * s, x, glow=4))
    return P


# ================================================================================================
# (a) Rebirth statue
# ================================================================================================

def rebirth_statue():
    name = "RebirthStatue"
    P = []
    # ---- plinth: stepped studded base, cream body with orange trims, gold top, corner posts
    P += [S("PlStep0", (14.0, 14.0, 0.8), (0, 0, 0), ST["dark"]),
          S("PlStep1", (12.4, 12.4, 0.8), (0, 0, 0.8), ST["base"]),
          S("PlBaseboard", (11.4, 11.4, 0.45), (0, 0, 1.6), ORANGE["dark"]),
          S("PlBody", (11.0, 11.0, 2.75), (0, 0, 2.05), CREAM["base"]),
          S("PlCornice", (11.7, 11.7, 0.5), (0, 0, 4.8), ORANGE["base"]),
          S("PlTop", (11.2, 11.2, 0.4), (0, 0, 5.3), GOLDS["dark"])]
    z0 = 5.7
    for sx in (-1, 1):
        for sy in (-1, 1):
            P += [S(f"PlPost{sx}{sy}", (1.5, 1.5, 3.2), (sx * 5.45, sy * 5.45, 1.6), CREAM["light"]),
                  S(f"PlPostCap{sx}{sy}", (1.8, 1.8, 0.4), (sx * 5.45, sy * 5.45, 4.8), ORANGE["light"]),
                  B(f"PlPostBall{sx}{sy}", (0.6, 0.6, 0.6), (sx * 5.45, sy * 5.45, 5.75), GOLDS["base"], segments=12, rings=8)]
    # front plaque with the rebirth icon (two chasing arrows around a bone)
    fy = 5.5
    P += [face_piece("PlPlaqueBack", rect(6.4, 2.5), 0.2, GOLDS["dark"], fy, 3.45),
          face_piece("PlPlaque", rect(5.9, 2.0), 0.15, GOLDS["base"], fy + 0.2, 3.45)]
    for k, (a0, a1) in enumerate(((20, 160), (200, 340))):
        arc = tube(f"PlArrowArc{k}", 0.85, 0.85, 0.2, 0.28, (0, 0, 0), SNAP, sides=20, a0=a0, a1=a1, studs="none")
        xf([arc], T(-1.6, fy + 0.35, 3.45) @ Rx(-90))
        P.append(N(arc, 3))
        a = math.radians(a1 if k == 0 else a1)
        hx, hz = math.cos(a) * 0.72, math.sin(a) * 0.72
        sgn = 1 if k == 0 else -1
        P.append(face_piece(f"PlArrowHead{k}", [(-0.35, 0), (0.35, 0), (0, 0.45 * -sgn)], 0.2, SNAP, fy + 0.35,
                            3.45 + hz + (0.12 * sgn), -1.6 + hx, glow=3))
    for i, o in enumerate(bone_icon("PlPlaqueBone", 0.75, BONES["base"], 0.2)):
        xf([o], T(0.9, fy + 0.45, 3.45))
        P.append(o)
    # side + back panels: inset navy panel with a bone icon (no blank faces)
    for k, (yaw, nx, ny) in enumerate(((-90, 1, 0), (90, -1, 0), (180, 0, -1))):
        pan = [face_piece(f"PlPanel{k}", rect(5.6, 2.0), 0.15, NAVY, 0, 2.45),
               face_piece(f"PlPanelTrim{k}", rect(6.0, 2.4), 0.1, ORANGE["dark"], -0.1, 2.25)]
        pan += bone_icon(f"PlPanelBone{k}", 0.75, BONES["light"], 0.18)
        xf(pan[2:], T(0, 0.24, 3.45) @ Ry(12))
        xf(pan, T(nx * 5.5, ny * 5.5, 0) @ Rz(yaw))
        P += pan
    # neon rebirth ring + 6 gold chevrons around the feet
    P.append(N(tube("PlRing", 4.7, 4.7, 0.18, 0.45, (0, 0, z0 + 0.01), SNAP, sides=32), 3))
    for i in range(6):
        a = 60 * i + 30
        ch = prism(f"PlChevron{i}", [(-0.5, 0), (0, 0.6), (0.5, 0), (0.5, 0.35), (0, 0.95), (-0.5, 0.35)], 0.2, GOLDS["light"], plane="xy")
        xf([ch], T(math.cos(math.radians(a)) * 3.9, math.sin(math.radians(a)) * 3.9, z0 + 0.1) @ Rz(a - 90))
        P.append(ch)
    # torches on the front corners of the lower step
    for sx in (-1, 1):
        x, y = sx * 6.4, 6.4
        P += [C(f"TorchPole{sx}", 0.3, 0.25, 3.2, (x, y, 0.8), INK, sides=8),
              C(f"TorchBowl{sx}", 0.5, 0.85, 0.7, (x, y, 4.0), GOLDS["dark"], sides=10),
              N(prism(f"TorchFlame{sx}", [(-0.55, 0), (0.55, 0), (0.3, 0.7), (0, 1.4), (-0.3, 0.7)], 0.6, "#FF9A2E", plane="xz",
                      loc=(x, y, 4.65), studs="none"), 4),
              N(prism(f"TorchFlameX{sx}", [(-0.35, 0), (0.35, 0), (0, 0.9)], 0.62, "#FFE45C", plane="yz",
                      loc=(x, y, 4.65), studs="none"), 4)]
    # ---- skeleton (blocky Roblox proportions: big head, hollow ribcage, chunky cartoon bones)
    BN, BL, BD = BONES["base"], BONES["light"], BONES["dark"]
    # feet + toes
    for sx in (-1, 1):
        fx = sx * 1.9
        P += [R(f"SkFoot{sx}", (1.8, 2.9, 0.9), (fx, 0.5, z0), BN, radius=0.25)]
        for t in range(3):
            P.append(B(f"SkToe{sx}{t}", (0.33, 0.33, 0.3), (fx - 0.55 + t * 0.55, 2.0, z0 + 0.35), BL, segments=8, rings=5))
    P += cartoon_bone("SkShinL", (-1.85, 0.3, z0 + 0.9), (-1.65, 0.2, z0 + 3.4), 0.45, BN)
    P += cartoon_bone("SkShinR", (1.85, 0.3, z0 + 0.9), (1.65, 0.2, z0 + 3.4), 0.45, BN)
    P += [B("SkKneeL", (0.6, 0.55, 0.55), (-1.65, 0.55, z0 + 3.55), BL, segments=10, rings=6),
          B("SkKneeR", (0.6, 0.55, 0.55), (1.65, 0.55, z0 + 3.55), BL, segments=10, rings=6)]
    P += cartoon_bone("SkFemurL", (-1.65, 0.2, z0 + 3.7), (-1.25, 0.0, z0 + 5.9), 0.5, BN)
    P += cartoon_bone("SkFemurR", (1.65, 0.2, z0 + 3.7), (1.25, 0.0, z0 + 5.9), 0.5, BN)
    # plaster cast on the right shin (on-theme: broken bones, kid-friendly)
    P += [C("SkCast", 0.78, 0.72, 1.5, (1.78, 0.27, z0 + 1.4), "#FFFFFF", sides=12),
          tube("SkCastBand", 0.8, 0.8, 0.25, 0.1, (1.78, 0.27, z0 + 2.3), "#FF5FA2", sides=12)]
    # pelvis (wide bowl + hip wings)
    P += [R("SkPelvis", (3.6, 1.9, 1.3), (0, 0, z0 + 5.6), BN, radius=0.35),
          R("SkHipWingL", (1.5, 1.6, 1.3), (-1.7, 0, z0 + 6.0), BD, radius=0.35, rot=(0, math.radians(-18), 0)),
          R("SkHipWingR", (1.5, 1.6, 1.3), (1.7, 0, z0 + 6.0), BD, radius=0.35, rot=(0, math.radians(18), 0))]
    # spine + ribcage + sternum + collar bar
    for i in range(6):
        P.append(R(f"SkVert{i}", (0.95, 0.95, 0.55), (0, -0.85, z0 + 6.9 + i * 0.72), BL if i % 2 else BN, radius=0.15))
    for i, (z, w, d) in enumerate(((z0 + 7.7, 3.4, 2.2), (z0 + 8.6, 4.0, 2.5), (z0 + 9.5, 4.4, 2.6), (z0 + 10.35, 4.6, 2.6))):
        col = BN if i % 2 else BL
        t = 0.5
        P += [R(f"SkRibBack{i}", (w, t, 0.55), (0, -d / 2 + t / 2, z), col, radius=0.15),
              R(f"SkRibSideL{i}", (t, d - 2 * t + 0.02, 0.55), (-w / 2 + t / 2, 0, z), col, radius=0.15),
              R(f"SkRibSideR{i}", (t, d - 2 * t + 0.02, 0.55), (w / 2 - t / 2, 0, z), col, radius=0.15)]
        for sx in (-1, 1):
            P.append(R(f"SkRibFront{i}{sx}", (w / 2 - 0.4, t, 0.55), (sx * (w / 4 + 0.2), d / 2 - t / 2, z - 0.15), col, radius=0.15,
                       rot=(0, math.radians(-sx * 8), 0)))
    P += [R("SkSternum", (0.9, 0.6, 3.6), (0, 1.15, z0 + 7.6), BD, radius=0.2),
          R("SkCollar", (6.2, 1.8, 0.85), (0, 0, z0 + 10.95), BN, radius=0.3)]
    zs = z0 + 11.4
    P += [B("SkShoulderL", (0.85, 0.85, 0.85), (-3.1, 0, zs), BL, segments=12, rings=8),
          B("SkShoulderR", (0.85, 0.85, 0.85), (3.1, 0, zs), BL, segments=12, rings=8)]
    # right arm raised with the trophy; left fist on hip
    P += cartoon_bone("SkHumerusR", (3.2, 0, zs + 0.4), (4.2, 0.25, zs + 2.6), 0.45, BN)
    P += cartoon_bone("SkForearmR", (4.2, 0.25, zs + 2.7), (3.9, 0.45, zs + 4.9), 0.4, BN)
    P += cartoon_bone("SkHumerusL", (-3.2, 0, zs - 0.3), (-4.6, 0.3, zs - 2.2), 0.45, BN)
    P += cartoon_bone("SkForearmL", (-4.6, 0.3, zs - 2.3), (-3.2, 0.7, zs - 3.9), 0.4, BN)
    P += [R("SkHandR", (1.4, 1.3, 1.4), (3.9, 0.45, zs + 5.0), BL, radius=0.3),
          R("SkThumbR", (0.45, 0.5, 0.8), (3.1, 0.75, zs + 5.3), BL, radius=0.15, rot=(0, math.radians(20), 0)),
          R("SkFistL", (1.3, 1.3, 1.3), (-2.9, 0.75, zs - 4.75), BL, radius=0.3)]
    P += trophy("Trophy", (3.9, 0.45, zs + 6.25), 1.15)
    # neck + big skull head
    P += [C("SkNeck", 0.6, 0.6, 0.9, (0, -0.2, zs + 0.2), BD, sides=10)]
    hz = zs + 0.9
    HW, HD, HH = 5.8, 4.9, 5.0
    P += [R("SkSkull", (HW, HD, HH), (0, 0, hz), BN, radius=0.9),
          R("SkSkullCap", (HW - 1.0, HD - 1.0, 0.5), (0, 0, hz + HH - 0.15), BL, radius=0.2),
          R("SkCheekL", (1.4, 1.2, 1.3), (-2.4, 1.6, hz + 0.6), BL, radius=0.4),
          R("SkCheekR", (1.4, 1.2, 1.3), (2.4, 1.6, hz + 0.6), BL, radius=0.4)]
    fy = HD / 2
    for sx in (-1, 1):  # big friendly eyes in dark sockets, looking up at the trophy
        ex = sx * 1.35
        P += [face_piece(f"SkSocket{sx}", ellipse(1.05, 1.2, 18), 0.12, "#2A2440", fy, hz + 2.75, ex),
              face_piece(f"SkEye{sx}", ellipse(0.8, 0.95, 18), 0.1, "#FFFFFF", fy + 0.12, hz + 2.8, ex),
              face_piece(f"SkPupil{sx}", ellipse(0.42, 0.5, 14), 0.08, INK, fy + 0.22, hz + 3.05, ex + 0.22),
              face_piece(f"SkSparkle{sx}", ellipse(0.16, 0.16, 8), 0.06, "#FFFFFF", fy + 0.3, hz + 3.3, ex + 0.38),
              R(f"SkBrow{sx}", (1.5, 0.5, 0.45), (ex, fy - 0.05, hz + 4.05), BD, radius=0.15, rot=(0, math.radians(-sx * 12), 0)),
              face_piece(f"SkBlush{sx}", ellipse(0.55, 0.3, 12), 0.06, "#FF8FB1", fy + 0.02, hz + 1.55, sx * 2.05)]
    P.append(face_piece("SkNose", [(-0.38, 0.35), (0.38, 0.35), (0, -0.25)], 0.1, "#2A2440", fy, hz + 1.85))
    smile = [(-1.9, 0.0), (1.9, 0.0)] + [(math.cos(math.radians(a)) * 1.9, -math.sin(math.radians(a)) * 1.15)
                                          for a in range(10, 171, 20)]
    smile = [smile[0]] + [smile[1]] + smile[2:]
    P.append(face_piece("SkMouth", [(-1.95, 0.05), (1.95, 0.05)] + [(math.cos(math.radians(a)) * 1.95, -math.sin(math.radians(a)) * 1.2)
                                                                  for a in range(15, 166, 15)], 0.1, "#2A2440", fy, hz + 1.25))
    for t in range(6):  # top teeth row inside the grin
        tx = -1.45 + t * 0.58
        P.append(face_piece(f"SkTooth{t}", rect(0.48, 0.42), 0.08, "#FFFFFF", fy + 0.1, hz + 1.03, tx))
    P.append(face_piece("SkTongue", ellipse(0.62, 0.32, 12), 0.06, "#FF6F91", fy + 0.1, hz + 0.45, 0.2))
    # bandage cross on the forehead (it's the bone game) + gold medal on the chest
    for k, ang in enumerate((35, -35)):
        b = R(f"SkBandage{k}", (2.2, 0.25, 0.6), (0, 0, 0), "#F2C9A0", radius=0.08)
        xf([b], T(-1.9, fy + 0.02 + k * 0.03, hz + 4.25) @ Ry(ang))
        P.append(b)
    P.append(R("SkBandagePad", (0.7, 0.3, 0.6), (-1.9, fy + 0.1, hz + 3.95), "#FFE3C7", radius=0.08))
    P += [beam("SkRibbonL", (-1.0, 1.0, z0 + 11.3), (-0.15, 1.5, z0 + 9.4), 0.6, 0.15, ORANGE["base"]),
          beam("SkRibbonR", (1.0, 1.0, z0 + 11.3), (0.15, 1.5, z0 + 9.4), 0.6, 0.15, ORANGE["dark"]),
          face_piece("SkMedal", ellipse(0.95, 0.95, 18), 0.25, GOLDS["base"], 1.5, z0 + 8.75),
          face_piece("SkMedalStar", star_pts(0.6, 0.27), 0.1, GOLDS["light"], 1.75, z0 + 8.75)]
    att = {"PromptAnchor": T(0, 7.5, 2.0)}
    return name, P, att


# ================================================================================================
# (b) Egg stand
# ================================================================================================

def egg_stand():
    name = "EggStand"
    A = ACCENT_HEX
    P = []
    P += [C("ESBase", 5.8, 5.6, 0.8, (0, 0, 0), ST["dark"], sides=12),
          C("ESDeck", 5.2, 5.2, 0.4, (0, 0, 0.8), CREAM["base"], sides=12),
          tube("ESDeckTrim", 5.45, 5.45, 0.3, 0.3, (0, 0, 0.85), A, sides=12)]
    for i in range(12):  # little rim posts with gold caps
        a = math.radians(15 + 30 * i)
        if 60 < (15 + 30 * i) < 120:
            continue  # leave the front open
        P += [S(f"ESRimPost{i}", (0.55, 0.55, 0.9), (math.cos(a) * 5.0, math.sin(a) * 5.0, 1.2), WOOD["dark"]),
              B(f"ESRimCap{i}", (0.3, 0.3, 0.3), (math.cos(a) * 5.0, math.sin(a) * 5.0, 2.2), GOLDS["base"], segments=8, rings=5)]
    # front step
    P += [S("ESStep", (4.0, 1.4, 0.45), (0, 5.8, 0), ST["base"])]
    # display pedestal: column + cradle ring + bone prongs; egg sits at EggSpot
    P += [C("ESColumn", 2.0, 1.6, 1.6, (0, 0, 1.2), WOOD["base"], sides=12),
          tube("ESColumnBand", 2.05, 2.05, 0.35, 0.3, (0, 0, 1.6), GOLDS["dark"], sides=12),
          C("ESCup", 1.8, 2.8, 0.8, (0, 0, 2.8), CREAM["light"], sides=16),
          tube("ESRing", 3.4, 3.4, 0.6, 0.65, (0, 0, 3.3), A, sides=20),
          N(tube("ESRingGlow", 2.8, 2.8, 0.2, 0.25, (0, 0, 3.75), "#FFF3A0", sides=20), 3)]
    for i in range(4):  # bone-shaped prongs holding the egg
        a = math.radians(45 + 90 * i)
        p0 = Vector((math.cos(a) * 2.9, math.sin(a) * 2.9, 3.6))
        p1 = Vector((math.cos(a) * 2.5, math.sin(a) * 2.5, 5.0))
        P += cartoon_bone(f"ESProng{i}", p0, p1, 0.22, BONES["base"])
    # sign arch behind the egg: 2 posts + beam + sign board + gable roof
    by = -3.6
    for sx in (-1, 1):
        x = sx * 4.4
        P += [S(f"ESPostFoot{sx}", (1.5, 1.5, 0.6), (x, by, 1.2), ST["base"]),
              S(f"ESPost{sx}", (1.0, 1.0, 9.0), (x, by, 1.8), WOOD["base"]),
              S(f"ESPostBand{sx}", (1.15, 1.15, 0.4), (x, by, 4.6), A),
              S(f"ESPostBand2{sx}", (1.15, 1.15, 0.4), (x, by, 7.6), A),
              # lamp arm + glowing lantern facing the egg
              S(f"ESLampArm{sx}", (0.3, 1.6, 0.3), (x, by + 0.9, 8.3), INK),
              R(f"ESLantern{sx}", (0.8, 0.8, 0.9), (x, by + 1.7, 7.5), INK, radius=0.12),
              N(R(f"ESLanternGlow{sx}", (0.55, 0.55, 0.6), (x, by + 1.7, 7.65), "#FFE7B0", radius=0.1, studs="none"), 4)]
    P += [S("ESBeam", (10.0, 1.2, 0.8), (0, by, 10.0), WOOD["dark"]),
          S("ESSign", (8.6, 0.6, 3.4), (0, by, 10.8), NAVY),
          S("ESSignFrameT", (9.2, 0.8, 0.35), (0, by, 14.2), A),
          S("ESSignFrameB", (9.2, 0.8, 0.35), (0, by, 10.6), A),
          S("ESSignFrameL", (0.35, 0.8, 3.5), (-4.45, by, 10.7), A),
          S("ESSignFrameR", (0.35, 0.8, 3.5), (4.45, by, 10.7), A)]
    sy = by + 0.3
    # egg icon on the sign: egg outline + zigzag crack + sparkles
    egg = [(math.cos(math.radians(a)) * 1.05, (math.sin(math.radians(a)) * (1.45 if math.sin(math.radians(a)) > 0 else 1.1)))
           for a in range(0, 360, 20)]
    P += [face_piece("ESIconEgg", egg, 0.15, CREAM["light"], sy, 12.5),
          face_piece("ESIconBand", [(-1.0, -0.15), (-0.5, 0.2), (0, -0.15), (0.5, 0.2), (1.0, -0.15), (1.0, -0.45), (-1.0, -0.45)],
                     0.1, A, sy + 0.15, 12.45)]
    for k, (x, z, r) in enumerate(((-2.6, 13.2, 0.45), (2.5, 11.8, 0.4), (-2.2, 11.6, 0.3), (2.9, 13.3, 0.3))):
        P.append(face_piece(f"ESIconSpark{k}", star_pts(r, r * 0.4, 4, 90), 0.1, GOLDS["base"], sy, z, x, glow=2))
    # gable roof over the sign (accent slabs + ridge + scallops)
    for sx in (-1, 1):
        sl = S(f"ESRoof{sx}", (5.6, 2.6, 0.45), (0, 0, 0), A)
        xf([sl], T(sx * 2.45, by, 14.55) @ Ry(sx * 18))
        P.append(sl)
    P += [S("ESRidge", (1.0, 2.8, 0.6), (0, by, 15.35), GOLDS["dark"]),
          B("ESRidgeBall", (0.6, 0.6, 0.6), (0, by, 16.3), GOLDS["base"], segments=12, rings=8)]
    for i in range(10):
        x = -4.6 + i * 1.02
        z = 14.55 + (2.45 - abs(x)) * math.tan(math.radians(18)) - 0.35
        P.append(B(f"ESScallop{i}", (0.42, 0.2, 0.32), (x, by + 1.35, z), CREAM["base"] if i % 2 else A, segments=10, rings=6))
    # side props: rope stanchions guiding the queue + a crate of straw
    for sx in (-1, 1):
        x = sx * 3.2
        P += [C(f"ESStanchion{sx}", 0.25, 0.25, 2.0, (x, 4.6, 1.2), GOLDS["dark"], sides=8),
              B(f"ESStanchionTop{sx}", (0.32, 0.32, 0.32), (x, 4.6, 3.3), GOLDS["light"], segments=8, rings=5)]
        P.append(beam(f"ESRope{sx}", (x, 4.6, 2.9), (sx * 4.9, 2.4, 2.4), 0.22, 0.22, CORAL["base"], kind="cyl", sides=8))
    att = {"EggSpot": T(0, 0, 4.0), "PromptAnchor": T(0, 5.5, 1.5)}
    return name, P, att


# ================================================================================================
# (c) Cannon shop + upgrade stand
# ================================================================================================

def cannon_icon(prefix, y, z, x=0.0, s=1.0, body=GOLD, wheel="#FF8A1F"):
    """Flat cannon silhouette (tilted barrel + wheel + muzzle burst) on a +Y face."""
    P = []
    barrel = [(-1.6 * s, -0.5 * s), (1.4 * s, -0.65 * s), (1.4 * s, 0.65 * s), (-1.6 * s, 0.5 * s)]
    a = math.radians(25)
    rot = [(u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a)) for u, v in barrel]
    P.append(face_piece(f"{prefix}Barrel", rot, 0.15, body, y, z + 0.4 * s, x))
    mx, mz = 1.4 * s * math.cos(a), 1.4 * s * math.sin(a)
    P.append(face_piece(f"{prefix}Muzzle", rect(0.35 * s, 1.5 * s), 0.18, SH(body)["dark"], y, z + 0.4 * s + mz - 0.1 * s, x + mx))
    P.append(face_piece(f"{prefix}Wheel", circle_pts(0.75 * s, 14), 0.2, wheel, y + 0.05, z - 0.35 * s, x - 0.3 * s))
    P.append(face_piece(f"{prefix}Hub", circle_pts(0.25 * s, 8), 0.1, INK, y + 0.2, z - 0.35 * s, x - 0.3 * s))
    P.append(face_piece(f"{prefix}Boom", star_pts(0.85 * s, 0.4 * s, 7, 0), 0.12, "#FF5FA2", y, z + 1.55 * s, x + 2.0 * s, glow=2.5))
    return P


def bone_arrow_icon(prefix, y, z, x=0.0, s=1.0, bone=BONE, arrow="#A8F03C", glow=3.0):
    """Bone (tilted) with a big up-arrow — the Upgrade icon — on a +Y face."""
    P = bone_icon(f"{prefix}Bone", 0.8 * s, bone, 0.18)
    xf(P, T(x - 0.3 * s, y + 0.1, z) @ Ry(-35))
    for o in P:
        o["vault_stud_mode"] = "none"
    arrowp = [(-0.45, 0), (0.45, 0), (0.45, 1.2), (1.0, 1.2), (0, 2.3), (-1.0, 1.2), (-0.45, 1.2)]
    P.append(face_piece(f"{prefix}Arrow", [(u * s, v * s) for u, v in arrowp], 0.16, arrow, y + 0.15, z - 1.0 * s, x + 1.1 * s, glow=glow))
    return P


def cannon_shop():
    name = "CannonShop"
    P = []
    W, D = 12.0, 9.0
    # deck + step + skirt
    P += [S("CSDeck", (W, D, 0.7), (0, 0, 0), WOOD["dark"]),
          S("CSDeckTop", (W - 0.4, D - 0.4, 0.2), (0, 0, 0.7), WOOD["base"]),
          S("CSStep", (5.0, 1.3, 0.4), (0, D / 2 + 0.6, 0), ST["base"])]
    # back wall in plank courses (2 shades) + side half walls
    for i in range(6):
        P.append(S(f"CSBackPlank{i}", (W - 1.0, 0.8, 1.3), (0, -D / 2 + 0.9, 0.9 + i * 1.3), WOOD["base"] if i % 2 else WOOD["light"]))
    for sx in (-1, 1):
        for i in range(3):
            P.append(S(f"CSSidePlank{sx}{i}", (0.8, D - 2.4, 1.2), (sx * (W / 2 - 0.9), -0.3, 0.9 + i * 1.2),
                       WOOD["light"] if i % 2 else WOOD["base"]))
    # corner posts (chunky, with orange collars)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.6), sy * (D / 2 - 0.6)
            P += [S(f"CSPost{sx}{sy}", (1.0, 1.0, 7.6), (x, y, 0.9), WOOD["deep"]),
                  S(f"CSPostCollar{sx}{sy}", (1.2, 1.2, 0.4), (x, y, 3.8), ORANGE["base"]),
                  S(f"CSPostFoot{sx}{sy}", (1.3, 1.3, 0.5), (x, y, 0.9), ST["dark"])]
    # counter: orange body + cream top + 3 framed panels, centre one with the cannon icon
    cy = D / 2 - 2.0
    P += [S("CSCounter", (W - 2.6, 1.6, 3.0), (0, cy, 0.9), ORANGE["base"]),
          S("CSCounterTop", (W - 2.2, 2.1, 0.4), (0, cy + 0.1, 3.9), CREAM["base"]),
          S("CSCounterKick", (W - 2.4, 1.7, 0.35), (0, cy + 0.02, 0.9), ORANGE["deep"])]
    for k, x in enumerate((-3.3, 0.0, 3.3)):
        P += [face_piece(f"CSPanelFrame{k}", rect(2.8, 2.0), 0.1, ORANGE["light"], cy + 0.8, 2.55, x),
              face_piece(f"CSPanel{k}", rect(2.4, 1.6), 0.1, ORANGE["dark"], cy + 0.9, 2.55, x)]
    P += cannon_icon("CSPanelIcon", cy + 1.0, 2.35, -0.25, 0.42)
    for k, x in enumerate((-3.3, 3.3)):
        P += bone_icon(f"CSPanelBone{k}", 0.4, BONES["base"], 0.12)
        xf(P[-5:], T(x, cy + 1.05, 2.55) @ Ry(20 if k else -20))
    # register + bell on the counter, price tag stand
    P += [R("CSRegister", (1.4, 1.0, 0.9), (2.8, cy, 4.3), "#5B6B82", radius=0.12),
          N(S("CSRegisterScreen", (1.0, 0.1, 0.4), (2.8, cy + 0.5, 4.75), "#A8F03C", studs="none"), 2.5),
          C("CSBellBase", 0.35, 0.35, 0.12, (-3.0, cy, 4.3), INK, sides=10),
          B("CSBell", (0.32, 0.32, 0.3), (-3.0, cy, 4.42), GOLDS["base"], segments=10, rings=6)]
    # display shelf on the back wall with mini cannons (something visible inside)
    P += [S("CSShelf", (8.0, 1.2, 0.35), (0, -D / 2 + 1.7, 4.4), WOOD["deep"])]
    for k, x in enumerate((-2.8, 0.0, 2.8)):
        col = (("#D98B3A", "#B5733A", "#E13A2A"))[k]
        mb = C(f"CSMiniBarrel{k}", 0.4, 0.5, 1.6, (0, 0, 0), col, sides=12)
        xf([mb], T(x, -D / 2 + 1.5, 4.95) @ Rx(-65))
        P += [mb, C(f"CSMiniWheel{k}a", 0.35, 0.35, 0.2, (x - 0.5, -D / 2 + 1.7, 5.1), INK, sides=10, rot=(0, math.radians(90), 0)),
              C(f"CSMiniWheel{k}b", 0.35, 0.35, 0.2, (x + 0.3, -D / 2 + 1.7, 5.1), INK, sides=10, rot=(0, math.radians(90), 0))]
    # roof: two slabs, ridge, eave trims
    for sy in (-1, 1):
        sl = S(f"CSRoof{sy}", (W + 1.4, 5.6, 0.55), (0, 0, 0), "#E13A2A" if sy > 0 else "#B6261D")
        xf([sl], T(0, sy * 2.45, 9.25) @ Rx(-sy * 20))
        P.append(sl)
        P.append(S(f"CSEave{sy}", (W + 1.6, 0.6, 0.5), (0, sy * 5.1, 8.05), CREAM["base"]))
    P += [S("CSRidge", (W + 1.6, 1.0, 0.7), (0, 0, 10.25), GOLDS["dark"])]
    for sx in (-1, 1):  # gable end triangles (no blank gaps)
        P.append(prism(f"CSGable{sx}", [(-4.4, 0), (4.4, 0), (0, 1.6)], 0.5, WOOD["light"], plane="yz", loc=(sx * (W / 2 - 0.2), 0, 8.4)))
    # striped awning (SNAP orange + cream) over the counter
    P += kit.striped_awning("CSAwning", -W / 2 + 0.8, W / 2 - 0.8, D / 2 - 0.2, 7.0, depth=2.2, tilt=24, colors=(SNAP, "#FFF6EA"))
    # big sign on the roof front: navy board, gold frame, cannon icon, bulbs
    sy_ = D / 2 - 1.6
    P += [S("CSSignBoard", (7.2, 0.5, 3.0), (0, sy_, 10.3), NAVY),
          S("CSSignFrameT", (7.8, 0.7, 0.35), (0, sy_, 13.3), GOLDS["base"]),
          S("CSSignFrameB", (7.8, 0.7, 0.35), (0, sy_, 9.95), GOLDS["base"]),
          S("CSSignFrameL", (0.35, 0.7, 3.0), (-3.75, sy_, 10.3), GOLDS["base"]),
          S("CSSignFrameR", (0.35, 0.7, 3.0), (3.75, sy_, 10.3), GOLDS["base"]),
          S("CSSignLegL", (0.4, 0.4, 2.0), (-2.5, sy_ - 0.4, 9.2), INK),
          S("CSSignLegR", (0.4, 0.4, 2.0), (2.5, sy_ - 0.4, 9.2), INK)]
    P += cannon_icon("CSSignIcon", sy_ + 0.25, 11.4, -0.6, 0.85)
    for k in range(8):
        x = -3.4 + k * (6.8 / 7)
        P.append(N(B(f"CSBulb{k}", (0.17, 0.17, 0.17), (x, sy_ + 0.42, 13.48), "#FFE45C", segments=8, rings=5, studs="none"), 4))
    # rooftop prop: chunky display cannon on the ridge (silhouette feature)
    rb = [C("CSTopBarrel", 0.85, 1.0, 3.2, (0, 0, 0), "#4A5260", sides=14),
          tube("CSTopMuzzle", 1.15, 1.15, 0.5, 0.45, (0, 0, 3.0), GOLDS["base"], sides=14),
          C("CSTopBack", 0.6, 0.6, 0.5, (0, 0, -0.45), "#4A5260", sides=12)]
    xf(rb, T(-3.0, -1.0, 12.0) @ Rx(-60))
    P += rb
    for sx in (-1, 1):
        P += [xf([tube(f"CSTopWheel{sx}", 0.95, 0.95, 0.35, 0.3, (0, 0, -0.17), "#8A5530", sides=14)], T(-3.0 + sx * 1.15, -1.0, 11.5) @ Ry(90))[0],
              C(f"CSTopHub{sx}", 0.3, 0.3, 0.4, (-3.0 + sx * 1.3, -1.0, 11.5), INK, sides=8, rot=(0, math.radians(90), 0))]
    P.append(S("CSTopCart", (2.0, 2.2, 0.5), (-3.0, -1.0, 10.95), "#8A5530"))
    # side props: cannonball pyramid + powder barrel + hazard crate
    rnd = random.Random(3)
    k = 0
    for layer, n in enumerate((3, 2, 1)):
        for i in range(n):
            for j in range(n):
                x = -W / 2 - 1.8 + (i - (n - 1) / 2) * 0.95
                y = 2.8 + (j - (n - 1) / 2) * 0.95
                P.append(B(f"CSBall{k}", (0.5, 0.5, 0.5), (x, y, 0.5 + layer * 0.72), "#3B4554" if k % 3 else "#5B6B82", segments=10, rings=6))
                k += 1
    P += [C("CSPowder", 0.9, 0.9, 1.8, (W / 2 + 1.6, 2.6, 0), "#B5733A", sides=12),
          tube("CSPowderHoop0", 0.95, 0.95, 0.25, 0.1, (W / 2 + 1.6, 2.6, 0.35), "#4A5260", sides=12),
          tube("CSPowderHoop1", 0.95, 0.95, 0.25, 0.1, (W / 2 + 1.6, 2.6, 1.3), "#4A5260", sides=12),
          S("CSCrate", (1.8, 1.8, 1.6), (W / 2 + 1.5, 0.2, 0), WOOD["light"], rot=(0, 0, math.radians(12))),
          S("CSCrateHaz", (1.9, 0.5, 0.5), (W / 2 + 1.5, 0.2, 0.6), "#FFC21A", rot=(0, 0, math.radians(12)))]
    # wall poster on the outside of the left half wall
    pst = [face_piece("CSPoster", rect(3.0, 2.4), 0.12, "#FFF6EA", 0, 0),
           face_piece("CSPosterBand", rect(3.0, 0.5), 0.06, "#E13A2A", 0.12, 0.95)]
    pst += cannon_icon("CSPosterIcon", 0.14, -0.35, -0.3, 0.45, body="#5B6B82", wheel="#E13A2A")
    xf(pst, T(-W / 2 + 0.45, -0.4, 2.0) @ Rz(90))
    P += pst
    # hanging lamps on the front posts
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.6)
        P += [S(f"CSLampArm{sx}", (0.25, 1.3, 0.25), (x, D / 2 + 0.2, 7.2), INK),
              R(f"CSLamp{sx}", (0.7, 0.7, 0.8), (x, D / 2 + 0.75, 6.4), INK, radius=0.1),
              N(R(f"CSLampGlow{sx}", (0.5, 0.5, 0.55), (x, D / 2 + 0.75, 6.52), "#FFE7B0", radius=0.08, studs="none"), 4)]
    att = {"PromptAnchor": T(0, D / 2 + 0.5, 2.5)}
    return name, P, att


def upgrade_stand():
    name = "UpgradeStand"
    P = []
    # round platform + steps
    P += [C("USBase", 6.0, 5.8, 0.8, (0, 0, 0), ST["dark"], sides=16),
          C("USDeck", 5.4, 5.4, 0.35, (0, 0, 0.8), CREAM["base"], sides=16),
          tube("USDeckTrim", 5.6, 5.6, 0.3, 0.3, (0, 0, 0.82), TEAL["base"], sides=16),
          S("USStep", (4.0, 1.3, 0.45), (0, 6.1, 0), ST["base"])]
    # half-round counter (front arc), top ring, coral band
    P += [tube("USCounter", 4.2, 4.2, 3.0, 1.0, (0, 0, 1.15), TEAL["base"], sides=24, a0=20, a1=160),
          tube("USCounterBand", 4.32, 4.32, 0.6, 0.3, (0, 0, 2.2), CORAL["base"], sides=24, a0=20, a1=160),
          tube("USCounterTop", 4.5, 4.5, 0.35, 1.6, (0, 0, 4.15), CREAM["light"], sides=24, a0=16, a1=164)]
    for k, a in enumerate((50, 90, 130)):  # medical-cross / bone badges on the counter front
        ar = math.radians(a)
        badge = [face_piece(f"USBadge{k}", circle_pts(0.75, 16), 0.12, "#FFFFFF", 0, 0)]
        if k == 1:
            badge += bone_arrow_icon(f"USBadgeIcon{k}", 0.12, -0.05, 0.0, 0.32, glow=2)
        else:
            badge += [face_piece(f"USCrossV{k}", rect(0.3, 0.95), 0.08, CORAL["base"], 0.12, 0),
                      face_piece(f"USCrossH{k}", rect(0.95, 0.3), 0.08, CORAL["base"], 0.12, 0)]
        xf(badge, T(math.cos(ar) * 4.42, math.sin(ar) * 4.42, 3.0) @ Rz(a - 90))
        P += badge
    # back shelving arc: milk bottles (calcium!) + bone pile + X-ray lightbox
    P += [tube("USBackWall", 4.6, 4.6, 6.0, 0.6, (0, 0, 1.15), CREAM["base"], sides=24, a0=200, a1=340),
          tube("USShelf", 4.0, 4.0, 0.3, 1.0, (0, 0, 3.6), WOOD["dark"], sides=24, a0=210, a1=330)]
    rnd = random.Random(5)
    for k in range(7):
        a = math.radians(215 + k * 16.5)
        x, y = math.cos(a) * 3.55, math.sin(a) * 3.55
        P += [C(f"USMilk{k}", 0.3, 0.3, 0.8, (x, y, 3.9), "#FFFFFF", sides=10),
              C(f"USMilkNeck{k}", 0.18, 0.18, 0.3, (x, y, 4.7), "#FFFFFF", sides=8),
              C(f"USMilkCap{k}", 0.22, 0.22, 0.14, (x, y, 5.0), (CORAL["base"], TEAL["base"], GOLD)[k % 3], sides=8),
              tube(f"USMilkLabel{k}", 0.32, 0.32, 0.25, 0.05, (x, y, 4.2), (CORAL["base"], TEAL["base"], GOLD)[k % 3], sides=10)]
    xr = [face_piece("USXrayFrame", rect(3.2, 2.4), 0.2, "#2E3440", 0, 0),
          face_piece("USXray", rect(2.8, 2.0), 0.08, "#9FE8FF", 0.2, 0.2, glow=2.0)]
    xr += [face_piece("USXrayBone", rect(1.9, 0.32), 0.05, "#FFFFFF", 0.3, 1.05, 0, glow=3),
           face_piece("USXrayKnobA", circle_pts(0.28, 10), 0.05, "#FFFFFF", 0.3, 1.0, -1.0, glow=3),
           face_piece("USXrayKnobB", circle_pts(0.28, 10), 0.05, "#FFFFFF", 0.3, 1.0, 1.0, glow=3)]
    xf(xr, T(0, -3.95, 5.3))
    P += xr
    # canopy: striped cone in arc segments + scalloped valance + bone finial
    for i in range(12):
        col = TEAL["base"] if i % 2 == 0 else "#FFF6EA"
        P.append(tube(f"USCanopy{i}", 6.3, 0.9, 2.4, 0.4, (0, 0, 8.4), col, sides=48, a0=i * 30, a1=(i + 1) * 30))
    for i in range(24):
        a = math.radians(i * 15 + 7.5)
        P.append(B(f"USScallop{i}", (0.55, 0.3, 0.4), (math.cos(a) * 6.15, math.sin(a) * 6.15, 8.2), CORAL["base"] if i % 2 else "#FFF6EA",
                   segments=10, rings=6, rot=(0, 0, a + math.pi / 2)))
    P += [C("USCanopyCap", 1.0, 0.6, 0.6, (0, 0, 10.7), CORAL["base"], sides=12)]
    # canopy posts (2 back posts + centre pole) — the back wall carries it
    for sx in (-1, 1):
        a = math.radians(270 + sx * 55)
        P += [C(f"USPost{sx}", 0.4, 0.4, 7.8, (math.cos(a) * 4.9, math.sin(a) * 4.9, 1.15), WOOD["deep"], sides=10),
              tube(f"USPostRing{sx}", 0.5, 0.5, 0.3, 0.12, (math.cos(a) * 4.9, math.sin(a) * 4.9, 4.4), CORAL["base"], sides=10)]
    # tower sign rising behind: tall teal panel with the bone + up-arrow icon, coral frame
    ty = -7.0
    P += [S("USTowerFoot", (3.4, 2.0, 1.8), (0, ty, 0), ST["base"]),
          S("USTower", (2.6, 1.0, 13.5), (0, ty, 1.8), TEAL["dark"]),
          S("USTowerFace", (3.8, 0.7, 4.6), (0, ty + 0.5, 11.0), TEAL["base"]),
          S("USTowerFrameT", (4.3, 0.9, 0.4), (0, ty + 0.5, 15.6), CORAL["base"]),
          S("USTowerFrameB", (4.3, 0.9, 0.4), (0, ty + 0.5, 10.6), CORAL["base"]),
          S("USTowerFrameL", (0.4, 0.9, 4.6), (-2.05, ty + 0.5, 11.0), CORAL["base"]),
          S("USTowerFrameR", (0.4, 0.9, 4.6), (2.05, ty + 0.5, 11.0), CORAL["base"]),
          B("USTowerBall", (0.55, 0.55, 0.55), (0, ty + 0.5, 16.45), GOLDS["base"], segments=12, rings=8)]
    P += bone_arrow_icon("USTowerIcon", ty + 0.85, 13.1, 0.0, 1.0, glow=3)
    for k in range(5):  # chevrons climbing the tower (upgrade = go up)
        P.append(face_piece(f"USTowerChev{k}", [(-0.9, 0), (0, 0.7), (0.9, 0), (0.9, 0.4), (0, 1.1), (-0.9, 0.4)], 0.12,
                            "#A8F03C" if k % 2 else "#FFF6EA", ty + 0.5, 4.2 + k * 1.2, glow=2 if k % 2 else 0))
    # bone pile beside the stand (story: spare bones)
    for k in range(5):
        a = rnd.uniform(0, math.pi)
        p0 = Vector((5.8 + rnd.uniform(-0.8, 0.8), 2.8 + rnd.uniform(-0.8, 0.8), 0.3 + k * 0.18))
        d = Vector((math.cos(a), math.sin(a), rnd.uniform(-0.1, 0.1))) * 1.0
        P += cartoon_bone(f"USPile{k}", p0 - d, p0 + d, 0.2, BONES["base"] if k % 2 else BONES["light"])
    att = {"PromptAnchor": T(0, 5.6, 2.5)}
    return name, P, att


# ================================================================================================
# (d) Season board, (e) Leaderboard, (f) Daily chest
# ================================================================================================

def season_board():
    name = "SeasonBoard"
    P = []
    W, H, zb = 13.0, 8.0, 3.2
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.7)
        P += [S(f"SBFoot{sx}", (2.4, 2.4, 0.9), (x, 0, 0), ST["dark"]),
              S(f"SBFootCap{sx}", (2.0, 2.0, 0.4), (x, 0, 0.9), ST["base"]),
              S(f"SBPost{sx}", (1.3, 1.3, zb + H + 1.2 - 1.3), (x, 0, 1.3), WOOD["dark"]),
              S(f"SBPostBand{sx}", (1.5, 1.5, 0.4), (x, 0, 2.5), ICE["dark"]),
              S(f"SBPostCap{sx}", (1.7, 1.7, 0.5), (x, 0, zb + H + 1.2), ICE["base"]),
              R(f"SBPostSnow{sx}", (1.9, 1.9, 0.6), (x, 0, zb + H + 1.65), SNOW["base"], radius=0.25)]
    # board backing + frame + Screen
    P += [S("SBBacking", (W + 0.6, 0.7, H + 0.6), (0, -0.2, zb - 0.3), WOOD["base"]),
          S("SBFrameT", (W + 1.2, 1.1, 0.6), (0, 0, zb + H), ICE["base"]),
          S("SBFrameB", (W + 1.2, 1.1, 0.6), (0, 0, zb - 0.6), ICE["base"]),
          S("SBFrameL", (0.6, 1.1, H), (-W / 2 - 0.3, 0, zb), ICE["light"]),
          S("SBFrameR", (0.6, 1.1, H), (W / 2 + 0.3, 0, zb), ICE["light"]),
          S("Screen", (W, 0.1, H), (0, 0.2, zb), "#1E2340", studs="none")]
    P += bolts("SBBolt", [(sx * (W / 2 + 0.3), 0.6, zb + z) for sx in (-1, 1) for z in (0.4, H - 0.4)], "#D9DEE6", 0.2)
    # snow cap with drips along the top
    P += [R("SBSnowCap", (W + 2.0, 1.8, 0.8), (0, 0, zb + H + 0.55), SNOW["base"], radius=0.3)]
    rnd = random.Random(8)
    for i in range(9):
        x = -W / 2 + 0.4 + i * (W - 0.8) / 8 + rnd.uniform(-0.3, 0.3)
        h = rnd.uniform(0.5, 1.1)
        P.append(R(f"SBDrip{i}", (rnd.uniform(0.6, 1.0), 0.6, h), (x, 0.65, zb + H + 0.6 - h), SNOW["light"] if i % 2 else SNOW["dark"], radius=0.22))
    # crest: navy badge + ice ring + snowflake + ribbon banner
    cz = zb + H + 1.4
    P += [face_piece("SBCrestRing", circle_pts(2.0, 20), 0.5, ICE["dark"], 0.1, cz + 1.9),
          face_piece("SBCrest", circle_pts(1.65, 20), 0.2, NAVY, 0.6, cz + 1.9)]
    for k in range(3):
        arm = face_piece(f"SBFlakeArm{k}", rect(0.3, 2.4), 0.12, "#BFF3FF", 0, 0, glow=2.5)
        xf([arm], T(0, 0.8, cz + 1.9) @ Ry(60 * k))
        P.append(arm)
        for j in (-1, 1):
            tip = face_piece(f"SBFlakeTip{k}{j}", [(-0.35, 0), (0, 0.35), (0.35, 0), (0.35, 0.18), (0, 0.55), (-0.35, 0.18)], 0.12,
                             "#BFF3FF", 0, 0, glow=2.5)
            xf([tip], T(0, 0.8, cz + 1.9) @ Ry(60 * k + (0 if j > 0 else 180)) @ T(0, 0, 0.75))
            P.append(tip)
    P += [face_piece("SBBanner", [(-3.2, 0), (3.2, 0), (2.8, 0.45), (3.2, 0.9), (-3.2, 0.9), (-2.8, 0.45)], 0.3, "#E13A2A", 0.6, cz - 0.15),
          face_piece("SBBannerHi", rect(5.2, 0.18), 0.05, "#FF8A80", 0.9, cz + 0.6)]
    # lamps on arms lighting the board
    for sx in (-1, 1):
        x = sx * (W / 2 - 1.5)
        P += [S(f"SBLampArm{sx}", (0.25, 1.8, 0.25), (x, 0.9, zb + H + 0.2), INK),
              R(f"SBLampHood{sx}", (1.0, 0.7, 0.5), (x, 1.75, zb + H - 0.2), INK, radius=0.1),
              N(S(f"SBLampGlow{sx}", (0.8, 0.5, 0.1), (x, 1.75, zb + H - 0.25), "#FFF3C8", studs="none"), 4)]
    # rope coil + carabiner on the right post (mountain theme), ice block at the left foot
    px = W / 2 + 0.7
    for k in range(3):
        rope = tube(f"SBRope{k}", 0.8, 0.8, 0.25, 0.25, (0, 0, -0.12), "#FFB13B" if k % 2 else "#E28A1C", sides=14)
        xf([rope], T(px + 0.8, 0.1 + k * 0.1, 5.8 - k * 0.15) @ Ry(90) @ Rx(10 * k))
        P.append(rope)
    cara = tube("SBCarabiner", 0.45, 0.45, 0.2, 0.14, (0, 0, -0.1), "#B678EA", sides=12, a0=40, a1=360)
    xf([cara], T(px + 0.8, 0.2, 6.7) @ Ry(90))
    P += [cara, S("SBHook", (0.6, 0.3, 0.3), (px + 0.55, 0, 6.9), INK)]
    P += [R("SBIce0", (1.6, 1.4, 1.2), (-px - 1.8, 0.8, 0), ICE["light"], radius=0.2, rot=(0, 0, 0.3)),
          R("SBIce1", (1.0, 0.9, 0.8), (-px - 1.3, 1.9, 0), ICE["base"], radius=0.15, rot=(0, 0, -0.4))]
    # back: cross braces so the back is not blank
    for k, ang in enumerate((28, -28)):
        br = S(f"SBBrace{k}", (W + 1.0, 0.4, 0.7), (0, 0, 0), WOOD["dark"])
        xf([br], T(0, -0.75, zb + H / 2 - 0.35) @ Ry(ang))
        P.append(br)
    P.append(S("SBBackRail", (W + 0.6, 0.4, 0.6), (0, -0.75, zb + H / 2 - 0.3), WOOD["light"]))
    return name, P, {}


def leaderboard():
    name = "Leaderboard"
    P = []
    # podium 2-1-3
    steps = ((-3.2, 2.2, "#C9D3DD", 2), (0.0, 3.2, GOLD, 1), (3.2, 1.5, "#D9874A", 3))
    P += [S("LBBase", (11.4, 5.6, 0.5), (0, 0.6, 0), ST["dark"])]
    for x, h, col, place in steps:
        sh = SH(col)
        P += [S(f"LBStep{place}", (3.2, 3.6, h), (x, 1.2, 0.5), sh["base"]),
              S(f"LBStepCap{place}", (3.5, 3.9, 0.35), (x, 1.2, 0.5 + h), sh["light"]),
              face_piece(f"LBPlate{place}", rect(1.8, 1.0), 0.12, NAVY, 3.0, 0.5 + h * 0.5 - 0.5, x)]
        for k in range(place):  # place stars (1 gold / 2 silver / 3 bronze)
            sx = x + (k - (place - 1) / 2) * 0.55
            P.append(face_piece(f"LBStar{place}{k}", star_pts(0.26, 0.11), 0.06, sh["light"], 3.12, 0.5 + h * 0.5 - 0.5, sx))
    # board
    W, H, zb = 10.0, 8.0, 4.4
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.6)
        P += [S(f"LBPillar{sx}", (1.2, 1.2, zb + H + 0.6), (x, -1.2, 0.5), NAVY),
              N(S(f"LBPillarGlow{sx}", (0.25, 0.1, H - 0.6), (x, -0.58, zb + 0.3), "#FFD93B", studs="none"), 3),
              B(f"LBPillarBall{sx}", (0.6, 0.6, 0.6), (x, -1.2, zb + H + 1.6), GOLDS["base"], segments=12, rings=8)]
    P += [S("LBBacking", (W + 0.4, 0.6, H + 0.4), (0, -1.5, zb - 0.2), "#2A2F5A"),
          S("LBFrameT", (W + 0.8, 0.9, 0.5), (0, -1.2, zb + H), GOLDS["dark"]),
          S("LBFrameB", (W + 0.8, 0.9, 0.5), (0, -1.2, zb - 0.5), GOLDS["dark"]),
          S("LBFrameL", (0.4, 0.9, H), (-W / 2 - 0.2, -1.2, zb), GOLDS["base"]),
          S("LBFrameR", (0.4, 0.9, H), (W / 2 + 0.2, -1.2, zb), GOLDS["base"]),
          S("Screen", (W, 0.1, H), (0, -0.95, zb), "#1E2340", studs="none")]
    # topper: crossed bones behind a trophy on a header block
    P += [S("LBHeader", (6.0, 1.2, 1.2), (0, -1.2, zb + H + 0.5), "#2A2F5A"),
          S("LBHeaderTrim", (6.3, 1.3, 0.3), (0, -1.2, zb + H + 1.7), GOLDS["dark"])]
    for k, ang in enumerate((30, -30)):
        bi = bone_icon(f"LBCrossBone{k}", 1.2, BONES["base"] if k else BONES["light"], 0.4)
        xf(bi, T(0, -1.6 - k * 0.45, zb + H + 3.4) @ Ry(ang))
        P += bi
    P += trophy("LBTrophy", (0, -1.0, zb + H + 2.0), 0.9, gem="#3EF0FF")
    # rail chain posts at the podium front corners
    for sx in (-1, 1):
        P += [C(f"LBRailPost{sx}", 0.25, 0.25, 1.8, (sx * 5.3, 3.3, 0.5), GOLDS["dark"], sides=8),
              B(f"LBRailTop{sx}", (0.3, 0.3, 0.3), (sx * 5.3, 3.3, 2.4), GOLDS["light"], segments=8, rings=5)]
    # back of the board: braces
    for k, ang in enumerate((35, -35)):
        br = S(f"LBBrace{k}", (W + 0.2, 0.3, 0.6), (0, 0, 0), "#1E2340")
        xf([br], T(0, -1.95, zb + H / 2 - 0.3) @ Ry(ang))
        P.append(br)
    return name, P, {}


def daily_chest():
    name = "DailyChest"
    P = []
    Wc, Dc, Hc = 5.6, 3.8, 2.6
    LW = SH("#9A5A2C")
    # reward pad underneath
    P += [R("DCPad", (7.6, 6.0, 0.4), (0, 0, 0), "#B678EA", radius=0.15),
          tube("DCPadRing", 3.4, 3.4, 0.12, 0.3, (0, 0, 0.4), GOLD, sides=24)]
    z0 = 0.4
    # feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(B(f"DCFoot{sx}{sy}", (0.4, 0.4, 0.35), (sx * (Wc / 2 - 0.4), sy * (Dc / 2 - 0.4), z0 + 0.3), GOLDS["dark"], segments=10, rings=6))
    zb = z0 + 0.5
    # body core + plank courses on all 4 sides (3 rows, varied shades)
    P.append(S("DCCore", (Wc - 0.3, Dc - 0.3, Hc), (0, 0, zb), LW["deep"]))
    for i in range(3):
        col = (LW["base"], LW["light"], LW["dark"])[i]
        z = zb + i * Hc / 3
        P += [S(f"DCPlankF{i}", (Wc, 0.3, Hc / 3 - 0.06), (0, Dc / 2 - 0.15, z + 0.03), col),
              S(f"DCPlankB{i}", (Wc, 0.3, Hc / 3 - 0.06), (0, -Dc / 2 + 0.15, z + 0.03), col),
              S(f"DCPlankL{i}", (0.3, Dc - 0.6, Hc / 3 - 0.06), (-Wc / 2 + 0.15, 0, z + 0.03), col),
              S(f"DCPlankR{i}", (0.3, Dc - 0.6, Hc / 3 - 0.06), (Wc / 2 - 0.15, 0, z + 0.03), col)]
    # gold corner caps + bands
    for sx in (-1, 1):
        for sy in (-1, 1):
            P += [S(f"DCCornerPost{sx}{sy}", (0.55, 0.55, Hc + 0.05), (sx * (Wc / 2 - 0.1), sy * (Dc / 2 - 0.1), zb), GOLDS["base"]),
                  S(f"DCCornerCap{sx}{sy}", (0.75, 0.75, 0.35), (sx * (Wc / 2 - 0.1), sy * (Dc / 2 - 0.1), zb), GOLDS["dark"])]
    for sx in (-1, 1):
        x = sx * 1.6
        P += [S(f"DCBandF{sx}", (0.55, 0.18, Hc), (x, Dc / 2 + 0.05, zb), GOLDS["base"]),
              S(f"DCBandB{sx}", (0.55, 0.18, Hc), (x, -Dc / 2 - 0.05, zb), GOLDS["base"])]
        P += bolts(f"DCBandRivet{sx}", [(x, Dc / 2 + 0.17, zb + z) for z in (0.4, 1.3, 2.2)], GOLDS["light"], 0.12)
    P.append(S("DCRimBand", (Wc + 0.2, Dc + 0.2, 0.35), (0, 0, zb + Hc - 0.35), GOLDS["dark"]))
    # domed lid: half-cylinder along X + gold arch bands + end caps
    lz = zb + Hc + 0.05
    lid = tube("DCLid", Dc / 2 + 0.1, Dc / 2 + 0.1, Wc, Dc / 2 + 0.05, (0, 0, -Wc / 2), "#B0683A", sides=20, a0=0, a1=180)
    xf([lid], T(0, 0, lz) @ Ry(90) @ Rz(90))
    P.append(lid)
    for k, x in enumerate((-Wc / 2 + 0.25, -1.6, 1.6, Wc / 2 - 0.25)):
        band = tube(f"DCLidBand{k}", Dc / 2 + 0.28, Dc / 2 + 0.28, 0.55, 0.35, (0, 0, -0.275), GOLDS["base"] if k in (1, 2) else GOLDS["dark"],
                    sides=20, a0=0, a1=180)
        xf([band], T(x, 0, lz) @ Ry(90) @ Rz(90))
        P.append(band)
    P += bolts("DCLidRivet", [(x, math.cos(math.radians(a)) * (Dc / 2 + 0.3), lz + math.sin(math.radians(a)) * (Dc / 2 + 0.3))
                              for x in (-1.6, 1.6) for a in (30, 90, 150)], GOLDS["light"], 0.13)
    P.append(S("DCLidSeam", (Wc + 0.1, Dc + 0.25, 0.12), (0, 0, lz - 0.08), GOLDS["deep"]))
    # glowing seam leaking treasure light (front)
    P.append(N(S("DCGlowSeam", (Wc - 1.6, 0.12, 0.14), (0, Dc / 2 + 0.12, lz - 0.1), "#FFE45C", studs="none"), 5))
    # bone-shaped lock: gold plate + bone + keyhole
    fy = Dc / 2 + 0.14
    P += [face_piece("DCLockPlate", [(-0.9, -0.9), (0.9, -0.9), (0.9, 0.6), (0, 1.1), (-0.9, 0.6)], 0.25, GOLDS["base"], fy, lz - 0.9),
          face_piece("DCLockKey", circle_pts(0.22, 10), 0.06, INK, fy + 0.25, lz - 1.05),
          face_piece("DCLockKeySlot", rect(0.16, 0.45), 0.06, INK, fy + 0.25, lz - 1.35)]
    bn = bone_icon("DCLockBone", 0.62, BONES["base"], 0.3)
    xf(bn, T(0, fy + 0.4, lz + 0.05))
    P += bn
    # gem on top in a gold setting + iron side handles
    P += [C("DCGemSeat", 0.7, 0.55, 0.3, (0, 0, lz + Dc / 2 + 0.02), GOLDS["dark"], sides=10)]
    gem = B("DCGem", (0.55, 0.55, 0.75), (0, 0, lz + Dc / 2 + 0.85), "#3EF0FF", segments=6, rings=2, studs="none")
    gem.data.polygons.foreach_set("use_smooth", [False] * len(gem.data.polygons))
    P.append(N(gem, 3))
    for sx in (-1, 1):
        h = tube(f"DCHandle{sx}", 0.6, 0.6, 0.25, 0.18, (0, 0, -0.12), "#4A5260", sides=12, a0=180, a1=360)
        xf([h], T(sx * (Wc / 2 + 0.15), 0, zb + Hc - 0.7) @ Ry(90))
        P += [h, S(f"DCHandlePlate{sx}", (0.15, 1.6, 0.5), (sx * (Wc / 2 + 0.07), 0, zb + Hc - 0.85), "#4A5260")]
    att = {"PromptAnchor": T(0, Dc / 2 + 1.5, 1.5)}
    return name, P, att


PROPS = [rebirth_statue, egg_stand, cannon_shop, upgrade_stand, season_board, leaderboard, daily_chest]


def flag_accent(objs):
    for o in objs:
        for m in o.data.materials:
            if m is not None and m.get("roblox_color") == ACCENT_HEX:
                m["vault_accent"] = True


def name_accent_material(meshes):
    for m in meshes:
        if m.name == "Accent":
            mat = m.data.materials[0]
            mat.name = "Accent"
            mat["roblox_color"] = ACCENT_HEX


def hero(prev_dir, samples):
    """In-context hero: the hub props arranged as a corner of the Bone Zone shops ring."""
    vb.reset_scene()
    layout = {rebirth_statue: (0, -6, 0), egg_stand: (-17, 2, 25), cannon_shop: (18, 0, -20), upgrade_stand: (-30, -12, 35),
              season_board: (31, -14, -35), leaderboard: (-6, 14, 0), daily_chest: (9, 15, -10)}
    allp = []
    for fn, (x, y, yaw) in layout.items():
        _, P, _ = fn()
        xf(P, T(x, y, 0) @ Rz(yaw))
        allp += P
    allp += review_ground(220, 0)
    allp += kit.path_network([[(-40, 26), (0, 22), (40, 26)], [(0, 22), (0, 6)]], tile=3.4, step=3.6)
    vb.restud(allp)
    setup_render(samples)
    return shoot(os.path.join(prev_dir, "HubProps_BoneZone_HERO.png"), (8, 62, 26), (0, -2, 6.5), 30)


def main():
    opts = cn.parse_args()
    entries = []
    for fn in PROPS:
        if opts["only"] and opts["only"].lower() not in fn.__name__.lower():
            continue
        vb.reset_scene()
        name, P, att = fn()
        flag_accent(P)
        entry, meshes = finish_model(name, P, opts["out"], "hub_prop", att)
        name_accent_material(meshes)
        if any(m.name == "Accent" for m in meshes):  # re-export so the material name lands in the files
            root = bpy.data.objects[name]
            vb.export_fbx(os.path.join(opts["out"], f"{name}.fbx"), [root])
            vb.export_glb(os.path.join(opts["out"], f"{name}.glb"), [root])
        entries.append(entry)
        if opts["render"]:
            review_ground(90, 0)
            setup_render(opts["samples"])
            render_views(name, meshes, PREVIEW_DIR, opts["samples"])
    merge_manifest(entries, os.path.join(GAME, "assets", "manifest-props.json"))
    if opts["render"] and opts["lineup"] and not opts["only"]:
        hero(PREVIEW_DIR, opts["samples"])


if __name__ == "__main__":
    main()
