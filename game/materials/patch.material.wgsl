material 3d;
render cutout;
// A patch of ground laid over another surface — sand, mud or ice across a road — its edges frayed
// into clumps rather than a hard line. Otherwise the same as the ground material.
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
// A patch laid over another surface (sand across a road): its edges ragged and broken up instead of
// a hard line, over `feather` metres. Its texture runs along the patch (a swept strip's does): it
// spans `across_from` to `across_to` across, and `length` metres along (0: its ends are not frayed).
param feather: f32 = 0.0 range(0, 4);
param across_from: f32 = -6.0 range(-40, 40);
param across_to: f32 = 6.0 range(-40, 40);
param length: f32 = 0.0 range(0, 2000);
param ruts: f32 = 0.0 range(0, 1);            // tyre tracks pressed along the patch
param rut_spacing: f32 = 2.6 range(0.5, 10);  // metres between them

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

// How much of a frayed patch is here: 1 well inside, 0 past its ragged edge.
fn patch_cover(s: SurfaceIn) -> f32 {
    if params.feather <= 0.0 {
        return 1.0;
    }
    // A patch's own thin sides and ends are not shown: it reads as lying on what it covers.
    if abs(s.normal.y) < 0.6 {
        return 0.0;
    }
    let a = -s.uv.y;
    var e = min(a - params.across_from, params.across_to - a);
    if params.length > 0.0 {
        e = min(e, min(s.uv.x, params.length - s.uv.x) * 0.5);
    }
    // Clumps thinning out toward the edge: big lobes, and scattered bits past them.
    let lobes = fbm(s.world.xz * 0.45) * 1.4 - 0.2;
    let bits = vnoise(s.world.xz * 5.0);
    let reach = e / params.feather;
    return select(0.0, 1.0, reach > lobes || (reach > lobes - 0.35 && bits > 0.72));
}

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    out.base_color.a = patch_cover(s);
    if out.base_color.a < 0.5 {
        return out;
    }
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
    // Tyre tracks: pairs of darker, smoother grooves along the patch, wandering a little.
    if params.ruts > 0.0 {
        let a = -s.uv.y + (vnoise(vec2<f32>(s.uv.x * 0.06, 7.0)) - 0.5) * 1.2;
        let lane = fract(a / params.rut_spacing);
        let groove = max(1.0 - smoothstep(0.0, 0.07, abs(lane - 0.38)), 1.0 - smoothstep(0.0, 0.07, abs(lane - 0.62)));
        let worn = groove * params.ruts * (1.0 - side) * (0.6 + 0.4 * vnoise(vec2<f32>(s.uv.x * 0.8, a * 4.0)));
        col *= 1.0 - worn * 0.35;
        roughness = mix(roughness, roughness * 0.7, worn);
    }
    // Puddles: where the ground lies lowest, darker and glossy, and flat.
    let puddle = smoothstep(0.42, 0.34, big) * params.wet * (1.0 - side);
    col *= 1.0 - puddle * 0.45;
    roughness = mix(roughness, 0.08, puddle);

    // Cracks: thin lines where the noise crosses its middle.
    let crack = (1.0 - smoothstep(0.0, 0.025, abs(vnoise(p * 0.9) - 0.5))) * params.cracks;
    col = mix(col, vec3<f32>(0.92, 0.97, 1.0), crack * 0.6);

    out.base_color = vec4<f32>(col, out.base_color.a);
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
