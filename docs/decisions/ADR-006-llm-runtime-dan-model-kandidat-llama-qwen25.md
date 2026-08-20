# ADR-006: LLM Runtime & Model Kandidat — llama.cpp + Qwen2.5-3B-Instruct (berbasis bukti Eksperimen 4)

- **Decision ID:** ADR-006
- **Status:** Accepted
- **Date:** 2026-08-20

## Context

AIOS memakai Local LLM untuk AI Manager, Workers, dan AI Schema Analyzer
(ADR-004). Keputusan runtime spesifik (kandidat awal: Ollama) dan model
spesifik (REQUIREMENTS.md LLM-05) semula **TBD** dan akan diputuskan pada fase
Local LLM integration (Fase 8).

Sebelumnya telah dilakukan rangkaian eksperimen 1 s.d. 4 (+ lanjutan) sebagai
*research spike / proof-of-feasibility* untuk memvalidasi kemampuan Local LLM
dalam **analisis skema semantik** dan **semantic mapping** ke Canonical Data
Model pada skema client yang sangat berbeda (Northwind, EAV+JSONB, Indonesia
relasional, flat, EAV Indonesia). Hasil eksperimen menghasilkan kandidat
runtime + model yang **terbukti secara empiris**, sehingga kandidat keputusan
perlu diarahkan ke bukti tersebut.

## Problem Statement

Runtime LLM dan model apa yang menjadi **kandidat utama** untuk prototype
AIOS, berdasarkan bukti empiris eksperimen yang sudah dilakukan, tanpa mengunci
keputusan final sebelum fase Local LLM integration (Fase 8)?

## Constraints

- Local-first: berjalan lokal/self-hosted, tanpa cloud LLM (NFR-03; untuk
  prototype di server Ekasa, data perusahaan mengalir ke server Ekasa —
  trade-off yang diterima).
- Cost Efficient: satu model kecil bersama untuk semua cabang/worker, hindari
  komputasi mahal berulang.
- Prototype: prioritas pada model sederhana, performa wajar, setup mudah,
  demonstrabilitas; jangan over-engineer AI model.
- Kesesuaian dengan hasil eksperimen internal (bukti empiris sendiri) adalah
  faktor penentu kandidat ini.
- Keputusan final runtime & model tetap **TBD** dan dikunci pada fase Local
  LLM integration (Fase 8), sesuai ADR-004 dan rencana fase.

## Options Considered

- Option A: Ollama sebagai kandidat runtime (kandidat awal di ADR-004,
  REQUIREMENTS.md LLM-01/02/05).
- Option B: llama.cpp (llama-server, OpenAI-compatible) sebagai kandidat
  runtime + Qwen2.5-3B-Instruct (Q4_K_M) sebagai model kandidat — runtime dan
  model yang sama persis dengan yang dipakai dan tervalidasi pada Eksperimen
  1–4.
- Option C: Runtime lain (mis. llama-cpp-python embedding dalam proses, atau
  server lain) — tidak pernah diuji dalam eksperimen.

## Decision

**Kandidat utama** runtime LLM untuk prototype AIOS adalah **llama.cpp
(llama-server dengan OpenAI-compatible API)** dengan model
**Qwen2.5-3B-Instruct-Q4_K_M** (CPU-only), sampling deterministik
(`temperature=0`, `seed` tetap). Kandidat ini dipilih karena **terbukti secara
empiris** pada Eksperimen 1–4:

- Pola C2 — ekstraksi struktur **deterministik oleh kode** (Database Adapter
  membaca katalog; untuk PostgreSQL: `pg_catalog` sebagai role read-only) +
  **LLM hanya usulan mapping** ke konsep canonical — menghasilkan **15/15
  usulan benar** pada PostgreSQL nyata, metadata-only, deterministik antar run
  (evaluasi_exp4.md, C2).
- Peran adapter (kode) yang menang, bukan LLM; LLM tidak menulis SQL bebas
  (A/B gagal, loop), tidak memilih alat eksplorasi (C1 halusinasi struktur) —
  konsisten dengan anti-fabrikasi AGENTS.md.
- Boundary teknis terbukti: struktur terbaca dari katalog, **0 baris data
  bisnis** pernah terpapar (role DB read-only, server yang menolak).
- Format input ringkas (F1/F3) + anotasi A2 (hint dari deteksi struktural,
  mis. EAV) paling stabil lintas 5 skema uji — acuan format input LLM untuk AI
  Schema Analyzer.

Ollama tetap menjadi **alternatif/cadangan** bila runtime utama bermasalah
pada setup Fase 8; tidak dihapus sepenuhnya dari dokumentasi.

**Keputusan final runtime & model tetap TBD** dan dikunci pada fase Local LLM
integration (Fase 8), berdasarkan verifikasi di setup lingkungan.

## Rationale

- Bukti empiris sendiri lebih kuat daripada kandidat yang belum pernah diuji:
  Exp-4 memakai llama.cpp + Qwen2.5-3B dan berhasil (15/15), sedangkan Ollama
  hanya kandidat awal di dokumen tanpa uji serupa.
- Model Qwen2.5-3B-Instruct kecil (3.09B) — sesuai prinsip Cost Efficient dan
  muat di 16 GB RAM CPU-only (NFR-05).
- llama.cpp menyediakan server dengan OpenAI-compatible API
  (REF-021), sehingga integrasi dari backend (termasuk Frappe v15, ADR-005)
  memakai protokol HTTP standar — mudah diganti runtime lain jika perlu.
- Qwen2.5-3B-Instruct adalah model open-weight resmi (REF-022) dengan
  varian GGUF (Q4_K_M) yang siap dipakai llama.cpp; telah terbukti stabil di
  eksperimen dengan sampling deterministik.
- Mengarahkan kandidat kini (bukan membiarkan TBD penuh) membuat dokumen
  konsisten dengan bukti yang sudah ada, sambil tetap menjaga keputusan final
  di Fase 8 (tidak premature).

## Evidence / References

- Bukti eksperimen internal: `docs/experiment/laporan-eksperimen-ai-analyze-schema.md`,
  `docs/experiment/evaluasi_exp4.md` (C2: 15/15), `evaluasi_exp2.md`,
  `evaluasi_exp3_hermes.md`, `evaluasi_exp1.md`.
- REF-021: llama.cpp — LLM inference in C/C++ (official GitHub repository;
  llama-server dengan OpenAI-compatible API)
- REF-022: Qwen2.5-3B-Instruct — model card (official, Hugging Face)
- REF-016: Ollama Documentation (kandidat alternatif)
- ADR-004: Kebijakan Model LLM — satu model default + override per peran
  (tetap berlaku)

## Trade-offs

- Kandidat ini belum diuji pada mesin DB selain PostgreSQL (MySQL/SQL Server/
  Oracle) dan belum diuji pada model lebih besar (7B+) — batas eksperimen
  (dicatat di evaluasi_exp4.md, Keterbatasan).
- llama.cpp membangun dari source / mengunduh binary + model GGUF — setup
  sedikit lebih teknis daripada Ollama; Ollama disiapkan sebagai alternatif.
- Hanya menjadikan kandidat (bukan final) berarti ada kemungkinan berubah di
  Fase 8 — diterima untuk menghindari komitmen premature.

## Consequences

- Dokumen inti diperbarui: REQUIREMENTS.md (LLM-01/02/05, C-02), AGENTS.md
  (Local AI), docs/analisis-kebutuhan.md (NFR-03, tabel teknologi), ADR-004
  (catatan kandidat) — kandidat utama = llama.cpp + Qwen2.5-3B-Instruct,
  Ollama = alternatif, final TBD di Fase 8.
- REFERENCES.md ditambah REF-021 (llama.cpp) dan REF-022 (Qwen2.5-3B-Instruct).
- Desain AI Schema Analyzer mengacu pola C2: ekstraksi deterministik oleh
  adapter + LLM hanya usulan mapping + format input ringkas + anotasi A2 +
  sampling deterministik.
- Pada Fase 8, kandidat diverifikasi di setup lingkungan dan keputusan final
  dicatat (bisa sebagai revisi ADR-006 atau ADR baru).

## Confidence

High untuk kandidat ini sebagai arah berbasis bukti: didukung eksperimen
internal 1–4 yang terdokumentasi (15/15 deterministik, boundary aman), sumber
resmi llama.cpp (REF-021) dan Qwen2.5-3B-Instruct (REF-022) diverifikasi.
Medium untuk keputusan final runtime (tetap TBD sampai verifikasi Fase 8 di
setup lingkungan).

## Reconsideration Conditions

- Jika setup Fase 8 menemukan kendala (build/install llama.cpp, performa CPU,
  kompatibilitas), aktifkan alternatif (Ollama) atau evaluasi runtime/model
  lain.
- Jika pengujian menunjukkan kualitas mapping/peran tertentu tidak memadai
  dengan model kecil, naikkan override per peran (ADR-004) dan/atau ganti
  model.
- Keputusan final runtime & model direvisi setelah benchmark di setup
  lingkungan (Fase 8).