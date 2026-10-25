# Setup: ComfyUI + character LoRA on a rented GPU

Tool versions change fast. Check each project's README before running.

## 1. Create the character (original, not a real person)
1. Generate one base character with any image model.
2. Make a character sheet (front, 3/4, profile, varied expressions, outfits, lighting) using a
   reference-based image tool.
3. Curate the 20-30 best, most varied images. Remove any with warped faces or hands. Save as `dataset/`.
4. Caption each image with a short sentence starting with your trigger word (e.g. `ohwx_char`).
5. Copy 5-10 clean face shots into `data/refs/` (used by the quality gate).

## 2. Rent a GPU
- RunPod or Vast.ai. Start with a 24 GB card (RTX 4090 class). Note the **$/hour**.
- Use a ComfyUI template and attach a persistent volume so models survive restarts.
- Stop the pod when idle. Idle time is the biggest hidden cost.

## 3. Train the LoRA
- Use a trainer that supports your base model (e.g. ostris/ai-toolkit, kohya_ss). Start from its example config.
- Record base model, steps, learning rate, dataset size and GPU hours in `docs/TRAINING_LOG.md`.
- Save checkpoints periodically and compare them. More steps is not always better.

## 4. Build the workflow in ComfyUI
- Base model -> LoRA loader -> prompt -> sampler -> save image. Test a few prompts.
- Enable Dev mode in settings, then **Save (API Format)** to `workflows/character_api.json`.
- Find the node IDs for the prompt text and sampler seed in that JSON; put them in `config.yaml`.

## 5. Run the pipeline
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml          # edit URL + node IDs
cp data/prompts.example.csv data/prompts.csv
python scripts/batch_generate.py --prompts data/prompts.csv --per-prompt 4
python scripts/quality_gate.py --images outputs/raw --refs data/refs
python scripts/contact_sheet.py --images outputs/approved
python scripts/cost_tracker.py log --gpu "RTX 4090" --rate <your rate> --hours <hours> --generated <n> --approved <n>
python scripts/cost_tracker.py report
```

## 6. Then extend
Image-to-video with Wan, more characters, a dashboard, Claude Code automation, multi-account publishing.
