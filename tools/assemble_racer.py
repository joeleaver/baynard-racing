"""Assemble a Braynard racer puppet from separately generated head, body and arm meshes, with its own skeleton.

blender -b --factory-startup --python tools/assemble_racer.py -- <racer>/puppet.json

Unlike assemble_puppet.py (Hettie, whose skeleton and face pieces come from a hifipushie build), this builds the
standard humanoid (Mixamo-named) skeleton from the racer's own pieces and cuts a hinged jaw out of the head.
Metres, Z up, the racer faces -Y. Paths are relative to the config file.

  head: {"glb", "z": [bottom, top], "centre": [x, y], "faces", "turn"}         rigid on the Head bone
  body: {"glb", "z": [0, top], "centre": [x, y], "faces", "turn"}              skinned to hips, spine and legs
  arm:  {"glb", "length", "shoulder": [x, y, z], "splay": deg, "faces", "turn"} left arm (mirrored for the right),
        hanging from the shoulder point and splayed out from the body; skinned to arm, forearm and hand
  jaw:  {"box": [[x0, y0, z0], [x1, y1, z1]], "pivot": [y, z], "open": deg}    head faces inside the box become the
        lower jaw, which opens on the "jawOpen" shape key; a dark mouth sits behind it
  rig:  optional landmark overrides: "crotch", "knee", "ankle", "neck", "elbow" (z values) ...
  edit: optional repairs on any piece before it is sized (see edit() below)
  "turn" is extra degrees about Z when a generated piece came out facing the wrong way.
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import import_generated, only, retopo, bounds

cfg_path = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
cfg = json.load(open(cfg_path))
here = os.path.dirname(cfg_path)
P = lambda p: os.path.normpath(os.path.join(here, p))
bpy.ops.wm.read_factory_settings(use_empty=True)
VOX = cfg.get("voxel", 0.005)
R = cfg.get("rig", {})


def edit(o, e):
    """Repair a generated piece before it is sized. Generated meshes guess at the sides their image didn't show,
    and sometimes put parts in the wrong place. Coordinates are the piece's own, as imported (after "turn").

      cut:    [box, ...]                       faces wholly inside a box are removed
      move:   [{"box", "turn", "about": [x, y], "shift": [x, y, z]}]   faces in the box are lifted off, turned
              about a vertical axis through "about", shifted, and put back after any mirroring
      mirror: "front" | "back", at "plane" (y, default 0): keep that half and mirror it onto the other
      clamp:  [{"box", "centre": [x, y, z], "radius"}]   lumps inside a box are pressed back onto a sphere, or an
              ellipsoid when "radius" is [rx, ry, rz]; it fades out
              over "feather" (default 0.05) inside the box's sides
              (smoothing doesn't work on generated shells: they tear). A box is [[x0, y0, z0], [x1, y1, z1]].
      press:  [{"box", "axis": "x"|"y"|"z", "to"}]       a lump inside a box is pressed flat at "to"
    """
    if not e: return
    bm = bmesh.new(); bm.from_mesh(o.data)
    inside = lambda box, p: all(box[0][i] <= p[i] <= box[1][i] for i in range(3))
    in_box = lambda box: [f for f in bm.faces if all(inside(box, v.co) for v in f.verts)]
    for box in e.get("cut", []):
        bmesh.ops.delete(bm, geom=in_box(box), context="FACES")
    parts = []
    for mv in e.get("move", []):
        faces = in_box(mv["box"])
        part = bmesh.ops.duplicate(bm, geom=faces)
        pv = [g for g in part["geom"] if isinstance(g, bmesh.types.BMVert)]
        ax, ay = mv.get("about", [0, 0])
        m = (Matrix.Translation(Vector(mv.get("shift", [0, 0, 0])) + Vector((ax, ay, 0))) @
             Matrix.Rotation(math.radians(mv.get("turn", 0)), 4, "Z") @ Matrix.Translation(Vector((-ax, -ay, 0))))
        bmesh.ops.transform(bm, matrix=m, verts=pv)
        parts.append(set(pv))
        bmesh.ops.delete(bm, geom=faces, context="FACES")
        print("moved", len(faces), "faces")
    if e.get("mirror"):
        moved = set().union(*parts) if parts else set()
        keep_front = e["mirror"] == "front"; py = e.get("plane", 0.0)
        side = [v for v in bm.verts if v not in moved]
        # bisect only the piece itself, then drop the far half
        bmesh.ops.bisect_plane(bm, geom=side + [f for f in bm.faces if all(v not in moved for v in f.verts)] +
                               [ed for ed in bm.edges if all(v not in moved for v in ed.verts)],
                               plane_co=(0, py, 0), plane_no=(0, 1, 0))
        far = [v for v in bm.verts if v not in moved and ((v.co.y > py + 1e-6) if keep_front else (v.co.y < py - 1e-6))]
        bmesh.ops.delete(bm, geom=far, context="VERTS")
        half = [f for f in bm.faces if all(v not in moved for v in f.verts)]
        dup = bmesh.ops.duplicate(bm, geom=half)
        dv = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
        for v in dv: v.co.y = 2 * py - v.co.y
        bmesh.ops.reverse_faces(bm, faces=[g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)])
        print("mirrored the", e["mirror"], "half")
    for cl in e.get("clamp", []):
        c = Vector(cl["centre"]); r = cl["radius"]; r = Vector(r if isinstance(r, list) else [r] * 3); n = 0
        for v in bm.verts:
            d = v.co - c; q = sum((d[i] / r[i]) ** 2 for i in range(3))
            if inside(cl["box"], v.co) and q > 1:
                # fade out towards the box's sides so the pressed patch meets the rest without a step
                edge = min(min(v.co[i] - cl["box"][0][i], cl["box"][1][i] - v.co[i]) for i in range(3))
                w = min(1.0, edge / cl.get("feather", 0.05)) if cl.get("feather", 0.05) > 0 else 1.0
                v.co = v.co.lerp(c + d / math.sqrt(q), w); n += 1
        print("clamped", n, "verts")
    for pr in e.get("press", []):
        i = "xyz".index(pr["axis"]); t = pr["to"]; n = 0
        up = (pr["box"][0][i] + pr["box"][1][i]) / 2 > t  # which side of "to" the lump is on
        for v in bm.verts:
            if inside(pr["box"], v.co) and ((v.co[i] > t) if up else (v.co[i] < t)):
                v.co[i] = t; n += 1
        print("pressed", n, "verts")
    bm.to_mesh(o.data); bm.free(); o.data.update()


def place(o, scale, offset):
    o.data.transform(Matrix.Translation(offset) @ Matrix.Scale(scale, 4)); o.data.update()


def fit_z(o, z0, z1, cx, cy):
    lo, hi = bounds(o); s = (z1 - z0) / (hi.z - lo.z)
    place(o, s, Vector((cx - (lo.x + hi.x) / 2 * s, cy - (lo.y + hi.y) / 2 * s, z0 - lo.z * s)))


# head
hc = cfg["head"]
h = import_generated(P(hc["glb"]), hc.get("turn", 0)); h.name = "head"; edit(h, hc.get("edit"))
fit_z(h, hc["z"][0], hc["z"][1], *hc["centre"])
h = retopo(h, hc.get("faces", 9000), VOX)

# body
bc = cfg["body"]
b = import_generated(P(bc["glb"]), bc.get("turn", 0)); b.name = "body"; edit(b, bc.get("edit"))
fit_z(b, bc["z"][0], bc["z"][1], *bc["centre"])
b = retopo(b, bc.get("faces", 9000), VOX)

# arm: long axis to Z, top at the shoulder, splayed out; then mirrored
ac = cfg["arm"]
a = import_generated(P(ac["glb"]), ac.get("turn", 0)); a.name = "arm_l"; edit(a, ac.get("edit"))
lo, hi = bounds(a); ext = hi - lo
long = max(range(3), key=lambda i: ext[i])
if long == 0: a.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
elif long == 1: a.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
lo, hi = bounds(a); s = ac["length"] / (hi.z - lo.z)
top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
a.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-top))  # top of the arm at the origin
a.data.transform(Matrix.Rotation(-math.radians(ac.get("splay", 12)), 4, "Y"))  # +X side: tilt the hand outward
a.data.transform(Matrix.Translation(Vector(ac["shoulder"]))); a.data.update()
a = retopo(a, ac.get("faces", 2500), VOX * 0.7, 512)
ar = a.copy(); ar.data = a.data.copy(); ar.name = "arm_r"; bpy.context.collection.objects.link(ar)
ar.data.transform(Matrix.Scale(-1, 4, Vector((1, 0, 0)))); ar.data.flip_normals(); ar.data.update()


# colour: pieces generated apart come out in slightly different tones of the same clay; match the head's and
# arms' light tones to the body's
def light_tone(img):
    px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    lum = px @ np.array([0.2126, 0.7152, 0.0722])
    return np.median(px[lum > 0.45], axis=0) if (lum > 0.45).sum() > 100 else None, px


if cfg.get("match_colour", True):
    target, _ = light_tone(b.data.materials[0].node_tree.nodes.active.image)
    for o in (h, a):
        img = o.data.materials[0].node_tree.nodes.active.image
        tone, px = light_tone(img)
        if target is None or tone is None: continue
        lum = px @ np.array([0.2126, 0.7152, 0.0722])
        k = np.clip((lum - 0.3) / 0.3, 0, 1)[:, None]
        img.pixels[:] = np.hstack([np.clip(px * (1 - k + k * (target / tone)), 0, 1), np.ones((len(px), 1))]).ravel()
        img.pack()
    ar.data.materials[0] = a.data.materials[0]

# jaw: the part of the head's face inside a smile-shaped outline becomes the lower jaw. The outline is flat along the
# box's top (under the snout or beak) and rounds down to the box's bottom; the head is cut cleanly along it first.
jc = cfg.get("jaw")
jaw = None
if jc:
    (x0, y0, z0), (x1, y1, z1) = jc["box"]
    cx, hx, hz = (x0 + x1) / 2, (x1 - x0) / 2, z1 - z0
    N = 12
    outline = [(cx + hx * math.cos(math.pi * i / N), z1 - hz * math.sin(math.pi * i / N)) for i in range(N + 1)]
    bm = bmesh.new(); bm.from_mesh(h.data)
    near = lambda v: x0 - 0.02 <= v.co.x <= x1 + 0.02 and y0 <= v.co.y <= y1 and z0 - 0.02 <= v.co.z <= z1 + 0.02
    for (ax, az), (bx, bz) in zip(outline, outline[1:] + outline[:1]):  # each side of the outline, closing along the top
        fs = [f for f in bm.faces if any(near(v) for v in f.verts)]
        es = list({e for f in fs for e in f.edges}); vs = list({v for f in fs for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=fs + es + vs, plane_co=(ax, 0, az), plane_no=(bz - az, 0, -(bx - ax)))
    def in_outline(x, z):
        if z > z1 or abs(x - cx) > hx: return False
        return ((x - cx) / hx) ** 2 + ((z1 - z) / hz) ** 2 <= 1.0 + 1e-6
    cut = set()
    for f in bm.faces:
        c = f.calc_center_median()
        if y0 <= c.y <= y1 and in_outline(c.x, c.z): cut.add(f.index)
    bm.to_mesh(h.data); bm.free()
    bm = bmesh.new(); bm.from_mesh(h.data)
    me = bpy.data.meshes.new("jaw"); tmp = bmesh.new(); tmp.from_mesh(h.data)
    bmesh.ops.delete(tmp, geom=[f for f in tmp.faces if f.index not in cut], context="FACES"); tmp.to_mesh(me); tmp.free()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in cut], context="FACES"); bm.to_mesh(h.data); bm.free()
    jaw = bpy.data.objects.new("jaw", me); bpy.context.collection.objects.link(jaw)
    me.materials.append(h.data.materials[0])
    print("jaw", len(cut), "faces")
    # give the jaw some thickness, so it doesn't read as a paper flap when it opens
    th = jc.get("thickness", 0.012)
    only(jaw); sd = jaw.modifiers.new("thick", "SOLIDIFY"); sd.thickness = th; sd.offset = -1
    bpy.ops.object.modifier_apply(modifier=sd.name)
    # the dark inside of the mouth, seen when the jaw opens
    mouth = bpy.data.meshes.new("mouth"); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    # it sits just behind the jaw's surface, hidden while the jaw is shut
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    jy = sum(v.co.y for v in me.vertices) / max(1, len(me.vertices))
    ry = max(0.03, hz * 0.6)
    jy += th
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector((cx, jy + ry + 0.008, z1 - hz * 0.35))) @
                        Matrix.Diagonal((hx * 0.98, ry, hz * 0.85, 1)), verts=bm.verts)
    for f in bm.faces: f.smooth = True
    bm.to_mesh(mouth); bm.free()
    mo = bpy.data.objects.new("mouth", mouth); bpy.context.collection.objects.link(mo)
    mm = bpy.data.materials.new("mouth"); mm.use_nodes = True
    mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.03, 0.03, 1)
    mm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    mouth.materials.append(mm)
    # jawOpen: the jaw turned down about its hinge (a positive turn about X drops the front, at -Y)
    jaw.shape_key_add(name="Basis"); sk = jaw.shape_key_add(name="jawOpen", from_mix=False)
    py, pz = jc["pivot"]; ang = math.radians(jc.get("open", 22))
    rot = Matrix.Translation(Vector((0, py, pz))) @ Matrix.Rotation(ang, 4, "X") @ Matrix.Translation(Vector((0, -py, -pz)))
    for i, v in enumerate(jaw.data.vertices): sk.data[i].co = rot @ v.co

# skeleton from the pieces
bco = np.array([v.co[:] for v in b.data.vertices])


def leg_split():
    """The crotch: the highest height where the body's bottom half splits into two legs (left and right)."""
    top = bco[:, 2].max()
    for z in np.arange(0.02, top * 0.6, 0.005):
        band = bco[np.abs(bco[:, 2] - z) < 0.006]
        if len(band) < 10: continue
        xs = np.sort(band[:, 0])
        gaps = np.diff(xs); g = gaps.argmax()
        if gaps[g] < 0.015 or not (xs[g] < 0 < xs[g + 1] or abs((xs[g] + xs[g + 1]) / 2) < 0.03):
            return z, None
    return top * 0.4, None


crotch = R.get("crotch")
if crotch is None:
    crotch, _ = leg_split()
legs = bco[bco[:, 2] < crotch]
leg_x = float(np.median(np.abs(legs[:, 0]))) if len(legs) else 0.08
foot = bco[bco[:, 2] < 0.03]
toe_y = float(foot[:, 1].min()) if len(foot) else -0.08
heel_y = float(np.median(foot[:, 1])) if len(foot) else 0.0
ankle = R.get("ankle", max(0.04, crotch * 0.15))
knee = R.get("knee", (crotch + ankle) / 2)
hips = crotch + R.get("hips_above_crotch", 0.03)
neck = R.get("neck", hc["z"][0] + 0.01)
sh = Vector(ac["shoulder"])
hand_len = ac["length"] * 0.28
spl = math.radians(ac.get("splay", 12))
along = lambda d: sh + Vector((math.sin(spl) * d, 0, -math.cos(spl) * d))
elbow, wrist, hand_end = along(ac["length"] * 0.45), along(ac["length"] * 0.72), along(ac["length"])
cy = float(np.median(bco[:, 1]))

ad = bpy.data.armatures.new("rig"); arm = bpy.data.objects.new("rig", ad); bpy.context.collection.objects.link(arm)
only(arm); bpy.ops.object.mode_set(mode="EDIT")
E = ad.edit_bones


def bone(name, head, tail, parent=None):
    e = E.new("mixamorig:" + name); e.head = Vector(head); e.tail = Vector(tail)
    if parent: e.parent = E["mixamorig:" + parent]; e.use_connect = False
    return e


sp = [hips + (neck - hips) * f for f in (0, 0.3, 0.6, 0.85, 1.0)]
bone("Hips", (0, cy, hips), (0, cy, sp[1]))
bone("Spine", (0, cy, sp[1]), (0, cy, sp[2]), "Hips")
bone("Spine1", (0, cy, sp[2]), (0, cy, sp[3]), "Spine")
bone("Spine2", (0, cy, sp[3]), (0, cy, neck), "Spine1")
bone("Neck", (0, cy, neck), (0, cy, neck + 0.03), "Spine2")
hy = hc["centre"][1]
bone("Head", (0, hy, neck + 0.03), (0, hy, hc["z"][1]), "Neck")
bone("HeadTop_End", (0, hy, hc["z"][1]), (0, hy, hc["z"][1] + 0.04), "Head")
for side, sx in (("Left", 1), ("Right", -1)):
    m = lambda v: (sx * v[0], v[1], v[2])
    bone(side + "Shoulder", (sx * 0.02, sh.y, sh.z), m(sh), "Spine2")
    bone(side + "Arm", m(sh), m(elbow), side + "Shoulder")
    bone(side + "ForeArm", m(elbow), m(wrist), side + "Arm")
    bone(side + "Hand", m(wrist), m(hand_end), side + "ForeArm")
    bone(side + "UpLeg", (sx * leg_x, cy, hips), (sx * leg_x, cy, knee), "Hips")
    bone(side + "Leg", (sx * leg_x, cy, knee), (sx * leg_x, heel_y, ankle), side + "UpLeg")
    bone(side + "Foot", (sx * leg_x, heel_y, ankle), (sx * leg_x, (heel_y + toe_y) / 2, 0.01), side + "Leg")
    bone(side + "ToeBase", (sx * leg_x, (heel_y + toe_y) / 2, 0.01), (sx * leg_x, toe_y, 0.01), side + "Foot")
    bone(side + "Toe_End", (sx * leg_x, toe_y, 0.01), (sx * leg_x, toe_y - 0.03, 0.01), side + "ToeBase")
bpy.ops.object.mode_set(mode="OBJECT")
print("rig", {"crotch": round(crotch, 3), "knee": round(knee, 3), "ankle": round(ankle, 3), "hips": round(hips, 3),
              "neck": round(neck, 3), "leg_x": round(leg_x, 3)})


def bind_rigid(o, bone_name):
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name=bone_name); g.add(range(len(o.data.vertices)), 1.0, "REPLACE")
    o.parent = arm; md = o.modifiers.new("Armature", "ARMATURE"); md.object = arm


def bind_auto(o, keys):
    """Automatic weights from only the named bones, computed on a closed voxel proxy and copied across."""
    saved = {bn.name: bn.use_deform for bn in ad.bones}
    for bn in ad.bones: bn.use_deform = any(bn.name.endswith(k) for k in keys)
    proxy = o.copy(); proxy.data = o.data.copy(); bpy.context.collection.objects.link(proxy)
    rm = proxy.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.008
    only(proxy); bpy.ops.object.modifier_apply(modifier=rm.name)
    bpy.ops.object.select_all(action="DESELECT")
    proxy.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    for bn in ad.bones: bn.use_deform = saved[bn.name]
    if not proxy.vertex_groups: raise SystemExit(f"automatic weights failed for {o.name}")
    for g in proxy.vertex_groups: o.vertex_groups.new(name=g.name)
    dt = o.modifiers.new("weights", "DATA_TRANSFER"); dt.object = proxy
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    only(o); bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(proxy)
    o.parent = arm; md = o.modifiers.new("Armature", "ARMATURE"); md.object = arm


bind_rigid(h, "mixamorig:Head")
if jaw:
    bind_rigid(jaw, "mixamorig:Head"); bind_rigid(mo, "mixamorig:Head")
bind_auto(b, [":Hips", ":Spine", ":Spine1", ":Spine2", "UpLeg", "Leg", "Foot", "ToeBase"])
for o, side in ((a, "Left"), (ar, "Right")):
    bind_auto(o, [side + "Arm", side + "ForeArm", side + "Hand"])

bpy.ops.object.select_all(action="DESELECT")
for o in [arm] + list(arm.children): o.select_set(True)
bpy.ops.export_scene.gltf(filepath=P(cfg["out"]), export_format="GLB", use_selection=True, export_skins=True,
                          export_morph=True, export_animations=False, export_apply=False)
print("assembled", P(cfg["out"]))
