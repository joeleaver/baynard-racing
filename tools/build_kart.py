"""Build a game kart from modelled parts, in the claymation look, with baked textures.

blender -b --factory-startup --python tools/build_kart.py -- <spec.json> [--render <prefix>] [--fast]

Generated meshes make good shape guides but poor game meshes (baked paint, fused wheels, triangle soup), so
karts are modelled from parts instead. Units are metres; the kart faces -Y, +X is its left, Z is up, and the
ground is z = 0. --fast skips the texture bake (for checking shapes and clashes).

Spec (paths relative to the spec file):
  colours   {name: {"rgb": [r, g, b] sRGB 0-1, "kind": "clay" | "wood" | "rubber" | "metal" | "rust"}}
            "roughness": overrides the kind's roughness (0.2 is polished chrome)
            "rust": 0-1 lets rust eat into the surface in ragged, crusty, dull patches (for tin and steel)
            "dirt": 0-1 adds patches of dried mud and dust (mud: [r, g, b] sets their colour for the whole kart;
            "dirt_rgb" on a colour sets it for that colour alone, e.g. scraps of red label on a tin)
            rust ignores rgb and paints patchy orange, brown and iron grey (rust_stops overrides the patches)
  parts     list of parts, each {"type": ..., "colour": ..., "id": label} plus:
    wheel   pos [x, y, z] hub centre, radius, width, hub (colour), name (wheel_FL/FR/RL/RR/F/R), lugs (count of
            chevron tread lugs; 0 gives a smooth balloon tyre with a groove round the middle)
            Each wheel is its own object with its origin at the hub, so the game spins it about X.
    tube    points [[x, y, z], ...], radius; "smooth": true bends through the points instead of jointing at them
    box     centre, size [x, y, z], bevel (rounding in metres), tilt [rx, ry, rz] degrees (optional)
    planks  centre, size, count, axis ("z" stacks planks upward; "x"/"y" lays them side by side), gap, bevel,
            jitter (small random tilt per plank, degrees), vary (tint spread, default 0.08)
    torus   centre, radius, thickness, tilt [rx, ry, rz] degrees
    disc    centre, radius, depth, tilt (a rounded cylinder along X before the tilt)
    ball    centre, radius, scale [x, y, z] (optional)
    tub     rings [[z, half-length, half-width, centre y], ...] from the bottom up, power (outline squareness,
            default 2.6), thickness (wall, default 0.03): a hollow open-topped shell such as a bathtub
    pipe_end  centre (the tube's end), radius (the tube's), lean (degrees about X), flare, wall, depth: the open
            mouth of an exhaust; give its tube "open_end": true
    can     centre, axis, length, radius, ridges, ridge_depth (fraction of radius), open (the +axis end is open
            and hollow, depth as a fraction of length): a tin can with beaded rims and dished lids
    turned  centre, axis, profile [[t, r], ...] (t along the axis): a lathe-turned shape such as a churn or bell
    coil    centre, axis, radius, turns, pitch, wire, messy (0-1): wire wound round something
    plate   points [[x, y], ...] (a convex outline in its own plane), thickness, centre, tilt (its face is local
            +Z), corner (rounding); layers [{points, colour, raise}], marks [{points | ball, radius, colour}] and
            bites [[x, y, r]] for a sign's face, artwork and teeth marks
  tube      "closed": true makes a loop (a rolled rim round a tub)
  wheel     "style": "drum" gives a tall drum tyre with soft shoulders instead of a balloon
            "cap": a colour gives a plain disc hub with a separate centre cap in that colour
  Parts that share a "fuse" label are melted into one soft piece (voxel remesh and smoothing), the way a clay
  seat is one lump rather than glued blocks.
  Parts may list "touches": ids they are meant to meet. Every other overlap between parts is reported as a CLASH,
  so a steering column through a board shows up before anyone sees a render.
  Any non-wheel part may carry "name" and "pivot" [x, y, z]: parts sharing a name become one moving object with
  its origin at the pivot (e.g. "steering_wheel", which the game turns with the steering). "axis" [x, y, z] says
  which way it turns (spec frame) and goes into the GLB as an extra, in the GLB's Y-up frame.
  Wheels carry extras too, in the GLB's frame: spin_axis [1, 0, 0] and, for front wheels (name ending F, FL or
  FR), steer_axis [0, 1, 0].
  view      camera angle for the 3/4 render, to match the concept (default 140: front to the left)
  lumps     clay lumpiness in metres (default 0.0025): a soft hand-made wobble on every surface
  texture   atlas size (default 2048); loose copies of the maps go to workspace/karts/<folder>/ unless
            texture_dir says otherwise
  budget    triangle budgets for the shipped mesh {"body", "wheel_F", "wheel_R", "other"}: the modelled parts are
            decimated to these and their full detail is baked into the colour and normal maps
  out       GLB to write: a "kart" root with "body" and the moving objects, all sharing one material whose colour
            (wood grain, clay grain, crease shading) and normal maps are baked into one atlas
"""
import bpy, bmesh, sys, os, json, math, random
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
spec_path = os.path.abspath(argv[0])
spec = json.load(open(spec_path))
here = os.path.dirname(spec_path)
render = argv[argv.index("--render") + 1] if "--render" in argv else None
fast = "--fast" in argv
random.seed(spec.get("seed", 1))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
LUMPS = spec.get("lumps", 0.0025)


def lin(c):  # sRGB -> linear
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def colour(name):
    c = spec["colours"][name]
    return (c, "clay") if isinstance(c, list) else (c["rgb"], c.get("kind", "clay"))


# ---------------------------------------------------------------- bake materials, one per kind of surface
def node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items(): setattr(n, k, v)
    return n


def ramp(nt, src, stops):
    r = node(nt, "ShaderNodeValToRGB"); el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*[stops[0][1]] * 3, 1)
    el[1].position, el[1].color = stops[-1][0], (*[stops[-1][1]] * 3, 1)
    for pos, v in stops[1:-1]:
        e = el.new(pos); e.color = (v, v, v, 1)
    nt.links.new(src, r.inputs[0])
    return r.outputs[0]


def make_material(kind, dirt=0.0, dirt_rgb=None, rust=0.0, rough=None):
    """A procedural material for baking: the part's tint (vertex colour Col) shaded with grain for its kind."""
    m = bpy.data.materials.new(kind); m.use_nodes = True
    nt = m.node_tree; L = nt.links.new
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough if rough is not None else \
        {"metal": 0.4, "rubber": 0.85, "rust": 0.88, "wood": 0.7}.get(kind, 0.75)
    col = node(nt, "ShaderNodeVertexColor", layer_name="Col").outputs["Color"]
    geo = node(nt, "ShaderNodeNewGeometry").outputs["Position"]
    # every kind: a slow mottle in colour and a fine sandy grain in the surface, like soft modelling clay
    mot = node(nt, "ShaderNodeTexNoise"); mot.inputs["Scale"].default_value = 7; mot.inputs["Detail"].default_value = 3
    L(geo, mot.inputs["Vector"])
    mot_k = ramp(nt, mot.outputs["Fac"], [(0.3, 0.9), (0.7, 1.07)])
    sand = node(nt, "ShaderNodeTexNoise"); sand.inputs["Scale"].default_value = 170
    sand.inputs["Detail"].default_value = 3; L(geo, sand.inputs["Vector"])
    height = sand.outputs["Fac"]; strength = 0.32
    tint = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); tint.inputs["Factor"].default_value = 1
    L(col, tint.inputs[6]); L(mot_k, tint.inputs[7]); out = tint.outputs[2]
    grit = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); grit.inputs["Factor"].default_value = 1
    L(out, grit.inputs[6]); L(ramp(nt, sand.outputs["Fac"], [(0.35, 0.9), (0.65, 1.06)]), grit.inputs[7])
    out = grit.outputs[2]  # the sandy grain shows a little in the colour too, as on a clay model
    if kind == "wood":
        rest = node(nt, "ShaderNodeAttribute", attribute_name="rest").outputs["Vector"]
        sq = node(nt, "ShaderNodeVectorMath", operation="MULTIPLY"); sq.inputs[1].default_value = (0.12, 1, 1)
        L(rest, sq.inputs[0])
        wave = node(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
        wave.inputs["Scale"].default_value = 4.5; wave.inputs["Distortion"].default_value = 3
        wave.inputs["Detail"].default_value = 2; wave.inputs["Detail Scale"].default_value = 1.5
        L(sq.outputs[0], wave.inputs["Vector"])
        groove = ramp(nt, wave.outputs["Fac"], [(0.0, 0.0), (0.07, 0.0), (0.16, 1.0), (1.0, 1.0)])  # dark cut lines
        streak = node(nt, "ShaderNodeTexNoise"); streak.inputs["Scale"].default_value = 3
        streak.inputs["Detail"].default_value = 4
        st = node(nt, "ShaderNodeVectorMath", operation="MULTIPLY"); st.inputs[1].default_value = (4, 90, 90)
        L(rest, st.inputs[0]); L(st.outputs[0], streak.inputs["Vector"])
        streak_k = ramp(nt, streak.outputs["Fac"], [(0.35, 0.86), (0.65, 1.06)])
        gk = ramp(nt, groove, [(0.0, 0.55), (1.0, 1.0)])
        for k in (streak_k, gk):
            mm = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); mm.inputs["Factor"].default_value = 1
            L(out, mm.inputs[6]); L(k, mm.inputs[7]); out = mm.outputs[2]
        h = node(nt, "ShaderNodeMath", operation="MULTIPLY_ADD"); h.inputs[1].default_value = 0.15
        L(sand.outputs["Fac"], h.inputs[0]); L(groove, h.inputs[2]); height = h.outputs[0]; strength = 0.45
    if kind == "rubber":
        strength = 0.25
    if rough is not None and rough < 0.35:
        strength = 0.03  # polished: only a faint grain
    if kind == "rust":
        pat = node(nt, "ShaderNodeTexNoise"); pat.inputs["Scale"].default_value = 5.5
        pat.inputs["Detail"].default_value = 9; pat.inputs["Roughness"].default_value = 0.62
        L(geo, pat.inputs["Vector"])
        rr = node(nt, "ShaderNodeValToRGB"); el = rr.color_ramp.elements
        stops = spec.get("rust_stops", [(0.0, (0.17, 0.13, 0.11)), (0.36, (0.33, 0.2, 0.13)), (0.47, (0.6, 0.3, 0.12)),
                                         (0.56, (0.44, 0.26, 0.15)), (0.66, (0.36, 0.34, 0.33)), (1.0, (0.2, 0.16, 0.14))])
        el[0].position, el[0].color = stops[0][0], (*lin(stops[0][1]), 1)
        el[1].position, el[1].color = stops[-1][0], (*lin(stops[-1][1]), 1)
        for pos, cc in stops[1:-1]:
            el.new(pos).color = (*lin(cc), 1)
        L(pat.outputs["Fac"], rr.inputs[0])
        fine = node(nt, "ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 30; fine.inputs["Detail"].default_value = 6
        L(geo, fine.inputs["Vector"])
        fine_k = ramp(nt, fine.outputs["Fac"], [(0.3, 0.72), (0.5, 1.0), (0.7, 1.22)])
        mm = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); mm.inputs["Factor"].default_value = 1
        L(rr.outputs[0], mm.inputs[6]); L(fine_k, mm.inputs[7]); out = mm.outputs[2]
        pit = node(nt, "ShaderNodeTexNoise"); pit.inputs["Scale"].default_value = 90; pit.inputs["Detail"].default_value = 4
        L(geo, pit.inputs["Vector"])
        h = node(nt, "ShaderNodeMath", operation="MULTIPLY_ADD"); h.inputs[1].default_value = 0.6
        L(pit.outputs["Fac"], h.inputs[0]); L(sand.outputs["Fac"], h.inputs[2]); height = h.outputs[0]; strength = 0.6
    if rust:  # rust eating into metal: ragged patches, crusty and pitted, dull where it has taken hold
        big = node(nt, "ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 3.2
        big.inputs["Detail"].default_value = 12; big.inputs["Roughness"].default_value = 0.72
        big.inputs["Distortion"].default_value = 0.6; L(geo, big.inputs["Vector"])
        lo = 0.6 - 0.25 * rust
        mask = ramp(nt, big.outputs["Fac"], [(lo, 0.0), (lo + 0.05, 1.0)])
        mnode = node(nt, "ShaderNodeMath", operation="MULTIPLY"); mnode.name = "rustmask"
        mnode.inputs[1].default_value = 1.0; L(mask, mnode.inputs[0]); mask = mnode.outputs[0]
        tone = node(nt, "ShaderNodeTexNoise"); tone.inputs["Scale"].default_value = 16; tone.inputs["Detail"].default_value = 8
        L(geo, tone.inputs["Vector"])
        rc = node(nt, "ShaderNodeValToRGB"); el = rc.color_ramp.elements
        stops = [(0.0, (0.2, 0.11, 0.07)), (0.38, (0.36, 0.17, 0.08)), (0.5, (0.62, 0.3, 0.1)), (0.6, (0.5, 0.25, 0.1)),
                 (1.0, (0.24, 0.13, 0.08))]
        el[0].position, el[0].color = stops[0][0], (*lin(stops[0][1]), 1)
        el[1].position, el[1].color = stops[-1][0], (*lin(stops[-1][1]), 1)
        for pos, cc in stops[1:-1]: el.new(pos).color = (*lin(cc), 1)
        L(tone.outputs["Fac"], rc.inputs[0])
        mx = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MIX")
        L(mask, mx.inputs["Factor"]); L(out, mx.inputs[6]); L(rc.outputs[0], mx.inputs[7]); out = mx.outputs[2]
        crust = node(nt, "ShaderNodeTexNoise"); crust.inputs["Scale"].default_value = 110; crust.inputs["Detail"].default_value = 5
        L(geo, crust.inputs["Vector"])
        cm = node(nt, "ShaderNodeMath", operation="MULTIPLY_ADD"); L(crust.outputs["Fac"], cm.inputs[0])
        cm.inputs[1].default_value = 0.9; cm.inputs[2].default_value = 0.35
        cmm = node(nt, "ShaderNodeMath", operation="MULTIPLY"); L(cm.outputs[0], cmm.inputs[0]); L(mask, cmm.inputs[1])
        hh = node(nt, "ShaderNodeMath", operation="ADD"); L(height, hh.inputs[0]); L(cmm.outputs[0], hh.inputs[1])
        height = hh.outputs[0]; strength = max(strength, 0.5)
        rg = node(nt, "ShaderNodeMath", operation="MULTIPLY_ADD"); L(mask, rg.inputs[0])
        base_r = b.inputs["Roughness"].default_value; rg.inputs[1].default_value = 0.92 - base_r
        rg.inputs[2].default_value = base_r; L(rg.outputs[0], b.inputs["Roughness"])
    if dirt:  # dried mud and dust in patches, more of it the higher dirt is (0-1)
        mud = node(nt, "ShaderNodeTexNoise"); mud.inputs["Scale"].default_value = 4.5 if dirt_rgb else 9
        mud.inputs["Detail"].default_value = 7; mud.inputs["Roughness"].default_value = 0.7; L(geo, mud.inputs["Vector"])
        lo = 0.62 - 0.3 * dirt
        if dirt_rgb:
            # scraps of label or paint: blocky cells (some kept, some torn away), with ragged edges from noise
            warp = node(nt, "ShaderNodeVectorMath", operation="ADD"); L(geo, warp.inputs[0])
            wsc = node(nt, "ShaderNodeVectorMath", operation="SCALE"); wsc.inputs["Scale"].default_value = 0.035
            L(mud.outputs["Color"], wsc.inputs[0]); L(wsc.outputs[0], warp.inputs[1])
            vor = node(nt, "ShaderNodeTexVoronoi", distance="CHEBYCHEV"); vor.inputs["Scale"].default_value = 7
            L(warp.outputs[0], vor.inputs["Vector"])
            sep = node(nt, "ShaderNodeSeparateColor"); L(vor.outputs["Color"], sep.inputs["Color"])
            keep = 1 - 0.75 * dirt
            mask = ramp(nt, sep.outputs["Red"], [(keep, 0.0), (keep + 0.005, 1.0)])
        else:
            mask = ramp(nt, mud.outputs["Fac"], [(lo, 0.0), (lo + 0.12, 0.9), (1.0, 1.0)])
        mm = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MIX")
        L(mask, mm.inputs["Factor"]); L(out, mm.inputs[6])
        mudc = lin(dirt_rgb or spec.get("mud", [0.4, 0.31, 0.22])); mm.inputs[7].default_value = (*mudc, 1)
        gr = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); gr.inputs["Factor"].default_value = 1
        L(mm.outputs[2], gr.inputs[6]); L(ramp(nt, sand.outputs["Fac"], [(0.3, 0.85), (0.7, 1.1)]), gr.inputs[7])
        out = gr.outputs[2]
    L(out, b.inputs["Base Color"])
    bump = node(nt, "ShaderNodeBump"); bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.002
    L(height, bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])
    return m


MATS = {}
def material(kind, dirt=0.0, dirt_rgb=None, rust=0.0, rough=None):
    key = (kind, dirt, tuple(dirt_rgb) if dirt_rgb else None, rust, rough)
    if key not in MATS: MATS[key] = make_material(kind, dirt, dirt_rgb, rust, rough)
    return MATS[key]


# ---------------------------------------------------------------- geometry helpers
def new_obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
    return o


def set_rest(o, inv, order=(0, 1, 2)):
    """Store each vertex's position in the part's own frame (long axis first) for the wood grain.

    Each part gets its own random offset, so no two boards share a grain (otherwise every board's pattern starts
    at its own centre and the same line runs through the middle of all of them)."""
    a = o.data.attributes.new("rest", "FLOAT_VECTOR", "POINT")
    off = [random.uniform(-3, 3) for _ in range(3)]
    for v, d in zip(o.data.vertices, a.data):
        q = inv @ v.co; d.vector = (q[order[0]] + off[0], q[order[1]] + off[1], q[order[2]] + off[2])


CLOUDS = bpy.data.textures.new("lumps", "CLOUDS"); CLOUDS.noise_scale = 0.09


def finish(o, colour_name, subdiv=2, vary=0.0, lumps=None):
    rgb, kind = colour(colour_name)
    c = spec["colours"][colour_name]; dirt = c.get("dirt", 0.0) if isinstance(c, dict) else 0.0
    drgb = c.get("dirt_rgb") if isinstance(c, dict) else None
    rst = c.get("rust", 0.0) if isinstance(c, dict) else 0.0
    rgh = c.get("roughness") if isinstance(c, dict) else None
    o.data.materials.clear(); o.data.materials.append(material(kind, dirt, drgb, rst, rgh))
    if subdiv:
        s = o.modifiers.new("subd", "SUBSURF"); s.levels = s.render_levels = subdiv
    lumps = LUMPS if lumps is None else lumps
    if lumps:
        d = o.modifiers.new("lumps", "DISPLACE"); d.texture = CLOUDS; d.strength = lumps; d.mid_level = 0.5
        d.texture_coords = "GLOBAL"
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    for p in o.data.polygons: p.use_smooth = True
    paint(o, rgb, vary)
    return o


def paint(o, rgb, vary=0.0):
    c = list(rgb)
    if vary:
        k = random.uniform(1 - vary, 1 + vary); c = [min(1, x * k) for x in c]
    c = lin(c); me = o.data
    if "Col" in me.color_attributes: me.color_attributes.remove(me.color_attributes["Col"])
    me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for d in me.color_attributes["Col"].data: d.color = (*c, 1)


def rounded_box(name, centre, size, bevel, tilt=(0, 0, 0), segments=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    b = min(bevel, min(size) / 2 - 1e-4)
    if b > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=segments, profile=0.5, affect="EDGES")
    M = Matrix.Translation(Vector(centre)) @ Euler([math.radians(a) for a in tilt]).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    o = new_obj(name, bm)
    order = sorted(range(3), key=lambda a: -size[a])  # grain runs along the longest side
    set_rest(o, M.inverted(), order)
    return o


def lathe(name, profile, segs=40):
    """Spin a closed 2D profile [(x, r), ...] round the X axis."""
    bm = bmesh.new()
    rings = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        rings.append([bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for x, r in profile])
    n = len(profile)
    for k in range(segs):
        A, B = rings[k], rings[(k + 1) % segs]
        for j in range(n - 1):
            if profile[j][1] == 0 and profile[j + 1][1] == 0: continue
            vs = [A[j], B[j], B[j + 1], A[j + 1]]
            if profile[j][1] == 0: vs = [A[j], B[j + 1], A[j + 1]]
            elif profile[j + 1][1] == 0: vs = [A[j], B[j], A[j + 1]]
            try: bm.faces.new(vs)
            except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = new_obj(name, bm); set_rest(o, Matrix())
    return o


def cylinder(name, radius, depth, bevel, segs=32):
    """A cylinder along X, centred on the origin, with rounded rims."""
    h = depth / 2; b = min(bevel, h * 0.95, radius * 0.95)
    prof = [(-h, 0), (-h, radius - b)]
    for k in range(1, 5):
        t = k / 5 * math.pi / 2
        prof.append((-h + b - b * math.cos(t), radius - b + b * math.sin(t)))
    prof += [(-h + b, radius), (h - b, radius)]
    for k in range(1, 5):
        t = k / 5 * math.pi / 2
        prof.append((h - b + b * math.sin(t), radius - b + b * math.cos(t)))
    prof += [(h, radius - b), (h, 0)]
    return lathe(name, prof, segs)


# ---------------------------------------------------------------- parts
def tiltM(p):
    return Matrix.Translation(Vector(p["centre"])) @ Euler([math.radians(t) for t in p.get("tilt", (0, 0, 0))]).to_matrix().to_4x4()


def part_box(p, i):
    return finish(rounded_box(f"box{i}", p["centre"], p["size"], p.get("bevel", 0.01), p.get("tilt", (0, 0, 0))),
                  p["colour"], p.get("subdiv", 2))


def part_planks(p, i):
    c, s, n = Vector(p["centre"]), Vector(p["size"]), p["count"]
    ax = "xyz".index(p.get("axis", "z")); gap = p.get("gap", 0.008); jit = p.get("jitter", 1.5)
    step = (s[ax] - gap * (n - 1)) / n
    out = []
    for k in range(n):
        ps = s.copy(); ps[ax] = step * random.uniform(0.94, 1.0)
        pc = c.copy(); pc[ax] = c[ax] - s[ax] / 2 + step / 2 + k * (step + gap)
        tilt = [random.uniform(-jit, jit) for _ in range(3)]; tilt[ax] = 0
        long = max(range(3), key=lambda a: ps[a] if a != ax else -1)
        ps[long] *= random.uniform(0.98, 1.015)  # hand-cut: boards differ a little
        o = rounded_box(f"plank{i}_{k}", pc, ps, p.get("bevel", 0.012), tilt)
        out.append(finish(o, p["colour"], p.get("subdiv", 2), p.get("vary", 0.08)))
    return out


def part_tube(p, i):
    cu = bpy.data.curves.new(f"tube{i}", "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = p["radius"]; cu.bevel_resolution = 4; cu.use_fill_caps = True
    pts = p["points"]; closed = p.get("closed", False); smooth = p.get("smooth", False) or closed
    sp = cu.splines.new("NURBS" if smooth else "POLY")
    sp.points.add(len(pts) - 1)
    for q, v in zip(sp.points, pts): q.co = (*v, 1)
    if smooth: sp.use_endpoint_u = not closed; sp.order_u = 3; sp.resolution_u = 10
    if closed: sp.use_cyclic_u = True
    o = bpy.data.objects.new(f"tube{i}", cu); scene.collection.objects.link(o)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target="MESH"); o.select_set(False)
    o = bpy.context.view_layer.objects.active
    set_rest(o, Matrix())
    parts = [o]
    ends = [] if closed else [pts[0], pts[-1]] if smooth else pts  # rounded ends; balls at jointed bends
    if p.get("open_end") and ends: ends = ends[:-1]  # a pipe_end part finishes this end instead
    for v in ends:
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=p["radius"] * 1.0)
        bmesh.ops.translate(bm, vec=Vector(v), verts=bm.verts); b = new_obj(f"joint{i}", bm); set_rest(b, Matrix())
        parts.append(b)
    for e in parts: finish(e, p["colour"], 0, lumps=LUMPS * 0.5)
    return parts


def part_torus(p, i):
    bm = bmesh.new()
    R, r = p["radius"], p["thickness"]
    segs, ring = 40, 12
    verts = []
    for a in range(segs):
        ta = 2 * math.pi * a / segs
        verts.append([bm.verts.new(((R + r * math.cos(2 * math.pi * b / ring)) * math.cos(ta),
                                    (R + r * math.cos(2 * math.pi * b / ring)) * math.sin(ta),
                                    r * math.sin(2 * math.pi * b / ring))) for b in range(ring)])
    for a in range(segs):
        for b in range(ring):
            bm.faces.new((verts[a][b], verts[(a + 1) % segs][b], verts[(a + 1) % segs][(b + 1) % ring], verts[a][(b + 1) % ring]))
    bmesh.ops.transform(bm, matrix=tiltM(p), verts=bm.verts)
    o = new_obj(f"torus{i}", bm); set_rest(o, Matrix())
    return finish(o, p["colour"], 0)


def part_disc(p, i):
    o = cylinder(f"disc{i}", p["radius"], p["depth"], p.get("bevel", p["depth"] / 3))
    o.data.transform(tiltM(p))
    return finish(o, p["colour"], 0)


def part_ball(p, i):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=p["radius"])
    bmesh.ops.scale(bm, vec=Vector(p.get("scale", (1, 1, 1))), verts=bm.verts)
    bmesh.ops.transform(bm, matrix=tiltM(p), verts=bm.verts)
    o = new_obj(f"ball{i}", bm); set_rest(o, Matrix())
    return finish(o, p["colour"], 0)


def part_pipe_end(p, i):
    """The open mouth of a pipe: a flared lip round a hollow, set on the end of a tube. centre is the tube's end,
    radius the tube's, lean tips it forward/back about X (degrees from upright), flare widens the lip."""
    r = p["radius"]; f = p.get("flare", 1.25); t = p.get("wall", 0.22) * r; d = p.get("depth", 1.0) * r
    R = r * f; ri = r - t
    prof = [(-0.9 * r, 0), (-0.9 * r, r * 1.02), (0.1 * r, r * 1.05), (0.3 * r, R * 0.96), (0.45 * r, R),
            (0.58 * r, R * 0.95), (0.62 * r, (R + ri) / 2), (0.55 * r, ri * 1.05), (0.4 * r, ri), (-d, ri), (-d, 0)]
    o = lathe(f"pipe_end{i}", prof, 40)
    M = Matrix.Translation(Vector(p["centre"])) @ Matrix.Rotation(math.radians(p.get("lean", 0)), 4, "X") \
        @ Matrix.Rotation(math.radians(-90), 4, "Y")
    o.data.transform(M)
    return finish(o, p["colour"], 1, lumps=LUMPS * 0.5)


def axis_matrix(centre, axis):
    """Place something built along X so that X runs along axis, centred on centre."""
    q = Vector((1, 0, 0)).rotation_difference(Vector(axis).normalized())
    return Matrix.Translation(Vector(centre)) @ q.to_matrix().to_4x4()


def part_can(p, i):
    """A tin can: ridged sides, beaded rims and dished lids with rings. centre, axis, length, radius, ridges."""
    L, R = p["length"], p["radius"]; h = L / 2; n = p.get("ridges", 4); bead = R * 0.06
    lid = [(-h + 0.016, 0), (-h + 0.012, R * 0.3), (-h + 0.018, R * 0.42), (-h + 0.01, R * 0.58), (-h + 0.016, R * 0.72),
           (-h + 0.008, R * 0.86), (-h - 0.004, R * 0.96), (-h, R + bead), (-h + 0.014, R + bead * 1.2), (-h + 0.028, R)]
    body = []
    if n:
        a, b = -h + 0.06, h - 0.06
        dep = p.get("ridge_depth", 0.035)
        for k in range(n * 6 + 1):  # rounded corrugations: a cosine bump per ridge
            x = a + (b - a) * k / (n * 6)
            body.append((x, R * (1 + dep * (0.5 - 0.5 * math.cos(2 * math.pi * k / 6)))))
    if p.get("open"):  # open top (the +axis end): a rolled lip and a hollow inside, like an exhaust
        ri = R * 0.9; dep = p.get("depth", 0.8) * L
        top = [(h - 0.028, R), (h - 0.014, R + bead * 1.2), (h, R + bead), (h + 0.006, (R + ri) / 2 + bead * 0.4),
               (h, ri), (h - 0.02, ri * 0.98), (h - dep, ri * 0.97), (h - dep, 0)]
    else:
        top = [(-x, r) for x, r in reversed(lid)]
    prof = lid + body + top
    o = lathe(f"can{i}", prof, 40)
    o.data.transform(axis_matrix(p["centre"], p["axis"]))
    return finish(o, p["colour"], 1, lumps=LUMPS * 0.5)


def part_turned(p, i):
    """A shape turned on a lathe: profile [[t, r], ...] runs along axis from centre (t = 0) outward; start and end
    the profile on the axis (r = 0) to close it. For churns, bells, knobs."""
    o = lathe(f"turned{i}", [tuple(q) for q in p["profile"]], p.get("segments", 40))
    o.data.transform(axis_matrix(p["centre"], p.get("axis", [0, 0, 1])))
    return finish(o, p["colour"], p.get("subdiv", 1), lumps=LUMPS * 0.5)


def part_coil(p, i):
    """Wire wound round something: turns about axis, radius out, pitch apart, as a tube. messy (0-1) makes it
    look wound in a hurry: uneven spacing, bunched and crossing turns, varying slack and loose ends."""
    ax = Vector(p["axis"]).normalized(); c = Vector(p["centre"])
    u = ax.orthogonal().normalized(); v = ax.cross(u)
    turns, pitch, rad = p["turns"], p["pitch"], p["radius"]; mess = p.get("messy", 0.0)
    rnd = random.Random(spec.get("seed", 1) * 1000 + i)
    per = 16; steps = int(turns * per); pts = []; along = -pitch * turns / 2
    slack = [1 + mess * rnd.uniform(0.0, 0.35) for _ in range(int(turns) + 2)]
    for k in range(steps + 1):
        t = 2 * math.pi * k / per; turn = k // per
        # spacing wanders: some turns bunch up, one may cross back over the last
        along += pitch / per * (1 + mess * rnd.uniform(-1.4, 1.6))
        sl = slack[turn] + (slack[turn + 1] - slack[turn]) * (k % per) / per
        wob = 1 + 0.06 * math.sin(t * 1.7 + i) + mess * 0.05 * math.sin(t * 3.1 + 2 * i)
        pt = c + ax * along + (u * math.cos(t) + v * math.sin(t)) * rad * sl * wob
        pts.append(list(pt))
    if mess:  # loose ends: the last bit sticks out and kinks, the first trails off
        end = Vector(pts[-1]); out_dir = (end - (c + ax * along)).normalized()
        for k, (o_, a_) in enumerate(((0.035, 0.01), (0.07, 0.03), (0.09, 0.06))):
            pts.append(list(end + out_dir * o_ * (1 + mess) + ax * a_ + u.cross(out_dir) * 0.012 * (-1) ** k))
        st = Vector(pts[0]); out0 = (st - (c - ax * pitch * turns / 2)).normalized()
        pts.insert(0, list(st + out0 * 0.03 - ax * 0.02))
    q = dict(p); q.update({"points": pts, "smooth": True, "radius": p["wire"]})
    return part_tube(q, i)


def rounded_polygon(pts, r, seg=6):
    """Round each corner of a convex 2D polygon with an arc of radius r."""
    out = []; n = len(pts)
    for k in range(n):
        a, b, c = Vector(pts[k - 1]), Vector(pts[k]), Vector(pts[(k + 1) % n])
        d1 = (a - b).normalized(); d2 = (c - b).normalized()
        ang = d1.angle(d2); t = r / math.tan(ang / 2)
        p1 = b + d1 * t; p2 = b + d2 * t
        bis = (d1 + d2).normalized(); cen = b + bis * (r / math.sin(ang / 2))
        a1 = math.atan2(*(p1 - cen).yx); a2 = math.atan2(*(p2 - cen).yx)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        for s_ in range(seg + 1):
            aa = a1 + da * s_ / seg; out.append(cen + Vector((math.cos(aa), math.sin(aa))) * r)
    return out


def part_plate(p, i):
    """A flat plate (a sign): a rounded polygon [[x, y], ...] in its own plane, thickness thick, set at centre and
    turned by tilt (its face, local +Z, points along tilt applied to +Z). layers: smaller polygons raised on the
    face in other colours; marks: tubes and balls on the face ([[x, y], ...] in the plate's frame); bites:
    [[x, y, r], ...] taken out of the edge like teeth marks."""
    M = tiltM(p); th = p["thickness"]
    def slab(poly, z0, z1, round_r, name):
        bm = bmesh.new()
        ring = rounded_polygon(poly, round_r)
        vs = [bm.verts.new((q.x, q.y, z0)) for q in ring]
        f = bm.faces.new(vs)
        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        rims = [e for e in bm.edges if len(e.link_faces) == 2 and abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5]
        bmesh.ops.bevel(bm, geom=rims, offset=min(0.4 * (z1 - z0), 0.012), segments=3, profile=0.5, affect="EDGES")
        return new_obj(name, bm)
    o = slab(p["points"], -th / 2, th / 2, p.get("corner", 0.04), f"plate{i}")
    for k, (bx, by, br) in enumerate(p.get("bites", [])):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=br)
        bmesh.ops.scale(bm, vec=(1, 1, th * 3 / br), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(bx, by, 0), verts=bm.verts); cutter = new_obj("bite", bm)
        bo = o.modifiers.new("bite", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = cutter; bo.solver = "EXACT"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=bo.name)
        bpy.data.objects.remove(cutter)
    o.data.transform(M); set_rest(o, Matrix())
    out = [finish(o, p["colour"], 0, lumps=0)]
    z = th / 2
    for k, lay in enumerate(p.get("layers", [])):
        lo = slab(lay["points"], z - 0.002, z + lay.get("raise", 0.006), lay.get("corner", 0.025), f"layer{i}_{k}")
        lo.data.transform(M); set_rest(lo, Matrix()); out.append(finish(lo, lay["colour"], 0, lumps=0))
    for k, mk in enumerate(p.get("marks", [])):
        mz = z + mk.get("raise", 0.008)
        if "ball" in mk:
            q = {"centre": list(M @ Vector((*mk["ball"], mz))), "radius": mk["radius"], "colour": mk["colour"],
                 "scale": [1, 1, 1]}
            out.append(part_ball(q, i))
        else:
            q = {"points": [list(M @ Vector((x, y, mz))) for x, y in mk["points"]], "radius": mk["radius"],
                 "colour": mk["colour"], "smooth": mk.get("smooth", False)}
            out.extend(part_tube(q, i))
    return out


def part_tub(p, i):
    """A hollow tub: rounded outlines (superellipses) stacked from the bottom up, closed at the bottom, open at the
    top, with walls of the given thickness. rings: [[z, half-length (y), half-width (x), centre y], ...]."""
    n_pow = p.get("power", 2.6); segs = p.get("segments", 64); e = 2.0 / n_pow
    bm = bmesh.new(); rings = []
    for z, a, b, cy in p["rings"]:
        ring = []
        for k in range(segs):
            t = 2 * math.pi * k / segs; ct, st = math.cos(t), math.sin(t)
            ring.append(bm.verts.new((b * math.copysign(abs(ct) ** e, ct), cy + a * math.copysign(abs(st) ** e, st), z)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    z0, _, _, cy0 = p["rings"][0]
    c = bm.verts.new((0, cy0, z0 - p.get("sag", 0.01)))
    for k in range(segs):
        bm.faces.new((c, rings[0][(k + 1) % segs], rings[0][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = new_obj(f"tub{i}", bm); set_rest(o, Matrix())
    sd = o.modifiers.new("solid", "SOLIDIFY"); sd.thickness = p.get("thickness", 0.03); sd.offset = -1
    sd.use_even_offset = True
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=sd.name)
    return finish(o, p["colour"], p.get("subdiv", 2))


def part_wheel(p, i):
    r, w = p["radius"], p["width"]; h = w / 2
    side = 1 if p["pos"][0] > 0 else -1  # hub faces outward
    n = p.get("lugs", 0)
    body_r = r * (0.9 if n else 1.0)  # lugs stand proud of a lugged tyre's carcass
    # balloon tyre: a fat rounded section, with a groove round the middle on a smooth tyre
    sec = []
    for k in range(25):
        t = -math.pi / 2 + math.pi * k / 24
        x = h * math.sin(t); rr = body_r * (0.62 + 0.38 * math.cos(t) ** 0.6)
        if not n and abs(x) < h * 0.12: rr -= r * 0.025 * (1 - abs(x) / (h * 0.12))
        sec.append((x, rr))
    sec = [(-h * 0.92, r * 0.5)] + sec + [(h * 0.92, r * 0.5)] + [(-h * 0.92, r * 0.5)]
    if p.get("style") == "drum":  # a tall drum with soft shoulders, like a wooden cart wheel
        sec = []
        for k in range(13):
            t = math.pi / 2 * k / 12; sh = h * 0.42
            sec.append((-h + sh - sh * math.cos(t), r - sh + sh * math.sin(t)))
        sec = [(-h * 0.92, r * 0.5), (-h, r - h * 0.42)] + sec + [(x, rr) for x, rr in reversed([(-x, rr) for x, rr in sec])] + \
              [(h, r - h * 0.42), (h * 0.92, r * 0.5)]
        sec = sec + [sec[0]]
    tyre = lathe(p["name"], sec[:-1] + [sec[0]], 48)
    finish(tyre, p["colour"], 1, lumps=LUMPS * 0.6)
    parts = [tyre]
    for k in range(n):  # chunky tread: two rows of slanted lugs, making chevrons like a tractor tyre
        for row in (-1, 1):
            a = 2 * math.pi * (k + (0.5 if row > 0 else 0)) / n
            lug = rounded_box("lug", (row * h * 0.42, 0, 0), (h * 1.05, r * 0.26, r * 0.12), r * 0.06, (0, 0, row * 30), segments=4)
            lug.data.transform(Matrix.Rotation(a, 4, "X") @ Matrix.Translation((0, 0, body_r * 0.97)))
            parts.append(finish(lug, p["colour"], 2, lumps=0))
    # dished hub: rim ring, a dip, and a domed centre cap
    R = r * p.get("hub_size", 0.56)
    prof = [(-h * 0.6, 0), (-h * 0.6, R * 0.95), (h * 0.55, R * 0.95), (h * 0.72, R * 0.9), (h * 0.78, R * 0.78),
            (h * 0.66, R * 0.66), (h * 0.52, R * 0.55), (h * 0.5, R * 0.36), (h * 0.7, R * 0.32), (h * 0.9, R * 0.22),
            (h * 0.96, R * 0.1), (h * 0.97, 0)]
    if p.get("cap"):  # a plain disc hub with a separate centre cap in its own colour
        prof = [(-h * 0.6, 0), (-h * 0.6, R * 0.95), (h * 0.55, R * 0.95), (h * 0.7, R * 0.85), (h * 0.72, 0)]
    hub = lathe(p["name"] + "_hub", [(side * x, rr) for x, rr in prof], 40)
    finish(hub, p["hub"], 1, lumps=0)
    parts.append(hub)
    if p.get("cap"):
        cap = cylinder(p["name"] + "_cap", R * 0.38, h * 0.5, R * 0.15, 24)
        cap.data.transform(Matrix.Translation((side * h * 0.82, 0, 0)))
        parts.append(finish(cap, p["cap"], 1, lumps=0))
    o = join(parts, p["name"])
    o.location = p["pos"]
    return o


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o


def fuse(objs, name, colour_name, voxel=0.009, faces=6000):
    """Melt several parts into one soft lump: a voxel union, smoothed, then cut to budget."""
    o = join(objs, name)
    rm = o.modifiers.new("rm", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = voxel
    sm = o.modifiers.new("sm", "SMOOTH"); sm.factor = 0.9; sm.iterations = 30
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if tris > faces:
        d = o.modifiers.new("dec", "DECIMATE"); d.ratio = faces / tris; bpy.ops.object.modifier_apply(modifier=d.name)
    for p in o.data.polygons: p.use_smooth = True
    set_rest(o, Matrix())
    paint(o, colour(colour_name)[0])
    return o


# ---------------------------------------------------------------- build
BUILD = {"box": part_box, "planks": part_planks, "tube": part_tube, "torus": part_torus, "disc": part_disc,
         "ball": part_ball, "wheel": part_wheel, "tub": part_tub, "pipe_end": part_pipe_end,
         "can": part_can, "coil": part_coil, "plate": part_plate,
         "turned": part_turned}
made_parts = []  # (spec part, [objects])
for i, p in enumerate(spec["parts"]):
    made = BUILD[p["type"]](p, i)
    made_parts.append((p, made if isinstance(made, list) else [made]))

fused = {}
for p, objs in made_parts:
    if p.get("fuse"): fused.setdefault(p["fuse"], []).append((p, objs))
groups = [(p, objs) for p, objs in made_parts if not p.get("fuse")]
for label, members in fused.items():
    p0 = dict(members[0][0]); allobjs = [o for _, objs in members for o in objs]
    p0["touches"] = sorted({t for p, _ in members for t in p.get("touches", [])})
    p0["id"] = label
    groups.append((p0, [fuse(allobjs, label, p0["colour"], p0.get("voxel", 0.009))]))


# ---------------------------------------------------------------- clash check
def bvh(objs):
    vs, fs = [], []
    for o in objs:
        M = o.matrix_world; base = len(vs)
        vs += [M @ v.co for v in o.data.vertices]; fs += [[base + j for j in f.vertices] for f in o.data.polygons]
    return BVHTree.FromPolygons(vs, fs)


bpy.context.view_layer.update()
TOUCH = {}  # parts sharing an id share what they may touch
for k, (p, objs) in enumerate(groups): TOUCH.setdefault(p.get("id", p["type"] + str(k)), set()).update(p.get("touches", []))
trees = [(p.get("id", p["type"] + str(k)), TOUCH[p.get("id", p["type"] + str(k))], bvh(objs)) for k, (p, objs) in enumerate(groups)]
clashes = 0
for a in range(len(trees)):
    for b in range(a + 1, len(trees)):
        ia, ta, A = trees[a]; ib, tb, B = trees[b]
        if ia == ib or ib in ta or ia in tb: continue
        hits = A.overlap(B)
        if hits:
            clashes += 1; print(f"CLASH {ia} x {ib}: {len(hits)} face pairs")
print(f"CLASHES {clashes}")

# ---------------------------------------------------------------- assemble moving parts
body, wheels, named = [], [], {}
for p, objs in groups:
    if p["type"] == "wheel": wheels.extend(objs)
    elif p.get("name"): named.setdefault(p["name"], [p, []])[1].extend(objs)
    else: body.extend(objs)
body = join(body, "body")
gl = lambda v: [v[0], v[2], -v[1]]  # extras are read in the GLB's own frame (Y up), not Blender's
for w in wheels:  # the game spins every wheel about its hub and steers the front ones
    w["spin_axis"] = gl([1, 0, 0])
    if w.name.split("_")[-1] in ("F", "FL", "FR"): w["steer_axis"] = gl([0, 0, 1])
movers = []
for name, (p, objs) in named.items():
    o = join(objs, name); piv = Vector(p["pivot"])
    o.data.transform(Matrix.Translation(-piv)); o.location = piv
    if p.get("axis"): o["axis"] = gl(p["axis"])
    movers.append(o)
moving = wheels + movers
meshes = [body] + moving
root = bpy.data.objects.new("kart", None); scene.collection.objects.link(root)
for o in meshes: o.parent = root
bpy.context.view_layer.update()
tris = sum(len(f.vertices) - 2 for o in meshes for f in o.data.polygons)
print(f"KART {os.path.basename(spec_path)}: body {len(body.data.polygons)} faces, {len(moving)} moving parts, {tris} triangles")

# ---------------------------------------------------------------- game mesh: decimate, then bake the detail onto it
def budget(name):
    B = {"body": 18000, "wheel_F": 2600, "wheel_R": 5000, "other": 1500}; B.update(spec.get("budget", {}))
    for k in ("wheel_F", "wheel_R"):
        if name.startswith(k): return B[k]
    return B.get(name, B["other"])


def copy_obj(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name; scene.collection.objects.link(c); return c


if not fast:
    highs, lows = [], []
    for o in meshes:  # the modelled part stays as the bake source; a lighter copy ships
        name = o.name; o.name = name + "_hi"; lo = copy_obj(o, name); lo.data.name = name
        tris = sum(len(f.vertices) - 2 for f in lo.data.polygons); want = budget(name)
        if tris > want:
            bpy.context.view_layer.objects.active = lo
            d = lo.modifiers.new("dec", "DECIMATE"); d.ratio = want / tris; bpy.ops.object.modifier_apply(modifier=d.name)
        highs.append(o); lows.append(lo)
    bpy.ops.object.select_all(action="DESELECT")
    for o in lows: o.select_set(True)
    bpy.context.view_layer.objects.active = lows[0]
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003)
    bpy.ops.uv.pack_islands(margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    # bake straight onto the shipped mesh: it keeps each part's tint and grain coordinates through the
    # decimation, so its own procedural material paints it with no rays cast between two meshes
    size = spec.get("texture", 2048)
    imgs = {k: bpy.data.images.new(f"kart_{k}", size, size, is_data=(k in ("normal", "rough"))) for k in ("color", "normal", "ao", "rough")}
    def target(img):
        for m in MATS.values():
            t = m.node_tree.nodes.get("bake") or m.node_tree.nodes.new("ShaderNodeTexImage")
            t.name = "bake"; t.image = img; m.node_tree.nodes.active = t
    for o in highs: o.hide_render = True  # the source parts must not shade the bake
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
    bk = scene.render.bake; bk.margin = 8; bk.use_selected_to_active = False
    bpy.ops.object.select_all(action="DESELECT")
    for o in lows: o.select_set(True)
    bpy.context.view_layer.objects.active = lows[0]
    for k, kind, samples, extra in (("color", "DIFFUSE", 4, {"pass_filter": {"COLOR"}}), ("normal", "NORMAL", 4, {}),
                                    ("rough", "ROUGHNESS", 1, {}), ("ao", "AO", 64, {})):
        scene.cycles.samples = samples; target(imgs[k])
        bpy.ops.object.bake(type=kind, use_selected_to_active=False, **extra)
        print("BAKED", k, flush=True)
    # metal map: bake each material's metalness as light, then pack it beside roughness (glTF: G rough, B metal)
    imgs["metal"] = bpy.data.images.new("kart_metal", size, size, is_data=True)
    for (kind, *_), m in MATS.items():
        bs_ = m.node_tree.nodes["Principled BSDF"]
        polished = _[3] is not None and _[3] < 0.3  # (dirt, dirt_rgb, rust, rough): polished metal is fully metal
        mv = (1.0 if polished else 0.85) if kind == "metal" else 0.0
        bs_.inputs["Emission Color"].default_value = (mv, mv, mv, 1); bs_.inputs["Emission Strength"].default_value = 1
        rm = m.node_tree.nodes.get("rustmask")
        if rm and mv:  # rusted patches are no longer bare metal
            inv = m.node_tree.nodes.new("ShaderNodeMath"); inv.operation = "MULTIPLY_ADD"
            m.node_tree.links.new(rm.outputs[0], inv.inputs[0]); inv.inputs[1].default_value = -mv; inv.inputs[2].default_value = mv
            m.node_tree.links.new(inv.outputs[0], bs_.inputs["Emission Color"])
    target(imgs["metal"]); scene.cycles.samples = 1
    bpy.ops.object.bake(type="EMIT", use_selected_to_active=False); print("BAKED metal", flush=True)
    import numpy as np
    rgh = np.array(imgs["rough"].pixels[:]).reshape(-1, 4); met = np.array(imgs["metal"].pixels[:]).reshape(-1, 4)
    rgh[:, 0] = 1.0; rgh[:, 2] = met[:, 0]
    imgs["rough"].pixels.foreach_set(rgh.ravel().astype(np.float32))
    # crease shading: darken the colour where light can't reach, as clay photographs
    import numpy as np
    c = np.array(imgs["color"].pixels[:]).reshape(-1, 4); a = np.array(imgs["ao"].pixels[:]).reshape(-1, 4)[:, :1]
    c[:, :3] *= 0.45 + 0.55 * a
    imgs["color"].pixels.foreach_set(c.ravel().astype(np.float32))
    # loose copies of the maps, for inspection (the GLB carries its own): git-ignored workspace by default
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tex_dir = os.path.join(here, spec["texture_dir"]) if "texture_dir" in spec else \
        os.path.join(repo, "workspace", "karts", os.path.basename(here))
    os.makedirs(tex_dir, exist_ok=True)
    for k in ("color", "normal", "rough", "ao"):
        im = imgs[k]; im.filepath_raw = os.path.join(tex_dir, f"kart_{k}.png"); im.file_format = "PNG"; im.save()
    # the game material: baked colour and normal, nothing procedural
    km = bpy.data.materials.new("kart"); km.use_nodes = True; nt = km.node_tree
    bs = nt.nodes["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.78
    ci = nt.nodes.new("ShaderNodeTexImage"); ci.image = imgs["color"]
    ni = nt.nodes.new("ShaderNodeTexImage"); ni.image = imgs["normal"]; ni.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(ci.outputs["Color"], bs.inputs["Base Color"]); nt.links.new(ni.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    # roughness from its own map, so tin shines a little and clay stays matte (glTF reads it from green)
    ri = nt.nodes.new("ShaderNodeTexImage"); ri.image = imgs["rough"]; ri.image.colorspace_settings.name = "Non-Color"
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(ri.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bs.inputs["Roughness"]); nt.links.new(sep.outputs["Blue"], bs.inputs["Metallic"])
    for o in lows:
        o.data.materials.clear(); o.data.materials.append(km)
        if "Col" in o.data.color_attributes: o.data.color_attributes.remove(o.data.color_attributes["Col"])
        if "rest" in o.data.attributes: o.data.attributes.remove(o.data.attributes["rest"])
    for o in highs: bpy.data.objects.remove(o)
    meshes = lows
    tris = sum(len(f.vertices) - 2 for o in meshes for f in o.data.polygons)
    print(f"GAME MESH {tris} triangles: " + ", ".join(f"{o.name} {sum(len(f.vertices) - 2 for f in o.data.polygons)}" for o in meshes))

if spec.get("out") and not fast:
    out = os.path.join(here, spec["out"])
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes + [root]: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_yup=True, export_extras=True)
    print("WROTE", out)

if render:
    sc = scene; sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = sc.render.resolution_y = 700
    wd = bpy.data.worlds.new("w"); wd.use_nodes = True
    # a bright sky over a darker ground, so metal has something to reflect (previews only)
    wn = wd.node_tree; bg = wn.nodes["Background"]; bg.inputs[1].default_value = 1.0
    tc = wn.nodes.new("ShaderNodeTexCoord"); sx = wn.nodes.new("ShaderNodeSeparateXYZ")
    wn.links.new(tc.outputs["Generated"], sx.inputs[0])
    sky = wn.nodes.new("ShaderNodeValToRGB"); el = sky.color_ramp.elements
    el[0].position, el[0].color = 0.45, (0.42, 0.41, 0.4, 1); el[1].position, el[1].color = 0.62, (1.0, 1.0, 1.0, 1)
    el.new(0.5).color = (0.08, 0.08, 0.08, 1)  # a dark horizon band: what makes chrome read as chrome
    el.new(0.53).color = (0.75, 0.75, 0.77, 1)
    wn.links.new(sx.outputs["Z"], sky.inputs[0]); wn.links.new(sky.outputs[0], bg.inputs[0]); sc.world = wd
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sun.data.energy = 3.2
    sun.data.angle = math.radians(15); sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=20); fl = bpy.context.active_object
    fm = bpy.data.materials.new("floor"); fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.75, 0.75, 1); fl.data.materials.append(fm)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); cam.data.lens = 85
    sc.collection.objects.link(cam); sc.camera = cam
    ctr = Vector((0, 0, 0.33))
    for n, a, el in (("q", spec.get("view", 140), 14), ("side", 270, 3), ("left", 90, 3), ("front", 180, 5), ("back", 40, 22), ("top", 180, 75)):
        r = math.radians(a); e = math.radians(el); d = 5.2
        cam.location = ctr + Vector((d * math.sin(r) * math.cos(e), d * math.cos(r) * math.cos(e), d * math.sin(e)))
        cam.rotation_euler = (math.radians(90) - e, 0, math.radians(180) - r)
        sun.rotation_euler = (math.radians(50), 0, math.radians(200) - r)
        sc.render.filepath = f"{render}_{n}.png"; bpy.ops.render.render(write_still=True)
