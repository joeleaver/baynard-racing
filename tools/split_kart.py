"""Split a built kart into the parts the game moves: its body, and each wheel with its origin at its hub.

blender -b --factory-startup --python tools/split_kart.py -- <kart.glb> <out folder>

Writes <out>/body.glb (the body and the steering wheel, as the kart sits) and <out>/wheel_FL.glb … one per
wheel, each centred on its hub, in the kart's own axes, so the game hangs each under its wheel. The engine
places a model whole, so a kart's wheels have to arrive as models of their own to spin and steer.
"""

import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1 :]
src, out = args[0], args[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

objects = [o for o in bpy.data.objects if o.type == "MESH"]
for o in objects:
    if o.parent is not None:
        world = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = world


def export(selected, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in selected:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f"{out}/{name}.glb", export_format="GLB", use_selection=True, export_yup=True, export_extras=True)


wheels = [o for o in objects if o.name.startswith("wheel_")]
for w in wheels:
    at = w.location.copy()
    w.location = (0.0, 0.0, 0.0)
    export([w], w.name)
    w.location = at
export([o for o in objects if o not in wheels], "body")
for w in wheels:
    print(f"part {w.name} hub {tuple(round(v, 4) for v in w.location)}")
