# ADR-002: Framework Backend FastAPI

- **Decision ID:** ADR-002
- **Status:** Superseded by ADR-005
- **Date:** 2026-08-18
- **Superseded by:** ADR-005 (Framework Backend Frappe Framework v15) —
  2026-08-20

## Context

AIOS adalah platform SaaS multi-tenant yang menyediakan API backend untuk
dua portal (klien dan pengembang Ekasa), integrasi dengan Ollama (Local LLM),
akses ke Client Database melalui Database Adapter, dan AIOS Internal Database
untuk metadata serta mapping. Backend perlu dikembangkan sebagai prototype
yang cepat, modular, dan mudah didemonstrasikan, dengan API REST yang jelas.

## Problem Statement

Framework backend mana yang dipakai untuk membangun prototype AIOS agar cepat
dikembangkan, mudah dibaca, dan mendukung integrasi dengan Ollama serta
berbagai database melalui adapter?

## Constraints

- Prototype: prioritas pada kecepatan pengembangan, kesederhanaan, dan
  kemudahan demonstrasi (bukan kompleksitas produksi).
- Harus mudah berkomunikasi dengan Ollama (HTTP API) dan mengakomodasi
  adapter database yang beragam.
- Modular dan mudah diperluas sesuai Development Priority (AIOS Core, Plugin
  Manager, Workers, dll).
- Bahasa pemrograman: tidak ditentukan secara kaku sebelumnya, tetapi
  ekosistem AI/data science adalah pertimbangan.

## Options Considered

- Option A: FastAPI (Python) — dokumentasi resmi dan dukungan async.
- Option B: Flask (Python) — lebih sederhana, WSGI sinkron.
- Option C: Django + Django REST Framework (Python) — full-stack, lebih berat.
- Option D: Node.js (Express/Fastify) — ekosistem non-Python.

## Decision

Gunakan FastAPI sebagai framework backend AIOS.

## Rationale

- FastAPI adalah kerangka modern dengan dokumentasi resmi yang lengkap,
  dukungan OpenAPI/docs interaktif otomatis, dan kinerja async yang baik
  (REF-003).
- Ekosistem Python sangat cocok dengan kebutuhan AIOS: integrasi Ollama,
  pemrosesan data, dan potensi RAG nanti semuanya memiliki dukungan Python
  yang matang.
- Type hints dan validasi otomatis (Pydantic) membantu menjaga kualitas kode
  prototype yang modular tanpa menambah kompleksitas berlebihan.
- Alternatif ditolak: Flask kurang terstruktur untuk API besar; Django terlalu
  berat untuk prototype berbasis API; Node.js berada di luar ekosistem data/AI
  utama yang digunakan AIOS.

## Evidence / References

- REF-003: FastAPI Documentation (official)

## Trade-offs

- FastAPI bukan framework "batteries-included" penuh seperti Django (auth,
  admin, ORM terintegrasi harus dirakit sendiri) — namun untuk prototype
  berbasis API, hal ini justru menjaga kesederhanaan.
- Memilih satu bahasa (Python) mengikat seluruh stack backend ke Python.

## Consequences

- Struktur backend akan dibuat modular: core, api, plugin_manager, workers,
  adapters, internal_db, data_layer.
- API endpoints disediakan untuk portal klien dan portal developer pada
  domain/port berbeda namun backend sama.
- Dokumentasi interaktif (Swagger UI) tersedia otomatis untuk debugging dan
  demonstrasi.

## Confidence

High. Keputusan ini didukung oleh dokumentasi resmi FastAPI (REF-003) dan
kesesuaian langsung dengan kebutuhan teknis prototype (Ollama, adapter,
modularitas). Tidak ada konflik dengan sumber resmi lain yang menyarankan
framework berbeda untuk kasus serupa.

> **Status:** Keputusan ini **Superseded** oleh ADR-005 (2026-08-20). AIOS
> backend kini memakai Frappe Framework v15. ADR ini dipertahankan sebagai
> catatan historis keputusan awal dan alasan penggantian.

## Reconsideration Conditions

- Jika kebutuhan auth, admin panel, dan ORM terintegrasi menjadi besar secara
  signifikan melebihi lingkup prototype, pertimbangkan Django.
- Jika tim memutuskan stack non-Python untuk produksi.
