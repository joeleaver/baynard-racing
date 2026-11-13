material 3d;
// Hay walls: a row of straw bales along a track's edge. Laid along the wall (a swept wall's texture
// runs along it), so every `bale` metres there is a break between two bales, each bale's straw runs
// its length, bulges a little between its breaks and is tied with two bands of twine.
param straw: color = (0.86, 0.69, 0.30, 1.0);
param dark: color = (0.60, 0.44, 0.16, 1.0);
param twine: color = (0.62, 0.14, 0.08, 1.0);
param bale: f32 = 1.1 range(0.3, 4);        // metres a bale
param gap: f32 = 0.07 range(0, 0.5);        // how far the dark break between bales reaches
param bulge: f32 = 0.6 range(0, 2);         // how round each bale is between its breaks
param rough: f32 = 0.95 range(0, 1);

fn hash1(x: f32) -> f32 {
    return fract(sin(x * 127.1) * 43758.5453);
}

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

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    let u = s.uv.x;
    let v = s.uv.y;
    let k = floor(u / params.bale);
    let f = fract(u / params.bale);
    let shade = hash1(k + 0.37);
    // Straw: long fibres along the bale, finer ones over them, each bale a little lighter or darker.
    let fibre = vnoise(vec2<f32>(u * 1.5 + k * 13.0, v * 38.0));
    let fine = vnoise(vec2<f32>(u * 7.0, v * 110.0));
    var col = mix(params.dark.rgb, params.straw.rgb, 0.45 + 0.55 * fibre);
    col *= (0.82 + 0.3 * shade) * (0.88 + 0.24 * fine);
    // The break between two bales: darker, the straw pressed into it.
    let to_break = min(f, 1.0 - f) * params.bale;
    let crevice = 1.0 - smoothstep(0.0, params.gap, to_break);
    col *= 1.0 - crevice * 0.65;
    // Two bands of twine round each bale.
    let width = 0.018 / params.bale;
    let band = max(1.0 - smoothstep(width, width * 1.8, abs(f - 0.3)), 1.0 - smoothstep(width, width * 1.8, abs(f - 0.7)));
    col = mix(col, params.twine.rgb, band * 0.9);

    out.base_color = vec4<f32>(col, 1.0);
    out.roughness = params.rough;
    out.metallic = 0.0;
    // Each bale rounds off toward its breaks, and its straw is rough to the touch.
    let lean = (2.0 * f - 1.0);
    let tilt = s.tangent * (lean * lean * lean) * params.bulge + s.bitangent * (fibre - 0.5) * 0.25;
    out.normal = normalize(s.normal + tilt);
    return out;
}
