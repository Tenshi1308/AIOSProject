# ADR-003: Database Engine untuk Prototype (Client Simulasi + IDB)

- **Decision ID:** ADR-003
- **Status:** Revised
- **Date:** 2026-08-18 (direvisi 2026-08-20)

## Context

AIOS memiliki dua jenis database: Client Database (milik klien, sumber data
bisnis) dan AIOS Internal Database (metadata, mapping, konfigurasi, state).
Untuk prototype, AIOS perlu mendemonstrasikan adaptasi terhadap berbagai
struktur database klien yang berbeda, sambil menyimpan metadata dan mapping
per tenant di Internal Database.

Revisi 2026-08-20 menyesuaikan keputusan ini dengan ADR-005 (backend Frappe
Framework v15):

- **Engine AIOS Internal Database (IDB)** ditetapkan menjadi **MariaDB yang
  dikelola Frappe** (diakses melalui DocTypes/ORM Frappe sebagai boundary).
  Bagian "engine IDB TBD (PostgreSQL primary, SQLite alternatif)" pada ADR-003
  ini di-SUPERSEDE oleh ADR-005.
- **Client Database simulasi** ditetapkan sebagai **multi-engine**: SQLite
  (ringan/portabel), PostgreSQL (sudah tervalidasi pada Eksperimen 4), dan
  MariaDB/MySQL (keluarga engine Frappe). Hal ini memperbaiki inkonsistensi
  keputusan sebelumnya yang hanya menyebut SQLite, bertentangan dengan
  REQUIREMENTS.md DS-01 dan AC-13 (client database dapat memakai engine
  berbeda-beda; pengujian harus mencakup "different database engines where
  practical") serta bukti empiris Eksperimen 4 yang memakai PostgreSQL nyata.

## Problem Statement

Database engine apa yang dipakai untuk database klien simulasi dan untuk
AIOS Internal Database di prototype, sehingga tetap menunjukkan kemampuan
adaptasi (multiple clients, different schemas, different engines) tanpa
kompleksitas produksi yang berlebihan, tanpa mengunci keputusan engine IDB
secara premature?

## Constraints

- Prototype: prioritas pada fungsionalitas end-to-end, kemudahan setup, dan
  demonstrabilitas.
- Harus bisa mensimulasikan beberapa klien dengan skema yang sangat berbeda
  (nama tabel/kolom, relasi, representasi data, bahkan bahasa).
- Harus mendukung migrasi ke engine lain (MySQL/PostgreSQL) nanti tanpa
  mengubah arsitektur adapter.
- Internal Database tidak boleh menjadi salinan Client Database.
- Internal Database wajib berjalan local / self-hosted (tanpa serverless /
  cloud-managed database service). Engine IDB ditetapkan = **MariaDB via Frappe
  Framework v15** (ADR-005, revisi 2026-08-20) — keputusan mengikuti keputusan
  framework backend, bukan menunggu evaluasi/PoC terpisah.

## Options Considered

- Option A: SQLite untuk semua (Internal Database + database klien simulasi),
  dengan interface adapter untuk engine lain.
- Option B: MySQL/PostgreSQL untuk Internal Database, SQLite untuk klien
  simulasi.
- Option C: MySQL/PostgreSQL untuk semuanya.
- Option D (keputusan 2026-08-18): SQLite untuk database klien simulasi; engine
  IDB dibiarkan **TBD** dengan PostgreSQL (self-hosted) sebagai kandidat utama
  evaluasi dan SQLite sebagai kandidat alternatif, sesuai hasil PoC.
- Option E (revisi 2026-08-20): **Client Database simulasi multi-engine**
  (SQLite + PostgreSQL + MariaDB/MySQL) sesuai DS-01/AC-13; **IDB = MariaDB via
  Frappe** sesuai ADR-005.

## Decision

### Client Database simulasi (revisi 2026-08-20)

Untuk database klien simulasi pada prototype, gunakan **multi-engine** sesuai
REQUIREMENTS.md DS-01 dan AC-13:

- **SQLite** — satu file per klien, skema sengaja berbeda; ringan dan mudah
  didemonstrasikan.
- **PostgreSQL** — engine yang sudah tervalidasi pada Eksperimen 4 (nyata,
  boundary read-only via `pg_catalog`).
- **MariaDB / MySQL** — keluarga engine yang dipakai Frappe dan banyak sistem
  ERP client.

Semua diakses melalui interface Database Adapter yang konsisten, sehingga
worker tidak bergantung pada engine tertentu (DS-12 s.d. DS-15).

### AIOS Internal Database (IDB) — superseded oleh ADR-005

Untuk AIOS Internal Database, engine ditetapkan menjadi **MariaDB yang
dikelola Frappe Framework v15**, diakses melalui lapisan DocTypes/ORM Frappe
sebagai data-access boundary (memenuhi IDB-29/IDB-30). Bagian keputusan
"engine IDB TBD (PostgreSQL primary, SQLite alternatif)" pada ADR-003 ini
**di-supersede oleh ADR-005** (2026-08-20). SQLite tetap valid hanya untuk
database klien simulasi, bukan untuk IDB.

## Rationale

- SQLite adalah engine yang tepat untuk salah satu varian database klien
  simulasi prototype: satu file per database, tanpa administrasi, dan sangat
  mudah disetup — cocok untuk demonstrasi multi-klien (REF-004).
- Dokumentasi resmi SQLite menyatakan SQLite bekerja sangat baik untuk
  aplikasi dengan trafik rendah hingga menengah dan sebagai stand-in database
  enterprise saat demo/testing (REF-004) — sesuai kebutuhan prototype.
- Namun, membatasi klien simulasi hanya ke SQLite bertentangan dengan
  REQUIREMENTS.md DS-01 (client database dapat berbeda engine) dan AC-13
  (pengujian "different database engines where practical"). Karena itu
  keputusan direvisi menjadi multi-engine (SQLite + PostgreSQL + MariaDB/
  MySQL), konsisten dengan prinsip AIOS "adapt to each client's existing
  system".
- PostgreSQL sudah terbukti pada Eksperimen 4 (nyata, boundary read-only via
  `pg_catalog`, ekstraksi deterministik + LLM mapping 15/15) sehingga menjadi
  bagian dari varian engine simulasi.
- MariaDB/MySQL ditambahkan karena merupakan keluarga engine yang dipakai
  Frappe dan umum pada sistem ERP client.
- Database Adapter abstraction menjaga Client Database tetap sebagai sumber
  kebenaran dan memungkinkan penggunaan banyak engine tanpa mendesain ulang
  arsitektur (sesuai AGENTS.md "Database Adapter").
- Untuk IDB, keputusan "engine TBD (PostgreSQL primary, SQLite alternatif)"
  pada revisi 2026-08-18 di-supersede oleh ADR-005: IDB = MariaDB via Frappe.
  Boundary DocTypes/ORM Frappe menjaga database-agnosticity pada level
  arsitektur (IDB-29/IDB-30), sementara perpindahan engine IDB hanya terjadi
  bersama pergantian mekanisme Frappe itu sendiri.

## Evidence / References

- REF-004: Appropriate Uses For SQLite — SQLite (official docs)
- REF-017: PostgreSQL documentation — PostgreSQL (official docs; dipakai pada
  Eksperimen 4 untuk varian engine klien simulasi PostgreSQL)
- REF-018: Frappe Framework Documentation (official; dasar keputusan IDB =
  MariaDB via Frappe, ADR-005)
- REF-020: Frappe Installation — system requirements (MariaDB 10.6.6+;
  dasar pemilihan MariaDB sebagai engine IDB)

## Trade-offs

- SQLite memiliki batas satu penulis per database pada saat yang sama, tetapi
  untuk prototype dengan beban rendah dan untuk database klien simulasi hal
  ini tidak menjadi masalah.
- Database klien simulasi multi-engine (SQLite/PostgreSQL/MariaDB) bukan
  representasi penuh dari sistem klien riil (misal kinerja, tipe data
  lanjutan), tetapi cukup untuk memvalidasi adaptasi skema, pemetaan, dan
  adaptasi lintas engine.
- Memakai PostgreSQL dan MariaDB untuk klien simulasi menambah kebutuhan
  instalasi/administrasi server dibanding SQLite file — diterima demi
  memenuhi AC-13 ("different database engines where practical").
- IDB terikat pada MariaDB via Frappe; perpindahan engine IDB berarti
  mengganti mekanisme Frappe (boundary DocTypes/ORM tetap menjaga
  database-agnosticity arsitektur).

## Consequences

- Database klien simulasi dibuat sebagai beberapa engine dengan skema yang
  sengaja berbeda (misal Inggris: products/orders; Indonesia:
  barang/penjualan; plus struktur yang tidak biasa), masing-masing diakses
  melalui Database Adapter.
- Database Adapter menyediakan interface konsisten; implementasi SQLite,
  PostgreSQL, dan MariaDB/MySQL dipakai untuk klien simulasi prototype.
- Engine AIOS Internal Database **= MariaDB via Frappe** (ADR-005). SQLite
  tidak dipakai untuk IDB; hanya untuk database klien simulasi.
- REQUIREMENTS.md IDB-13, AGENTS.md (bagian IDB), dan dokumen terkait
  diperbarui sesuai ADR-005/ADR-003 revisi ini.

## Confidence

High untuk keputusan multi-engine client simulasi (didukung REQUIREMENTS.md
DS-01/AC-13, bukti Eksperimen 4 di PostgreSQL, dan dokumentasi resmi SQLite
REF-004). High untuk IDB = MariaDB via Frappe (didukung dokumentasi resmi
Frappe REF-018/REF-020 dan ADR-005).

## Reconsideration Conditions

- Jika kebutuhan konkurensi tulis tinggi atau data melampaui kapasitas file
  SQLite (banyak penulis simultan, data sangat besar) pada varian klien
  simulasi, ganti varian tersebut dengan server RDBMS.
- Jika demonstrasi membutuhkan representasi klien riil yang lebih akurat
  (misal klien memakai engine lain), tambahkan implementasi adapter engine
  tersebut.
- Jika isolasi tenant satu site terbukti tidak memadai atau IDB perlu
  berpindah dari MariaDB (Frappe), tinjau kembali ADR-005 dan ADR-003.
