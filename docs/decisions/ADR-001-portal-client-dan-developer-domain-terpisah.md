# ADR-001: Portal Client dan Developer pada Domain Terpisah

- **Decision ID:** ADR-001
- **Status:** Accepted
- **Date:** 2026-08-18

## Context

AIOS adalah SaaS multi-tenant: setiap perusahaan klien login ke workspace-nya
sendiri, dan semua data, metadata, serta mapping diisolasi per perusahaan
(tenant). Ada dua audiens berbeda: klien (yang menggunakan AIOS) dan
pengembang Ekasa (yang hanya memantau pemakaian). Klien tidak boleh melihat
data monitoring internal; pengembang Ekasa tidak boleh mengakses data bisnis
atau percakapan klien. Kedua audiens membutuhkan halaman login dan portal yang
berbeda secara fungsional.

## Problem Statement

Bagaimana memisahkan portal klien dan portal pengembang Ekasa sehingga kedua
peran terisolasi, mudah dikenali oleh pengguna, dan tetap memakai infrastruktur
AIOS yang sama?

## Constraints

- Prototype SaaS multi-tenant; pemisahan data per tenant wajib (Client A tidak
  boleh mengakses data Client B).
- Deployment model AIOS adalah standalone SaaS dengan domain sendiri; tidak
  tertanam di aplikasi klien.
- Prototype: hindari kompleksitas produksi yang tidak perlu; backend dan
  Internal Database tunggal lebih sederhana untuk dibangun dan didemonstrasikan.
- Tidak ada role picker di halaman login; role harus ditentukan dengan cara
  yang tidak dapat dipilih langsung oleh pengguna.

## Options Considered

- Option A: Satu domain, halaman login dengan menu pilih role.
- Option B: Dua domain terpisah (`client.aios.*` dan `developer.aios.*`),
  role ditentukan dari domain mana pengguna login, tanpa role picker,
  enforced server-side.
- Option C: Dua domain terpisah + dua backend dan dua database terpisah.

## Decision

Gunakan dua portal pada domain terpisah: Portal Klien di `client.aios.*` dan
Portal Monitoring Pengembang Ekasa di `developer.aios.*`. Role ditentukan dari
domain portal tempat pengguna login (tidak ada role picker), dan ditegakkan di
sisi server. Kedua portal berbagi backend AIOS yang sama dan AIOS Internal
Database yang sama. Domain terpisah TIDAK berarti database terpisah.

## Rationale

- Pemisahan domain membuat setiap audiens masuk melalui "pintu" yang jelas dan
  tidak ambigu, sehingga permukaan serangan per role lebih kecil (REF-001,
  REF-002).
- Tanpa role picker, pengguna tidak bisa memilih role sesukanya; role berasal
  dari jalur masuk (domain) dan diverifikasi server-side, mengurangi risiko
  privilege escalation.
- Berbagi satu backend dan satu Internal Database menjaga biaya dan kompleksitas
  tetap rendah (prinsip Cost Efficient), sementara isolasi tetap dijamin pada
  level tenant (metadata, mapping, data Client A terpisah dari Client B).
- Multi-tenancy dengan satu infrastruktur bersama adalah pola baku SaaS
  (model pool) dan tetap mampu memberikan isolasi yang memadai (REF-001,
  REF-002).

## Evidence / References

- REF-001: SaaS Tenant Isolation Strategies — AWS (2020)
- REF-002: Degrees of tenant isolation for cloud-hosted software services —
  Ochei, Bass, Petrovski (2018)

## Trade-offs

- Dua domain menambah sedikit konfigurasi (DNS, sertifikat, routing) dibanding
  satu domain dengan role picker.
- Pengguna harus tahu domain mana yang sesuai (klien vs developer) — ini
  dikomunikasikan melalui alamat resmi masing-masing portal.
- Tidak memakai dua database terpisah berarti isolasi bergantung pada desain
  tenant-awareness yang benar di aplikasi, bukan pada isolasi fisik database.

## Consequences

- REQUIREMENTS.md, docs/analisis-kebutuhan.md, dan docs/use-case-description.md
  sudah diperbarui; use case C2 menjadi "Login (Role dari Domain)".
- Prototype akan menyimulasikan dua domain via port berbeda (misal
  localhost:8000 untuk klien, localhost:8001 untuk developer).
- Backend harus menerapkan tenant scoping (perusahaan klien) pada semua
  akses data dan metadata.
- Pengembang Ekasa hanya melihat metrik penggunaan (token), bukan data bisnis
  atau percakapan klien.
- **Re-affirm 2026-08-20 (ADR-005):** Dengan backend Frappe Framework v15,
  kedua portal dipetakan ke **satu site** (`aios.localhost`) + penentuan
  portal dari domain (Host header: `client.aios.localhost` → Client,
  `developer.aios.localhost` → Ekasa Developer), diverifikasi server-side.
  Tidak memakai multi-site Frappe agar kedua portal tetap berbagi satu
  backend dan satu AIOS Internal Database (konsisten dengan keputusan ini).
  Detail implementasi di Fase 4.

## Confidence

High. Pemisahan domain untuk pemisahan peran didukung oleh dokumentasi resmi
AWS tentang isolasi tenant (REF-001) dan studi peer-reviewed tentang derajat
isolasi multi-tenant (REF-002), serta selaras dengan kebutuhan fungsional
yang sudah disetujui.

## Reconsideration Conditions

- Jika di kemudian hari satu backend bersama terbukti tidak cukup untuk
  memisahkan beban atau jika muncul kebutuhan isolasi fisik (compliance),
  ADR ini perlu ditinjau kembali.
- Jika produk memutuskan untuk menggabungkan portal kembali ke satu domain.
