"""Exp-4 Opsi 2 lanjutan: deteksi EAV generik + anotasi input untuk LLM mapping.

Latar: format "lengkap" (F2) menurunkan hasil mapping client_b (Product.price
gagal) karena token berulang mengganggu penalaran 3B pada skema EAV. Akar
masalah: makna baris di tabel nilai (EAV) ditentukan oleh kolom kode di tabel
definisi, dan 3B kesulitan menelusuri rantai FK itu sendiri.

Opsi 2 menyelesaikan akar masalah dengan anotasi DETERMINISTIK (hasil deteksi
struktural di extractor_pg.detect_eav), tetap metadata-only, tanpa LLM menebak:
  A0 = tanpa anotasi (baseline / kontrol)
  A1 = tambah objek top-level "eav": {...} DI DALAM schema JSON yang dikirim
       ke LLM (anotasi di data).
  A2 = tambah hint kalimat DI PROMPT (di luar JSON skema), dibangun dari hasil
       deteksi (nama tabel/kolom aktual client, bukan hardcoded).

Matriks yang dijalankan (temp=0, seed=42, 2 run per sel):
  - client_e (EAV Indonesia): F1+A0, F1+A1, F1+A2
  - client_b (EAV+JSONB):    F1+A1, F1+A2, F2+A2 (diagnostik: bisakah anotasi
                             menyelamatkan format lengkap yang tadinya gagal?)
  client_a/c/d (non-EAV) tidak perlu di-re-run: tanpa klaster EAV, A1/A2 tidak
  mengubah input vs baseline F1 -> deterministik identik.

Penggunaan:
  python eav_compare.py <db> <meta.json> <out_prefix> <FMT> <ANN> [n_runs]
    FMT: F1 | F2 | F3
    ANN: A0 | A1 | A2
"""
import json
import sys
from pathlib import Path

from format_compare import (PROMPT_TEMPLATE, call_llm, parse_answer,
                            render_f1, render_f2, render_f3)

FORMAT_FUNCS = {"F1": render_f1, "F2": render_f2, "F3": render_f3}


def build_eav_note(cluster):
    """Kalimat hint generik dari hasil deteksi (nama tabel/kolom aktual)."""
    vt = ", ".join(cluster["value_tables"])
    defs = f"{cluster['definitions_table']}.{cluster['discriminator']}"
    return (f"Catatan struktur: skema ini memakai pola EAV (entity-attribute-value). "
            f"Tabel nilai ({vt}) menyimpan SATU nilai per atribut sebagai baris; "
            f"makna sebuah baris ditentukan oleh kolom {defs} di tabel definisi "
            f"atribut (mis. kode 'name', 'price', 'stock'). Saat mengevaluasi "
            f"Product.name/price/stock, periksa tabel nilai yang terhubung ke "
            f"tabel definisi tersebut, bukan hanya mencari kolom literal.")


def apply_annotation(schema_for_llm, meta, ann):
    """Return (schema_or_None, prompt_suffix_or_None). None berarti tidak ada
    perubahan (baseline)."""
    clusters = meta.get("eav_clusters", [])
    if not clusters:
        return None, None
    if ann == "A1":
        extra = {
            "eav": {
                "value_tables": clusters[0]["value_tables"],
                "parents": clusters[0]["parents"],
                "definitions_table": clusters[0]["definitions_table"],
                "discriminator": clusters[0]["discriminator"],
            }
        }
        merged = dict(schema_for_llm)
        merged.update(extra)
        return merged, None
    if ann == "A2":
        return None, build_eav_note(clusters[0])
    return None, None


def run(db, meta_path: Path, out_prefix: str, fmt: str, ann: str, n_runs: int):
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    render = FORMAT_FUNCS[fmt]
    schema_for_llm = render(meta)
    new_schema, suffix = apply_annotation(schema_for_llm, meta, ann)

    prompt = PROMPT_TEMPLATE.format(
        schema=json.dumps(new_schema if new_schema is not None
                          else schema_for_llm, ensure_ascii=False))
    if suffix:
        prompt = prompt.replace(
            "jawab untuk 3 konsep: Product.name, Product.price, Product.stock.",
            suffix + "\n\njawab untuk 3 konsep: Product.name, Product.price, Product.stock.")

    if new_schema is None and suffix is None:
        tag = f"{fmt}+{ann} (tidak ada klaster EAV -> identik baseline)"
    else:
        tag = f"{fmt}+{ann}"
    print(f"=== {db} [{tag}] :: {len(prompt.split())} kata prompt ===")

    all_runs = []
    for i in range(n_runs):
        content, usage = call_llm(prompt)
        parsed = parse_answer(content)
        all_runs.append({"run": i + 1, "raw": content, "parsed": parsed,
                         "usage": usage})
        found = {k: v.get("ditemukan") for k, v in parsed.items()}
        print(f"  run{i+1} = {json.dumps(found, ensure_ascii=False)}")

    fname = Path(out_prefix + f"_{fmt}_{ann}.json")
    fname.write_text(json.dumps(all_runs, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    print(f"  Wrote {fname}")
    for r in all_runs:
        u = r["usage"]
        print(f"  run{r['run']}: in={u.get('prompt_tokens')} "
              f"out={u.get('completion_tokens')} total={u.get('total_tokens')}")
    return all_runs


if __name__ == "__main__":
    db = sys.argv[1]
    meta_path = Path(sys.argv[2])
    out_prefix = sys.argv[3]
    fmt = sys.argv[4]
    ann = sys.argv[5]
    n_runs = int(sys.argv[6]) if len(sys.argv) > 6 else 2
    run(db, meta_path, out_prefix, fmt, ann, n_runs)