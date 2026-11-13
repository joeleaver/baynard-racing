material 3d;
// A boost pad: glowing chevrons on a dark plate, sliding the way karts cross it, inside a rim of
// yellow-and-black hazard stripes. Laid on a world-shape box's top face, whose texture runs in metres
// from the box's middle: `uv.x` across, `uv.y` toward the box's own −Z. `way` turns the chevrons round
// (1 points them toward −Z, -1 toward +Z); `half_width` and `half_length` are half the pad's size.
param plate: color = (0.10, 0.08, 0.09, 1.0);
param arrow: color = (1.0, 0.52, 0.06, 1.0);
param hazard: color = (1.0, 0.78, 0.12, 1.0);
param glow: f32 = 4.0 range(0, 30);
param half_width: f32 = 1.5 range(0.1, 20);
param half_length: f32 = 1.5 range(0.1, 20);
param rim: f32 = 0.22 range(0, 2);
param spacing: f32 = 1.0 range(0.2, 5);
param slant: f32 = 0.7 range(0, 3);
param speed: f32 = 2.2 range(0, 20);
param way: f32 = 1.0 range(-1, 1);

fn surface(s: SurfaceIn) -> Surface {
    var out = standard(s);
    let p = s.uv;
    // How far in from the pad's nearest edge: the rim, then the plate the chevrons slide over.
    let inset = min(params.half_width - abs(p.x), params.half_length - abs(p.y));
    let on_top = smoothstep(0.5, 0.8, s.normal.y);
    let in_rim = 1.0 - smoothstep(params.rim - 0.02, params.rim, inset);

    // Chevrons: bands across the pad, swept back at the sides, moving the way they point. Each band
    // is brightest at its leading edge and fades behind it.
    // A V's point is where `along` is greatest across a band, so it leads the way the bands slide.
    let along = p.y * sign(params.way + 0.0001) + abs(p.x) * params.slant;
    let k = fract((along - frame.time * params.speed) / params.spacing);
    let band = smoothstep(0.55, 0.62, k) * (1.0 - smoothstep(0.95, 1.0, k));
    let lead = mix(0.35, 1.0, smoothstep(0.55, 0.97, k));
    let chevron = band * lead * (1.0 - in_rim) * on_top;

    // Hazard stripes round the rim, and on the pad's sides.
    let stripe = step(0.5, fract((p.x + p.y) / 0.36));
    let rim_colour = mix(params.plate.rgb, params.hazard.rgb, stripe);
    let edge = max(in_rim * on_top, 1.0 - on_top);

    var base = mix(params.plate.rgb, params.arrow.rgb, chevron);
    base = mix(base, rim_colour, edge);
    out.base_color = vec4<f32>(base, 1.0);
    out.roughness = mix(0.35, 0.6, edge);
    out.metallic = 0.0;
    out.emission = params.arrow.rgb * params.glow * chevron;
    return out;
}
