"""Exp-4 spike harness: AI yang menentukan cara query struktur sendiri.

Konteks:
- AIOS DB adapter: role PostgreSQL `aios_schema_reader` (LOGIN only, TANPA
  privilege di tabel bisnis). Dapat membaca katalog (pg_catalog/information_schema)
  tapi MUSTAHIL membaca baris data bisnis (ditolak server).
- Sub-agent analyze schema = Qwen2.5-3B (llama.cpp, OpenAI-compatible di
  127.0.0.1:8080). AI memilih & menulis sendiri SQL katalog untuk memahami
  struktur database client, lalu menyusun skema + usulan mapping.
- boundary keamanan DITEGAKKAN SERVER (role tak punya hak), bukan filter teks.

Loop sederhana (1 tool: query):
  LLM -> {"tool":"query","args":{"sql":"..."}} -> eksekusi psql sebagai
  aios_schema_reader -> hasil stdout/stderr diteruskan ke LLM -> ulang,
  hingga LLM menjawab "final" berisi kesimpulan skema + mapping.

Semua query yang dikirim AKAN dicatat (log per run).
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "Qwen2.5-3B-Instruct-Q4_K_M"
SEED = 42
TEMPERATURE = 0.0
MAX_TOKENS = 1024
MAX_ITER = 10
PSQL = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
PGPASSWORD = os.environ.get("AIOS_PG_PASSWORD", "")
PGUSER = "aios_schema_reader"
PGHOST = "localhost"
PGPORT = "5432"

SYSTEM_PROMPT = """Anda adalah sub-agent 'Analyze Schema' AIOS, sebuah AI yang
BERADAPTASI pada database client yang beragam. Anda diberi koneksi RE-AD-ONLY
yang TIDAK dapat mengakses isi data bisnis (server menolak). Anda hanya dapat
melihat STRUKTUR (katalog) database.

Jenis database client: PostgreSQL.

PENTING untuk PostgreSQL: view information_schema hanya menampilkan objek yang
dimiliki user (privilege-filtered). Akun yang Anda pakai TIDAK memiliki hak apa
pun di tabel bisnis, jadi menanyakan information_schema kemungkinan besar
mengembalikan KOSONG. Gunakan pg_catalog (tidak difilter oleh privilege) —
itu sumber struktur yang ANDA harus pakai. Jika Anda salah dan server menolak,
jangan ulangi query yang sama persis; perbaiki.

Contoh query pg_catalog yang valid (Anda bebas menulis query lain yang sah):
- daftar tabel:   SELECT c.relname AS table_name, c.relkind
                  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                  WHERE n.nspname='public' AND c.relkind='r' ORDER BY c.relname;
- daftar kolom:   SELECT a.attname AS column_name,
                         format_type(a.atttypid,a.atttypmod) AS data_type,
                         a.attnotnull
                  FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
                  WHERE c.relname='<TABEL>' AND a.attnum>0 AND NOT a.attisdropped
                  ORDER BY a.attnum;
- primary key:    SELECT a.attname FROM pg_index i
                  JOIN pg_class c ON c.oid=i.indrelid
                  JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=ANY(i.indkey)
                  WHERE c.relname='<TABEL>' AND i.indisprimary;
- foreign key:    SELECT cc.conname, t2.relname AS ref_table
                  FROM pg_constraint cc
                  JOIN pg_class t1 ON t1.oid=cc.conrelid
                  JOIN pg_class t2 ON t2.oid=cc.confrelid
                  WHERE t1.relname='<TABEL>' AND cc.contype='f';

ATURAN:
1. Anda TIDAK akan pernah bisa membaca baris data (SELECT * FROM ...) karena
   server menolak. Jika server menolak, simpan fakta itu dan lanjutkan.
2. Tujuan: pahami SEMUA tabel: nama tabel, kolom, tipe data, primary key,
   foreign key, dan kemungkinan makna semantiknya.
3. Setiap keluaran Anda adalah SATU objek JSON SAJA (tanpa ```json, tanpa teks
   lain di sekitar, tanpa baris baru di dalam string SQL):
   - Untuk menjalankan query:
     {"tool":"query","args":{"sql":"<SQL KATALOG>"}}
   - Untuk MENYELESAIKAN (ketika Anda sudah cukup paham):
     {"tool":"final","args":{"schema":{...},"mapping":{...},"catatan":"..."}}
   Field 'schema': objek JSON berisi daftar tabel/kolom/tipe/PK/FK.
   Field 'mapping': usulan pemetaan konsep canonical (Product.name/price/stock)
     dengan {found:true|false, source, confidence: tinggi/sedang/rendah, alasan}.
   Field 'catatan': kesimpulan singkat + apakah ada kolom yang maknanya tidak
     jelas dan perlu validasi client.
4. Satu respons = SATU tindakan. Jangan menggabungkan beberapa query dalam
   satu respons.
5. JANGAN menebak data; hanya struktur dan makna semantik dari nama/tipe.
6. Bekerja efisien: batch query bila memungkinkan, hindari pengulangan."""


def call_llm(messages):
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "seed": SEED,
        "max_tokens": MAX_TOKENS,
    }
    req = Request(BASE_URL, data=json.dumps(body).encode("utf-8"),
                  headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(5):
        try:
            with urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [llm retry {attempt+1}] {e}", flush=True)
            time.sleep(3)
    raise RuntimeError("LLM call failed")


def run_psql(dbname, sql):
    """Eksekusi sebagai aios_schema_reader (read-only boundary). Return (ok, output)."""
    env = dict(os.environ)
    env["PGPASSWORD"] = PGPASSWORD
    cmd = [PSQL, "-U", PGUSER, "-h", PGHOST, "-p", PGPORT, "-d", dbname,
           "-X", "-tA", "-c", sql]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    out = p.stdout.strip()
    err = p.stderr.strip()
    if p.returncode != 0:
        return False, err
    return True, out


def _fix_raw_newlines_in_strings(text: str) -> str:
    """Ganti baris-baru mentah di dalam string literal JSON dengan \\n (escape)."""
    out = []
    in_str = False
    for ch in text:
        if ch == '"':
            in_str = not in_str
            out.append(ch)
        elif ch in "\r\n" and in_str:
            out.append("\\n")
        else:
            out.append(ch)
    return "".join(out)


def parse_all_jsons(content):
    """Ambil SEMUA objek JSON bertool query/final dari respons, urut kemunculan."""
    import re
    text = content.strip()
    candidates = []
    for m in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.DOTALL):
        candidates.append(m.group(1).strip())
    candidates.append(text)
    results = []
    scanned = set()
    for cand in candidates:
        for attempt in (cand, _fix_raw_newlines_in_strings(cand)):
            key = attempt
            if key in scanned:
                continue
            scanned.add(key)
            try:
                obj = json.loads(attempt)
            except Exception:
                continue
            if isinstance(obj, dict) and obj.get("tool") in ("query", "final"):
                results.append(obj)
    return results


def parse_llm_json(content):
    """Ambil objek JSON pertama yang valid (buang fence/teks di sekitarnya)."""
    res = parse_all_jsons(content)
    return res[0] if res else {"tool": "invalid", "raw": content}


def run(dbname, out_dir: Path, run_no: int):
    log = {"db": dbname, "run": run_no, "queries": [], "turns": []}
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    final = None
    out_dir.mkdir(parents=True, exist_ok=True)
    snap_path = out_dir / f"snap_{dbname}_run{run_no}.json"

    def save(force_final=None):
        log2 = dict(log)
        fl = force_final if force_final is not None else dict(log.get("final") or {})
        log2["final"] = fl
        snap_path.write_text(json.dumps(log2, indent=2, ensure_ascii=False), encoding="utf-8")

    for it in range(1, MAX_ITER + 1):
        content = call_llm(messages)
        msg = {"role": "assistant", "content": content}
        messages.append(msg)
        actions = parse_all_jsons(content)
        turn = {"iter": it, "raw": content, "actions": actions,
                "n_actions": len(actions)}
        log["turns"].append(turn)
        if not actions:
            log["queries"].append({"iter": it, "sql": None, "ok": False,
                                   "output": "(no valid JSON action)"})
            messages.append({"role": "user",
                             "content": "Respons tidak valid. Kirim SATU objek JSON dengan tool query atau final."})
            save()
            continue
        # proses semua aksi dalam urutan, hentikan pada tool final pertama
        for act in actions:
            tool = act.get("tool")
            if tool == "final":
                final = act.get("args", {})
                log["final"] = final
                save(final)
                print(f"  [run {run_no}] FINAL at iter {it}", flush=True)
                break
            if tool == "query":
                sql = act.get("args", {}).get("sql", "")
                if not sql:
                    log["queries"].append({"iter": it, "sql": sql, "ok": False,
                                           "output": "(empty sql)"})
                    messages.append({"role": "user",
                                     "content": "JSON dengan field sql kosong. Kirim query sah."})
                    continue
                ok, output = run_psql(dbname, sql)
                log["queries"].append({"iter": it, "sql": sql, "ok": ok,
                                       "output": output[:4000]})
                save()
                if ok:
                    print(f"  [run {run_no}] Q{it} OK ({len(sql)} chars) -> {output[:120]!r}", flush=True)
                    user_msg = f"Hasil query (kode keluar sukses):\n{output[:4000]}"
                else:
                    print(f"  [run {run_no}] Q{it} DENIED/ERROR: {output[:120]!r}", flush=True)
                    user_msg = f"Query ditolak/error oleh server:\n{output[:4000]}\n(Lanjutkan memahami struktur tanpa data.)"
                messages.append({"role": "user", "content": user_msg})
        else:
            save()
            continue
        break  # keluar bila ada tool final
    if final is None:
        log["final"] = None
        save(force_final=None)

    # simpan log final (rename dari snapshot)
    fname = out_dir / f"log_{dbname}_run{run_no}.json"
    fname.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    if snap_path.exists():
        snap_path.unlink()
    print(f"Wrote {fname}", flush=True)
    return log


if __name__ == "__main__":
    db = sys.argv[1]
    n_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("out")
    for r in range(1, n_runs + 1):
        run(db, out_dir, r)