"""
Render the style test collection (blender/templates/test_collection.py) for owner review:
one wide "all five together" shot + a close-up of each model. Cycles CPU, headless-safe.

Usage: python blender/tools/render_collection.py <out_dir> [samples]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import test_collection  # noqa: E402

SHOTS = {  # cameras on the +y side: every model's front faces +y
    "collection_wide": ((32, 46, 26), (3, -1, 5), 32),
    "tree": ((-1, 11, 11), (-13, -5, 8), 38),
    "rock": ((-5, 17, 6), (-12, 8, 1.5), 40),
    "building": ((19, 13, 13), (5, -9, 8), 32),
    "conveyor": ((16, 22, 10), (5, 7, 3), 36),
    "brainrot": ((23, 23, 9), (20, 2, 6.2), 38),
}


def setup(samples):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.33, 0.64, 1.0, 1)
    bg.inputs[1].default_value = 0.9
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 5.0
    sun.data.color = (1.0, 0.96, 0.9)
    sun.data.angle = 0.12  # soft-edged daylight shadows like the references
    sun.rotation_euler = (0.75, 0.15, 0.55)
    scene.collection.objects.link(sun)
    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "SUN"))
    fill.data.energy = 1.2
    fill.rotation_euler = (1.1, -0.3, 3.7)
    scene.collection.objects.link(fill)
    return scene


def main(out_dir, samples=24):
    test_collection.build_all()
    scene = setup(samples)
    os.makedirs(out_dir, exist_ok=True)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    out = []
    for name, (loc, target, lens) in SHOTS.items():
        cam.location = loc
        cam.data.lens = lens
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(out_dir, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        out.append(scene.render.filepath)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    print(main(argv[0] if argv else "previews", int(argv[1]) if len(argv) > 1 else 24))
