"""Render each kart for the lobby's racer cards: three-quarters from the front, on a transparent ground.

blender -b --factory-startup --python tools/kart_cards.py
   ->   art/karts/<name>/card.png (480 × 320), imported into the game as "<Name> kart".
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
KARTS = ["hettie", "max", "puddles", "the-major", "mabel", "scraps", "marmalade", "duvet"]

for name in KARTS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / "art" / "karts" / name / "kart.glb"))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    lo = Vector((min(min((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in meshes) for i in range(3)))
    hi = Vector((max(max((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for o in meshes) for i in range(3)))
    centre = (lo + hi) / 2
    size = max((hi - lo).x, (hi - lo).y, (hi - lo).z)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 480, 320
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    scene.world = world

    # The kart faces -Y in Blender (its nose is +Z in the game's turned axes): look from front-left, a little above.
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    # Orthographic and fitted to the kart, so every card frames its kart alike, tall parts and all.
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = size * 1.85
    d = size * 4
    yaw = math.radians(-35)
    cam.location = centre + Vector((math.sin(yaw) * d, -math.cos(yaw) * d, d * 0.42))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.collection.objects.link(sun)

    scene.render.filepath = str(ROOT / "art" / "karts" / name / "card.png")
    bpy.ops.render.render(write_still=True)
    print("card", name)
