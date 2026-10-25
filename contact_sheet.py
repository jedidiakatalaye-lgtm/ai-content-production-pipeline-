"""Build a grid image to prove identity consistency.

  python scripts/contact_sheet.py --images outputs/approved --cols 5 --out docs/consistency_grid.jpg
"""
import argparse, pathlib
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--images", required=True); ap.add_argument("--cols", type=int, default=5)
ap.add_argument("--max", type=int, default=20); ap.add_argument("--size", type=int, default=320)
ap.add_argument("--out", default="docs/consistency_grid.jpg")
a = ap.parse_args()
files = sorted(pathlib.Path(a.images).glob("*.png"))[: a.max]
rows = (len(files) + a.cols - 1) // a.cols
sheet = Image.new("RGB", (a.cols * a.size, max(rows, 1) * a.size), "white")
for i, p in enumerate(files):
    im = Image.open(p).convert("RGB"); im.thumbnail((a.size, a.size))
    sheet.paste(im, ((i % a.cols) * a.size, (i // a.cols) * a.size))
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
sheet.save(a.out, quality=88)
print("saved", a.out)
