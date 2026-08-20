"""Memuat dan menyimpan cache dataset saham dari CSV.

Data: stock_details_5_years.csv (491 perusahaan, 602.962 baris,
2018-11-29 s.d. 2023-11-29).
Kolom: Date, Open, High, Low, Close, Volume, Dividends, Stock Splits, Company.

Sumber data hanya dibaca (read-only). Tidak ada tulis ke file data.
"""

import os
from functools import lru_cache

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "stock_details_5_years.csv")


@lru_cache(maxsize=1)
def load_dataframe() -> pd.DataFrame:
    """Membaca CSV sekali, meng-cache hasilnya, dan mempersiapkan kolom tanggal."""
    df = pd.read_csv(CSV_PATH)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True)

    df = df.dropna(subset=["Date", "Close"])

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.strftime("%B")

    df = df.sort_values(["Company", "Date"]).reset_index(drop=True)

    return df


def company_list() -> list[str]:
    """Daftar nama perusahaan yang tersedia di dataset."""
    return sorted(load_dataframe()["Company"].unique().tolist())