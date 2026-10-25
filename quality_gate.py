"""Sort generated images into approved/ and rejected/.

Checks: (1) blur via Laplacian variance, (2) exactly one face,
(3) face similarity to your reference images (identity consistency).

Usage:
  python scripts/quality_gate.py --images outputs/raw --refs data/refs
"""
import argparse, csv, pathlib, shutil
import cv2, numpy as np


def embed(app, path):
    img = cv2.imread(str(path))
    if img is None:
        return None, None, 0
    faces = app.get(img)
    blur = cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    if len(faces) != 1:
        return None, len(faces), blur
    return faces[0].normed_embedding, 1, blur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--sim", type=float, default=0.45, help="min cosine similarity")
    ap.add_argument("--blur", type=float, default=60.0, help="min Laplacian variance")
    a = ap.parse_args()

    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))

    refs = [embed(app, p)[0] for p in pathlib.Path(a.refs).glob("*.*") if p.name != ".gitkeep"]
    refs = [r for r in refs if r is not None]
    if not refs:
        raise SystemExit("No usable reference faces in --refs")
    ref = np.mean(refs, axis=0); ref /= np.linalg.norm(ref)

    root = pathlib.Path(a.images).parent
    ok_dir, bad_dir = root / "approved", root / "rejected"
    ok_dir.mkdir(exist_ok=True); bad_dir.mkdir(exist_ok=True)
    rows, ok_n = [], 0
    for p in sorted(pathlib.Path(a.images).glob("*.png")):
        e, nfaces, blur = embed(app, p)
        sim = float(e @ ref) if e is not None else None
        passed = e is not None and sim >= a.sim and blur >= a.blur
        shutil.copy(p, (ok_dir if passed else bad_dir) / p.name)
        ok_n += passed
        rows.append([p.name, nfaces, round(blur, 1), None if sim is None else round(sim, 3), passed])
    with open(root / "quality_report.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["file", "faces", "blur", "similarity", "approved"]); w.writerows(rows)
    print(f"{ok_n}/{len(rows)} approved ({100*ok_n/max(len(rows),1):.0f}%)")


if __name__ == "__main__":
    main()
