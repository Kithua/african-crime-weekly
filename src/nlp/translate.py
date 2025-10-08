"""
Helsinki-NLP offline translation (xx → en).
Caches models in /app/cache/translate.
"""
import os, pathlib as pl, iso639
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

CACHE = pl.Path("/app/cache/translate")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def load_model(src_lang: str):
    code = iso639.to_iso639_1(src_lang)
    model_name = f"Helsinki-NLP/opus-mt-{code}-en"
    tok = AutoTokenizer.from_pretrained(model_name, cache_dir=CACHE)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=CACHE).to(DEVICE)
    return tok, mdl

def translate(text: str, src_lang: str) -> str:
    tok, mdl = load_model(src_lang)
    batch = tok(text, return_tensors="pt", truncation=True, max_length=512).to(DEVICE)
    out = mdl.generate(**batch, max_length=512, num_beams=5)
    return tok.decode(out[0], skip_special_tokens=True)
