"""Exp-4 hybrid: alat katalog terverifikasi, LLM memilih + mapping.

Konteks (kelanjutan spike):
- "AI yang menulis SQL sendiri" (exp4/agent_query.py) terbukti lambat & loop
  pada Qwen2.5-3B (sintaks salah, tak pernah self-correct).
- Opsi C: beri LLM alat katalog GENERIK yang sudah terverifikasi benar:
    * list_tables()
    * list_columns(table)
    * list_foreign_keys()
  LLM memutuskan alat mana dipakai + memahami makna + usulan mapping.
- Tetap BERJALAN di boundary read-only: role `aios_schema_reader` (LOGIN only,
  tanpa privilege ke tabel bisnis). Alat hanya SELECT pg_catalog -> tidak ada
  baris data bisnis yang pernah terbaca.
- Model: Qwen2.5-3B-Instruct-Q4_K_M (llama.cpp, :8080), temp=0, seed=42.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "Qwen2.5-3B-Instruct-Q4_K_M"
SEED = 42
TEMPERATURE = 0.0
MAX_TOKENS = 2048
MAX_ITER = 15
PSQL = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
PGPASSWORD = os.environ.get("AIOS_PG_PASSWORD", "")
PGUSER = "aios_schema_reader"
PGHOST = "localhost"
PGPORT = "5432"

SYSTEM_PROMPT = """Anda adalah sub-agent 'Analyze Schema' AIOS, sebuah AI yang
BERADAPTASI pada database client yang beragam. Anda bekerja di kanal RE-AD-ONLY:
server menolak akses data bisnis, Anda hanya melihat STRUKTUR (katalog).

Anda DISEDIAKAN alat berikut (jangan menulis SQL sendiri, gunakan alat):
1. {"tool":"list_tables","args":{}}  -> daftar tabel user (schema public)
2. {"tool":"list_columns","args":{"table":"<nama tabel>"}} -> kolom (nama, tipe, not null)
3. {"tool":"list_foreign_keys","args":{}} -> relasi foreign key antar tabel

Tujuan:
- Pahami SEMUA tabel & kolom di database ini.
- Untuk memahami makna kolom, gunakan nama kolom, tipe data, dan konteks relasi.
- Kemudian usulkan pemetaan ke konsep canonical.

Setiap keluaran Anda adalah SATU objek JSON SAJA (tanpa ```json, tanpa teks lain):
- Panggil alat: {"tool":"list_tables"} / {"tool":"list_columns","args":{"table":"X"}} / {"tool":"list_foreign_keys"}
- SELESAIKAN: {"tool":"final","args":{
    "schema": {"tables":[{"name":"...","columns":[{"name":"...","type":"..."}],"primary_key":["..."],"foreign_keys":["..->.."]}]},
    "mapping": {"Product.name":{"found":true|false,"source":"tabel.kolom","confidence":"tinggi|sedang|rendah","alasan":"..."},
                "Product.price":{...},
                "Product.stock":{...}},
    "catatan":"...kesimpulan + kolom yang maknanya tidak jelas dan perlu validasi client..."}}

Aturan:
1. "found:true" hanya bila ada bukti jelas dari struktur bahwa konsep tersedia.
2. "found:false" hanya bila konsep benar-benar tidak ada. JANGAN false hanya
   karena ragu atau tak ada kolom literal bernama "name" (mis. di skema EAV,
   nama bisa tersimpan via tabel atribut -> evaluasi dan jelaskan).
3. JANGAN menebak nilai data; cukup source/cara representasi.
4. Saat mendapat hasil alat, lanjutkan menggali struktur yang belum dipahami.
5. Satu respons = SATU tindakan (satu alat ATAU final)."""


def call_llm(messages):
    body = {"model": MODEL, "messages": messages, "temperature": TEMPERATURE,
            "seed": SEED, "max_tokens": MAX_TOKENS}
    req = Request(BASE_URL, data=json.dumps(body).encode("utf-8"),
                  headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def run_psql(dbname, sql):
    env = dict(os.environ)
    env["PGPASSWORD"] = PGPASSWORD
    p = subprocess.run(
        [PSQL, "-U", PGUSER, "-h", PGHOST, "-p", PGPORT, "-d", dbname,
         "-X", "-tA", "-c", sql],
        capture_output=True, text=True, env=env, timeout=60)
    out = p.stdout.strip()
    err = p.stderr.strip()
    return (p.returncode == 0), (out or err)


# --- Tools (query memakai pg_catalog: tidak difilter privilege) ------------

def tool_list_tables(dbname):
    sql = """SELECT c.relname FROM pg_class c
             JOIN pg_namespace n ON n.oid=c.relnamespace
             WHERE n.nspname='public' AND c.relkind='r'
             ORDER BY c.relname;"""
    return run_psql(dbname, sql)


def tool_list_columns(dbname, table):
    sql = f"""SELECT a.attname || '|' || format_type(a.atttypid,a.atttypmod)
                   || '|' || (CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END)
              FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
              JOIN pg_namespace n ON n.oid=c.relnamespace
              WHERE n.nspname='public' AND c.relname={_lit(table)}
                AND a.attnum>0 AND NOT a.attisdropped
              ORDER BY a.attnum;"""
    return run_psql(dbname, sql)


def tool_list_foreign_keys(dbname):
    sql = """SELECT t1.relname || '.' || a1.attname || ' -> ' ||
                    t2.relname || '.' || a2.attname
             FROM pg_constraint cc
             JOIN pg_class t1 ON t1.oid=cc.conrelid
             JOIN pg_namespace n1 ON n1.oid=t1.relnamespace
             JOIN pg_class t2 ON t2.oid=cc.confrelid
             JOIN pg_attribute a1 ON a1.attrelid=cc.conrelid AND a1.attnum=cc.conkey[1]
             JOIN pg_attribute a2 ON a2.attrelid=cc.confrelid AND a2.attnum=cc.confkey[1]
             WHERE cc.contype='f' AND n1.nspname='public'
             ORDER BY t1.relname, a1.attname;"""
    return run_psql(dbname, sql)


def _lit(s):
    return "'" + s.replace("'", "''") + "'"


TOOL_FUNCS = {
    "list_tables": tool_list_tables,
    "list_columns": tool_list_columns,
    "list_foreign_keys": tool_list_foreign_keys,
}


def parse_action(content):
    """Ambil objek JSON pertama yang punya field tool."""
    import re
    text = content.strip()
    candidates = []
    for m in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.DOTALL):
        candidates.append(m.group(1).strip())
    candidates.append(text)
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("tool"):
            return obj
    return None


def run(dbname, out_dir: Path, run_no: int):
    log = {"db": dbname, "run": run_no, "actions": [], "final": None}
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    final = None
    for it in range(1, MAX_ITER + 1):
        content = call_llm(messages)
        act = parse_action(content)
        if act is None:
            messages.append({"role": "user",
                             "content": "Respons tidak valid. Kirim SATU objek JSON alat atau final."})
            log["actions"].append({"iter": it, "tool": None, "args": None,
                                   "ok": False, "output": "(invalid JSON)"})
            continue
        tool = act["tool"]
        args = act.get("args", {}) or {}
        log["actions"].append({"iter": it, "tool": tool, "args": args})
        if tool == "final":
            final = args
            log["final"] = final
            print(f"  [run {run_no}] FINAL at iter {it}", flush=True)
            break
        if tool in TOOL_FUNCS:
            try:
                ok, output = TOOL_FUNCS[tool](dbname, **args)
            except TypeError as e:
                ok, output = False, f"args salah: {e}"
            log["actions"][-1]["ok"] = ok
            log["actions"][-1]["output"] = output[:4000]
            if not ok:
                log["actions"][-1]["denied"] = "permission denied" in output.lower()
            print(f"  [run {run_no}] {tool}({json.dumps(args,ensure_ascii=False)}) ok={ok} -> {output[:100]!r}", flush=True)
            messages.append({"role": "user",
                             "content": f"Hasil {tool}:\n{output[:4000]}"})
        else:
            log["actions"][-1]["ok"] = False
            log["actions"][-1]["output"] = f"tool tidak dikenal: {tool}"
            messages.append({"role": "user",
                             "content": f"Tool {tool!r} tidak dikenal. Gunakan list_tables / list_columns / list_foreign_keys / final."})
    if final is None:
        log["final"] = None
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f"log_{dbname}_run{run_no}.json"
    fname.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {fname}", flush=True)
    return log


if __name__ == "__main__":
    db = sys.argv[1]
    n_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("hybrid_out")
    for r in range(1, n_runs + 1):
        run(db, out_dir, r)