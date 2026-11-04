"""Shared Blender helpers for turning generated (oxidegen / Trellis) meshes into game meshes."""
import bpy, math
from mathutils import Vector, Matrix


def import_generated(path, turn=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in new:  # keep world transforms, drop the importer's parents
        if o.type == "MESH":
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.context.view_layer.update()
    if len(meshes) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes: o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
    m = meshes[0]
    for o in new:
        if o.type != "MESH" and o.name in bpy.data.objects: bpy.data.objects.remove(o)
    bpy.context.view_layer.objects.active = m
    m.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # Trellis meshes face +Y once unparented: turn to face -Y, plus any extra turn the config asks for
    m.data.transform(Matrix.Rotation(math.pi + math.radians(turn), 4, "Z"))
    m.data.update()
    return m


def only(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True); bpy.context.view_layer.objects.active = o


def retopo(hi, faces, voxel, tex=1024):
    """Rebuild a generated mesh as a clean closed low-poly mesh and bake its colour onto it.

    Generated meshes are open, self-intersecting shells; cutting their faces down shreds them. A voxel remesh
    closes them, decimation brings them to budget, and the original's colour is baked onto new UVs."""
    name = hi.name; hi.name = name + "_src"
    lo = hi.copy(); lo.data = hi.data.copy(); lo.name = name; bpy.context.collection.objects.link(lo)
    lo.data.materials.clear()
    only(lo)
    rm = lo.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = voxel; rm.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier=rm.name)
    sm = lo.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); sm.iterations = 4; sm.use_only_smooth = True
    bpy.ops.object.modifier_apply(modifier=sm.name)
    tris = sum(len(f.vertices) - 2 for f in lo.data.polygons)  # the budget is in triangles; the remesh makes quads
    if tris > faces:
        md = lo.modifiers.new("decimate", "DECIMATE"); md.ratio = faces / tris
        bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    img = bpy.data.images.new(lo.name + "_color", tex, tex)
    mat = bpy.data.materials.new(lo.name + "_clay"); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"]); nt.nodes.active = tn
    lo.data.materials.append(mat)
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 1; sc.cycles.device = "CPU"
    bk = sc.render.bake; bk.use_pass_direct = False; bk.use_pass_indirect = False; bk.use_pass_color = True
    bk.use_selected_to_active = True; bk.cage_extrusion = voxel * 3; bk.max_ray_distance = voxel * 8; bk.margin = 8
    bpy.ops.object.select_all(action="DESELECT")
    hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    bpy.ops.object.bake(type="DIFFUSE")
    img.pack()
    bpy.data.objects.remove(hi)
    print("retopo", lo.name, len(lo.data.polygons), "faces")
    return lo


def bounds(o):
    P = [o.matrix_world @ v.co for v in o.data.vertices]
    return Vector([min(p[i] for p in P) for i in range(3)]), Vector([max(p[i] for p in P) for i in range(3)])


def reduce(o, faces, tex=None):
    """Bring a generated hard-surface mesh (open plates and frames, which a voxel rebuild can't close) down to a
    triangle budget, keeping its own UVs and texture; optionally scale the texture down to tex pixels."""
    only(o)
    bm_tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if bm_tris > faces:
        md = o.modifiers.new("decimate", "DECIMATE"); md.ratio = faces / bm_tris
        md.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=md.name)
    if tex:
        for m in o.data.materials:
            for n in (m.node_tree.nodes if m and m.use_nodes else []):
                if n.type == "TEX_IMAGE" and n.image and max(n.image.size) > tex:
                    n.image.scale(tex, tex); n.image.pack()
    print("reduce", o.name, len(o.data.polygons), "faces")
    return o
