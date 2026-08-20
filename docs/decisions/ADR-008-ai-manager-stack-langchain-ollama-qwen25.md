# ADR-008: Runtime & Stack AI Manager Multi-Agent — LangChain + Ollama qwen2.5 (Eksperimen 5)

- **Decision ID:** ADR-008
- **Status:** Accepted
- **Date:** 2026-08-20

## Context

Eksperimen 5 mengimplementasikan AI Manager (primary) yang mendelegasikan
tugas ke sub-agent spesialis (pola orchestrator multi-agent) untuk percakapan
cabang Finance. ADR-006 memutuskan kandidat runtime llama.cpp + Qwen2.5-3B
untuk **analisis skema** (schema analysis, Fase 8). Eksperimen 5 adalah
konteks berbeda: percakapan multi-turn dengan tool-calling dan delegasi
sub-agent, yang membutuhkan kualitas instruksi-following dan tool-calling
yang lebih baik daripada analisis skema terstruktur.

Sebelumnya ada upaya implementasi Eksperimen 5 dengan llama.cpp + Qwen2.5-3B
(yang ditarik/di-rollback) karena hasilnya on-rails dan templated, tidak
natural untuk obrolan. Eksperimen 5 dibangun ulang dengan pendekatan yang
berbeda.

## Problem Statement

Runtime, arsitektur agent, dan model apa untuk Eksperimen 5 (AI Manager +
sub-agents, chat Finance) yang memungkinkan:

- delegasi sub-agent via tool-calling,
- obrolan umum yang natural dan ramah,
- anti-fabrication (data angka berasal dari kode, bukan dari model),
- full conversation history (konteks multi-turn),

tanpa membuang keputusan ADR-006 untuk konteks schema analysis?

## Constraints

- Local-first: berjalan lokal/self-hosted (prototype di server Ekasa).
- Ollama sudah terpasang global (client 0.32.x) — bukan llama-server.
- RAM 16 GB, CPU-only → model 7B (Q4) muat.
- Delegasi sub-agent via tool-calling (keputusan user).
- Anti-fabrication: data angka dihitung dari dataset (pandas), bukan dari LLM.
- Interface: CLI REPL (keputusan user).
- Konsisten dengan ADR-006: llama.cpp + Qwen2.5-3B tetap acuan untuk
  schema analysis (konteks berbeda).

## Options Considered

- Option A: llama.cpp + Qwen2.5-3B (mengikuti ADR-006) untuk Eksperimen 5.
  Sudah dicoba dan di-rollback karena hasil on-rails/templated dan tidak
  natural untuk obrolan; juga butuh build/setup llama-server.
- Option B: LangChain `create_agent` + Ollama `qwen2.5:latest` (7B) dengan
  sub-agents sebagai tools sederhana dalam satu create_agent (pola
  mini-agent). Ringan (1 LLM call/pertanyaan).
- Option C: LangChain `create_agent` + Ollama `qwen2.5:latest` (7B) dengan
  pola orchestrator multi-agent (pola SIPUS): AI Manager (primary) + tiap
  sub-agent sebagai `create_agent` terpisah (system prompt + tools sendiri),
  AI Manager mendelegasikan via tool-calling.

## Decision

Mengadopsi **Option C**: LangChain `create_agent` + `ChatOllama(qwen2.5:latest)`
dengan AI Manager (primary) yang mendelegasikan ke 5 sub-agent spesialis
(Finance Staff, Financial Analyst, Budgeting Staff, Treasurer, CFO), masing-
masing `create_agent` terpisah dengan system prompt dan tools sendiri.
Tools sub-agent menghitung data dari dataset via pandas (anti-fabrication).
Full conversation history dikirim tiap turn. Interface CLI REPL.

Implementasi: `docs/experiment/exp5/` (`load_data.py`, `aggregator.py`,
`subagents_finance.py`, `primary.py`, `chat.py`, `requirements.txt`).

### Tambahan (2026-08-20): Review Deterministik Output Sub-Agent

Untuk mencegah hasil sub-agent yang tidak menjawab/tidak ada data lolos
begitu saja ke user, ditambahkan mekanisme **review deterministik** pada
hasil sub-agent sebelum dikompilasi oleh AI Manager:

- Setiap sub-agent mengembalikan **output terstruktur** (`SubAgentAnswer`
  Pydantic: `summary`, `answered`, `confidence`, `data_sources`) via
  `response_format` (REF-023), dengan fallback aman bila model tidak
  menghasilkan structured_response yang valid.
- Fungsi `_review_answer` di `primary.py` menilai hasil secara
  **deterministik**: menolak jika `answered=False`, `summary` kosong, atau
  berisi penanda tidak ada data/error (mis. "tidak ditemukan", "error").
- Jika ditolak, sub-agent **dipanggil ulang** dengan query diperbaiki
  (maks 2×); hanya hasil yang lolos review yang dikirim ke AI Manager
  untuk dirangkum.
- Keputusan ini mengikuti prinsip LangChain bahwa kebijakan seperti ini
  sebaiknya **ditegakkan deterministik di kode, bukan lewat prompt**
  (REF-023, bagian guardrails), dan peran orkestrator mengawasi/memverifikasi
  hasil sebelum kompilasi (REF-006).

## Rationale

- `create_agent` (LangChain) menyediakan loop tool-calling yang stabil dan
  dapat dikonfigurasi (`model`, `tools`, `system_prompt`) (REF-023), serta
  mendukung delegasi sub-agent (REF-024).
- Ollama mudah disetup (sudah terpasang global) dan `qwen2.5:latest` = 7B
  (REF-025), lebih besar dari 3B → instruksi-following dan tool-calling
  lebih baik untuk chat multi-agent, dan muat di 16 GB RAM CPU.
- Pola orchestrator (Option C) mengikuti referensi arsitektur multi-agent
  (REF-006, REF-009) dan pola referensi SIPUS: tiap sub-agent punya konteks
  sendiri, AI Manager merangkum untuk user.
- Anti-fabrication dijaga karena data angka dihitung dari pandas oleh tools
  sub-agent; model hanya merangkum hasilnya, tidak mengarang.
- CLI REPL (bukan Web) sesuai keputusan user; `chat.py` mudah dibaca dan
  didemonstrasikan.

## Evidence / References

- Bukti eksperimen internal: evaluasi Eksperimen 5 — `chat.py` dijalankan
  dan terverifikasi: data nyata (sub-agent Finance Staff & Financial Analyst),
  sapaan langsung, anti-fabrication (prediksi Bitcoin dijawab jujur),
  multi-turn (konteks AAPL dibawa ke pertanyaan berikutnya), Bahasa Indonesia
  murni setelah prompt diperkuat.
- Validasi review deterministik: kasus error (perusahaan tidak ada)
  ditolak oleh `_review_answer` (berbasis isi `summary`), walau model
  kadang salah mengisi `answered=True`; AI Manager lalu menjawab jujur.
  Ini membenarkan review berbasis isi, bukan hanya field `answered`.
- REF-016: Ollama Documentation (runtime) — sudah ada di registry.
- REF-023: LangChain Agents — official docs (`create_agent`, tool-calling loop).
- REF-024: LangChain subagents / planning & delegation — official docs.
- REF-025: Qwen2.5-7B-Instruct Model Card — official (7.61B, multilingual
  termasuk Bahasa Indonesia).
- ADR-006: kandidat llama.cpp + Qwen2.5-3B untuk schema analysis — tidak
  diganti; konteks berbeda.

## Trade-offs

- Model 7B lebih berat daripada 3B (perf & RAM) — diterima demi kualitas
  chat/tool-calling multi-agent.
- LangChain + langgraph menambah dependency dibanding llama.cpp langsung.
- Model 7B kadang mencampur bahasa (mis. muncul karakter non-Indonesia) →
  perlu prompt tegas "Bahasa Indonesia murni" (sudah diatasi dalam
  implementasi).
- Pola orchestrator (Option C) lebih berat daripada Option B (beberapa
  LLM call per pertanyaan: sub-agent + AI Manager) — diterima untuk
  kejelasan delegasi per sub-agent.

## Consequences

- `docs/experiment/exp5/` berisi implementasi lengkap (read-only data,
  tools sub-agent, AI Manager, CLI REPL).
- REFERENCES.md ditambah REF-023, REF-024, REF-025 (diverifikasi).
- ADR-006 tetap berlaku untuk schema analysis (konteks berbeda); ADR-008
  melengkapi untuk AI Manager chat multi-agent.
- `.gitignore` diperbarui untuk mengecualikan `.venv/` dan `__pycache__/`.

## Confidence

High untuk stack LangChain + Ollama + qwen2.5 (7B) sebagai solusi Eksperimen 5:
terverifikasi dengan menjalankan `chat.py` (data nyata, sapaan,
anti-fabrication, multi-turn). Referensi resmi LangChain (REF-023/024) dan
Qwen2.5-7B (REF-025) diverifikasi langsung di sumbernya.

## Reconsideration Conditions

- Jika fase produksi (Fase 8) menuntut schema analysis → ADR-006 tetap acuan.
- Jika RAM/performa menjadi kendala → turun ke model lebih kecil atau
  terapkan caching TTL.
- Jika tool-calling 7B tidak konsisten → evaluasi ulang prompt/arsitektur
  (mis. pindah ke Option B atau middleware sub-agent LangChain).
- Jika model terbukti terlalu sering tidak konsisten pada `answered` di
  structured output → perkuat heuristik `_review_answer` atau pertimbangkan
  output `confidence` sebagai ambang penerimaan.