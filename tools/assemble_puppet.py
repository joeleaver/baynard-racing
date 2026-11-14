"""Assemble a Braynard racer puppet in Blender from separately generated piece meshes.

blender -b --factory-startup --python tools/assemble_puppet.py -- <config.json>

The config names a rig source (a hifipushie export that carries the Mixamo skeleton and the moving face pieces with
their face shapes), the piece meshes (head, body, wing) and where each piece goes, measured on the character's full
reference mesh (metres, Z up, the character faces -Y). Pieces are scaled uniformly and placed by those targets:
  head: {"glb", "z": [hem bottom, top], "centre": [x, y]}            rigid on the Head bone
  body: {"glb", "z": [0, top], "centre": [x, y]}                      skinned to hips, spine and legs only
  wing: {"glb", "height", "centre": [x, y, z]} (left side; mirrored)  rigid on LeftArm / RightArm
  each piece may give "faces" (its face budget after retopo) and "turn" (extra degrees about Z if the
  generated piece came out facing the wrong way); "voxel" (metres) sets the retopo resolution
  face: {"keep": [rig-source meshes to keep], "anchor": [x, z]}       moved in Y onto the new head's surface
Paths in the config are relative to the config file. Writes config["out"] (GLB with skin and shape keys).
"""
import bpy, bmesh, sys, json, math, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import import_generated as imported, only, retopo, bounds

import os
_cfg_path = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
cfg = json.load(open(_cfg_path))
_here = os.path.dirname(_cfg_path)


def _abs(p):  # paths in the config are relative to the config file
    return os.path.normpath(os.path.join(_here, os.path.expanduser(p)))


cfg["rig_source"] = _abs(cfg["rig_source"]); cfg["out"] = _abs(cfg["out"])
for _k in ("head", "body", "wing"): cfg[_k]["glb"] = _abs(cfg[_k]["glb"])
bpy.ops.wm.read_factory_settings(use_empty=True)


def place(o, scale, offset):
    o.data.transform(Matrix.Translation(offset) @ Matrix.Scale(scale, 4))
    o.data.update()


def surface_y(o, x, z):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm)
    hit = t.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
    bm.free()
    return hit[0].y if hit[0] else None


# rig source: skeleton + face pieces
bpy.ops.import_scene.gltf(filepath=cfg["rig_source"])
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
src_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
keep = set(cfg["face"]["keep"])
old_head = next(o for o in src_meshes if o.name.endswith("_head"))
ax, az = cfg["face"]["anchor"]
old_y = surface_y(old_head, ax, az)

# head
h = imported(cfg["head"]["glb"], cfg["head"].get("turn", 0)); h.name = "head"
lo, hi = bounds(h); z0, z1 = cfg["head"]["z"]; s = (z1 - z0) / (hi.z - lo.z)
cx, cy = cfg["head"]["centre"]
place(h, s, Vector((cx - (lo.x + hi.x) / 2 * s, cy - (lo.y + hi.y) / 2 * s, z0 - lo.z * s)))
h = retopo(h, cfg["head"].get("faces", 8000), cfg.get("voxel", 0.004))
new_y = surface_y(h, ax, az)
dy = (new_y - old_y) if (new_y is not None and old_y is not None) else 0.0
print("face shift dy", round(dy, 4), "old", old_y, "new", new_y)

# body
b = imported(cfg["body"]["glb"], cfg["body"].get("turn", 0)); b.name = "body"
lo, hi = bounds(b); z0, z1 = cfg["body"]["z"]; s = (z1 - z0) / (hi.z - lo.z)
cx, cy = cfg["body"]["centre"]
place(b, s, Vector((cx - (lo.x + hi.x) / 2 * s, cy - (lo.y + hi.y) / 2 * s, z0 - lo.z * s)))
b = retopo(b, cfg["body"].get("faces", 8000), cfg.get("voxel", 0.004))

# wings: thinnest axis -> X, sized by height, mirrored
w = imported(cfg["wing"]["glb"], cfg["wing"].get("turn", 0)); w.name = "wing_l"
lo, hi = bounds(w); ext = hi - lo
thin = min(range(3), key=lambda i: ext[i])
if thin == 1: w.data.transform(Matrix.Rotation(math.pi / 2, 4, "Z"))
elif thin == 2: w.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
lo, hi = bounds(w); s = cfg["wing"]["height"] / (hi.z - lo.z)
c = Vector(cfg["wing"]["centre"])
place(w, s, c - (lo + hi) / 2 * s)
w = retopo(w, cfg["wing"].get("faces", 2000), cfg.get("voxel", 0.004) * 0.75, 512)
wr = w.copy(); wr.data = w.data.copy(); wr.name = "wing_r"; bpy.context.collection.objects.link(wr)
wr.data.transform(Matrix.Scale(-1, 4, Vector((1, 0, 0)))); wr.data.flip_normals(); wr.data.update()

# Pieces generated separately come out in slightly different creams: match the head's and wings' light tones to
# the body's (only bright pixels are compared, so the red comb and empty texture space don't skew it).
def light_tone(img):
    import numpy as np
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    lum = px @ np.array([0.2126, 0.7152, 0.0722])
    return np.median(px[lum > 0.45], axis=0), px


if cfg.get("match_colour", True):
    import numpy as np
    target, _ = light_tone(b.data.materials[0].node_tree.nodes.active.image)
    for o in (h, w):
        img = o.data.materials[0].node_tree.nodes.active.image
        tone, px = light_tone(img)
        lum = px @ np.array([0.2126, 0.7152, 0.0722])
        k = np.clip((lum - 0.3) / 0.3, 0, 1)[:, None]  # full correction on the cream, none on darker colours
        out = px * (1 - k + k * (target / tone))
        a = np.ones((len(px), 1))
        img.pixels[:] = np.hstack([np.clip(out, 0, 1), a]).ravel()
        img.pack()
        print("colour matched", o.name, tone.round(3), "->", target.round(3))

# drop the rig source's sculpted pieces, shift the kept face pieces onto the new head
for o in src_meshes:
    short = o.name.split("_", 1)[-1]
    if short in keep:
        o.location.y += dy
    else:
        bpy.data.objects.remove(o)
bpy.context.view_layer.update()


def bind_rigid(o, bone):
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name=bone); g.add(range(len(o.data.vertices)), 1.0, "REPLACE")
    o.parent = arm; o.parent_type = "OBJECT"
    md = o.modifiers.new("Armature", "ARMATURE"); md.object = arm


bind_rigid(h, "mixamorig:Head")
bind_rigid(w, "mixamorig:LeftArm"); bind_rigid(wr, "mixamorig:RightArm")
# body: automatic weights with only hips, spine and leg bones deforming
skin = ("Hips", "Spine", "UpLeg", "Leg", "Foot", "Toe")
saved = {bn.name: bn.use_deform for bn in arm.data.bones}
for bn in arm.data.bones:
    bn.use_deform = any(k in bn.name for k in skin) and "Bend" not in bn.name
# Generated meshes are rarely closed, which makes Blender's heat weighting fail silently. Weight a closed
# voxel-remeshed proxy instead, then copy its weights onto the body by nearest surface.
proxy = b.copy(); proxy.data = b.data.copy(); proxy.name = "body_proxy"; bpy.context.collection.objects.link(proxy)
rm = proxy.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.008
bpy.ops.object.select_all(action="DESELECT")
proxy.select_set(True); bpy.context.view_layer.objects.active = proxy
bpy.ops.object.modifier_apply(modifier=rm.name)
bpy.ops.object.select_all(action="DESELECT")
proxy.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
for bn in arm.data.bones: bn.use_deform = saved[bn.name]
if not proxy.vertex_groups:
    raise SystemExit("automatic weights failed on the body proxy too")
for g in proxy.vertex_groups: b.vertex_groups.new(name=g.name)
dt = b.modifiers.new("weights", "DATA_TRANSFER"); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
bpy.ops.object.select_all(action="DESELECT")
b.select_set(True); bpy.context.view_layer.objects.active = b
bpy.ops.object.modifier_apply(modifier=dt.name)
bpy.data.objects.remove(proxy)
b.parent = arm; b.parent_type = "OBJECT"
md = b.modifiers.new("Armature", "ARMATURE"); md.object = arm
print("body weighted:", len(b.vertex_groups), "groups")

bpy.ops.object.select_all(action="DESELECT")
for o in [arm] + [c for c in arm.children]: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=cfg["out"], export_format="GLB", use_selection=True, export_skins=True,
                          export_morph=True, export_animations=False, export_apply=False)
print("assembled", cfg["out"])
