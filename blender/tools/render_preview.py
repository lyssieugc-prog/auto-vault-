"""
Render PNG previews of a template/game asset script with Cycles CPU (works headless, no GPU/EGL).
Use previews for owner review BEFORE Roblox import (style/house-style.md §4).

Usage (repo root):
    python blender/tools/render_preview.py <out_dir> [creature|map|both]
    blender -b -P blender/tools/render_preview.py -- <out_dir> [creature|map|both]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import creature  # noqa: E402
import map_layout  # noqa: E402


def setup_scene():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.view_settings.view_transform = "Standard"  # keep palette colors saturated
    scene.render.resolution_x, scene.render.resolution_y = 800, 600
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.8, 1.0, 1)
    bg.inputs[1].default_value = 0.8
    if "PreviewSun" not in scene.objects:
        sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
        sun.data.energy = 4
        sun.rotation_euler = (0.7, 0.2, 0.6)
        scene.collection.objects.link(sun)
    return scene


def shoot(path, location, target, lens=50):
    scene = setup_scene()
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def main(out_dir, which="both"):
    os.makedirs(out_dir, exist_ok=True)
    outputs = []
    if which in ("creature", "both"):
        creature.build()
        outputs.append(shoot(os.path.join(out_dir, "creature.png"), (7, 9, 5), (0, 1, 1.8)))
    if which in ("map", "both"):
        map_layout.build()
        outputs.append(shoot(os.path.join(out_dir, "map.png"), (0, -260, 220), (0, 0, 0), lens=30))
        outputs.append(shoot(os.path.join(out_dir, "zone.png"), (150, -60, 40), (150, 0, 0), lens=35))
    return outputs


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    print(main(argv[0] if argv else "previews", argv[1] if len(argv) > 1 else "both"))
