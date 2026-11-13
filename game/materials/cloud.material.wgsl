material 3d;
// A fair-weather cloud: white, soft and lit through, its shaded side never going grey as a solid's
// would. Its normals lean upward so it takes the sky's light from above.
param tint: color = (1.0, 1.0, 1.0, 1.0);
param lift: f32 = 0.8 range(0, 3);       // how far the normals lean up: higher is softer and brighter
param through: f32 = 1.0 range(0, 1);    // how much sunlight shows through it

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    out.base_color = vec4<f32>(params.tint.rgb, 1.0);
    out.roughness = 1.0;
    out.metallic = 0.0;
    out.normal = normalize(s.normal + vec3<f32>(0.0, params.lift, 0.0));
    out.translucency = params.through;
    return out;
}
