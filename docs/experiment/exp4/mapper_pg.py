"""Exp-4 C2 mapper: LLM hanya usulan mapping dari schema.json hasil ekstraksi
deterministik pg_catalog. TIDAK ada baris data bisnis di input.

Ini pola Exp-2 yang terbukti andal, dijalankan pada PostgreSQL NYATA dengan
boundary read-only (`aios_schema_reader`). Hanya perbedaan: skema == metadata-only
(no sample rows), dan tipe kolom memakai format PostgreSQL (mis. smallint,
character varying(40), real).

Model: Qwen2.5-3B-Instruct-Q4_K_M, temp=0, seed=42.
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
kolom, tipe, primary key, foreign key) hasil ekstraksi otomatis dari katalog
database. Struktur ini METADATA-ONLY: TIDAK berisi contoh baris data.

Tugas Anda HANYA: menyarankan pemetaan ke konsep canonical.

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
- "ditemukan: true" hanya bila ada bukti jelas dari struktur bahwa konsep
  tersedia (nama/tipe/relasi/representasi non-literal).
- "ditemukan: false" hanya bila konsep benar-benar tidak ada di skema.
  JANGAN false hanya karena ragu atau tak ada kolom literal bernama "name".
  Di skema EAV (mis. kolom dengan tipe/relasi atribut), nama/harga/stok dapat
  tersimpan via tabel atribut -> evaluasi representasi non-literal.
- Tanpa contoh baris, makna kolom disimpulkan dari nama, tipe, dan relasi.
  Jika makna tidak cukup jelas, beri confidence rendah dan jelaskan bahwa
  perlu validasi client.
- JANGAN menebak nilai data. Beri source/cara representasi, bukan angka.

jawab untuk 3 konsep: Product.name, Product.price, Product.stock."""

CANONICAL = ["Product.name", "Product.price", "Product.stock"]


def call_llm(prompt):
    body = {"model": "Qwen2.5-3B-Instruct-Q4_K_M",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": TEMPERATURE, "seed": SEED, "max_tokens": 512}
    req = Request(BASE_URL, data=json.dumps(body).encode("utf-8"),
                  headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(5):
        try:
            with urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"], data.get("usage", {})
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}", flush=True)
            time.sleep(3)
    raise RuntimeError("LLM call failed")


def parse_answer(content):
    import re

    text = content.strip()

    def try_json(txt):
        objs = re.findall(r"\{[^{}]*\}", txt, re.DOTALL)
        res = {}
        for o in objs:
            try:
                d = json.loads(o)
            except Exception:
                continue
            k = d.get("konsep")
            if not k:
                continue
            res[k] = {"ditemukan": str(d.get("ditemukan", "")).lower(),
                      "source": d.get("source", ""),
                      "confidence": d.get("confidence", ""),
                      "alasan": d.get("alasan", "")}
        return res

    res = try_json(text)
    if res:
        return res
    lines = content.splitlines()
    cur = None
    out = {}
    for ln in lines:
        ln = ln.strip()
        if not ln or ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        key = key.strip().lower().lstrip("#-*.").strip()
        val = val.strip()
        if key == "konsep":
            cur = val
            out[cur] = {}
        elif cur and key in ("ditemukan", "source", "confidence", "alasan"):
            out[cur][key] = val
    return out


def run(schema_path: Path, out_path: Path, n_runs: int = 2):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    prompt = PROMPT_TEMPLATE.format(schema=json.dumps(schema, ensure_ascii=False))
    all_runs = []
    for i in range(n_runs):
        content, usage = call_llm(prompt)
        parsed = parse_answer(content)
        all_runs.append({"run": i + 1, "raw": content, "parsed": parsed, "usage": usage})
        print(f"[run {i+1}] =", json.dumps(parsed, ensure_ascii=False))
    out_path.write_text(json.dumps(all_runs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    for r in all_runs:
        u = r["usage"]
        print(f"  run{r['run']}: in={u.get('prompt_tokens')} out={u.get('completion_tokens')} total={u.get('total_tokens')}")


if __name__ == "__main__":
    run(Path(sys.argv[1]), Path(sys.argv[2]),
        int(sys.argv[3]) if len(sys.argv) > 3 else 2)