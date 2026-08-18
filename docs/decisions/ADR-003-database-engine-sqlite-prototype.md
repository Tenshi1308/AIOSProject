# ADR-003: Database Engine untuk Prototype (Client Simulasi + IDB)

- **Decision ID:** ADR-003
- **Status:** Accepted
- **Date:** 2026-08-18 (direvisi 2026-08-18)

## Context

AIOS memiliki dua jenis database: Client Database (milik klien, sumber data
bisnis) dan AIOS Internal Database (metadata, mapping, konfigurasi, state).
Untuk prototype, AIOS perlu mendemonstrasikan adaptasi terhadap berbagai
struktur database klien yang berbeda, sambil menyimpan metadata dan mapping
per tenant di Internal Database.

Revisi ini menegaskan bahwa keputusan engine Internal Database (IDB) harus
kembali terbuka (TBD) setelah evaluasi/PoC, dan bahwa SQLite tidak boleh
diperlakukan sebagai keputusan final untuk IDB.

## Problem Statement

Database engine apa yang dipakai untuk database klien simulasi dan untuk
AIOS Internal Database di prototype, sehingga tetap menunjukkan kemampuan
adaptasi (multiple clients, different schemas) tanpa kompleksitas produksi
yang berlebihan, tanpa mengunci keputusan engine IDB secara premature?

## Constraints

- Prototype: prioritas pada fungsionalitas end-to-end, kemudahan setup, dan
  demonstrabilitas.
- Harus bisa mensimulasikan beberapa klien dengan skema yang sangat berbeda
  (nama tabel/kolom, relasi, representasi data, bahkan bahasa).
- Harus mendukung migrasi ke engine lain (MySQL/PostgreSQL) nanti tanpa
  mengubah arsitektur adapter.
- Internal Database tidak boleh menjadi salinan Client Database.
- Internal Database wajib berjalan local / self-hosted (tanpa serverless /
  cloud-managed database service); engine final ditentukan dari evaluasi/PoC,
  bukan di awal.

## Options Considered

- Option A: SQLite untuk semua (Internal Database + database klien simulasi),
  dengan interface adapter untuk engine lain.
- Option B: MySQL/PostgreSQL untuk Internal Database, SQLite untuk klien
  simulasi.
- Option C: MySQL/PostgreSQL untuk semuanya.
- Option D: SQLite untuk database klien simulasi; engine IDB dibiarkan **TBD**
  dengan PostgreSQL (self-hosted) sebagai kandidat utama evaluasi dan SQLite
  sebagai kandidat alternatif, sesuai hasil PoC.

## Decision

Untuk database klien simulasi pada prototype, gunakan SQLite (satu file per
klien, skema sengaja berbeda) dengan interface Database Adapter.

Untuk AIOS Internal Database, engine adalah **TBD**: PostgreSQL (self-hosted)
adalah kandidat utama yang dievaluasi, dan SQLite tetap merupakan kandidat
alternatif — bukan keputusan final. Keputusan final ditentukan berdasarkan
hasil evaluasi / PoC. IDB dirancang database-agnostic melalui data-access
layer / database adapter boundary sehingga engine dapat diganti tanpa
mendesain ulang arsitektur.

## Rationale

- SQLite adalah engine yang tepat untuk database klien simulasi prototype:
  satu file per database, tanpa administrasi, dan sangat mudah disetup —
  cocok untuk demonstrasi multi-klien (REF-004).
- Dokumentasi resmi SQLite menyatakan SQLite bekerja sangat baik untuk
  aplikasi dengan trafik rendah hingga menengah dan sebagai stand-in database
  enterprise saat demo/testing (REF-004) — sesuai kebutuhan prototype.
- Menggunakan file SQLite terpisah untuk setiap klien simulasi memudahkan
  demonstrasi isolasi antar tenant dan skema yang berbeda tanpa infrastruktur
  database server.
- Adapter abstraction menjaga Client Database tetap sebagai sumber kebenaran
  dan memungkinkan pindah ke engine produksi nanti tanpa mendesain ulang
  arsitektur (sesuai AGENTS.md "Database Adapter").
- Untuk IDB, SQLite tidak dijadikan keputusan final karena IDB bersifat
  multi-tenant dan akan menyimpan metadata/mapping/state sejumlah client;
  PostgreSQL (self-hosted) menjadi kandidat utama yang dievaluasi, sedangkan
  keputusan menunggu hasil evaluasi/PoC (tidak diputuskan di awal).

## Evidence / References

- REF-004: Appropriate Uses For SQLite — SQLite (official docs)
- REF-017: PostgreSQL documentation — PostgreSQL (official docs, kandidat
  evaluasi IDB)

## Trade-offs

- SQLite memiliki batas satu penulis per database pada saat yang sama, tetapi
  untuk prototype dengan beban rendah dan untuk database klien simulasi hal
  ini tidak menjadi masalah.
- Database klien simulasi SQLite bukan representasi penuh dari sistem klien
  riil (misal kinerja, tipe data lanjutan), tetapi cukup untuk memvalidasi
  adaptasi skema dan pemetaan.
- Engine IDB yang dibiarkan TBD berarti evaluasi/PoC IDB belum final; ini
  menghindari komitmen premature pada satu engine (PostgreSQL vs SQLite).
- PostgreSQL (self-hosted) membutuhkan instalasi/administrasi server yang
  lebih banyak daripada SQLite bila dipilih; keputusan menunggu hasil PoC.

## Consequences

- Database klien simulasi dibuat sebagai file SQLite terpisah dengan skema
  yang sengaja berbeda (misal Inggris: products/orders; Indonesia:
  barang/penjualan; plus struktur yang tidak biasa).
- Database Adapter menyediakan interface konsisten; implementasi SQLite
  dipakai sekarang untuk klien simulasi, implementasi lain bisa ditambahkan
  kemudian.
- Engine AIOS Internal Database **tidak terkunci**: PostgreSQL (self-hosted)
  menjadi kandidat utama, SQLite kandidat alternatif, keputusan final dari
  hasil evaluasi/PoC (REQUIREMENTS.md IDB-13, IDB-28 s.d. IDB-30).
- REQUIREMENTS.md DS-01/IDB-13 akan diperbarui pada fase setup lingkungan.

## Confidence

High untuk keputusan database klien simulasi SQLite (didukung dokumentasi
resmi SQLite, REF-004). Medium untuk keputusan engine IDB yang sengaja
dibiarkan TBD menunggu evaluasi/PoC — keputusan final memerlukan hasil PoC.

## Reconsideration Conditions

- Jika kebutuhan konkurensi tulis tinggi atau data melampaui kapasitas file
  SQLite (banyak penulis simultan, data sangat besar), ganti dengan server
  RDBMS.
- Jika demonstrasi membutuhkan representasi klien riil yang lebih akurat
  (misal klien memakai MySQL), tambahkan implementasi adapter MySQL.
- Setelah evaluasi/PoC IDB selesai, revisi keputusan engine IDB (pilih
  PostgreSQL self-hosted atau engine lain, atau konfirmasi SQLite) dan catat
  sebagai ADR baru/tersendiri.
