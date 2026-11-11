"""
My Vet Office — exam-room props (ORIGINAL, SOLID construction language, texture studs on all sides).

    ExamTable          stainless top + rolled rim + rubber mat with paw-print inlays, teal apron with built-in
                       pet scale (neon readout), drawer, rubber corner bumpers, end handles, hydraulic column
                       (telescoping chrome + rubber bellows), foot pedal + pump housing, levelling feet.
    EquipmentCabinet   wall cabinet: carcass + cornice + red-cross sign + 2 supply shelves (bottles, glove box,
                       cotton jar, gauze boxes) + 2 drawers.  CabinetDoor is a SEPARATE mesh whose origin is the
                       hinge axis (rotate about +Z to open) — Roblox: HingeConstraint / Motor6D at that pivot.
    Stethoscope        separate grip-able tool; origin = grip point (tubing Y-junction) -> Roblox Tool.Handle.
    Otoscope, Thermometer, BandageRoll   hand-held tools, origin = grip point.

Usage (repo root, bpy python):
    python games/my-vet-office/blender/exam_room_props.py            # build + check + export
    python games/my-vet-office/blender/exam_room_props.py --render   # + previews
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vet_common as vc  # noqa: E402
from vet_common import box, orb, pipe, ring, torus, tube, vb, vk  # noqa: E402

TEAL = vk.shades("#22C3A6")
CORAL = vk.shades("#FF6B6B")
C = {
    "teal": TEAL["base"], "teal_l": TEAL["light"], "teal_d": TEAL["dark"],
    "coral": CORAL["base"], "coral_d": CORAL["dark"],
    "steel": "#C9D3DE", "steel_l": "#E6ECF2", "steel_d": "#8E9BAA", "steel_dd": "#5F6B7A",
    "rubber": "#2F4858", "rubber_l": "#43627A",
    "white": "#F5F7FA", "cream": "#FFF6EA", "glass": "#9BE1FF", "glow": "#7CFFB2",
    "amber": "#E89A2C", "blue": "#326BE3", "purple": "#B678EA", "yellow": "#FFD93B", "tan": "#D9B98A",
}
METAL = 0.3  # lower roughness reads as polished stainless

MAX_TRIS = {"ExamTable": 6000, "EquipmentCabinet": 8000, "CabinetDoor": 2000, "Stethoscope": 3000,
            "Otoscope": 2000, "Thermometer": 1500, "BandageRoll": 1500}


# ------------------------------------------------------------------------------------------------ exam table
def exam_table():
    P = []
    a = P.append
    # base + levelling feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            a(tube(f"Foot{sx}{sy}", 0.2, 0.14, (sx * 1.45, sy * 0.95, 0.07), C["rubber"], sides=10))
    a(box("BasePlate", (3.4, 2.4, 0.3), (0, 0, 0.29), C["steel_dd"], r=0.08))
    a(box("BaseCap", (3.0, 2.0, 0.12), (0, 0, 0.5), C["steel_d"], r=0.04))
    a(box("BaseStripe", (3.42, 0.08, 0.1), (0, 1.2, 0.29), C["coral"], r=0.02))
    a(box("BaseStripeB", (3.42, 0.08, 0.1), (0, -1.2, 0.29), C["coral"], r=0.02))
    # hydraulic column: lower housing, rubber bellows, chrome ram, top bracket
    a(tube("ColumnLower", 0.62, 0.9, (0, 0, 1.01), C["steel_d"], sides=16, roughness=METAL))
    a(ring("ColumnCollar", 0.66, 0.1, 0.14, (0, 0, 1.46), C["teal_d"], sides=16))
    a(tube("BellowsCore", 0.46, 0.8, (0, 0, 1.9), C["rubber"], sides=14))
    for i in range(4):
        a(torus(f"Bellow{i}", 0.48, 0.1, (0, 0, 1.6 + i * 0.2), C["rubber_l"] if i % 2 else C["rubber"], sides=14,
                csides=6))
    a(tube("Ram", 0.36, 0.6, (0, 0, 2.55), C["steel_l"], sides=14, roughness=METAL))
    a(box("TopBracket", (2.4, 1.6, 0.22), (0, 0, 2.93), C["steel_dd"], r=0.05))
    # foot pedal + pump housing
    a(box("PumpHousing", (0.9, 0.7, 0.5), (0.95, 0.75, 0.69), C["teal"], r=0.08))
    a(box("PumpLabel", (0.5, 0.04, 0.2), (0.95, 1.11, 0.74), C["white"], r=0.01))
    a(box("Pedal", (0.7, 0.95, 0.12), (0.95, 1.45, 0.62), C["coral"], r=0.04, rot=(-12, 0, 0)))
    for k in range(3):
        a(box(f"PedalTread{k}", (0.6, 0.08, 0.05), (0.95, 1.2 + k * 0.25, 0.7 + (0.25 * k - 0.25) * 0.21),
              C["coral_d"], r=0.01, rot=(-12, 0, 0)))
    # apron (skirt) + coral band + drawer + scale readout
    a(box("Apron", (5.6, 2.8, 0.42), (0, 0, 2.83), C["teal"], r=0.08))
    for y in (-1.43, 1.43):
        a(box(f"ApronBand{y:+.0f}", (5.5, 0.06, 0.1), (0, y, 2.86), C["coral"], r=0.02))
    for x in (-2.83, 2.83):
        a(box(f"ApronBandS{x:+.0f}", (0.06, 2.7, 0.1), (x, 0, 2.86), C["coral"], r=0.02))
    a(box("ScaleBezel", (1.3, 0.12, 0.34), (-1.75, 1.46, 2.83), C["white"], r=0.04))
    a(box("ScaleScreen", (0.8, 0.05, 0.2), (-1.9, 1.53, 2.84), C["glow"], r=0.01, emission=3.0))
    a(orb("ScaleBtnA", (0.06, 0.04, 0.06), (-1.32, 1.53, 2.87), C["coral"], segs=8, rings=5))
    a(orb("ScaleBtnB", (0.06, 0.04, 0.06), (-1.32, 1.53, 2.77), C["teal_d"], segs=8, rings=5))
    a(box("DrawerFace", (1.5, 0.08, 0.3), (1.4, 1.43, 2.78), C["teal_l"], r=0.03))
    a(box("DrawerPull", (0.6, 0.1, 0.07), (1.4, 1.5, 2.82), C["steel"], r=0.02, roughness=METAL))
    # stainless top + rolled rim + rubber mat + paw-print inlays
    a(box("TopSlab", (6.0, 3.2, 0.22), (0, 0, 3.15), C["steel"], r=0.05, roughness=METAL))
    for y in (-1.5, 1.5):
        a(box(f"RimLong{y:+.0f}", (6.0, 0.2, 0.16), (0, y, 3.33), C["steel_l"], r=0.06, roughness=METAL))
    for x in (-2.9, 2.9):
        a(box(f"RimShort{x:+.0f}", (0.2, 2.8, 0.16), (x, 0, 3.33), C["steel_l"], r=0.06, roughness=METAL))
    a(box("Mat", (5.4, 2.6, 0.08), (0, 0, 3.3), C["rubber"], r=0.03))
    for i, x in enumerate((-2.2, -0.73, 0.73, 2.2)):
        a(box(f"MatRib{i}", (0.08, 2.4, 0.03), (x, 0, 3.355), C["rubber_l"], r=0.01))
    for j, (px, py, rz) in enumerate(((-1.45, -0.35, -18), (0.0, 0.35, 12), (1.45, -0.3, -10))):
        r = math.radians(rz)

        def rot(dx, dy):
            return (px + dx * math.cos(r) - dy * math.sin(r), py + dx * math.sin(r) + dy * math.cos(r))

        a(box(f"Paw{j}Pad", (0.5, 0.4, 0.035), (*rot(0, -0.1), 3.355), C["teal"], r=0.06, seg=2, rot=(0, 0, rz)))
        for k, (dx, dy) in enumerate(((-0.24, 0.2), (-0.09, 0.3), (0.09, 0.3), (0.24, 0.2))):
            a(box(f"Paw{j}Toe{k}", (0.15, 0.17, 0.035), (*rot(dx, dy), 3.355), C["teal_l"], r=0.05, seg=2,
                  rot=(0, 0, rz)))
    # back apron: towel bar with a folded towel + clinic label plate (no blank back side)
    for x in (-0.2, 1.6):
        a(box(f"TowelBracket{x:+.1f}", (0.1, 0.24, 0.1), (x, -1.5, 2.8), C["steel_d"], r=0.02))
    a(tube("TowelBar", 0.05, 2.0, (0.7, -1.6, 2.8), C["steel_l"], sides=8, rot=(0, 90, 0), roughness=METAL))
    a(box("TowelFront", (1.1, 0.06, 0.7), (0.75, -1.68, 2.48), C["coral"], r=0.03))
    a(box("TowelBack", (1.1, 0.06, 0.5), (0.75, -1.55, 2.56), C["coral_d"], r=0.03))
    a(box("TowelFold", (1.1, 0.18, 0.1), (0.75, -1.61, 2.82), C["coral"], r=0.05, seg=2))
    for k in range(2):
        a(box(f"TowelStripe{k}", (1.12, 0.07, 0.06), (0.75, -1.69, 2.24 + k * 0.12), C["white"], r=0.01))
    a(box("LabelPlate", (1.0, 0.06, 0.24), (-1.7, -1.43, 2.83), C["white"], r=0.03))
    a(box("LabelCrossV", (0.07, 0.04, 0.18), (-2.05, -1.47, 2.83), C["coral"], r=0.01))
    a(box("LabelCrossH", (0.18, 0.04, 0.07), (-2.05, -1.47, 2.83), C["coral"], r=0.01))
    a(box("LabelText", (0.55, 0.04, 0.06), (-1.6, -1.47, 2.83), C["teal_d"], r=0.01))
    # rubber corner bumpers + end handles
    for sx in (-1, 1):
        for sy in (-1, 1):
            a(box(f"Bumper{sx}{sy}", (0.34, 0.34, 0.44), (sx * 2.9, sy * 1.5, 3.12), C["coral"], r=0.1, seg=2))
        x0, x1 = sx * 3.0, sx * 3.4
        a(pipe(f"Handle{sx}", [(x0, -0.8, 3.05), (x1, -0.8, 3.05), (x1, 0.8, 3.05), (x0, 0.8, 3.05)], 0.07,
               C["steel_l"], csides=8))
    return P


# ------------------------------------------------------------------------------------------------ cabinet
CAB_W, CAB_D, CAB_H = 3.2, 1.3, 4.2
HINGE = (-CAB_W / 2 + 0.02, CAB_D + 0.06, 0.0)  # door hinge axis (vertical, +Z), on the carcass front-left edge


def cabinet():
    W, D, H = CAB_W, CAB_D, CAB_H
    P = []
    a = P.append
    a(box("Back", (W, 0.12, H), (0, 0.06, H / 2), C["white"], r=0.03))
    for s in (-1, 1):
        a(box(f"Side{s}", (0.16, D, H), (s * (W / 2 - 0.08), D / 2, H / 2), C["teal"], r=0.04))
    a(box("Bottom", (W + 0.04, D + 0.02, 0.2), (0, D / 2, 0.1), C["teal_d"], r=0.04))
    a(box("Top", (W + 0.04, D + 0.02, 0.16), (0, D / 2, H - 0.08), C["teal"], r=0.04))
    a(box("Cornice", (W + 0.3, D + 0.25, 0.2), (0, (D + 0.25) / 2, H + 0.1), C["teal_d"], r=0.05))
    a(box("CorniceLip", (W + 0.4, 0.1, 0.12), (0, D + 0.3, H + 0.1), C["coral"], r=0.03))
    # red-cross sign on the crown
    a(box("SignBoard", (1.3, 0.14, 0.72), (0, D * 0.55, H + 0.56), C["white"], r=0.06))
    a(box("SignFrame", (1.44, 0.1, 0.86), (0, D * 0.55 - 0.08, H + 0.56), C["teal_d"], r=0.05))
    a(box("CrossV", (0.18, 0.08, 0.52), (0, D * 0.55 + 0.1, H + 0.56), C["coral"], r=0.02))
    a(box("CrossH", (0.52, 0.08, 0.18), (0, D * 0.55 + 0.1, H + 0.56), C["coral"], r=0.02))
    # drawers (lower section)
    a(box("DrawerDivider", (W - 0.32, D - 0.05, 0.12), (0, D / 2, 1.06), C["teal_d"], r=0.03))
    for k, x in enumerate((-W / 4 + 0.04, W / 4 - 0.04)):
        a(box(f"Drawer{k}", (W / 2 - 0.24, 0.1, 0.72), (x, D - 0.02, 0.6), C["teal_l"], r=0.04))
        a(box(f"DrawerPull{k}", (0.6, 0.1, 0.08), (x, D + 0.07, 0.72), C["steel"], r=0.03, roughness=METAL))
        a(box(f"DrawerTag{k}", (0.42, 0.04, 0.16), (x, D + 0.045, 0.48), C["white"], r=0.01))
    # interior shelves + supplies (visible through the glass door)
    for z in (2.1, 3.15):
        a(box(f"Shelf{z}", (W - 0.32, D - 0.25, 0.1), (0, (D - 0.25) / 2 + 0.12, z), C["white"], r=0.02))
        a(box(f"ShelfLip{z}", (W - 0.32, 0.06, 0.14), (0, D - 0.12, z + 0.02), C["coral"], r=0.02))
    # shelf 0 (z 1.12): glove box + gauze boxes
    a(box("GloveBox", (0.95, 0.6, 0.5), (-0.85, 0.6, 1.37), C["blue"], r=0.04))
    a(box("GloveSlot", (0.5, 0.04, 0.16), (-0.85, 0.91, 1.42), C["white"], r=0.02))
    a(box("GloveTuft", (0.26, 0.2, 0.16), (-0.85, 0.9, 1.65), C["white"], r=0.05, seg=2))
    for k in range(2):
        a(box(f"Gauze{k}", (0.7, 0.55, 0.42), (0.35 + k * 0.78, 0.6, 1.33 + k * 0.0), C["cream"], r=0.04))
        a(box(f"GauzeStripe{k}", (0.72, 0.04, 0.1), (0.35 + k * 0.78, 0.89, 1.4), C["teal"], r=0.01))
    # shelf 1 (z 2.2): medicine bottles with caps + labels
    for k, (x, col, h) in enumerate(((-1.1, C["amber"], 0.6), (-0.7, C["amber"], 0.5), (-0.25, C["blue"], 0.66),
                                      (0.2, C["purple"], 0.48), (0.62, C["white"], 0.58), (1.05, C["amber"], 0.52))):
        a(tube(f"Bottle{k}", 0.16, h, (x, 0.65, 2.2 + h / 2), col, sides=10))
        a(tube(f"BottleCap{k}", 0.12, 0.12, (x, 0.65, 2.2 + h + 0.06), C["white"] if col != C["white"] else
               C["coral"], sides=10))
        a(box(f"BottleLabel{k}", (0.2, 0.04, h * 0.42), (x, 0.82, 2.2 + h * 0.45), C["white"] if col != C["white"]
              else C["teal"], r=0.01))
    # shelf 2 (z 3.25): cotton jar + bandage rolls + spray bottle
    a(tube("JarGlass", 0.3, 0.6, (-0.8, 0.65, 3.55), C["glass"], sides=12, studs=False))
    a(tube("JarLid", 0.32, 0.12, (-0.8, 0.65, 3.91), C["teal_d"], sides=12))
    for k, (dx, dz) in enumerate(((-0.1, 0.0), (0.1, 0.05), (0.0, 0.2), (-0.12, 0.33), (0.1, 0.36))):
        a(orb(f"Cotton{k}", (0.13, 0.13, 0.12), (-0.8 + dx, 0.65, 3.42 + dz), C["white"], segs=8, rings=5))
    for k in range(2):
        a(tube(f"ShelfRoll{k}", 0.24, 0.36, (0.05 + k * 0.5, 0.62, 3.43), C["cream"], sides=12))
        a(tube(f"ShelfRollCore{k}", 0.09, 0.37, (0.05 + k * 0.5, 0.62, 3.43), C["tan"], sides=8))
    a(tube("SprayBody", 0.17, 0.55, (1.1, 0.6, 3.52), C["teal_l"], sides=10))
    a(box("SprayHead", (0.18, 0.3, 0.16), (1.1, 0.68, 3.88), C["coral"], r=0.04))
    return P


def cabinet_door():
    W, D, H = CAB_W, CAB_D, CAB_H
    P = []
    a = P.append
    x0 = -W / 2 + 0.04
    dw, dz0, dz1 = W - 0.08, 1.14, H - 0.18
    cx, cz, dh = x0 + dw / 2, (dz0 + dz1) / 2, dz1 - dz0
    y = D + 0.06
    t = 0.26
    a(box("DoorRailT", (dw, 0.14, t), (cx, y, dz1 - t / 2), C["teal_l"], r=0.04))
    a(box("DoorRailB", (dw, 0.14, t), (cx, y, dz0 + t / 2), C["teal_l"], r=0.04))
    a(box("DoorStileL", (t, 0.14, dh - 2 * t), (x0 + t / 2, y, cz), C["teal_l"], r=0.04))
    a(box("DoorStileR", (t, 0.14, dh - 2 * t), (x0 + dw - t / 2, y, cz), C["teal_l"], r=0.04))
    a(box("DoorMullion", (0.12, 0.1, dh - 2 * t), (cx, y + 0.01, cz), C["teal_l"], r=0.03))
    a(box("DoorGlass", (dw - 2 * t + 0.04, 0.05, dh - 2 * t + 0.04), (cx, y, cz), C["glass"], r=0.01, studs=False))
    a(box("DoorHandle", (0.1, 0.12, 0.8), (x0 + dw - 0.13, y + 0.14, cz), C["steel"], r=0.04, roughness=METAL))
    for z in (cz - 0.3, cz + 0.3):
        a(box(f"HandlePost{z:.1f}", (0.08, 0.1, 0.08), (x0 + dw - 0.13, y + 0.08, z), C["steel"], r=0.02,
              roughness=METAL))
    a(tube("Lock", 0.07, 0.06, (x0 + dw - 0.13, y + 0.1, cz - 0.62), C["steel_d"], sides=10, rot=(-90, 0, 0)))
    for z in (dz0 + 0.4, dz1 - 0.4):
        a(tube(f"Knuckle{z:.1f}", 0.07, 0.32, (HINGE[0], HINGE[1], z), C["steel_d"], sides=8, roughness=METAL))
    # paw-print sticker on the glass: clinic branding
    a(box("StickerPad", (0.3, 0.03, 0.24), (cx - 0.7, y + 0.04, cz + 0.6), C["coral"], r=0.05, seg=2))
    for k, (dx, dz) in enumerate(((-0.14, 0.17), (-0.05, 0.24), (0.05, 0.24), (0.14, 0.17))):
        a(box(f"StickerToe{k}", (0.08, 0.03, 0.09), (cx - 0.7 + dx, y + 0.04, cz + 0.6 + dz), C["coral"], r=0.03))
    return P


# ------------------------------------------------------------------------------------------------ hand tools
def stethoscope():
    """Origin (0,0,0) = grip point at the Y-junction of the tubing."""
    P = []
    a = P.append
    a(orb("YJunction", (0.15, 0.15, 0.17), (0, 0, 0), C["steel"], segs=10, rings=6))
    a(pipe("TubeMain", [(0, 0, -0.05), (0.04, 0.02, -0.35), (0.16, 0.06, -0.7), (0.1, 0.04, -1.0), (0, 0, -1.2)],
           0.1, C["teal"], csides=8))
    for s in (-1, 1):
        a(pipe(f"TubeArm{s}", [(0, 0, 0.05), (s * 0.18, 0, 0.3), (s * 0.3, 0, 0.6)], 0.085, C["teal"], csides=8))
        a(pipe(f"Binaural{s}", [(s * 0.3, 0, 0.55), (s * 0.36, 0, 0.95), (s * 0.3, 0.06, 1.25), (s * 0.2, 0.14, 1.4)],
               0.055, C["steel_l"], csides=8))
        a(orb(f"EarTip{s}", (0.1, 0.1, 0.1), (s * 0.18, 0.16, 1.44), C["coral"], segs=8, rings=6))
    a(box("SpringBar", (0.72, 0.08, 0.1), (0, 0, 0.62), C["steel_d"], r=0.03, roughness=METAL))
    # chest piece: stem, diaphragm disc, rim, bell
    a(tube("Stem", 0.07, 0.26, (0, 0, -1.3), C["steel_l"], sides=8, roughness=METAL))
    a(tube("Diaphragm", 0.34, 0.14, (0, 0, -1.55), C["steel"], sides=16, rot=(90, 0, 0), roughness=METAL))
    a(ring("DiaphragmRim", 0.34, 0.06, 0.18, (0, 0, -1.55), C["coral"], sides=16, rot=(90, 0, 0)))
    a(tube("DiaphragmFace", 0.27, 0.04, (0, 0.08, -1.55), C["white"], sides=16, rot=(90, 0, 0)))
    a(tube("Bell", 0.2, 0.18, (0, -0.15, -1.55), C["steel_d"], sides=12, rot=(90, 0, 0), r2=0.12, roughness=METAL))
    return P


def otoscope():
    """Origin = grip (middle of the handle)."""
    P = []
    a = P.append
    a(tube("Handle", 0.19, 1.0, (0, 0, 0), C["rubber"], sides=12))
    for k, z in enumerate((-0.3, -0.1, 0.1, 0.3)):
        a(ring(f"Knurl{k}", 0.2, 0.05, 0.08, (0, 0, z), C["teal"] if k % 2 else C["teal_d"], sides=12))
    a(tube("BaseCap", 0.21, 0.12, (0, 0, -0.55), C["steel_d"], sides=12, roughness=METAL))
    a(tube("Rheostat", 0.22, 0.14, (0, 0, 0.56), C["coral"], sides=12))
    a(tube("Neck", 0.13, 0.16, (0, 0, 0.7), C["steel"], sides=10, roughness=METAL))
    a(box("Head", (0.42, 0.44, 0.38), (0, 0, 0.96), C["white"], r=0.12, seg=2))
    a(tube("Speculum", 0.17, 0.42, (0, 0.42, 0.96), C["white"], sides=12, rot=(-90, 0, 0), r2=0.06))
    a(tube("SpeculumTip", 0.065, 0.06, (0, 0.65, 0.96), C["teal"], sides=10, rot=(-90, 0, 0)))
    a(ring("LightRing", 0.17, 0.04, 0.05, (0, 0.21, 0.96), C["glow"], sides=12, rot=(90, 0, 0), studs=False))
    a(tube("Lens", 0.15, 0.05, (0, -0.24, 0.96), C["glass"], sides=12, rot=(90, 0, 0), studs=False))
    a(ring("LensRim", 0.16, 0.04, 0.07, (0, -0.24, 0.96), C["steel_d"], sides=12, rot=(90, 0, 0)))
    # the light ring glows
    P[-3].data.materials[0] = vb.palette_material(C["glow"] + "_neon", C["glow"], 3.0)
    return P


def thermometer():
    """Origin = grip (middle of the body)."""
    P = []
    a = P.append
    a(box("Body", (0.36, 0.22, 1.0), (0, 0, 0.1), C["white"], r=0.1, seg=2, top=(0.85, 0.9)))
    a(box("TopCap", (0.3, 0.2, 0.18), (0, 0, 0.66), C["teal"], r=0.07, seg=2))
    a(box("ScreenBezel", (0.28, 0.04, 0.36), (0, 0.11, 0.3), C["rubber"], r=0.03))
    a(box("Screen", (0.2, 0.03, 0.26), (0, 0.135, 0.3), C["glow"], r=0.01, emission=3.0))
    a(orb("Button", (0.08, 0.05, 0.08), (0, 0.12, -0.02), C["coral"], segs=8, rings=5))
    for k in range(3):
        a(box(f"Grip{k}", (0.38, 0.12, 0.05), (0, -0.07, -0.18 - k * 0.1), C["teal_d"], r=0.02))
    a(tube("ProbeBase", 0.09, 0.1, (0, 0, -0.45), C["teal"], sides=10))
    a(tube("Probe", 0.055, 0.5, (0, 0, -0.75), C["steel_l"], sides=10, r2=0.05, roughness=METAL))
    a(orb("ProbeTip", (0.06, 0.06, 0.07), (0, 0, -1.0), C["steel_d"], segs=8, rings=5))
    return P


def bandage_roll():
    """Origin = roll centre (grip)."""
    P = []
    a = P.append
    a(ring("Roll", 0.28, 0.26, 0.5, (0, 0, 0), C["cream"], sides=18, rot=(0, 90, 0)))
    a(ring("RollEdgeL", 0.39, 0.04, 0.05, (-0.24, 0, 0), C["coral"], sides=18, rot=(0, 90, 0)))
    a(ring("RollEdgeR", 0.39, 0.04, 0.05, (0.24, 0, 0), C["coral"], sides=18, rot=(0, 90, 0)))
    a(ring("Core", 0.15, 0.04, 0.52, (0, 0, 0), C["tan"], sides=14, rot=(0, 90, 0)))
    # loose outer layer where the tail peels off (one intentional step, not random tabs)
    a(box("LooseEnd", (0.5, 0.34, 0.035), (0, 0.3, -0.31), C["white"], r=0.01, rot=(-45, 0, 0)))
    # unrolled tail lying forward + its coral stripes + butterfly clip
    a(box("Tail", (0.46, 0.8, 0.04), (0, 0.42, -0.4), C["cream"], r=0.01, rot=(-8, 0, 0)))
    for x in (-0.16, 0.16):
        a(box(f"TailStripe{x:+.1f}", (0.04, 0.78, 0.015), (x, 0.42, -0.375), C["coral"], r=0.004, rot=(-8, 0, 0)))
    a(box("Clip", (0.3, 0.14, 0.06), (0, 0.72, -0.43), C["steel"], r=0.02, rot=(-8, 0, 0), roughness=METAL))
    for s in (-1, 1):
        a(box(f"ClipTooth{s}", (0.06, 0.06, 0.08), (s * 0.13, 0.79, -0.42), C["steel_d"], r=0.01))
    return P


PROPS = {  # name -> (builder, pivot)
    "ExamTable": (exam_table, (0, 0, 0)),
    "EquipmentCabinet": (cabinet, (0, 0, 0)),
    "CabinetDoor": (cabinet_door, HINGE),
    "Stethoscope": (stethoscope, (0, 0, 0)),
    "Otoscope": (otoscope, (0, 0, 0)),
    "Thermometer": (thermometer, (0, 0, 0)),
    "BandageRoll": (bandage_roll, (0, 0, 0)),
}
FILES = {"ExamTable": "exam_table", "EquipmentCabinet": "equipment_cabinet", "Stethoscope": "stethoscope",
         "Otoscope": "otoscope", "Thermometer": "thermometer", "BandageRoll": "bandage_roll"}


def build_one(name):
    fn, pivot = PROPS[name]
    parts = fn()
    obj = vc.join_into(name, parts, origin=pivot)
    obj["vault_parts_before_join"] = len(parts)
    obj["vault_asset"] = name
    return obj, len(parts)


def check(objs):
    rep = {}
    for name, (obj, n) in objs.items():
        tris = vc.tri_count(obj)
        assert tris <= MAX_TRIS[name] <= vc.MAX_TRIS_PER_MESH, f"{name} {tris} tris > {MAX_TRIS[name]}"
        assert not any(o.get("vault_kind") == "studs" for o in [obj]), "no stud geometry"
        studded = sum(1 for m in obj.data.materials if m and m.get("vault_studs"))
        assert studded > 0, f"{name} has no stud texture"
        rep[name] = {"tris": tris, "parts_before_join": n, "materials": len(obj.data.materials)}
    return rep


def export_all():
    out = {}
    for name, fname in FILES.items():
        vb.reset_scene()
        objs = {name: build_one(name)}
        if name == "EquipmentCabinet":
            objs["CabinetDoor"] = build_one("CabinetDoor")
        rep = check(objs)
        sel = [o for o, _ in objs.values()]
        base = os.path.join(vc.EXPORT_DIR, fname)
        vb.export_fbx(base + ".fbx", sel)
        vb.export_glb(base + ".glb", sel)
        for k, v in rep.items():
            v.update({"fbx": base + ".fbx", "glb": base + ".glb"})
            out[k] = v
    return out


def place(obj, loc, rot_z=0.0, rot=None):
    obj.location = loc
    obj.rotation_euler = tuple(math.radians(a) for a in (rot or (0, 0, rot_z)))


def render(out_dir=vc.PREVIEW_DIR, samples=24, with_dog=True):
    """Previews: table front/side/back/3-4, cabinet closed + door open, tools close-up, in-context exam room."""
    os.makedirs(out_dir, exist_ok=True)
    outs = []
    # 1) table alone
    vb.reset_scene()
    table, _ = build_one("ExamTable")
    vc.setup_render(samples=samples)
    for key, yaw, pitch in (("front", 0, 10), ("side", 90, 8), ("back", 180, 10), ("34", 35, 22)):
        outs.append(vc.shoot(os.path.join(out_dir, f"exam_table_{key}.png"), vc.orbit((0, 0, 1.9), 15, yaw, pitch),
                             (0, 0, 1.8), lens=50))
    # 2) cabinet closed / open
    vb.reset_scene()
    cab, _ = build_one("EquipmentCabinet")
    door, _ = build_one("CabinetDoor")
    vc.setup_render(samples=samples)
    back = box("PreviewWall", (14, 0.3, 9), (0, -0.15, 4.5), "#FFF6EA", r=0.0)
    back.hide_select = True
    tgt = (0, 0.6, 2.4)
    outs.append(vc.shoot(os.path.join(out_dir, "equipment_cabinet_closed.png"), vc.orbit(tgt, 12, 28, 8), tgt))
    door.rotation_euler = (0, 0, math.radians(105))
    outs.append(vc.shoot(os.path.join(out_dir, "equipment_cabinet_open.png"), vc.orbit(tgt, 12, 28, 8), tgt))
    outs.append(vc.shoot(os.path.join(out_dir, "equipment_cabinet_side.png"), vc.orbit(tgt, 12, 80, 6), tgt))
    # 3) hand tools close-up (laid out like a tray)
    vb.reset_scene()
    vc.setup_render(samples=samples)
    tray = box("Tray", (5.2, 2.6, 0.12), (0.2, 0, 0.06), C["steel"], r=0.05)
    s, _ = build_one("Stethoscope")
    place(s, (-1.6, 0, 2.02))
    o, _ = build_one("Otoscope")
    place(o, (-0.3, 0.1, 0.68), rot_z=60)
    t, _ = build_one("Thermometer")
    place(t, (0.75, 0.0, 1.14))
    b, _ = build_one("BandageRoll")
    place(b, (1.85, -0.25, 0.53), rot_z=-20)
    tgt = (0.1, 0, 1.0)
    outs.append(vc.shoot(os.path.join(out_dir, "vet_tools_front.png"), vc.orbit(tgt, 8.5, 12, 14), tgt, lens=50))
    outs.append(vc.shoot(os.path.join(out_dir, "vet_tools_back.png"), vc.orbit(tgt, 8.5, 192, 16), tgt, lens=50))
    # 4) in-context: dog on the table, cabinet on a wall, tools on the mat
    if with_dog:
        import golden_retriever as gr

        arm, meshes, _ = gr.build()  # resets the scene
        gr_pose = gr.POSES["sit"]
        vc.set_pose(arm, gr_pose)
        arm.location = (-0.4, 0.2, 3.34)
        arm.rotation_euler = (0, 0, math.radians(20))
        table, _ = build_one("ExamTable")
        cab, _ = build_one("EquipmentCabinet")
        door, _ = build_one("CabinetDoor")
        for ob in (cab, door):
            ob.location = (ob.location[0] - 5.2, ob.location[1] - 4.2, ob.location[2] + 0.0)
        door.rotation_euler = (0, 0, math.radians(70))
        s, _ = build_one("Stethoscope")
        place(s, (2.1, -0.2, 3.42), rot=(90, 0, 70))
        t, _ = build_one("Thermometer")
        place(t, (1.6, 0.8, 3.48), rot=(90, 0, 110))
        b, _ = build_one("BandageRoll")
        place(b, (2.35, 0.75, 3.75), rot_z=10)
        vc.setup_render(samples=samples)
        wall = box("PreviewWall", (20, 0.3, 10), (0, -4.35, 5), "#FFF6EA", r=0.0)
        wall.hide_select = True
        tgt = (-1.2, -0.8, 2.8)
        outs.append(vc.shoot(os.path.join(out_dir, "exam_room_context.png"), vc.orbit(tgt, 17, 24, 14), tgt, lens=45))
    return outs


def main(argv):
    rep = export_all()
    for k, v in rep.items():
        print(k, {kk: vv for kk, vv in v.items() if kk in ("tris", "parts_before_join", "materials")})
    if "--render" in argv:
        print(render(with_dog="--no-dog" not in argv))
    return rep


if __name__ == "__main__":
    main(sys.argv[1:])
