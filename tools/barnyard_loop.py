"""The Barnyard Loop's block-out: its centre line, and the road and hay walls swept along it.

python3 tools/barnyard_loop.py

Prints what the editor was asked to build the loop with (its `addShape` and `set_component` tools):
three Sweeps under the Barnyard Loop group — the road (Tarmac) and a hay wall down each side (Hay) —
each following the same closed Curve, which is also what the lap counter measures progress along
(the kart's `track` link names the road). The ground is a Grass box under everything.
"""

import json

# The centre line, in metres (x, height, z). The start is at the first point, heading toward the
# second: the start straight on a low plateau, a kicker at its end that throws the kart onto the road
# sloping away below it, a climbing right-hander up onto the barn hill,
# a crest at its top that lifts a fast kart, a steep run back down through the S, a hairpin banked 15° (raised, so its low side stays
# above the grass),
# and back. Each point's last number is its tilt, in degrees: how far the road leans into the corner.
POINTS = [
    (0, 1.5, 30, 0), (0, 1.5, 10, 0), (0, 0, -12, 0), (0, 0, -30, 0), (6, 1.5, -52, 0), (26, 4, -64, 0), (50, 6.5, -60, 0),
    (62, 8, -42, 0), (56, 8.3, -22, 0), (40, 4.5, -10, 0), (38, 1.5, 8, 0), (52, 1.0, 24, 5),
    (62, 1.8, 44, 15), (52, 1.8, 64, 15), (28, 0.8, 70, 5), (8, 0, 58, 0),
]
WIDTH = 12.0


def handles(points):
    """Catmull-Rom handles: each point's leaves toward the next, a sixth of the way from the one before."""
    n = len(points)
    out = []
    for i, (x, y, z, tilt) in enumerate(points):
        a, b = points[i - 1], points[(i + 1) % n]
        h = [(b[k] - a[k]) / 6 for k in range(3)]
        point = {"position": [x, y, z], "handle_in": [-v for v in h], "handle_out": h}
        if tilt:
            point["tilt"] = tilt
        out.append(point)
    return out


def bezier(p0, h0, h1, p1, t):
    u = 1 - t
    return [u**3 * p0[k] + 3 * u * u * t * h0[k] + 3 * u * t * t * h1[k] + t**3 * p1[k] for k in range(3)]


def stretch(first, last, step=2.0):
    """The centre line from point `first` to point `last` (indices into POINTS), as points about
    `step` apart: the path a patch of surface follows."""
    curve = handles(POINTS)
    out = []
    for i in range(first, last):
        a, b = curve[i % len(curve)], curve[(i + 1) % len(curve)]
        p0, p1 = a["position"], b["position"]
        h0 = [p0[k] + a["handle_out"][k] for k in range(3)]
        h1 = [p1[k] + b["handle_in"][k] for k in range(3)]
        n = 64
        for j in range(n + (i == last - 1)):
            q = bezier(p0, h0, h1, p1, j / n)
            if not out or sum((q[k] - out[-1][k]) ** 2 for k in range(3)) >= step * step:
                out.append(q)
    return out


# The surfaces laid on the road, each a thin strip 5 cm proud of it (so its straight steps stay above the
# curving road) along a stretch of the centre line,
# in a Surfaces group of their own: as the road's siblings they would be cut into it, and an exact union
# of long faces a centimetre apart takes the editor many minutes.
# (name, material, first point, last point, across from, across to). Across is metres from the centre
# line, positive to its right. The boost pad is a box of its own (below).
# What each surface is made of, as its material says (Playweft reads these for physics): colour,
# roughness, friction (for things that slide on it), its surface word (what game code and sound read),
# a tyre's grip on it (a share of the tyre's own) and its rolling resistance (a share of the load).
MATERIALS = {
    "Tarmac": ("#4a4a50", 0.9, 1.0, "tarmac", 1.0, 0.015),
    "Grass": ("#6fae3c", 0.95, 0.55, "grass", 0.6, 0.05),
    "Dirt": ("#9a6b42", 0.95, 0.7, "dirt", 0.7, 0.04),
    "Hay": ("#e2b84a", 0.9, 0.4, "hay", 0.6, 0.1),
    "Ice": ("#cfe9f5", 0.15, 0.05, "ice", 0.35, 0.01),
    "Mud": ("#5b3a22", 0.8, 0.6, "mud", 0.65, 0.12),
    "Sand": ("#e3cf98", 1.0, 0.6, "sand", 0.75, 0.08),
    "Boost": ("#ff8a1e", 0.4, 1.0, "boost", 1.0, 0.0),
}

# Each stretch runs between points with no tilt: a patch is swept upright.
PATCHES = [
    ("Dirt inside", "dirt", 3, 5, 0.0, 6.0),       # the first right-hander: grip splits across the kart
    ("Mud", "mud", 5, 6, -6.0, -1.5),             # the outside of the climb
    ("Ice", "ice", 8, 10, -6.0, 6.0),             # the S on the way down
    ("Sand", "sand", 15, 16, -6.0, 6.0),          # the run back up to the start
]


def patch(name, first, last, a, b):
    return {"kind": "Sweep", "name": name, "position": [0, 0, 0], "size": [1, 1, 1],
            "outline": [[a, -0.05], [b, -0.05], [b, 0.1], [a, 0.1]],
            "path": stretch(first, last, 1.0), "interval": 1.0, "rings": "Square"}


def sweep(name, outline):
    return {"kind": "Sweep", "name": name, "position": [0, 0, 0], "size": [1, 1, 1], "outline": outline,
            "path": [[x, y, z] for x, y, z, _ in POINTS], "interval": 1.0, "rings": "Square"}


def main():
    half = WIDTH / 2
    shapes = [
        # The road stands on its own embankment, down into the ground, with a grass shoulder each side
        # for the hay walls.
        sweep("Road", [[-half - 1.6, -10], [half + 1.6, -10], [half + 1.6, 0], [half, 0], [half, 0.05],
                       [-half, 0.05], [-half, 0], [-half - 1.6, 0]]),
        sweep("Hay wall left", [[-half - 1.5, 0], [-half - 0.3, 0], [-half - 0.3, 0.9], [-half - 1.5, 0.9]]),
        sweep("Hay wall right", [[half + 0.3, 0], [half + 1.5, 0], [half + 1.5, 0.9], [half + 0.3, 0.9]]),
    ]
    # The jump at the end of the start plateau: a kicker on the road, which then falls away below it,
    # so a kart flies off it and lands on the downslope.
    jump = [{"kind": "Wedge", "name": "Kicker", "position": [0, 1.85, 13], "size": [half * 2, 0.6, 6]}]
    # A boost pad on the plateau, just before the kicker.
    # Its height is the road's there: the curve's smoothing lifts the plateau above its points.
    road_y = min(stretch(0, 1, 0.1), key=lambda q: abs(q[2] - 18.5))[1] + 0.05
    boost = {"kind": "Box", "name": "Boost pad", "position": [0, road_y + 0.03, 18.5], "size": [3, 0.1, 3]}
    patches = [dict(patch(n, f, l, a, b), surface=m) for n, m, f, l, a, b in PATCHES]
    materials = {name: {"color": c, "metallic": 0, "roughness": r, "friction": f, "surface": w, "tyre_grip": g, "rolling": k}
                 for name, (c, r, f, w, g, k) in MATERIALS.items()}
    print(json.dumps({"materials": materials, "jump": jump, "boost": boost, "patches": patches, "ground": {"kind": "Box", "name": "Ground", "position": [30, -0.5, 0], "size": [400, 1, 400]},
                      "shapes": shapes, "curve": {"points": handles(POINTS), "closed": True}}, indent=1))


if __name__ == "__main__":
    main()
