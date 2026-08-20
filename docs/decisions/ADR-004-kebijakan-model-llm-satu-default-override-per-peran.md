# ADR-004: Kebijakan Model LLM — Satu Model Default + Override per Peran

- **Decision ID:** ADR-004
- **Status:** Accepted
- **Date:** 2026-08-18

## Context

AIOS memakai Local LLM (runtime lokal, kandidat utama: Ollama, final **TBD**)
untuk AI Manager, Workers, dan AI Schema Analyzer. Prinsip Cost Efficient
menuntut biaya operasi minimal: satu model lokal bersama untuk semua
cabang/worker, model kecil, dan hindari komputasi mahal berulang. Namun setiap
peran (AI Manager, worker spesialis, schema analyzer) memiliki kebutuhan yang
berbeda terhadap kemampuan model.

## Problem Statement

Model LLM apa yang dipakai, dan bagaimana mengelola trade-off antara biaya
(model kecil = murah) dan kualitas (model besar = lebih baik) untuk berbagai
peran di AIOS?

## Constraints

- Prototype memakai Local LLM runtime (kandidat: Ollama) di server Ekasa; data
  perusahaan mengalir ke server Ekasa (trade-off yang sudah diterima untuk
  prototype). Runtime spesifik belum diputuskan — lihat "Reconsideration
  Conditions".
- Prinsip Cost Efficient: satu model lokal bersama untuk semua cabang/worker,
  model tetap kecil, dan hindari komputasi mahal berulang.
- Prinsip "Do NOT over-engineer the AI model" — prototype tidak mengejar
  optimasi model produksi.
- Namun pemilihan model default tetap perlu keputusan yang sadar.

## Options Considered

- Option A: Satu model kecil untuk semua peran, tanpa override.
- Option B: Satu model kecil sebagai default + kebijakan override model per
  peran melalui konfigurasi (misal AI Manager / schema analyzer memakai model
  lebih besar, worker rutin memakai model kecil).
- Option C: Selalu memakai model besar untuk semua peran.
- Option D: Dynamic model routing/cascading otomatis berbasis kompleksitas
  query.

## Decision

Gunakan satu model kecil sebagai default bersama untuk semua cabang/worker,
dengan kebijakan override model per peran melalui konfigurasi (setting default
yang dapat diganti per peran di config). Model final belum ditentukan
(TBD) dan dipilih saat setup lingkungan; default diarahkan ke model kecil
yang cocok untuk prototype (misal qwen2.5:3b sebagai kandidat awal). Routing
dinamis otomatis (Option D) tidak dipakai di prototype.

## Rationale

- Satu model kecil bersama sesuai prinsip Cost Efficient dan prinsip prototype
  "simple models, reasonable performance, easy setup, demonstrability"
  (REF-007 menunjukkan on-premise deployment baru ekonomis di titik break-even
  tertentu; model kecil menekan biaya hardware dan operasi).
- Override per peran mengakui bahwa peran berbeda membutuhkan kemampuan
  berbeda: AI Schema Analyzer melakukan analisis semantik skema (dibantu
  pendekatan LLM-based schema matching — REF-005, REF-008, REF-013, REF-014,
  REF-015), AI Manager mengorkestrasi beberapa worker (multi-agent
  orchestration — REF-006, REF-009, REF-012), sedangkan worker rutin
  menangani tugas domain yang lebih sederhana.
- Literatur routing/cascading (REF-010, REF-011) menunjukkan trade-off
  biaya-kualitas; untuk prototype, konfigurasi statis per peran sudah cukup
  dan lebih sederhana daripada routing dinamis otomatis.
- Option A kurang fleksibel; Option C mahal dan melanggar Cost Efficient;
  Option D terlalu kompleks untuk prototype (over-engineering).

## Evidence / References

- REF-005: A survey of approaches to automatic schema matching — Rahm &
  Bernstein (2001)
- REF-006: Navigating Complexity: Orchestrated Problem Solving with Multi-Agent
  LLMs — Rasal & Hauer (2024)
- REF-007: A Cost-Benefit Analysis of On-Premise Large Language Model
  Deployment — Pan et al. (2025)
- REF-008: ReMatch: Retrieval Enhanced Schema Matching with LLMs — Sheetrit et
  al. (2024)
- REF-009: AgentOrchestra — Zhang et al. (2025)
- REF-010: Dynamic Model Routing and Cascading for Efficient LLM Inference —
  Moslem & Kelleher (2026)
- REF-011: Is Escalation Worth It? A Decision-Theoretic Characterization of LLM
  Cascades — Bouchard (2026)
- REF-012: AOrchestra: Automating Sub-Agent Creation for Agentic Orchestration
  — Ruan et al. (2026)
- REF-013: Schemora — Gungor et al. (2025)
- REF-014: LLMATCH — Wang et al. (2025)
- REF-015: Bootstrapping Self-Improvement of Language Model Programs for
  Zero-Shot Schema Matching (Matchmaker) — Seedat & Van Der Schaar (2025)
- REF-016: Ollama Documentation (kandidat runtime)

## Trade-offs

- Memakai model kecil untuk worker rutin dapat menghasilkan kualitas jawaban
  sedikit lebih rendah dibanding model besar — diterima demi biaya rendah.
- Konfigurasi override per peran menambah sedikit kompleksitas konfigurasi
  dibanding satu model untuk semua.
- Tidak memakai routing dinamis (Option D) berarti tidak ada optimasi otomatis
  biaya-kualitas per query — keputusan ini ditunda pasca-prototype.

## Consequences

- Config backend menyertakan pengaturan model default dan override per peran
  (misal AI Manager, AI Schema Analyzer, masing-masing worker).
- Pada setup lingkungan, model default dipilih (kandidat qwen2.5:3b) dan
  diuji; pemilihan final dicatat saat Fase setup.
- REQUIREMENTS.md LLM-05 akan diperbarui sesuai kebijakan ini.
- Prototype tidak menerapkan dynamic routing; evaluasi ulang jika terbukti
  dibutuhkan setelah prototype.
- Keputusan runtime spesifik (kandidat: Ollama) dilakukan terpisah saat fase
  Local LLM integration, dan dapat dicatat sebagai ADR tersendiri.

## Confidence

Medium. Kebijakan "satu model kecil + override per peran" selaras dengan
prinsip Cost Efficient dan literatur multi-agent serta model cascading
(REF-006, REF-009, REF-010, REF-011, REF-012), namun pemilihan model spesifik
final (TBD) belum diverifikasi secara empiris di lingkungan prototype ini.

## Reconsideration Conditions

- Jika pengujian prototype menunjukkan kualitas AI Schema Analyzer atau AI
  Manager tidak memadai dengan model kecil, naikkan override per peran tersebut
  dan/atau evaluasi routing dinamis.
- Jika biaya hardware turun sehingga model lebih besar terjangkau, default
  dapat dinaikkan.
- Keputusan model final direvisi setelah benchmark di setup lingkungan.
- Keputusan runtime spesifik (misal memilih Ollama secara final) ditinjau saat
  fase Local LLM integration — dokumen ini tidak mengunci runtime.

> **Re-affirm 2026-08-20 (ADR-005):** Keputusan backend Frappe Framework v15
> tidak mengubah kebijakan ini. Runtime LLM final (kandidat: Ollama) tetap
> **TBD** dan diputuskan pada fase Local LLM integration (Fase 8). ADR-005
> tidak mengunci runtime LLM.
