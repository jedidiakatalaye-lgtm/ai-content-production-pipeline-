"""Log GPU sessions and compute cost per piece.

  python scripts/cost_tracker.py log --gpu "RTX 4090" --rate 0.69 --hours 2.5 --generated 300 --approved 210 --note "lora v1"
  python scripts/cost_tracker.py report
"""
import argparse, csv, pathlib, datetime

F = pathlib.Path("costs.csv")
H = ["date", "gpu", "rate_usd_hr", "hours", "generated", "approved", "note"]


def log(a):
    new = not F.exists()
    with open(F, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(H)
        w.writerow([datetime.date.today(), a.gpu, a.rate, a.hours, a.generated, a.approved, a.note])


def report(_):
    rows = list(csv.DictReader(open(F)))
    cost = sum(float(r["rate_usd_hr"]) * float(r["hours"]) for r in rows)
    gen = sum(int(r["generated"]) for r in rows)
    app = sum(int(r["approved"]) for r in rows)
    print(f"Sessions: {len(rows)} | Total GPU spend: ${cost:.2f}")
    print(f"Cost per generated piece: ${cost/max(gen,1):.4f}")
    print(f"Cost per APPROVED piece:  ${cost/max(app,1):.4f}  (approval rate {100*app/max(gen,1):.0f}%)")
    print("Levers to halve it: raise approval rate, batch larger, cheaper/faster GPU, fewer steps.")


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
l = sp.add_parser("log")
l.add_argument("--gpu", required=True); l.add_argument("--rate", type=float, required=True)
l.add_argument("--hours", type=float, required=True); l.add_argument("--generated", type=int, required=True)
l.add_argument("--approved", type=int, required=True); l.add_argument("--note", default="")
l.set_defaults(fn=log)
sp.add_parser("report").set_defaults(fn=report)
a = ap.parse_args()
a.fn(a)
