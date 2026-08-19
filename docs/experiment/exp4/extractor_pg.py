"""Exp-4 C2: ekstraksi katalog DETERMINISTIK dari PostgreSQL nyata.

Lanjutan spike Exp-4:
- C1 (LLM pilih alat, agent_tools.py) terbukti punya risiko halusinasi: model
  mengisi struktur tabel yang TIDAK pernah ia query dengan kolom karangan.
- C2 = pola Exp-2 yang andal tapi pada DB nyata: ekstraktor kode (deterministik,
  terverifikasi) mengambil SELURUH struktur via pg_catalog sebagai role
  `aios_schema_reader` (read-only boundary), menghasilkan schema.json.
- LLM TIDAK lagi menulis SQL / memilih alat: ia hanya menerima schema.json
  untuk usulan MAPPING (mapper.py style). Tidak ada celah halusinasi struktur.

Output: schema.json (semua tabel+kolom+PK+FK, tanpa baris data bisnis).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PSQL = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
PGPASSWORD = os.environ.get("AIOS_PG_PASSWORD", "")
PGUSER = "aios_schema_reader"
PGHOST = "localhost"
PGPORT = "5432"


def run_psql(dbname, sql):
    env = dict(os.environ)
    env["PGPASSWORD"] = PGPASSWORD
    p = subprocess.run(
        [PSQL, "-U", PGUSER, "-h", PGHOST, "-p", PGPORT, "-d", dbname,
         "-X", "-tA", "-c", sql],
        capture_output=True, text=True, env=env, timeout=60)
    out = p.stdout.strip()
    err = p.stderr.strip()
    if p.returncode != 0:
        raise RuntimeError(f"psql error: {err}")
    return [ln for ln in out.splitlines() if ln.strip()]


def list_tables(dbname):
    """Semua tabel+view di semua schema USER (bukan pg_catalog/information_schema/
    pg_toast). Output: 'schema|relname|relkind'."""
    sql = ("SELECT n.nspname || '|' || c.relname || '|' || c.relkind::text "
           "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
           "WHERE n.nspname NOT IN ('pg_catalog','information_schema','pg_toast') "
           "  AND n.nspname NOT LIKE 'pg_toast%' AND n.nspname NOT LIKE 'pg_temp%' "
           "  AND c.relkind IN ('r','v') "
           "ORDER BY n.nspname, c.relname;")
    return run_psql(dbname, sql)


def list_columns(dbname, schema, table):
    sql = (f"SELECT a.attname || '|' || format_type(a.atttypid,a.atttypmod) "
           f"|| '|' || (CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END), "
           f"CASE WHEN pk.attnum IS NOT NULL THEN 'PK' ELSE '' END "
           f"FROM pg_attribute a "
           f"JOIN pg_class t ON t.oid=a.attrelid "
           f"JOIN pg_namespace n ON n.oid=t.relnamespace "
           f"LEFT JOIN (SELECT i.indrelid, unnest(i.indkey) AS attnum "
           f"           FROM pg_index i WHERE i.indisprimary) pk "
           f"  ON pk.indrelid=t.oid AND pk.attnum=a.attnum "
           f"WHERE n.nspname='{schema}' AND t.relname='{table}' "
           f"  AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum;")
    return run_psql(dbname, sql)


def list_foreign_keys(dbname):
    sql = ("""SELECT n1.nspname || '.' || t1.relname || '.' || a1.attname ||
                     ' -> ' || n2.nspname || '.' || t2.relname || '.' || a2.attname
              FROM pg_constraint cc
              JOIN pg_class t1 ON t1.oid=cc.conrelid
              JOIN pg_namespace n1 ON n1.oid=t1.relnamespace
              JOIN pg_class t2 ON t2.oid=cc.confrelid
              JOIN pg_namespace n2 ON n2.oid=t2.relnamespace
              JOIN pg_attribute a1 ON a1.attrelid=cc.conrelid AND a1.attnum=cc.conkey[1]
              JOIN pg_attribute a2 ON a2.attrelid=cc.confrelid AND a2.attnum=cc.confkey[1]
              WHERE cc.contype='f'
                AND n1.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
                AND n2.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
              ORDER BY n1.nspname, t1.relname, a1.attname;""")
    return run_psql(dbname, sql)


def list_unique_columns(dbname):
    """Kolom yang termasuk index/constraint UNIQUE NON-PK (untuk deteksi EAV:
    tabel definisi atribut biasanya punya kolom kode UNIQUE). Output
    'schema|table|column'."""
    sql = ("""SELECT n.nspname || '|' || c.relname || '|' || a.attname
              FROM pg_index i
              JOIN pg_class c ON c.oid=i.indrelid
              JOIN pg_namespace n ON n.oid=c.relnamespace
              JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=ANY(i.indkey)
              WHERE i.indisunique AND NOT i.indisprimary
                AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
              ORDER BY n.nspname, c.relname, a.attnum;""")
    return run_psql(dbname, sql)


def detect_eav(data):
    """Deteksi pola EAV secara STRUKTURAL dan generik (tanpa mengandalkan nama
    tabel tertentu), dari schema.json hasil ekstraksi.

    Definisi tabel nilai (candidate):
      - PK komposit (>= 2 kolom) dan SEMUA kolom PK adalah kolom FK;
      - punya >= 1 kolom yang BUKAN PK dan BUKAN FK (kolom nilai).

    Klaster EAV: >= 2 tabel nilai yang mereferensikan 2 parent yang SAMA.
    Di antara parent, tabel 'definisi' diidentifikasi sebagai parent yang punya
    kolom varchar non-PK non-FK yang UNIQUE (atau nama mirip kode/nama), yang
    menjadi pembeda makna baris nilai.

    Return: list of dict {value_tables, parents, definitions_table,
    discriminator, note}.
    """
    from collections import defaultdict

    def qkey(schema, table):
        return schema + "." + table

    tables = {qkey(t["schema"], t["table"]): t for t in data["tables"]}
    unique_cols = defaultdict(set)
    for u in data.get("unique_columns", []):
        parts = u.split("|")
        if len(parts) == 3:
            unique_cols[qkey(parts[0], parts[1])].add(parts[2])

    fk_from_cols = defaultdict(list)
    fk_out = defaultdict(list)
    for f in data["foreign_keys"]:
        fs = f["from"].split(".")
        ts = f["to"].split(".")
        if len(fs) == 3 and len(ts) == 3:
            src = qkey(fs[0], fs[1])
            dst = qkey(ts[0], ts[1])
            fk_from_cols[src].append(fs[2])
            fk_out[src].append((fs[2], dst))

    value_tables = []
    for key, t in tables.items():
        pk = set(t["primary_key"])
        fks = set(fk_from_cols.get(key, []))
        if len(pk) < 2 or not pk.issubset(fks):
            continue
        value_cols = [c["name"] for c in t["columns"]
                      if c["name"] not in pk and c["name"] not in fks]
        if not value_cols:
            continue
        parents = sorted({dst for _, dst in fk_out.get(key, [])})
        value_tables.append({"key": key, "table": t["table"],
                             "value_columns": value_cols, "parents": parents})

    groups = defaultdict(list)
    for vt in value_tables:
        groups[tuple(vt["parents"])].append(vt)

    code_like = ("code", "kode", "nama", "name", "label", "type", "domain")
    clusters = []
    for parents, vts in groups.items():
        if len(vts) < 2 or len(parents) != 2:
            continue
        def_table = None
        def_col = None
        for pkey in parents:
            pt = tables.get(pkey)
            if not pt:
                continue
            for col in pt["columns"]:
                if col["name"] in pt["primary_key"]:
                    continue
                is_str = (col["type"].startswith("character varying")
                          or col["type"] == "text")
                is_unique = col["name"] in unique_cols.get(pkey, set())
                if is_str and (is_unique
                               or any(s in col["name"].lower() for s in code_like)):
                    def_table = pt["table"]
                    def_col = col["name"]
                    break
            if def_table:
                break
        clusters.append({
            "value_tables": [vt["table"] for vt in vts],
            "parents": [tables[p]["table"] for p in parents],
            "definitions_table": def_table,
            "discriminator": def_col,
            "note": ("Skema memakai pola EAV: baris di tabel nilai menyimpan "
                     "satu nilai per atribut; makna baris ditentukan oleh "
                     "kolom kode di tabel definisi." if def_table else
                     "Pola EAV terdeteksi tetapi tabel definisi/pembeda makna "
                     "tidak teridentifikasi."),
        })
    return clusters


def extract(dbname):
    tables = list_tables(dbname)
    result = {"tables": []}
    for ln in tables:
        parts = ln.split("|")
        schema, name, relkind = parts[0], parts[1], parts[2]
        cols = []
        pk_cols = []
        for cln in list_columns(dbname, schema, name):
            cparts = cln.split("|")
            col_name, col_type = cparts[0], cparts[1]
            notnull = cparts[2] == "NO"
            is_pk = len(cparts) > 3 and cparts[3] == "PK"
            cols.append({"name": col_name, "type": col_type, "nullable": not notnull})
            if is_pk:
                pk_cols.append(col_name)
        result["tables"].append({"schema": schema, "table": name, "kind": relkind,
                                 "columns": cols, "primary_key": pk_cols})
    fks = []
    for ln in list_foreign_keys(dbname):
        parts = ln.split(" -> ")
        fks.append({"from": parts[0], "to": parts[1]})
    result["foreign_keys"] = fks
    result["unique_columns"] = list_unique_columns(dbname)
    result["eav_clusters"] = detect_eav(result)
    return result


if __name__ == "__main__":
    db = sys.argv[1]
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("schema.json")
    data = extract(db)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {db} -> {out_path}")
    for t in data["tables"]:
        fk_from = len([f for f in data["foreign_keys"]
                       if f['from'].startswith(t['schema'] + '.' + t['table'] + '.')])
        print(f"  {t['schema']}.{t['table']} ({t['kind']}): {len(t['columns'])} kolom, FK-out={fk_from}")
    print("FK:")
    for f in data["foreign_keys"]:
        print(f"  {f['from']} -> {f['to']}")
    print("EAV clusters:")
    for c in data["eav_clusters"]:
        print(f"  value_tables={c['value_tables']} parents={c['parents']} "
              f"definitions={c['definitions_table']}.{c['discriminator']}")