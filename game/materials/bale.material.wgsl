material 3d;
// A straw bale model: its own picture (where the straw and the twine are, and its shading) with straw
// drawn over it — strands running the way the picture's u runs, finer ones crossing them, clumps a
// shade lighter or darker, and each strand raised a little so the light catches them.
param map: texture = white;                  // the model's colour picture
param normals: texture = white data;         // the model's normal picture
param pale: color = (0.85, 0.62, 0.28, 1.0);  // sun-bleached strands
param gold: color = (0.62, 0.38, 0.10, 1.0);  // the body of the straw
param brown: color = (0.24, 0.13, 0.04, 1.0); // old, damp strands and the shadows between them
param strands: f32 = 420.0 range(50, 1200);   // strands across the picture
param depth: f32 = 0.7 range(0, 2);          // how far each strand stands out
param rough: f32 = 0.82 range(0, 1);

fn hash2(p: vec2<f32>) -> f32 {
    let q = fract(p * vec2<f32>(0.1031, 0.1030));
    let r = q + dot(q, q.yx + 33.33);
    return fract((r.x + r.y) * r.x);
}

fn vnoise(p: vec2<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash2(i), hash2(i + vec2<f32>(1.0, 0.0)), u.x), mix(hash2(i + vec2<f32>(0.0, 1.0)), hash2(i + vec2<f32>(1.0, 1.0)), u.x), u.y);
}

// How much straw stands at `uv`: long strands along u, a second layer laid a little across them, and
// the odd bright stalk.
fn straw(uv: vec2<f32>) -> f32 {
    let n = params.strands;
    let a = vnoise(vec2<f32>(uv.x * n * 0.035, uv.y * n));
    let c = cos(0.35);
    let s = sin(0.35);
    let r = vec2<f32>(uv.x * c - uv.y * s, uv.x * s + uv.y * c);
    let b = vnoise(vec2<f32>(r.x * n * 0.05 + 17.0, r.y * n * 1.4));
    let stalk = smoothstep(0.82, 0.95, vnoise(vec2<f32>(uv.x * n * 0.03 + 5.0, uv.y * n * 0.7)));
    return clamp(0.55 * a + 0.45 * b + 0.35 * stalk, 0.0, 1.0);
}

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    let uv = s.uv;
    let pic = sample(params.map, uv).rgb;
    // Twine is the picture's red; everything else is straw.
    let twine = smoothstep(0.25, 0.45, pic.r - pic.g * 1.6);
    let f = straw(uv);
    let clump = vnoise(uv * params.strands * 0.08 + vec2<f32>(3.1, 7.7));
    // The straw's colour from the strand: brown in the gaps, gold through the body, pale on top.
    var col = mix(params.brown.rgb, params.gold.rgb, smoothstep(0.08, 0.42, f));
    col = mix(col, params.pale.rgb, smoothstep(0.62, 0.92, f) * (0.4 + 0.6 * clump));
    // None of the picture's own light and dark: it was painted with shade baked in, one side of a
    // bale darker than the other, so bales laid turned about read as a checkerboard. The scene's
    // light shades it.
    col *= 0.85 + 0.3 * clump;
    let rope = pic * (0.8 + 0.3 * vnoise(uv * params.strands * vec2<f32>(0.5, 0.15)));
    out.base_color = vec4<f32>(mix(col, rope, twine), 1.0);
    // Between the strands it is darker still: light does not get in.
    out.occlusion = mix(0.7 + 0.3 * smoothstep(0.05, 0.5, f), 1.0, twine);
    out.roughness = params.rough - 0.12 * smoothstep(0.7, 1.0, f) * (1.0 - twine);
    out.metallic = 0.0;
    // Each strand raised: the slope of the straw across the strands bends the normal.
    let e = 0.5 / params.strands;
    let slope = (straw(uv + vec2<f32>(0.0, e)) - f) / e / params.strands;
    let base = normal_map(s, sample(params.normals, uv), 1.0);
    let tilt = s.bitangent * slope * params.depth * 3.0 * (1.0 - twine);
    out.normal = normalize(base - tilt);
    return out;
}
