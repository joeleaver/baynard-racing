"""Make each racer's headshot from their concept, for the corner of their lobby card: the head, square, 128 pixels.

python3 tools/headshots.py   ->   art/racers/<name>/headshot.png, imported into the game as "<Name> headshot".
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
# Each concept's head: its centre, across and down, and its size, as shares of the picture.
HEADS = {
    "hettie": (0.50, 0.27, 0.34),
    "max": (0.46, 0.25, 0.30),
    "puddles": (0.50, 0.28, 0.36),
    "the-major": (0.43, 0.14, 0.32),
    "mabel": (0.50, 0.29, 0.36),
    "scraps": (0.48, 0.33, 0.32),
    "marmalade": (0.50, 0.33, 0.38),
    "duvet": (0.53, 0.33, 0.36),
}

for name, (cx, cy, share) in HEADS.items():
    concept = Image.open(ROOT / "art" / "racers" / name / "concept.webp").convert("RGB")
    w, h = concept.size
    side = int(w * share)
    left = int(w * cx - side / 2)
    up = int(h * cy - side / 2)
    concept.crop((left, up, left + side, up + side)).resize((128, 128), Image.LANCZOS).save(ROOT / "art" / "racers" / name / "headshot.png")
    print("headshot", name)
