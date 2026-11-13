material 3d;
// Chequers laid in the object's own space, so a banner or a line keeps its squares however it is placed.
param a: color = (0.95, 0.95, 0.93, 1.0);
param b: color = (0.05, 0.05, 0.06, 1.0);
param size: f32 = 0.5 range(0.02, 10);
param rough: f32 = 0.6 range(0, 1);

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    let w = s.world / params.size;
    let side = 1.0 - smoothstep(0.35, 0.75, abs(s.normal.y));
    let across = select(w.z, w.x, abs(s.normal.z) > abs(s.normal.x));
    let p = mix(w.xz, vec2<f32>(across, w.y), side);
    let c = (i32(floor(p.x)) + i32(floor(p.y))) & 1;
    out.base_color = vec4<f32>(select(params.a.rgb, params.b.rgb, c == 1), 1.0);
    out.roughness = params.rough;
    out.metallic = 0.0;
    return out;
}
