"""Scale reference: a 4x4x4 stud cube + 1-stud studs. Import first in every new game to confirm
the Blender->Roblox scale. Usage: blender -b -P blender/templates/scale_reference.py -- <out_dir>"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import vault_blocky as vb  # noqa: E402


def build():
    vb.reset_scene()
    cube = vb.block("ScaleRef_4studs", (4, 4, 4), (0, 0, 0), "yellow", bevel=0.0)
    vb.studs(cube)
    return [cube]


def main(out_dir):
    objs = build()
    fbx = vb.export_fbx(os.path.join(out_dir, "ScaleRef.fbx"), objs)
    return {"name": "ScaleRef", "fbx": fbx, **vb.poly_report()}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    print(main(argv[0] if argv else "out"))
