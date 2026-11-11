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
    print(json.dumps({"jump": jump, "ground": {"kind": "Box", "name": "Ground", "position": [30, -0.5, 0], "size": [400, 1, 400]},
                      "shapes": shapes, "curve": {"points": handles(POINTS), "closed": True}}, indent=1))


if __name__ == "__main__":
    main()
