material 3d;
// A track's racing surface, laid along the track: its texture's u is how far along the track, v how far
// across it from the middle (a swept road's texture runs this way). Worn darker and smoother where
// the karts run, painted lines and striped kerbs at the edges, and dust gathered at the sides.
param base: color = (0.18, 0.18, 0.19, 1.0);
param worn: color = (0.10, 0.10, 0.11, 1.0);
param dust: color = (0.42, 0.37, 0.30, 1.0);
param line: color = (0.92, 0.92, 0.88, 1.0);
param kerb_a: color = (0.80, 0.08, 0.06, 1.0);
param kerb_b: color = (0.95, 0.95, 0.93, 1.0);
param half_width: f32 = 6.0 range(0.5, 40);   // metres from the middle to the edge
param kerb: f32 = 0.9 range(0, 4);            // the kerbs' width; 0 for none
param kerb_length: f32 = 1.5 range(0.2, 10);  // metres a stripe
param line_in: f32 = 1.1 range(0, 6);         // how far in from the edge the painted line runs; 0 for none
param ruts: f32 = 0.7 range(0, 1);            // how worn the lines the karts run are
param rut_spacing: f32 = 2.6 range(0.5, 10);  // metres between the worn lines
param grain: f32 = 0.35 range(0, 1);
param rough: f32 = 0.85 range(0, 1);

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
    let along = s.uv.x;
    let across = -s.uv.y;
    let edge = params.half_width - abs(across);           // metres in from the nearer edge
    let w = fwidth(across) + 0.002;                        // a pixel's width, for soft paint edges

    // The asphalt: blotches along the track and aggregate speckle.
    let blotch = vnoise(vec2<f32>(along * 0.08, across * 0.25));
    var col = params.base.rgb * (0.85 + blotch * 0.3);
    col *= 1.0 + (vnoise(s.world.xz * 11.0) - 0.5) * params.grain * 0.6;

    // Worn lines: darker, smoother bands where wheels run, wandering a little along the track.
    let wander = (vnoise(vec2<f32>(along * 0.05, 3.0)) - 0.5) * 0.8;
    let lane = (across + wander) / params.rut_spacing;
    let rut = pow(0.5 + 0.5 * cos(lane * 6.2831853), 6.0) * params.ruts * smoothstep(0.5, 2.5, edge);
    let streak = 0.75 + 0.25 * vnoise(vec2<f32>(along * 0.6, across * 6.0));
    col = mix(col, params.worn.rgb, rut * streak);
    var roughness = mix(params.rough, params.rough * 0.6, rut);

    // Dust gathered near the edges, where nothing runs.
    let dusty = (1.0 - smoothstep(0.0, 1.6, edge - params.kerb)) * (0.6 + 0.4 * vnoise(vec2<f32>(along * 0.4, across * 2.0)));
    col = mix(col, params.dust.rgb, dusty * 0.55);

    // The painted line, a little in from each edge.
    if params.line_in > 0.0 {
        let d = abs(edge - params.line_in);
        let paint = 1.0 - smoothstep(0.07, 0.07 + w, d);
        let chipped = smoothstep(0.25, 0.45, vnoise(vec2<f32>(along * 3.0, across * 3.0)));
        col = mix(col, params.line.rgb, paint * chipped * 0.9);
        roughness = mix(roughness, 0.55, paint);
    }

    // Kerbs: stripes along the track at both edges.
    if params.kerb > 0.0 {
        let on = 1.0 - smoothstep(params.kerb - w, params.kerb + w, edge);
        let stripe = step(0.5, fract(along / (params.kerb_length * 2.0)));
        let k = mix(params.kerb_a.rgb, params.kerb_b.rgb, stripe) * (0.9 + 0.1 * vnoise(s.world.xz * 7.0));
        col = mix(col, k, on);
        roughness = mix(roughness, 0.5, on);
    }

    out.base_color = vec4<f32>(col, 1.0);
    out.roughness = roughness;
    out.metallic = 0.0;
    return out;
}
