material 3d;
// Ground: grass, tarmac, dirt, mud, sand, ice. Patterns are laid in the world, so a surface reads the
// same whatever shape it is on, and neighbouring shapes of one material meet without a seam.
param base: color = (0.30, 0.30, 0.32, 1.0);
param dark: color = (0.20, 0.20, 0.22, 1.0);
param light: color = (0.42, 0.42, 0.44, 1.0);
param scale: f32 = 4.0 range(0.1, 64);        // metres across a large blotch
param grain: f32 = 0.3 range(0, 1);           // fine speckle (tarmac aggregate, sand grains)
param stripes: f32 = 0.0 range(0, 1);         // mown stripes (grass) or tyre lines (dirt)
param stripe_width: f32 = 6.0 range(0.5, 40); // metres between stripes
param streaks: f32 = 0.0 range(0, 1);         // long fibres (straw), along X
param wet: f32 = 0.0 range(0, 1);             // glossy puddles in the low places
param cracks: f32 = 0.0 range(0, 1);          // thin bright lines (ice)
param bump: f32 = 0.3 range(0, 2);
param rough: f32 = 0.9 range(0, 1);

fn hash2(p: vec2<f32>) -> f32 {
    let q = fract(p * vec2<f32>(0.1031, 0.1030));
    let r = q + dot(q, q.yx + 33.33);
    return fract((r.x + r.y) * r.x);
}

fn vnoise(p: vec2<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u = f * f * (3.0 - 2.0 * f);
    let a = hash2(i);
    let b = hash2(i + vec2<f32>(1.0, 0.0));
    let c = hash2(i + vec2<f32>(0.0, 1.0));
    let d = hash2(i + vec2<f32>(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

fn fbm(p: vec2<f32>) -> f32 {
    var sum = 0.0;
    var amp = 0.5;
    var q = p;
    for (var i = 0; i < 4; i++) {
        sum += vnoise(q) * amp;
        q = q * 2.03 + vec2<f32>(17.0, 31.0);
        amp *= 0.5;
    }
    return sum;
}

// The pattern's height at a ground point: what the colour and the bump both read.
fn height(p: vec2<f32>) -> f32 {
    let big = fbm(p / params.scale);
    let fine = vnoise(p * 9.0) * params.grain;
    let straw = vnoise(vec2<f32>(p.x * 1.5, p.y * 28.0)) * params.streaks;
    return big + fine * 0.5 + straw * 0.6;
}

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    // Laid on the ground from above, and on a wall from the side, so neither is smeared.
    let w = s.world;
    let side = 1.0 - smoothstep(0.35, 0.75, abs(s.normal.y));
    let across = select(w.z, w.x, abs(s.normal.z) > abs(s.normal.x));
    let p = mix(w.xz, vec2<f32>(across, w.y * 1.0), side);
    let h = height(p);
    let big = fbm(p / params.scale);

    var col = mix(params.dark.rgb, params.base.rgb, smoothstep(0.25, 0.55, big));
    col = mix(col, params.light.rgb, smoothstep(0.55, 0.85, big));
    // Fine speckle: grains lighter and darker than the ground round them.
    let g = vnoise(p * 9.0) - 0.5;
    col *= 1.0 + g * params.grain * 0.5;
    // Straw fibres, and mown or tyre stripes.
    let fibre = vnoise(vec2<f32>(p.x * 1.5, p.y * 28.0)) - 0.5;
    col *= 1.0 + fibre * params.streaks * 0.7;
    let band = sin((w.x + w.z * 0.35) * 3.14159 / params.stripe_width);
    let striped = params.stripes * (1.0 - side);
    col *= 1.0 + smoothstep(-0.2, 0.2, band) * striped * 0.18 - striped * 0.09;

    var roughness = params.rough;
    // Puddles: where the ground lies lowest, darker and glossy, and flat.
    let puddle = smoothstep(0.42, 0.34, big) * params.wet * (1.0 - side);
    col *= 1.0 - puddle * 0.45;
    roughness = mix(roughness, 0.08, puddle);

    // Cracks: thin lines where the noise crosses its middle.
    let crack = (1.0 - smoothstep(0.0, 0.025, abs(vnoise(p * 0.9) - 0.5))) * params.cracks;
    col = mix(col, vec3<f32>(0.92, 0.97, 1.0), crack * 0.6);

    out.base_color = vec4<f32>(col, 1.0);
    out.roughness = roughness;
    out.metallic = 0.0;

    // The bump: the height's slope, tipping the normal on the faces that look up.
    let e = 0.05;
    let dx = height(p + vec2<f32>(e, 0.0)) - h;
    let dz = height(p + vec2<f32>(0.0, e)) - h;
    let up = clamp(s.normal.y, 0.0, 1.0);
    let tilt = vec3<f32>(dx, 0.0, dz) / e * params.bump * 0.08 * up * (1.0 - puddle);
    out.normal = normalize(s.normal - tilt);
    return out;
}
