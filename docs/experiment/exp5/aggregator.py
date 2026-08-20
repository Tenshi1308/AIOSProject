"""Fungsi agregasi data saham dari dataset.

Semua angka dihitung dari data (pandas), bukan dikarang. Tools read-only.
Fungsi di sini dipakai oleh sub-agent spesialis sebagai sumber data.
"""

import pandas as pd

from load_data import load_dataframe

_DF: pd.DataFrame | None = None


def _df() -> pd.DataFrame:
    global _DF
    if _DF is None:
        _DF = load_dataframe()
    return _DF


def _to_float(value: float) -> float:
    """Pembulatan nilai float agar ringkas dan stabil."""
    return round(float(value), 4)


def list_companies() -> list[str]:
    """Daftar semua perusahaan yang tersedia."""
    return sorted(_df()["Company"].unique().tolist())


def _match_company(name: str) -> list[str]:
    """Cari perusahaan yang cocok dengan nama (case-insensitive, sebagian)."""
    query = str(name).strip().lower()
    if not query:
        return []
    companies = _df()["Company"].unique().tolist()
    return [c for c in companies if query in c.lower()]


def get_company_summary(company: str) -> dict:
    """Ringkasan satu perusahaan: rentang data, harga terakhir, min/max, volume."""
    matches = _match_company(company)
    if not matches:
        return {"error": f"Perusahaan '{company}' tidak ditemukan di dataset."}

    rows = []
    for name in matches[:5]:
        sub = _df()[_df()["Company"] == name].sort_values("Date")
        if sub.empty:
            continue

        last = sub.iloc[-1]
        first = sub.iloc[0]

        rows.append(
            {
                "company": name,
                "data_points": int(len(sub)),
                "date_start": str(first["Date"].date()),
                "date_end": str(last["Date"].date()),
                "open_first": _to_float(first["Open"]),
                "close_last": _to_float(last["Close"]),
                "low_min": _to_float(sub["Low"].min()),
                "high_max": _to_float(sub["High"].max()),
                "avg_close": _to_float(sub["Close"].mean()),
                "total_volume": int(sub["Volume"].sum()),
            }
        )

    return {"matches": rows}


def get_price_history(company: str, limit: int = 5) -> dict:
    """Riwayat harga penutupan terakhir untuk satu perusahaan."""
    matches = _match_company(company)
    if not matches:
        return {"error": f"Perusahaan '{company}' tidak ditemukan di dataset."}

    name = matches[0]
    sub = _df()[_df()["Company"] == name].sort_values("Date")
    limit = max(1, min(int(limit), len(sub)))

    recent = sub.tail(limit)
    history = [
        {
            "date": str(r["Date"].date()),
            "open": _to_float(r["Open"]),
            "high": _to_float(r["High"]),
            "low": _to_float(r["Low"]),
            "close": _to_float(r["Close"]),
            "volume": int(r["Volume"]),
        }
        for _, r in recent.iterrows()
    ]

    return {"company": name, "history": history}


def compare_companies(company_a: str, company_b: str) -> dict:
    """Perbandingan kinerja dua perusahaan (rata-rata close dan perubahan)."""
    a = _match_company(company_a)
    b = _match_company(company_b)

    if not a or not b:
        return {"error": "Salah satu perusahaan tidak ditemukan di dataset."}

    result = {}
    for name, matches in (("a", a), ("b", b)):
        sub = _df()[_df()["Company"] == matches[0]].sort_values("Date")
        if sub.empty:
            return {"error": f"Tidak ada data untuk '{matches[0]}'."}
        first_close = float(sub.iloc[0]["Close"])
        last_close = float(sub.iloc[-1]["Close"])
        pct = ((last_close - first_close) / first_close * 100) if first_close else 0.0
        result[name] = {
            "company": matches[0],
            "avg_close": _to_float(sub["Close"].mean()),
            "close_first": _to_float(first_close),
            "close_last": _to_float(last_close),
            "pct_change": round(pct, 2),
        }

    return result


def top_by_volume(limit: int = 5) -> list[dict]:
    """Perusahaan dengan total volume transaksi terbesar."""
    limit = max(1, min(int(limit), 20))
    grouped = _df().groupby("Company")["Volume"].sum().reset_index()
    grouped = grouped.sort_values("Volume", ascending=False).head(limit)
    return [
        {"company": row.Company, "total_volume": int(row.Volume)}
        for row in grouped.itertuples()
    ]


def top_by_price(limit: int = 5) -> list[dict]:
    """Perusahaan dengan harga penutupan rata-rata tertinggi."""
    limit = max(1, min(int(limit), 20))
    grouped = _df().groupby("Company")["Close"].mean().reset_index()
    grouped = grouped.sort_values("Close", ascending=False).head(limit)
    return [
        {"company": row.Company, "avg_close": _to_float(row.Close)}
        for row in grouped.itertuples()
    ]


def summarize_period(year: int | None = None, month: int | None = None) -> dict:
    """Ringkasan statistik keseluruhan dataset (opsional filter tahun/bulan)."""
    df = _df()

    if year is not None:
        df = df[df["Year"] == int(year)]
    if month is not None:
        df = df[df["Month"] == int(month)]

    if df.empty:
        return {"error": "Tidak ada data pada periode yang diminta."}

    by_company = df.groupby("Company")

    return {
        "companies": int(df["Company"].nunique()),
        "rows": int(len(df)),
        "period_start": str(df["Date"].min().date()),
        "period_end": str(df["Date"].max().date()),
        "avg_close": _to_float(df["Close"].mean()),
        "avg_volume": _to_float(df["Volume"].mean()),
        "best_company": {
            "company": by_company["Close"].mean().idxmax(),
            "avg_close": _to_float(by_company["Close"].mean().max()),
        },
        "worst_company": {
            "company": by_company["Close"].mean().idxmin(),
            "avg_close": _to_float(by_company["Close"].mean().min()),
        },
    }