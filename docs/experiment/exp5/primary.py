"""AI Manager cabang Finance (primary agent).

AI Manager adalah create_agent utama. Ia mendelegasikan pertanyaan data
ke sub-agent spesialis dengan memanggil sub-agent sebagai tool.
Setiap tool sub-agent menjalankan create_agent sub-agent tersebut dengan
query dari user, lalu mengembalikan jawabannya ke AI Manager yang
merangkumnya untuk user.

AI Manager juga bisa diajak ngobrol umum (sapaan, dsb) tanpa memanggil
tool. Data angka selalu berasal dari sub-agent (anti-fabrication).
"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_ollama import ChatOllama

from subagents_finance import SUB_AGENTS, SUB_AGENT_META, run_subagent

MODEL_NAME = "qwen2.5:latest"

SYSTEM_PROMPT = """Kamu adalah AI Manager cabang Finance di platform AIOS,
asisten yang ramah, ringkas, dan membantu dalam Bahasa Indonesia.
Data yang tersedia adalah data saham historis (harga/volume) dari
dataset, BUKAN crypto dan BUKAN prediksi masa depan.

Kamu memiliki sub-agent spesialis yang bisa kamu panggil sebagai tool:
- agent_finance_staff: data harga saham dasar satu perusahaan (harga
  penutupan, riwayat, rentang, min/max, volume).
- agent_financial_analyst: analisis & perbandingan kinerja antar perusahaan
  (rata-rata harga, persentase perubahan, peringkat harga).
- agent_budgeting_staff: ringkasan statistik per periode (bulan/tahun),
  rata-rata harga/volume, perusahaan terbaik/terburuk.
- agent_treasurer: likuiditas & volume transaksi (total volume, perusahaan
  dengan volume terbesar).
- agent_cfo: rekap eksekutif keseluruhan (jumlah perusahaan, rata-rata,
  perusahaan terbaik/terburuk, peringkat).

Aturan:
1. Untuk pertanyaan tentang DATA, DELEGASIKAN ke sub-agent yang relevan
   dengan memanggil tool-nya (isi parameter query dengan pertanyaan/
   permintaan user). JANGAN menjawab data angka dari ingatanmu sendiri.
2. Jika pertanyaan butuh data dari beberapa domain, panggil sub-agent yang
   sesuai satu per satu lalu gabungkan hasilnya.
3. Untuk sapaan, ucapan terima kasih, atau pertanyaan umum di luar data,
   jawab langsung tanpa memanggil tool.
4. Hasil sub-agent yang kamu terima SUDAH melalui review deterministik
   (ditolak dan dipanggil ulang bila tidak menjawab). Jika kamu menerima
   teks yang menandakan sub-agent gagal (mis. "tidak berhasil menjawab"),
   sampaikan dengan jujur ke user dan tawarkan bantuan lain. Jika tidak,
   rangkum jawabannya untuk user dalam Bahasa Indonesia yang ramah,
   ringkas, dan mudah dibaca.
5. Jangan mengarang atau menambah angka yang tidak ada pada hasil sub-agent.
6. Selalu jawab 100% dalam Bahasa Indonesia. JANGAN mencampur dengan
   bahasa lain (Inggris, Mandarin, dll). Gunakan kata/kalimat Indonesia
   yang natural. Jangan terlalu formal seperti customer service; gunakan
   gaya ramah dan ringkas.
"""


def _review_answer(answer, query: str) -> tuple[bool, str]:
    """Review deterministik hasil sub-agent.

    Menolak (return False) jika sub-agent tidak menjawab dengan data:
    `answered=False`, atau isi `summary` kosong/menandakan error/tidak ada
    data. Mengembalikan (ok, alasan).
    """
    if answer is None:
        return False, "tidak ada hasil dari sub-agent"
    if not getattr(answer, "answered", False):
        return False, "sub-agent tidak dapat menjawab (tidak ada data/error)"

    summary = getattr(answer, "summary", "") or ""
    lower = summary.lower().strip()
    if not lower:
        return False, "jawaban sub-agent kosong"

    # Tanda umum bahwa hasil tidak mengandung data nyata.
    if any(marker in lower for marker in ("error", "tidak ditemukan", "tidak ada data", "tidak dikenal")):
        return False, "jawaban sub-agent menandakan tidak ada data yang valid"

    return True, ""


def _make_subagent_tool(name: str, max_retries: int = 2):
    """Membangun tool delegasi untuk satu sub-agent.

    Memanggil sub-agent, lalu melakukan review deterministik. Jika hasil
    ditolak, sub-agent dipanggil ulang dengan perbaikan (maks `max_retries`).
    Hanya hasil yang lolos review yang dikembalikan ke AI Manager sebagai
    string; jika tetap gagal, dikembalikan pesan jujur yang jelas.
    """
    desc = SUB_AGENT_META[name]["description"]

    @tool(name)
    def subagent_tool(query: str) -> str:
        """Delegasikan pertanyaan data ke sub-agent spesialis."""
        q = (query or "").strip()
        if not q:
            return "Pertanyaan untuk sub-agent kosong."

        last_summary = ""
        for attempt in range(max_retries + 1):
            answer = run_subagent(name, q)
            ok, reason = _review_answer(answer, q)
            if ok:
                return f"[Sub-agent {name} menjawab]\n{answer.summary}"

            last_summary = answer.summary if answer else ""
            # Perbaiki query untuk percobaan berikutnya.
            q = (
                f"{q} (Sebelumnya tidak terjawab: {reason}. "
                f"Coba lagi dan pastikan menjawab dengan data yang tersedia.)"
            )

        return (
            f"Sub-agent {name} tidak berhasil menjawab setelah beberapa "
            f"percobaan. {last_summary or 'Tidak ada data yang dapat diberikan.'} "
            "Sampaikan ini dengan jujur ke user dan tawarkan bantuan lain."
        )

    subagent_tool.description = desc
    return subagent_tool


def build_manager() -> create_agent:
    """Membangun AI Manager dengan tools delegasi ke semua sub-agent."""
    tools = [_make_subagent_tool(name) for name in SUB_AGENTS.keys()]
    return create_agent(
        model=ChatOllama(model=MODEL_NAME, temperature=0),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        name="aios_finance_manager",
    )


def run_manager(messages: list[dict]) -> str:
    """Menjalankan AI Manager dengan riwayat messages dan mengembalikan jawaban."""
    manager = build_manager()
    result = manager.invoke({"messages": messages})
    return result["messages"][-1].content