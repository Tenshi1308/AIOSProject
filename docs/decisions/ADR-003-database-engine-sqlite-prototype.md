# ADR-003: Database Engine SQLite untuk Prototype

- **Decision ID:** ADR-003
- **Status:** Accepted
- **Date:** 2026-08-18

## Context

AIOS memiliki dua jenis database: Client Database (milik klien, sumber data
bisnis) dan AIOS Internal Database (metadata, mapping, konfigurasi, state).
Untuk prototype, AIOS perlu mendemonstrasikan adaptasi terhadap berbagai
struktur database klien yang berbeda, sambil menyimpan metadata dan mapping
per tenant di Internal Database.

## Problem Statement

Database engine apa yang dipakai untuk AIOS Internal Database dan untuk
database klien simulasi di prototype, sehingga tetap menunjukkan kemampuan
adaptasi (multiple clients, different schemas) tanpa kompleksitas produksi
yang berlebihan?

## Constraints

- Prototype: prioritas pada fungsionalitas end-to-end, kemudahan setup, dan
  demonstrabilitas.
- Harus bisa mensimulasikan beberapa klien dengan skema yang sangat berbeda
  (nama tabel/kolom, relasi, representasi data, bahkan bahasa).
- Harus mendukung migrasi ke engine lain (MySQL/PostgreSQL) nanti tanpa
  mengubah arsitektur adapter.
- Internal Database tidak boleh menjadi salinan Client Database.

## Options Considered

- Option A: SQLite untuk semua (Internal Database + database klien simulasi),
  dengan interface adapter untuk engine lain.
- Option B: MySQL/PostgreSQL untuk Internal Database, SQLite untuk klien
  simulasi.
- Option C: MySQL/PostgreSQL untuk semuanya.

## Decision

Gunakan SQLite untuk AIOS Internal Database dan untuk database klien simulasi
pada prototype. Sediakan interface Database Adapter yang memungkinkan engine
lain (MySQL, PostgreSQL, dll) digunakan nanti tanpa mengubah arsitektur.

## Rationale

- SQLite adalah engine yang tepat untuk prototype: satu file per database,
  tanpa administrasi, dan sangat mudah disetup — cocok untuk demonstrasi
  multi-klien (REF-004).
- Dokumentasi resmi SQLite menyatakan SQLite bekerja sangat baik untuk
  aplikasi dengan trafik rendah hingga menengah dan sebagai stand-in database
  enterprise saat demo/testing (REF-004) — sesuai kebutuhan prototype.
- Menggunakan file SQLite terpisah untuk setiap klien simulasi memudahkan
  demonstrasi isolasi antar tenant dan skema yang berbeda tanpa infrastruktur
  database server.
- Adapter abstraction menjaga Client Database tetap sebagai sumber kebenaran
  dan memungkinkan pindah ke engine produksi nanti tanpa mendesain ulang
  arsitektur (sesuai AGENTS.md "Database Adapter").

## Evidence / References

- REF-004: Appropriate Uses For SQLite — SQLite (official docs)

## Trade-offs

- SQLite memiliki batas satu penulis per database pada saat yang sama, tetapi
  untuk prototype dengan beban rendah ini tidak menjadi masalah.
- Database klien simulasi SQLite bukan representasi penuh dari sistem klien
  riil (misal kinerja, tipe data lanjutan), tetapi cukup untuk memvalidasi
  adaptasi skema dan pemetaan.
- Internal Database SQLite tidak scalable seperti server RDBMS, tetapi di luar
  lingkup prototype.

## Consequences

- AIOS Internal Database dibuat sebagai file SQLite.
- Database klien simulasi dibuat sebagai file SQLite terpisah dengan skema
  yang sengaja berbeda (misal Inggris: products/orders; Indonesia:
  barang/penjualan; plus struktur yang tidak biasa).
- Database Adapter menyediakan interface konsisten; implementasi SQLite
  dipakai sekarang, implementasi lain bisa ditambahkan kemudian.
- REQUIREMENTS.md DS-01/IDB-13 akan diperbarui pada fase setup lingkungan.

## Confidence

High. Rekomendasi SQLite didukung langsung oleh dokumentasi resmi SQLite yang
menyebutkan penggunaannya untuk demo/testing dan aplikasi dengan trafik
rendah-menengah (REF-004), cocok dengan karakter prototype.

## Reconsideration Conditions

- Jika kebutuhan konkurensi tulis tinggi atau data melampaui kapasitas file
  SQLite (banyak penulis simultan, data sangat besar), ganti dengan server
  RDBMS.
- Jika demonstrasi membutuhkan representasi klien riil yang lebih akurat
  (misal klien memakai MySQL), tambahkan implementasi adapter MySQL.
