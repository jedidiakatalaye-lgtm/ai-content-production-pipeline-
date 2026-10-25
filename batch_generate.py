"""Queue many generations on a ComfyUI server and save the results.

Usage:
  python scripts/batch_generate.py --prompts data/prompts.csv --per-prompt 4
"""
import argparse, csv, json, pathlib, random, time, uuid
import requests, yaml


def queue(cfg, wf):
    r = requests.post(f"{cfg['comfyui_url']}/prompt",
                      json={"prompt": wf, "client_id": str(uuid.uuid4())}, timeout=30)
    r.raise_for_status()
    return r.json()["prompt_id"]


def wait(cfg, pid):
    start = time.time()
    while time.time() - start < cfg["timeout_seconds"]:
        h = requests.get(f"{cfg['comfyui_url']}/history/{pid}", timeout=30).json()
        if pid in h:
            return h[pid]
        time.sleep(cfg["poll_seconds"])
    raise TimeoutError(f"prompt {pid} timed out")


def save_images(cfg, hist, stem):
    out = pathlib.Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for node in hist["outputs"].values():
        for img in node.get("images", []):
            data = requests.get(f"{cfg['comfyui_url']}/view", params={
                "filename": img["filename"], "subfolder": img["subfolder"],
                "type": img["type"]}, timeout=60).content
            path = out / f"{stem}_{img['filename']}"
            path.write_bytes(data)
            saved.append(str(path))
    return saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--per-prompt", type=int, default=1)
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config))
    base = json.load(open(cfg["workflow_file"]))
    n = cfg["nodes"]
    manifest = pathlib.Path(cfg["output_dir"]).parent / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)

    with open(a.prompts, newline="", encoding="utf-8") as f, open(manifest, "a") as mf:
        for i, row in enumerate(csv.DictReader(f)):
            text = row["prompt"].replace("{trigger}", cfg["trigger_word"])
            for k in range(a.per_prompt):
                wf = json.loads(json.dumps(base))
                seed = random.randint(0, 2**32 - 1)
                wf[n["prompt_node"]]["inputs"][n["prompt_field"]] = text
                wf[n["seed_node"]]["inputs"][n["seed_field"]] = seed
                t0 = time.time()
                pid = queue(cfg, wf)
                files = save_images(cfg, wait(cfg, pid), f"p{i:03d}_s{seed}")
                rec = {"prompt": text, "seed": seed, "files": files,
                       "seconds": round(time.time() - t0, 1)}
                mf.write(json.dumps(rec) + "\n"); mf.flush()
                print(rec)


if __name__ == "__main__":
    main()
