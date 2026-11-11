"""The Barnyard Loop's block-out: its centre line, and the road and hay walls swept along it.

python3 tools/barnyard_loop.py

Prints what the editor was asked to build the loop with (its `addShape` and `set_component` tools):
three Sweeps under the Barnyard Loop group — the road (Tarmac) and a hay wall down each side (Hay) —
each following the same closed Curve, which is also what the lap counter measures progress along
(the kart's `track` link names the road). The ground is a Grass box under everything.
"""

import json

# The centre line, in metres on the ground (x, z). The start is at the first point, heading toward
# the second: a long straight, a sweeping right-hander, a hairpin, an S through the barns, and back.
POINTS = [
    (0, 30), (0, 0), (0, -30), (6, -52), (26, -64), (50, -60), (62, -42), (56, -22),
    (40, -10), (38, 8), (52, 24), (62, 44), (52, 64), (28, 70), (8, 58),
]
WIDTH = 12.0


def handles(points):
    """Catmull-Rom handles: each point's leaves toward the next, a sixth of the way from the one before."""
    n = len(points)
    out = []
    for i, (x, z) in enumerate(points):
        (ax, az), (bx, bz) = points[i - 1], points[(i + 1) % n]
        hx, hz = (bx - ax) / 6, (bz - az) / 6
        out.append({"position": [x, 0, z], "handle_in": [-hx, 0, -hz], "handle_out": [hx, 0, hz]})
    return out


def sweep(name, outline):
    return {"kind": "Sweep", "name": name, "position": [0, 0, 0], "size": [1, 1, 1], "outline": outline,
            "path": [[x, 0, z] for x, z in POINTS], "interval": 2.0}


def main():
    half = WIDTH / 2
    shapes = [
        sweep("Road", [[-half, -0.3], [half, -0.3], [half, 0.05], [-half, 0.05]]),
        sweep("Hay wall left", [[-half - 1.5, 0], [-half - 0.3, 0], [-half - 0.3, 0.9], [-half - 1.5, 0.9]]),
        sweep("Hay wall right", [[half + 0.3, 0], [half + 1.5, 0], [half + 1.5, 0.9], [half + 0.3, 0.9]]),
    ]
    print(json.dumps({"ground": {"kind": "Box", "name": "Ground", "position": [30, -0.5, 0], "size": [400, 1, 400]},
                      "shapes": shapes, "curve": {"points": handles(POINTS), "closed": True}}, indent=1))


if __name__ == "__main__":
    main()
