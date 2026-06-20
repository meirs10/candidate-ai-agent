"""
predict.py – Inference wrapper around the trained skill-scoring model.

Given a skill name and the evidence chunks retrieved for it, predict the
candidate's proficiency level (1-5). The input is serialized exactly as in
training (`dataset._build_input_text`): "{skill} {sep} {chunk1} {chunk2} ...",
so the model sees inputs in the same format it was trained on.

The best checkpoint is `coral_top3` (see runs/report.md); this module forces
that experiment so the correct head + checkpoint are loaded regardless of the
`config.EXPERIMENT` default. The model is loaded lazily on first use and cached
as a module-level singleton (loading the 700 MB checkpoint is expensive).
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

# Make the sibling modules (config / heads / model) importable when this file is
# imported from anywhere (e.g. the representor app), mirroring build_dataset.py.
_THIS_DIR = Path(__file__).resolve().parent  # scoring_model/
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import config
import heads
from model import ScoringModel
from transformers import AutoTokenizer

# The trained/best experiment — overrides the config default so inference always
# loads the coral_top3 head + checkpoint (the only one with a saved best_model.pt).
INFERENCE_EXPERIMENT = "coral_top3"

# Number of evidence chunks the model was trained to read (chunk1..chunkN).
RETRIEVE_TOP_K = config.RETRIEVE_TOP_K

_model: ScoringModel | None = None
_tokenizer = None
_device: torch.device | None = None


def _ensure_loaded() -> None:
    """Lazy-load the tokenizer + best checkpoint once, cached module-wide."""
    global _model, _tokenizer, _device
    if _model is not None:
        return

    config.apply_experiment(INFERENCE_EXPERIMENT)
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt = config.checkpoint_path()
    if not Path(ckpt).exists():
        raise FileNotFoundError(
            f"No checkpoint for '{INFERENCE_EXPERIMENT}' at {ckpt} — train it first "
            f"(python scoring_model/train.py --experiment {INFERENCE_EXPERIMENT})."
        )

    _tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
    model = ScoringModel().to(_device)
    model.load_state_dict(torch.load(ckpt, map_location=_device))
    model.eval()
    _model = model


def _build_input_text(skill: str, chunks: list[str], sep: str) -> str:
    """Match training serialization: "{skill} {sep} {chunk1} {chunk2} ..."."""
    joined = " ".join(c for c in chunks if c and str(c).strip())
    return f"{skill} {sep} {joined}"


@torch.no_grad()
def predict_levels(items: list[tuple[str, list[str]]], batch_size: int = 8) -> list[int]:
    """Predict 1-5 proficiency for a batch of (skill, chunks) pairs.

    Returns one int per item, in input order. A skill with no chunks still gets a
    prediction (the model reads just the skill name) — typically a low level.
    """
    if not items:
        return []
    _ensure_loaded()
    sep = _tokenizer.sep_token
    amp = config.USE_AMP and _device.type == "cuda"

    preds: list[int] = []
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        texts = [_build_input_text(skill, chunks, sep) for skill, chunks in batch]
        enc = _tokenizer(
            texts,
            max_length=config.MAX_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(_device)
        attention_mask = enc["attention_mask"].to(_device)
        with torch.autocast(device_type=_device.type, dtype=torch.bfloat16, enabled=amp):
            logits = _model(input_ids, attention_mask)
        decoded = heads.decode(config.HEAD_TYPE, logits)  # 0-4
        preds.extend(int(p) + 1 for p in decoded.cpu().tolist())  # shift to 1-5
    return preds


def predict_level(skill: str, chunks: list[str]) -> int:
    """Predict 1-5 proficiency for a single (skill, chunks) pair."""
    return predict_levels([(skill, chunks)])[0]
