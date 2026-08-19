"""Eksperimen 2 - Mapper.

Memanggil Local LLM (llama.cpp OpenAI-compatible di 127.0.0.1:8080) untuk
menyarankan pemetaan konsep canonical (Product.name/price/stock) dari
skema yang sudah diekstrak secara deterministik oleh extractor.py.

Model: Qwen2.5-3B-Instruct-Q4_K_M. Menggunakan temperature=0 dan seed tetap
untuk memaksimalkan determinisme (kontrol variabel sampling).
"""
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8080/v1/chat/completions"
SEED = 42
TEMPERATURE = 0.0

PROMPT_TEMPLATE = """Anda adalah AI Schema Analyzer untuk platform AIOS yang
beradaptasi pada database client beragam. Anda diberi struktur skema (tabel,
kolom, tipe, relasi, dan baris sampel) yang SUDAH diekstrak secara otomatis
oleh kode (deterministik dan terverifikasi). Tugas Anda HANYA: menyarankan
pemetaan ke konsep canonical.

Canonical Model yang dicari:
  Product.name   (string) - wajib cari
  Product.price  (number) - opsional
  Product.stock  (number) - opsional

Skema (JSON) dari client:
{schema}

Untuk SETIAP konsep canonical, jawab dengan blok kata kunci:
  konsep: <nama konsep>
  ditemukan: <true|false>
  source: <tabel.kolom atau cara representasi data>
  confidence: <tinggi|sedang|rendah>
  alasan: <satu kalimat>

Aturan:
- "ditemukan: true" hanya bila ada bukti jelas dari skema/sampel bahwa
  konsep tersedia (nama/kombinasi kolom atau representasi non-literal).
- "ditemukan: false" hanya bila konsep benar-benar tidak ada di skema.
  JANGAN false hanya karena ragu atau tak ada kolom literal bernama "name".
- JANGAN menebak nilai data. Beri source/cara representasi, bukan angka.

jawab untuk 3 konsep: Product.name, Product.price, Product.stock."""

CANONICAL = ["Product.name", "Product.price", "Product.stock"]


def call_llm(prompt: str):
    body = {
        "model": "Qwen2.5-3B-Instruct-Q4_K_M",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "seed": SEED,
        "max_tokens": 512,
    }
    req = Request(
        BASE_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    usage_raw = data.get("usage", {})
    return content, usage_raw


def parse_answer(content: str):
    """Parsing hasil LLM: mendukung blok JSON (dengan atau tanpa ```json fence)
    maupun blok kata kunci (konsep:/ditemukan:/...). Mengembalikan dict
    {nama_konsep: {ditemukan, source, confidence, alasan}}."""
    import re

    text = content.strip()

    # 1) Jika terbungkus fenced code block JSON, ambil isinya.
    m_fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m_fence:
        text = m_fence.group(1).strip()

    # 2) Coba ekstrak objek JSON datar {...} (tanpa kurung bersarang).
    results = {}
    objs = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
    for o in objs:
        try:
            d = json.loads(o)
        except Exception:
            continue
        k = d.get("konsep")
        if not k:
            continue
        results[k] = {
            "ditemukan": str(d.get("ditemukan", "")).lower(),
            "source": d.get("source", ""),
            "confidence": d.get("confidence", ""),
            "alasan": d.get("alasan", ""),
        }
    if results:
        return results

    # 3) Fallback: blok kata kunci bergaya list.
    lines = content.splitlines()
    cur = None
    for ln in lines:
        ln = ln.strip()
        if not ln or ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        key = key.strip().lower()
        # buang penanda daftar (###, -, *, ., dst) agar "### Konsep:" -> "konsep"
        key = key.lstrip("#-*.").strip()
        val = val.strip()
        if key == "konsep":
            cur = val
            results[cur] = {}
        elif cur and key in ("ditemukan", "source", "confidence", "alasan"):
            results[cur][key] = val
    return results


def run(schema_path: Path, out_path: Path, n_runs: int = 2):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    prompt = PROMPT_TEMPLATE.format(schema=json.dumps(schema, ensure_ascii=False))
    all_runs = []
    for i in range(n_runs):
        content, usage = call_llm(prompt)
        parsed = parse_answer(content)
        all_runs.append({"run": i + 1, "raw": content, "parsed": parsed, "usage": usage})
        print(f"[run {i+1}] reasoning=", json.dumps(parsed, ensure_ascii=False))
    out_path.write_text(json.dumps(all_runs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    # ringkasan usage
    for r in all_runs:
        u = r["usage"]
        print(f"  run{r['run']}: in={u.get('prompt_tokens')} out={u.get('completion_tokens')} total={u.get('total_tokens')}")


if __name__ == "__main__":
    run(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        int(sys.argv[3]) if len(sys.argv) > 3 else 2,
    )