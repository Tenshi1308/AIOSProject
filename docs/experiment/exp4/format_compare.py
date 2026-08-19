"""Exp-4 Opsi B: bandingkan 3 format prompt untuk LLM mapping.

Latar: format "lengkap" (meta.json dari extractor_pg.py, dengan field schema/kind
dan FK ber-prefix public.) menurunkan hasil mapping client_b (Product.price
true->false) dibanding format ringkas v1. Dugaan: token berulang yang tidak
membantu mengganggu penalaran 3B pada kasus EAV.

Di sini kita MENGUJI dugaan itu secara terkontrol:
- F1 (ringkas): tabel tanpa field schema/kind, FK tanpa prefix schema. Bentuk
  mendekati v1 yang terbukti benar di A/B, tapi konten tetap dari extractor
  baru (semua schema user + view).
- F2 (lengkap): meta.json apa adanya (dengan schema/kind + prefix) = bentuk v2
  yang membuat B.price gagal. Sebagai pembanding.
- F3 (ringkas + qualified): seperti F1, tapi FK memakai prefix schema HANYA
  bila ada lebih dari satu schema di database (uji apakah prefix penting saat
  schema ganda).

Setiap format dijalankan n_runs kali (temp=0, seed=42). Output per format
disimpan terpisah untuk dibandingkan.

Penggunaan:
  python format_compare.py <db> <meta.json> <out_prefix> [n_runs]
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


def strip_schema(ref):
    """'public.tabel.kolom' -> 'tabel.kolom' (hapus prefix schema pertama)."""
    parts = ref.split(".")
    if len(parts) == 3:
        return parts[1] + "." + parts[2]
    return ref


def render_f1(meta):
    """Ringkas: tanpa schema/kind, FK tanpa prefix schema."""
    tables = [{"table": t["table"], "columns": t["columns"],
               "primary_key": t["primary_key"]} for t in meta["tables"]]
    fks = [{"from": strip_schema(f["from"]), "to": strip_schema(f["to"])}
           for f in meta["foreign_keys"]]
    return {"tables": tables, "foreign_keys": fks}


def render_f2(meta):
    """Lengkap: meta apa adanya (dengan schema/kind + prefix)."""
    return meta


def render_f3(meta):
    """Ringkas + qualified: seperti F1, tapi FK ber-prefix bila >1 schema."""
    schemas = {t["schema"] for t in meta["tables"]}
    qualified = len(schemas) > 1
    tables = [{"table": t["table"], "columns": t["columns"],
               "primary_key": t["primary_key"]} for t in meta["tables"]]
    fks = []
    for f in meta["foreign_keys"]:
        if qualified:
            fks.append({"from": f["from"], "to": f["to"]})
        else:
            fks.append({"from": strip_schema(f["from"]), "to": strip_schema(f["to"])})
    return {"tables": tables, "foreign_keys": fks}


FORMATS = {"F1": render_f1, "F2": render_f2, "F3": render_f3}


def main():
    db = sys.argv[1]
    meta_path = Path(sys.argv[2])
    out_prefix = sys.argv[3]
    n_runs = int(sys.argv[4]) if len(sys.argv) > 4 else 2

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    print(f"=== {db}: {len(meta['tables'])} tabel, "
          f"{len(meta['foreign_keys'])} FK, {n_runs} run per format ===")

    summary = {}
    for name in ("F1", "F2", "F3"):
        render = FORMATS[name]
        schema_for_llm = render(meta)
        prompt = PROMPT_TEMPLATE.format(
            schema=json.dumps(schema_for_llm, ensure_ascii=False))
        n_tokens = len(prompt.split())
        print(f"\n--- {name} ({n_tokens} kata prompt) ---")
        all_runs = []
        for i in range(n_runs):
            content, usage = call_llm(prompt)
            parsed = parse_answer(content)
            all_runs.append({"run": i + 1, "raw": content, "parsed": parsed,
                             "usage": usage})
            found = {k: v.get("ditemukan") for k, v in parsed.items()}
            print(f"  run{i+1} ditemukan = {json.dumps(found, ensure_ascii=False)}")
        out_path = Path(out_prefix + "_" + name + ".json")
        out_path.write_text(json.dumps(all_runs, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        print(f"  Wrote {out_path}")
        for r in all_runs:
            u = r["usage"]
            print(f"  run{r['run']}: in={u.get('prompt_tokens')} "
                  f"out={u.get('completion_tokens')} total={u.get('total_tokens')}")
        summary[name] = [
            {k: v.get("ditemukan") for k, v in r["parsed"].items()}
            for r in all_runs
        ]

    print("\n=== RINGKASAN ditemukan (benar jika sesuai ground truth) ===")
    for name, runs in summary.items():
        print(f"{name}: {json.dumps(runs, ensure_ascii=False)}")


if __name__ == "__main__":
    main()