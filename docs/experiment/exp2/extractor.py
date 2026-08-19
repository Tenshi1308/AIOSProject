"""Eksperimen 2 - Extractor.

Memparsing file skema SQL (2 file eksperimen: client_a, client_b) menjadi
struktur JSON deterministik: tabel -> kolom (nama, tipe, primary key,
foreign key) + baris sampel.

Konteks: proof-of-feasibility "Opsi C" - kode deterministik yang menangani
ekstraksi skema, LLM hanya untuk usulan mapping. Ini BUKAN parser SQL
universal; cukup untuk format CREATE TABLE / INSERT yang kita tulis di
docs/experiment.
"""
import json
import re
import sys
from pathlib import Path


def _strip_sql_comments(sql: str) -> str:
    """Hilangkan komentar SQL (-- baris  dan  /* ... */ blok) sambil tetap
    menghormati string literal ('...', dengan '' untuk escape quote)."""
    out = []
    i, n = 0, len(sql)
    in_block = False
    while i < n:
        c = sql[i]
        if in_block:
            if c == "*" and i + 1 < n and sql[i + 1] == "/":
                in_block = False
                i += 2
            else:
                i += 1
            continue
        if c == "'":
            # string literal: salin sampai penutup (dua kutip = escape)
            j = i + 1
            buf = ["'"]
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        buf.append("''")
                        j += 2
                        continue
                    buf.append("'")
                    j += 1
                    break
                buf.append(sql[j])
                j += 1
            out.append("".join(buf))
            i = j
            continue
        if c == "-" and i + 1 < n and sql[i + 1] == "-":
            j = sql.find("\n", i)
            i = n if j == -1 else j + 1  # buang sampai akhir baris
            continue
        if c == "/" and i + 1 < n and sql[i + 1] == "*":
            in_block = True
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def parse_create_table(sql: str) -> dict:
    """Parse satu blok CREATE TABLE ... (...) menjadi struktur tabel."""
    # Ambil nama tabel dari "CREATE TABLE <name> ("
    m = re.search(r"CREATE\s+TABLE\s+(\S+)\s*\(", sql, re.IGNORECASE)
    name = m.group(1).strip() if m else "?"
    # Potong isi parentheses (paling luar)
    body = sql[sql.index("(") + 1 : sql.rindex(")")]
    # split top-level by comma (tidak di dalam paren/bracket/quote)
    parts = _split_top_level(body)
    columns = []
    for part in parts:
        p = part.strip()
        if not p or p.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK", "CONSTRAINT")):
            continue
        col = _parse_column(p)
        if col:
            columns.append(col)
    return {"table": name, "columns": columns, "rows": []}


def _split_top_level(s: str):
    """Split string by commas that are outside () [] and quotes."""
    parts, depth, quote, start = [], 0, None, 0
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"', '`'):
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _parse_column(part: str) -> dict:
    """Parse baris kolom: "colname TYPE ... REFERENCES..."."""
    m = re.match(r"(\S+)\s+([A-Za-z_]+(?:\s*\([^)]*\))?)", part)
    if not m:
        return {}
    col = {"name": m.group(1), "type": m.group(2).replace(" ", ""), "pk": False, "fk": None}
    if re.search(r"\bPRIMARY\s+KEY\b", part, re.IGNORECASE):
        col["pk"] = True
    r = re.search(r"\bREFERENCES\s+(\S+)\s*\((\S+)\)", part, re.IGNORECASE)
    if r:
        col["fk"] = f"{r.group(1)}.{r.group(2)}"
    return col


def _strip_outer(s):
    """Hilangkan satu pasangan kurung paling luar bila ada."""
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        return s[1:-1]
    return s


def _split_values(text: str):
    """Pecah '(...),(...),...' menjadi list tuple-mentah (strip paren luar)."""
    # kumpulkan segment antar top-level comma (di luar paren/string)
    out, start, depth, quote = [], 0, 0, None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append(text[start:i])
            start = i + 1
    out.append(text[start:])
    return [_strip_outer(x) for x in out if x.strip()]


def _split_items(text: str):
    """Pecah isi satu tuple: koma di depth 0, string/kurung diabaikan."""
    items, start, depth, quote = [], 0, 0, None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "," and depth == 0:
            items.append(text[start:i])
            start = i + 1
    items.append(text[start:])
    return [x.strip() for x in items]


_LITERAL_RE = re.compile(r"^(['\"])(.*)\1$", re.DOTALL)


def _clean_literal(v: str) -> str:
    v = v.strip()
    m = _LITERAL_RE.match(v)
    if m:
        return m.group(2)
    return v


def parse_inserts(sql: str) -> dict:
    """Map tabel -> list rows, dari semua INSERT di file."""
    out = {}
    for m in re.finditer(
        r"INSERT\s+INTO\s+(\S+)\s*(?:\(([^)]+)\))?\s*VALUES\s*(.*?);", sql, re.IGNORECASE | re.DOTALL
    ):
        table = m.group(1).strip()
        cols = [c.strip() for c in m.group(2).split(",")] if m.group(2) else None
        for tup in _split_values(m.group(3)):
            items = _split_items(tup)
            vals = [_clean_literal(x) for x in items]
            if cols:
                out.setdefault(table, []).append(dict(zip(cols, vals)))
            else:
                out.setdefault(table, []).append(vals)
    return out


def extract(sql: str) -> dict:
    """Ekstrak semua tabel dari satu file SQL."""
    sql = _strip_sql_comments(sql)
    tables, inserts = [], parse_inserts(sql)
    for m in re.finditer(
        r"CREATE\s+TABLE\s+(?:\S+\s+)?(\S+)\s*\(", sql, re.IGNORECASE
    ):
        name = m.group(1).strip()
        # ambil blok CREATE hingga ");" di depth luar
        start = m.start()
        begin_body = sql.index("(", m.end() - 1)
        depth = 0
        i = begin_body
        while i < len(sql):
            c = sql[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = sql[start : i + 2]
        t = parse_create_table(block)
        t["rows"] = inserts.get(name, [])
        tables.append(t)
    return {"tables": tables}


def main(path_in: Path, path_out: Path):
    sql = path_in.read_text(encoding="utf-8", errors="replace")
    data = extract(sql)
    # de-dup (CREATE + INSERT di file sama, tabel unik)
    seen = {}
    for t in data["tables"]:
        seen[t["table"]] = t
    data["tables"] = list(seen.values())
    path_out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # ringkasan ke stdout
    print(f"Parsed {path_in.name} -> {path_out.name}")
    for t in data["tables"]:
        print(f"  {t['table']}: {len(t['columns'])} kolom, {len(t['rows'])} baris")


if __name__ == "__main__":
    in_p = Path(sys.argv[1])
    out_p = Path(sys.argv[2])
    main(in_p, out_p)