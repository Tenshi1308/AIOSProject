"""Sub-agent spesialis cabang Finance.

Setiap sub-agent adalah create_agent independen dengan system prompt
dan tools sendiri. Semua tools menghitung data dari dataset (read-only,
anti-fabrication). Sub-agent dipanggil (di-invoke) oleh AI Manager
(primary) sebagai tool delegasi.
"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

import aggregator

MODEL_NAME = "qwen2.5:latest"


class SubAgentAnswer(BaseModel):
    """Struktur output sub-agent untuk mendukung review deterministik oleh
    AI Manager. `answered=False` menandakan sub-agent tidak dapat menjawab
    (tidak ada data, perusahaan tidak ditemukan, atau error)."""

    summary: str = Field(description="Jawaban ringkas sub-agent dalam Bahasa Indonesia")
    answered: bool = Field(
        description="True jika berhasil menjawab dengan data; False jika tidak ada data/error"
    )
    confidence: str = Field(
        default="medium",
        description="Tingkat keyakinan: high, medium, atau low",
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="Nama tool/sumber data yang dipakai sub-agent",
    )


def _make_model():
    return ChatOllama(model=MODEL_NAME, temperature=0)


# ---------------------------------------------------------------------------
# Tools bersama (didefinisikan per sub-agent agar deskripsi cocok dengan peran)
# ---------------------------------------------------------------------------


def _tools_finance_staff():
    @tool
    def get_company_summary(company: str) -> str:
        """Mengambil ringkasan data harga saham satu perusahaan (rentang, harga
        terakhir, min/max, rata-rata, total volume). Parameter: nama perusahaan."""
        return str(aggregator.get_company_summary(company))

    @tool
    def get_price_history(company: str, limit: int = 5) -> str:
        """Mengambil riwayat harga penutupan terakhir untuk satu perusahaan.
        Parameter: nama perusahaan, jumlah baris terakhir (default 5)."""
        return str(aggregator.get_price_history(company, limit))

    return [get_company_summary, get_price_history]


def _tools_financial_analyst():
    @tool
    def compare_companies(company_a: str, company_b: str) -> str:
        """Membandingkan kinerja dua perusahaan (rata-rata close dan persentase
        perubahan). Parameter: dua nama perusahaan."""
        return str(aggregator.compare_companies(company_a, company_b))

    @tool
    def top_by_price(limit: int = 5) -> str:
        """Perusahaan dengan rata-rata harga penutupan tertinggi. Parameter:
        jumlah teratas (default 5)."""
        return str(aggregator.top_by_price(limit))

    return [compare_companies, top_by_price]


def _tools_budgeting_staff():
    @tool
    def summarize_period(year: int | None = None, month: int | None = None) -> str:
        """Ringkasan statistik dataset per periode (opsional tahun/bulan):
        jumlah perusahaan, rata-rata close/volume, perusahaan terbaik/terburuk."""
        return str(aggregator.summarize_period(year, month))

    return [summarize_period]


def _tools_treasurer():
    @tool
    def top_by_volume(limit: int = 5) -> str:
        """Perusahaan dengan total volume transaksi terbesar. Parameter:
        jumlah teratas (default 5)."""
        return str(aggregator.top_by_volume(limit))

    @tool
    def get_company_summary(company: str) -> str:
        """Ringkasan data satu perusahaan termasuk total volume transaksi."""
        return str(aggregator.get_company_summary(company))

    return [top_by_volume, get_company_summary]


def _tools_cfo():
    @tool
    def summarize_period(year: int | None = None, month: int | None = None) -> str:
        """Rekap eksekutif statistik dataset per periode (jumlah perusahaan,
        rata-rata close/volume, perusahaan terbaik/terburuk)."""
        return str(aggregator.summarize_period(year, month))

    @tool
    def top_by_volume(limit: int = 5) -> str:
        """Perusahaan dengan total volume transaksi terbesar."""
        return str(aggregator.top_by_volume(limit))

    @tool
    def top_by_price(limit: int = 5) -> str:
        """Perusahaan dengan rata-rata harga penutupan tertinggi."""
        return str(aggregator.top_by_price(limit))

    return [summarize_period, top_by_volume, top_by_price]


def _build_subagent(name: str, system_prompt: str, tools):
    return create_agent(
        model=_make_model(),
        tools=tools,
        system_prompt=system_prompt,
        response_format=SubAgentAnswer,
        name=name,
    )


# ---------------------------------------------------------------------------
# Definisi sub-agent (nama, deskripsi untuk AI Manager, agent, system prompt)
# ---------------------------------------------------------------------------

AGENT_FINANCE_STAFF = _build_subagent(
    "agent_finance_staff",
    """Kamu adalah sub-agent spesialis Finance Staff pada cabang Finance.
Tugasmu: menyediakan data harga saham dasar suatu perusahaan (harga
penutupan, rentang, riwayat, min/max, volume).

Gunakan tools yang tersedia untuk mengambil data dari dataset.
JANGAN PERNAH mengarang atau menebak angka — semua angka harus berasal
dari hasil tools.
Jika perusahaan tidak ditemukan, sampaikan dengan jujur dan tawarkan
perusahaan yang tersedia.
Jawab 100%% dalam Bahasa Indonesia murni (tanpa campur bahasa lain), ringkas dan jelas. Isi field answered=True jika berhasil menjawab dengan data, dan answered=False jika tidak ada data, perusahaan tidak ditemukan, atau terjadi error.""",
    _tools_finance_staff(),
)

AGENT_FINANCIAL_ANALYST = _build_subagent(
    "agent_financial_analyst",
    """Kamu adalah sub-agent spesialis Financial Analyst pada cabang Finance.
Tugasmu: menganalisis dan membandingkan kinerja antar perusahaan
(rata-rata harga, persentase perubahan, peringkat harga).

Gunakan tools untuk mengambil data. JANGAN PERNAH mengarang angka.
Jika data tidak tersedia, sampaikan dengan jujur.
Jawab 100%% dalam Bahasa Indonesia murni (tanpa campur bahasa lain), ringkas, dengan angka jelas. Isi field answered=True jika berhasil menjawab dengan data, dan answered=False jika tidak ada data atau error.""",
    _tools_financial_analyst(),
)

AGENT_BUDGETING_STAFF = _build_subagent(
    "agent_budgeting_staff",
    """Kamu adalah sub-agent spesialis Budgeting Staff pada cabang Finance.
Tugasmu: menyediakan ringkasan statistik dataset per periode (bulan/tahun),
seperti rata-rata harga, rata-rata volume, dan perusahaan terbaik/terburuk.

Gunakan tools untuk mengambil data. JANGAN PERNAH mengarang angka.
Jawab 100%% dalam Bahasa Indonesia murni (tanpa campur bahasa lain), ringkas dan jelas. Isi field answered=True jika berhasil menjawab dengan data, dan answered=False jika tidak ada data, perusahaan tidak ditemukan, atau terjadi error.""",
    _tools_budgeting_staff(),
)

AGENT_TREASURER = _build_subagent(
    "agent_treasurer",
    """Kamu adalah sub-agent spesialis Treasurer pada cabang Finance.
Tugasmu: menyediakan informasi likuiditas dan volume transaksi
perusahaan (total volume, perusahaan dengan volume terbesar).

Gunakan tools untuk mengambil data. JANGAN PERNAH mengarang angka.
Jawab 100%% dalam Bahasa Indonesia murni (tanpa campur bahasa lain), ringkas dan jelas. Isi field answered=True jika berhasil menjawab dengan data, dan answered=False jika tidak ada data, perusahaan tidak ditemukan, atau terjadi error.""",
    _tools_treasurer(),
)

AGENT_CFO = _build_subagent(
    "agent_cfo",
    """Kamu adalah sub-agent spesialis CFO pada cabang Finance.
Tugasmu: menyediakan rekap/ringkasan eksekutif keseluruhan dataset:
jumlah perusahaan, rata-rata close/volume, perusahaan terbaik/terburuk,
dan peringkat volume/harga.

Gunakan tools untuk mengambil data. JANGAN PERNAH mengarang angka.
Jawab 100%% dalam Bahasa Indonesia murni (tanpa campur bahasa lain), ringkas, padat, dan mudah dibaca. Isi field answered=True jika berhasil menjawab dengan data, dan answered=False jika tidak ada data atau error.""",
    _tools_cfo(),
)

SUB_AGENTS = {
    AGENT_FINANCE_STAFF.name: AGENT_FINANCE_STAFF,
    AGENT_FINANCIAL_ANALYST.name: AGENT_FINANCIAL_ANALYST,
    AGENT_BUDGETING_STAFF.name: AGENT_BUDGETING_STAFF,
    AGENT_TREASURER.name: AGENT_TREASURER,
    AGENT_CFO.name: AGENT_CFO,
}


def run_subagent(name: str, query: str) -> SubAgentAnswer:
    """Menjalankan sub-agent dengan satu pesan user.

    Mengembalikan objek `SubAgentAnswer` (structured_response) sehingga AI
    Manager bisa mereview hasil secara deterministik (answered, isi summary).
    Jika model tidak mengembalikan structured_response yang valid, dihasilkan
    `SubAgentAnswer(answered=False, ...)` sebagai fallback yang aman.
    """
    agent = SUB_AGENTS.get(name)
    if agent is None:
        return SubAgentAnswer(
            summary=f"Sub-agent '{name}' tidak dikenal.",
            answered=False,
            confidence="low",
        )
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        structured = result.get("structured_response")
        if isinstance(structured, SubAgentAnswer):
            return structured
        # Fallback: model tidak memberi structured_response valid.
        text = result["messages"][-1].content
        return SubAgentAnswer(summary=text, answered=True, confidence="low")
    except Exception as exc:  # noqa: BLE001
        return SubAgentAnswer(
            summary=f"Sub-agent gagal diproses: {exc}",
            answered=False,
            confidence="low",
        )


# Metadata untuk AI Manager (deskripsi delegasi)
SUB_AGENT_META = {
    "agent_finance_staff": {
        "description": (
            "Spesialis data harga saham dasar: harga penutupan, riwayat, "
            "rentang, min/max, dan volume satu perusahaan. Untuk pertanyaan "
            "tentang harga/riwayat saham perusahaan tertentu."
        ),
    },
    "agent_financial_analyst": {
        "description": (
            "Spesialis analisis & perbandingan kinerja antar perusahaan: "
            "rata-rata harga, persentase perubahan, peringkat harga. Untuk "
            "pertanyaan membandingkan beberapa perusahaan atau peringkat."
        ),
    },
    "agent_budgeting_staff": {
        "description": (
            "Spesialis statistik per periode: ringkasan rata-rata harga/volume "
            "dan perusahaan terbaik/terburuk per bulan/tahun."
        ),
    },
    "agent_treasurer": {
        "description": (
            "Spesialis likuiditas & volume transaksi: total volume dan "
            "perusahaan dengan volume terbesar."
        ),
    },
    "agent_cfo": {
        "description": (
            "Spesialis rekap eksekutif: ringkasan keseluruhan dataset "
            "(jumlah perusahaan, rata-rata, perusahaan terbaik/terburuk, peringkat)."
        ),
    },
}