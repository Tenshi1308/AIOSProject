# ADR-005: Framework Backend Frappe Framework v15

- **Decision ID:** ADR-005
- **Status:** Accepted
- **Date:** 2026-08-20
- **Supersedes:** ADR-002 (Framework Backend FastAPI)

## Context

AIOS adalah platform SaaS multi-tenant yang menyediakan API backend untuk dua
portal (klien dan pengembang Ekasa), integrasi dengan Local LLM, akses ke
Client Database melalui Database Adapter, dan AIOS Internal Database untuk
metadata serta mapping.

Pada ADR-002, backend diputuskan memakai FastAPI. Sejak itu, kebutuhan yang
lebih jelas muncul: backend AIOS membutuhkan autentikasi per perusahaan dengan
role (Client dan Ekasa Developer), admin panel, ORM terintegrasi, migrasi
database, dan mekanisme multi-tenant secara bawaan. Selain itu, stakeholder
(Ekasa Technology) mengarahkan penggunaan framework Python yang "batteries-
included" agar prototype dapat dikembangkan lebih cepat dan mudah
didemonstrasikan.

## Problem Statement

Framework backend mana yang dipakai untuk membangun prototype AIOS agar cepat
dikembangkan, mudah dibaca, menyediakan autentikasi/role/admin/ORM yang sudah
terintegrasi, dan tetap mendukung integrasi dengan Local LLM serta berbagai
database client melalui adapter?

## Constraints

- Prototype: prioritas pada kecepatan pengembangan, kesederhanaan, dan
  kemudahan demonstrasi (bukan kompleksitas produksi).
- Harus berbahasa Python (kebutuhan stakeholder Ekasa Technology; ekosistem
  AI/data science).
- Harus mendukung autentikasi per perusahaan (multi-tenant), role (Client dan
  Ekasa Developer), dan isolasi data antar tenant.
- Harus mudah berkomunikasi dengan Local LLM (HTTP API) dan mengakomodasi
  adapter database yang beragam (Database Adapter).
- IDB harus tetap database-agnostic pada level arsitektur: AIOS Core, AI
  Managers, dan Workers tidak boleh bergantung langsung pada API spesifik satu
  engine database (IDB-29, IDB-30).
- Runtime LLM final tetap **TBD** (ADR-004); keputusan ini tidak mengunci
  runtime.

## Options Considered

- Option A: FastAPI (Python) — framework API modern, ringan, async.
- Option B: Frappe Framework v15 (Python) — full-stack "batteries-included":
  auth, role-based permissions, admin panel (Desk), ORM (DocTypes), migrasi,
  scheduler.
- Option C: Django + Django REST Framework (Python) — full-stack klasik.
- Option D: Node.js (Express/Fastify) — non-Python.

## Decision

Gunakan **Frappe Framework v15** sebagai framework backend AIOS. Keputusan ini
menggantikan (supersedes) ADR-002.

Sub-keputusan yang menyertai:

1. **AIOS Internal Database (IDB) = MariaDB yang dikelola Frappe.** IDB diakses
   melalui lapisan DocTypes/ORM Frappe (data-access boundary). Hal ini tetap
   memenuhi IDB-29/IDB-30: AIOS Core, AI Managers, dan Workers tidak
   bergantung langsung pada SQL MariaDB, melainkan melalui DocTypes/ORM — engine
   IDB tetap bisa diganti sepanjang boundary itu dijaga. Ini merevisi bagian
   "engine IDB TBD (PostgreSQL primary, SQLite alternatif)" pada ADR-003.
2. **Multi-tenancy AIOS = satu site `aios.localhost` + scoping tenant via
   DocType** (bukan memakai multi-site silo Frappe). Alasan: ADR-001 dan
   FR-27/FR-28 menetapkan kedua portal berbagi satu backend dan satu AIOS
   Internal Database; di Frappe, tiap site = satu database terpisah, sehingga
   multi-site akan memisahkan database dan melanggar ADR-001. Dengan satu
   site, isolasi antar tenant (Client A vs Client B) dijaga di lapisan aplikasi
   melalui field tenant pada DocType dan filter wajib pada data-access layer.
3. **Portal Client vs Ekasa Developer ditentukan dari domain (Host header)**
   pada site yang sama: `client.aios.localhost` → role Client;
   `developer.aios.localhost` → role Ekasa Developer. Role diverifikasi
   server-side, tanpa role picker (sesuai ADR-001, FR-28, SEC-01).
4. **Pemakaian token (usage metering)** dicatat per (company/tenant, branch,
   worker) sebagai DocType metrik di IDB; role Developer membaca lintas-tenant
   hanya untuk DocType metrik, sementara role Client terscope ke tenant-nya
   (FR-30, IDB-27, SEC-03).

## Rationale

- Frappe menyediakan, secara bawaan, komponen yang pada ADR-002 justru harus
  dirakit manual dengan FastAPI: autentikasi login, role/permissions, admin
  panel (Desk), ORM (DocTypes) beserta migrasi otomatis, dan scheduler. Ini
  mempercepat prototype secara signifikan tanpa melanggar prinsip "do NOT
  over-engineer" — komponen itu memang dibutuhkan AIOS (auth multi-tenant,
  CRUD metadata/mapping, worker jobs) (REF-018).
- Frappe resmi mendukung persyaratan yang dibutuhkan prototype: MariaDB
  10.6.6+, Python 3.10+, NodeJS 18+, Redis/Valkey 6+, Yarn 1.12+ (REF-020).
- Ekosistem Python dipertahankan, konsisten dengan kebutuhan integrasi Local
  LLM dan pemrosesan data (keunggulan yang juga mendasari ADR-002).
- Multi-tenancy satu site + scoping DocType dipilih karena kedua portal harus
  berbagi satu IDB (ADR-001); pola ini adalah bentuk SaaS pool model yang
  didokumentasikan (REF-001, REF-002).
- Windows tidak didukung Frappe secara native; penggunaan WSL2 (Ubuntu) adalah
  jalur resmi yang didokumentasikan (REF-020; discuss.frappe.io). Ini
  disepakati sebagai lingkungan development (Fase 0/1).
- Option A (FastAPI) ditolak/digantikan karena auth/ORM/admin/migrasi harus
  dirakit manual dan tidak memenuhi arah stakeholder untuk framework
  full-stack. Option C (Django) juga full-stack namun ekosistem Frappe lebih
  cocok untuk demo cepat dengan DocTypes + Desk bawaan. Option D (Node.js)
  keluar dari ekosistem Python yang diminta.

## Evidence / References

- REF-018: Frappe Framework Documentation (official) —
  https://docs.frappe.io/framework
- REF-019: Frappe Bench — CLI to manage multi-tenant deployments (official
  GitHub) — https://github.com/frappe/bench
- REF-020: Frappe Installation — System requirements & installation steps
  (official) — https://docs.frappe.io/framework/user/en/installation
- REF-001: SaaS Tenant Isolation Strategies — AWS (2020)
- REF-002: Degrees of tenant isolation for cloud-hosted software services —
  Ochei, Bass, Petrovski (2018)

## Trade-offs

- Frappe lebih berat daripada FastAPI (dengan admin panel, ORM, dan ekosistem
  lengkap); untuk prototype ini trade-off diterima karena komponen tersebut
  memang dipakai AIOS.
- IDB terikat MariaDB selama menggunakan Frappe secara default; database-
  agnosticity dijaga lewat boundary DocTypes/ORM (IDB-29/IDB-30), tetapi
  mengganti engine IDB berarti mengganti mekanisme Frappe itu sendiri.
- Satu site + scoping DocType berarti isolasi tenant bergantung pada disiplin
  filter tenant di data-access layer (bukan isolasi fisik database) — sama
  dengan trade-off ADR-001.
- Frontend Frappe Desk memakai Vue 3 + Frappe UI; pemisahan tampilan portal
  (Client vs Developer) perlu dirancang di lapisan aplikasi (Host header →
  role), bukan otomatis dari Frappe.

## Consequences

- ADR-002 (FastAPI) ditandai Superseded oleh ADR-005.
- ADR-003 direvisi: bagian IDB "TBD (PostgreSQL primary, SQLite alternatif)"
  digantikan oleh "MariaDB via Frappe" (lihat ADR-005); bagian Client Database
  simulasi multi-engine tetap berlaku.
- Struktur backend AIOS dibangun sebagai app Frappe `aios` (bench, satu site
  `aios.localhost`) dengan DocTypes untuk tenant, connection, schema metadata,
  semantic mapping, plugin/worker config, conversation/memory summary, dan
  usage log.
- Autentikasi dan role (Client/Ekasa Developer) memakai mekanisme role Frappe
  dengan penentuan portal dari domain (Fase 4).
- Setup lingkungan prototype: Frappe v15 di WSL2 (Ubuntu 24.04), MariaDB via
  Frappe, frontend Vue 3 + Frappe UI (Fase 1 dan Fase 9).
- REQUIREMENTS.md IDB-13, AGENTS.md (bagian AIOS Internal Database),
  docs/analisis-kebutuhan.md, dan docs/use-case-description.md disinkronkan
  dengan keputusan ini.

## Confidence

High untuk pemilihan Frappe v15 sebagai backend (didukung dokumentasi resmi
Frappe REF-018/REF-020, kesesuaian langsung dengan kebutuhan auth/ORM/admin/
multi-tenant AIOS, dan arahan stakeholder). Medium untuk keputusan "satu site +
scoping tenant" — pola ini konsisten dengan literatur multi-tenant SaaS
(REF-001/REF-002), tetapi efektivitas isolasi bergantung pada disiplin
implementasi filter tenant yang akan diverifikasi di Fase 3–4.

## Reconsideration Conditions

- Jika isolasi tenant dengan satu site terbukti tidak memadai dalam pengujian
  (misal kebocoran data lintas tenant), pertimbangkan kembali pendekatan
  multi-site atau mekanisme isolasi yang lebih ketat.
- Jika performa/migrasi Frappe menjadi hambatan prototype, evaluasi kembali
  pemilihan framework.
- Jika stakeholder memutuskan stack non-Frappe untuk produksi, keputusan ini
  ditinjau ulang.