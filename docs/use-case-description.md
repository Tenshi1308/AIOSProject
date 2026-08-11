# Use Case Description — AIOS Plugin Platform

**Proyek:** Prototype AIOS Plugin Platform (Immersion Program)
**Pelaksana:** Samuel Karel Augusta / 233016011
**Mitra:** Ekasa Technology (software house)
**Status:** Draft v4 — berdasarkan `AGENTS.md`, `REQUIREMENTS.md`, dan keputusan
stakeholder (AI Manager & Worker AI dijadikan actor); selaras dengan
`docs/diagrams/use-case-diagram.drawio`

Diagram: `docs/diagrams/use-case-diagram.drawio`

---

## 1. Pendahuluan

Dokumen ini mendeskripsikan use case diagram AIOS. Use case disusun berdasarkan
kebutuhan yang terdapat pada `AGENTS.md` dan `REQUIREMENTS.md` saja. Tidak ada
fitur atau requirement baru yang ditambahkan.

Prinsip yang menjadi dasar:

- AIOS adalah **plugin** yang menempel pada sistem client; sistem client tetap.
- AIOS dipandang seperti **organisasi/perusahaan dengan 9 cabang bidang**
  (modul ERP). Setiap cabang dikepalai oleh satu **AI Manager**, dan di bawahnya
  terdapat **Worker AI** yang meniru job role spesifik pada bidang tersebut.
  Contoh bidang Finance: Finance Staff, Financial Analyst, Budgeting Staff,
  Treasurer, CFO.
- AIOS **bukan chatbot umum**; user memilih AI Manager / kapabilitas terlebih
  dahulu di interface.
- **Client Database** tetap menjadi source of truth business data.
- **AIOS Internal Database** menyimpan metadata, mapping, konfigurasi, dan state.
- Database adaptation berlangsung terutama saat **integrasi/setup**, bukan per
  request.
- AIOS berjalan **lokal** (Ollama); pipeline RAG untuk dokumen berjalan internal
  di AIOS (retrieval oleh Worker AI saat interaksi UC-02/UC-09).

---

## 2. Actor

Berdasarkan keputusan stakeholder, **AI Manager dan Worker AI dijadikan actor**.
Keduanya adalah aktor internal AIOS yang diangkat sebagai actor pada use case
diagram untuk memperlihatkan hierarki "AI sebagai manager dan bawahan".

Komponen internal lain (Plugin Manager, Database Adapter, AI Schema Analyzer,
AIOS Internal Database, RAG pipeline, Ollama) tetap **tidak** dijadikan actor.
`AIOS System` adalah subjek (system boundary), bukan actor.

| Actor | Peran | Use case terkait |
|---|---|---|
| **User** | Pengguna akhir yang memilih AI Manager/kapabilitas dan berinteraksi melalui AIOS Interface, di dalam environment client yang sudah terautentikasi. Tidak perlu memahami detail internal. | UC-01, UC-02 |
| **AI Manager** (9 cabang) | "Manager bidang" di AIOS. Setiap cabang (modul ERP) dikepalai satu AI Manager: Finance, HR, Sales/CRM, Procurement, Inventory, Production, Logistics, Maintenance, Reporting/BI. Bertanggung jawab mengelola & mengoordinasikan Worker AI di bidangnya. | UC-08 |
| **Worker AI** (per job role) | "Bawahan" AI Manager yang meniru job role spesifik pada bidangnya (contoh Finance: Finance Staff, Financial Analyst, Budgeting Staff, Treasurer, CFO). Mengeksekusi tugas domain melalui abstraksi AIOS. | UC-09 |
| **Client System** | Sistem existing milik client (aplikasi, autentikasi, database). Tetap menjadi sistem utama dan sumber kebenaran business data; tidak dimodifikasi. Actor sekunder. | UC-03, UC-04, UC-05, UC-06 |
| **Developer / Intern (Admin AIOS)** | Membuat & mengintegrasikan plugin AIOS ke sistem client, serta mengonfigurasi plugin dan worker. | UC-03, UC-07 |

### 9 Cabang Bidang (Modul ERP) dan Job Role Worker AI

| # | Cabang (AI Manager) | Contoh Job Role / Worker AI |
|---|---|---|
| 1 | Finance | Finance Staff, Financial Analyst, Budgeting Staff, Treasurer, CFO |
| 2 | Human Resources | HR Staff, Recruiter, Payroll Officer, Training Specialist, HR Manager |
| 3 | Sales / CRM | Sales Representative, Customer Service, Sales Data Analyst, Marketing Specialist |
| 4 | Procurement | Procurement Staff, Senior Procurement Specialist, Purchasing Officer |
| 5 | Inventory | Inventory Control Manager, Warehouse Inventory Manager, Retail Inventory Manager |
| 6 | Production | Production Planner, Production Scheduler, Production Supervisor |
| 7 | Logistics | Logistics Coordinator, Shipping & Receiving Clerk, Fleet Manager |
| 8 | Maintenance | Maintenance Planner, Reliability Engineer, Maintenance Technician |
| 9 | Reporting / BI | BI Analyst, Report Developer, Data Steward |

> Daftar job role adalah contoh yang mewakili tiap bidang dan dapat disesuaikan
> pada implementasi. Prinsip utama: tiap AI Manager memimpin Worker AI pada
> bidangnya; daftar worker bersifat modular (Plugin Manager / UC-07).

> Catatan UC-02: akses business data dari Client Database dilakukan secara
> internal melalui AIOS Data Layer / Database Adapter / canonical model, sehingga
> relasi Client System ke UC-02 tidak digambar pada diagram.

> Catatan database adaptation (UC-04, UC-05, UC-06): dieksekusi **otomatis oleh
> AIOS** saat integrasi/setup dan saat perubahan skema terdeteksi — tidak memiliki
> actor inisiator manusia. Pemicu (trigger) tiap use case dijelaskan pada
> deskripsi masing-masing.

---

## 3. Ringkasan Use Case

| ID | Nama | Kelompok | Actor utama | Actor sekunder |
|---|---|---|---|---|
| UC-01 | Memilih AI Manager / Kapabilitas | A. Penggunaan AIOS | User | – |
| UC-02 | Berinteraksi dengan AI Manager dan Worker | A. Penggunaan AIOS | User | AI Manager, Worker AI |
| UC-03 | Mendaftarkan Integrasi Client (Plugin Setup) | B. Integrasi Client | Developer / Intern | Client System |
| UC-04 | Menganalisis Skema Database Client | C. Database Adaptation | – (otomatis oleh AIOS) | Client System |
| UC-05 | Memetakan Skema ke Canonical Data Model | C. Database Adaptation | – (otomatis oleh AIOS) | Client System |
| UC-06 | Memperbarui Mapping saat Skema Berubah | C. Database Adaptation | – (otomatis oleh AIOS) | Client System |
| UC-07 | Mengonfigurasi Plugin dan Worker | D. Plugin & Worker | Developer / Intern | – |
| UC-08 | AI Manager Mengelola & Mengkoordinasikan Worker | E. AI Manager & Worker | AI Manager | Worker AI |
| UC-09 | Worker AI Mengeksekusi Tugas Domain | E. AI Manager & Worker | Worker AI | – |

\* Client System berpartisipasi secara internal sebagai sumber business data
(lihat catatan pada bagian Actor).

---

## 4. Deskripsi Use Case

### UC-01 — Memilih AI Manager / Kapabilitas

- **Tujuan:** User memilih AI Manager (cabang bidang/kapabilitas) spesifik
  sebelum berinteraksi.
- **Actor:** User (utama).
- **Deskripsi:** Melalui AIOS Interface, user memilih salah satu AI Manager dari
  9 cabang bidang (Finance, HR, Sales/CRM, Procurement, Inventory, Production,
  Logistics, Maintenance, Reporting/BI). Sistem membuka workspace AI Manager
  yang dipilih beserta Worker AI di bawahnya.
- **Pre-condition:**
  - User terautentikasi pada environment client.
  - AIOS telah terintegrasi (UC-03) dan plugin/worker tersedia (UC-07).
- **Alur utama:**
  1. User membuka AIOS Interface.
  2. Interface menampilkan AI Manager / kapabilitas yang tersedia.
  3. User memilih AI Manager.
  4. Interface membuka workspace AI Manager beserta worker-nya.
- **Alur alternatif:**
  - AI Manager/kapabilitas yang dipilih tidak tersedia → sistem menampilkan
    informasi bahwa kapabilitas tersebut tidak tersedia untuk client ini.
- **Post-condition:** Workspace AI Manager terbuka dan siap digunakan.
- **Referensi:** FR-01, FR-02, FR-03, FR-04, OS-01, OS-10.

---

### UC-02 — Berinteraksi dengan AI Manager dan Worker

- **Tujuan:** User bertanya/memberi tugas dan menerima respons AI dari AI
  Manager beserta Worker AI-nya.
- **Actor:** User (utama); AI Manager & Worker AI (sekunder, berpartisipasi
  dalam alur).
- **Deskripsi:** AI Manager mengelola eksekusi worker di bidangnya
  (mengelola/koordinasi — UC-08) dan Worker AI mengeksekusi tugas domain
  (UC-09). Worker memakai tools dan data melalui abstraksi AIOS (canonical
  model, RAG bila diperlukan) dan Local LLM. User tidak perlu memahami detail
  internal.
- **Pre-condition:** UC-01 selesai (workspace AI Manager terbuka).
- **Alur utama:**
  1. User mengirimkan pertanyaan/tugas pada workspace AI Manager.
  2. AI Manager mengelola & mengoordinasikan worker yang relevan (UC-08).
  3. Worker AI mengeksekusi tugas domain (UC-09) menggunakan tools dan data
     yang tersedia (via canonical model dan abstraksi data AIOS; termasuk RAG
     bila tugas memerlukan dokumen).
  4. Local LLM menghasilkan respons.
  5. Interface menampilkan respons kepada user.
- **Alur alternatif:**
  - Konsep yang diminta tidak tersedia pada database client → worker tidak
    mengarang data; sistem menginformasikan keterbatasan data yang tersedia.
- **Post-condition:**
  - User menerima respons.
  - Business data tidak disalin ke AIOS Internal Database; Client Database
    tetap source of truth.
- **Relasi:** **&lt;&lt;include&gt;&gt;** UC-08 (AI Manager Mengelola &
  Mengkoordinasikan Worker) — interaksi selalu melalui pengelolaan oleh AI
  Manager.
- **Referensi:** FR-04, FR-05, FR-06, FR-07, FR-08 s.d. FR-16 (peran AI
  Manager), FR-20, FR-21, FR-22, RAG-03, LLM-02, LLM-03, SEC-05, IDB-14 s.d.
  IDB-21, AC-04, AC-12.

---

### UC-03 — Mendaftarkan Integrasi Client (Plugin Setup)

- **Tujuan:** Mengintegrasikan AIOS sebagai plugin ke sistem client dan
  mendaftarkan konfigurasi client.
- **Actor:** Developer / Intern (utama); Client System (sekunder).
- **Deskripsi:** Mendaftarkan client baru: metadata client, metadata koneksi
  database, dan integrasi dengan environment client yang sudah terautentikasi.
  Dapat diulang untuk banyak client secara independen dan terisolasi.
- **Pre-condition:**
  - Developer memiliki akses ke environment client.
  - Sistem client tidak dimodifikasi.
- **Alur utama:**
  1. Developer memulai setup integrasi client baru.
  2. Sistem mencatat metadata client.
  3. Sistem menyimpan metadata koneksi database.
  4. AIOS terintegrasi dengan environment client yang sudah terautentikasi
     (tanpa lapisan autentikasi JWT baru).
  5. Metadata disimpan di AIOS Internal Database, terisolasi per client.
- **Post-condition:** Integrasi client tersimpan dan siap menjalankan database
  adaptation.
- **Referensi:** IR-01, IR-02, IR-03, IR-04, IR-05, IR-06, IR-07, IR-08, IR-09,
  PW-01, SEC-01, SEC-02, SEC-03, IDB-01, IDB-02, IDB-22, IDB-23, IDB-24, AC-01,
  AC-15.

---

### UC-04 — Menganalisis Skema Database Client

- **Tujuan:** Memahami skema database client secara semantik.
- **Actor:** – (dieksekusi otomatis oleh AIOS); Client System (sekunder, sumber
  skema).
- **Trigger:** Dijalankan otomatis oleh AIOS sebagai bagian database adaptation
  pada proses integrasi/setup client (setelah UC-03). Tidak dijalankan dari nol
  pada setiap request user (DS-09, DS-11).
- **Deskripsi:** Schema Extraction mengekstrak metadata skema melalui Database
  Adapter; AI Schema Analyzer menganalisis skema secara semantik (tabel, kolom,
  tipe data, relasi, constraint, sample values, naming pattern, makna semantik)
  menggunakan Local LLM.
- **Pre-condition:** UC-03 selesai (koneksi database tersedia).
- **Alur utama:**
  1. Sistem mengekstrak metadata skema melalui Database Adapter.
  2. AI Schema Analyzer menganalisis skema secara semantik.
  3. Hasil analisis (schema understanding) disimpan bila berguna.
- **Alur alternatif:**
  - Skema client berubah → alur UC-06 (perbarui mapping).
- **Post-condition:** Pemahaman skema tersedia sebagai input untuk semantic
  mapping.
- **Referensi:** DS-01, DS-02, DS-03, DS-04, DS-05, LLM-03, IDB-03, IDB-04,
  AC-06, AC-07.

---

### UC-05 — Memetakan Skema ke Canonical Data Model

- **Tujuan:** Menghasilkan semantic mapping skema client ke canonical model dan
  menyimpannya agar dapat digunakan kembali.
- **Actor:** – (dieksekusi otomatis oleh AIOS); Client System (sekunder).
- **Trigger:** Dijalankan otomatis oleh AIOS setelah UC-04 sebagai bagian
  database adaptation pada integrasi/setup client.
- **Deskripsi:** Sistem membuat pemetaan semantik konsep client ke konsep
  canonical (contoh: `barang.nama` → `Product.name`, `barang.tersedia` →
  `Product.stock`). Mapping beserta metadata (versi/status/confidence bila
  diperlukan) disimpan di AIOS Internal Database agar tidak perlu analisis ulang
  pada setiap request.
- **Pre-condition:** UC-04 selesai (pemahaman skema tersedia).
- **Alur utama:**
  1. Sistem membuat semantic mapping dari schema understanding ke Canonical
     Data Model.
  2. Sistem menyimpan mapping dan metadata (versi/status/confidence bila
     diperlukan) di AIOS Internal Database.
  3. Worker siap beroperasi melalui canonical model untuk client ini.
- **Post-condition:** Mapping tersimpan dan dapat digunakan kembali tanpa
  analisis skema ulang.
- **Relasi:** **&lt;&lt;include&gt;&gt;** UC-04 (Menganalisis Skema Database
  Client) — pemetaan selalu membutuhkan hasil analisis skema.
- **Referensi:** DS-06, DS-07, DS-08, DS-09, DS-10, DS-11, DS-14, DS-15, DS-16,
  IDB-05, IDB-06, IDB-10, IDB-26, AC-08, AC-09.

---

### UC-06 — Memperbarui Mapping saat Skema Berubah

- **Tujuan:** Menjaga mapping tetap sesuai ketika skema client berubah.
- **Actor:** – (dieksekusi otomatis oleh AIOS); Client System (sekunder, sumber
  perubahan skema).
- **Trigger:** Perubahan skema terdeteksi pada Client Database (event).
- **Deskripsi:** Jika skema client berubah, sistem dapat mendeteksi perubahan,
  melakukan re-analysis, dan memperbarui mapping yang terdampak.
- **Pre-condition:** Mapping pernah dibuat (UC-05).
- **Alur utama:**
  1. Sistem mendeteksi perubahan skema client.
  2. Sistem melakukan re-analysis skema.
  3. Sistem memperbarui mapping yang terdampak di AIOS Internal Database.
- **Post-condition:** Mapping yang diperbarui tersimpan dan konsisten dengan
  skema terbaru.
- **Relasi:** **&lt;&lt;extend&gt;&gt;** UC-05 (Memetakan Skema ke Canonical
  Data Model) — hanya berjalan bila perubahan skema terdeteksi.
- **Referensi:** IDB-11.

---

### UC-07 — Mengonfigurasi Plugin dan Worker

- **Tujuan:** Mendaftarkan dan mengonfigurasi plugin, capability, worker, dan
  tool yang tersedia untuk client.
- **Actor:** Developer / Intern (utama).
- **Deskripsi:** Plugin Manager mengelola plugin AIOS beserta kapabilitasnya.
  Developer mengonfigurasi worker/tool yang tersedia; konfigurasi disimpan di
  AIOS Internal Database. Mendukung arsitektur modular agar kapabilitas baru
  dapat ditambahkan tanpa mendesain ulang inti AIOS.
- **Pre-condition:** AIOS telah terpasang; developer memiliki hak konfigurasi.
- **Alur utama:**
  1. Developer mendaftarkan/mengonfigurasi plugin dan capability.
  2. Developer mengonfigurasi worker dan tool.
  3. Konfigurasi disimpan di AIOS Internal Database.
- **Post-condition:** Plugin/worker siap digunakan pada UC-01 dan UC-02.
- **Referensi:** FR-23, FR-24, FR-25, FR-26, PW-02, PW-03, PW-04, PW-05, PW-07,
  IDB-07, IDB-08.

---

### UC-08 — AI Manager Mengelola & Mengkoordinasikan Worker

- **Tujuan:** AI Manager mengelola dan mengoordinasikan Worker AI pada
  bidangnya sehingga tugas user dapat dieksekusi dengan benar.
- **Actor:** AI Manager (utama); Worker AI (sekunder).
- **Deskripsi:** AI Manager sebagai "manager bidang" memilih/mengoordinasikan
  worker yang relevan, mengelola konteks, dan mengoordinasikan tools yang
  diperlukan (sesuai peran AI Manager pada AGENTS.md). AI Manager tidak
  menggantikan worker; eksekusi tugas domain tetap dilakukan Worker AI (UC-09).
- **Pre-condition:** AI Manager terpilih pada UC-01; worker terkonfigurasi
  (UC-07).
- **Alur utama:**
  1. AI Manager menerima tugas dari user (melalui UC-02).
  2. AI Manager mengidentifikasi/mengoordinasikan worker yang relevan pada
     bidangnya.
  3. AI Manager mengoordinasikan konteks dan tools yang dibutuhkan.
  4. AI Manager mengarahkan Worker AI untuk mengeksekusi tugas (UC-09).
- **Alur alternatif:**
  - Tidak ada worker yang sesuai untuk tugas → AI Manager menginformasikan
    keterbatasan kapabilitas untuk client ini.
- **Post-condition:** Tugas didelegasikan ke Worker AI yang tepat.
- **Relasi:** **&lt;&lt;include&gt;&gt;** UC-09 (Worker AI Mengeksekusi Tugas
  Domain) — mengelola & mengoordinasikan worker selalu diikuti eksekusi tugas
  oleh worker.
- **Referensi:** FR-04, FR-05, FR-06, FR-07, FR-08 s.d. FR-16 (peran AI
  Manager), OS-10, PW-04.

---

### UC-09 — Worker AI Mengeksekusi Tugas Domain

- **Tujuan:** Worker AI mengeksekusi tugas domain spesifik pada bidangnya
  menggunakan tools dan data melalui abstraksi AIOS.
- **Actor:** Worker AI (utama).
- **Deskripsi:** Worker AI meniru job role spesifik (mis. Finance Staff,
  Inventory Control Manager, BI Analyst). Worker mengeksekusi tugas domain
  dengan memakai canonical model, AIOS Data Layer, dan Local LLM; tidak
  bergantung langsung pada skema client.
- **Pre-condition:** Tugas didelegasikan oleh AI Manager (UC-08); data yang
  dibutuhkan tersedia melalui abstraksi AIOS.
- **Alur utama:**
  1. Worker menerima tugas dari AI Manager.
  2. Worker menggunakan tools dan data yang tersedia (via canonical model dan
     abstraksi data AIOS; termasuk RAG bila diperlukan).
  3. Local LLM menghasilkan respons/hasil.
  4. Worker mengembalikan hasil kepada AI Manager.
- **Alur alternatif:**
  - Konsep yang diminta tidak tersedia pada database client → worker tidak
    mengarang data; hasil mencerminkan keterbatasan data yang tersedia.
- **Post-condition:** Hasil tugas diserahkan ke AI Manager untuk diteruskan ke
  user.
- **Referensi:** FR-04, FR-06, FR-20, FR-21, FR-22, RAG-01, RAG-03, LLM-02,
  LLM-03, AC-04, AC-12.

---

## 5. Relasi Antara Use Case

- **&lt;&lt;include&gt;&gt;** — UC-05 (Memetakan Skema) *includes* UC-04
  (Menganalisis Skema): alur pemetaan selalu menjalankan analisis skema sebagai
  prasyarat hasilnya.
- **&lt;&lt;extend&gt;&gt;** — UC-06 (Memperbarui Mapping) *extends* UC-05
  (Memetakan Skema): alur pembaruan mapping hanya berjalan sebagai perluasan
  opsional ketika perubahan skema terdeteksi.
- **&lt;&lt;include&gt;&gt;** — UC-02 (Berinteraksi) *includes* UC-08 (AI
  Manager Mengelola & Mengkoordinasikan Worker): interaksi user selalu melalui
  pengelolaan oleh AI Manager.
- **&lt;&lt;include&gt;&gt;** — UC-08 (AI Manager Mengelola) *includes* UC-09
  (Worker AI Mengeksekusi Tugas Domain): pengelolaan & koordinasi worker selalu
  diikuti eksekusi tugas domain oleh worker.
- **Precondition (bukan include):** UC-02 memerlukan UC-01. Pemilihan
  kapabilitas/AI Manager adalah *entry point* sebelum interaksi, bukan sub-langkah
  yang diulang pada setiap interaksi, sehingga tidak dimodelkan sebagai include.

## 6. Catatan

- Berdasarkan keputusan stakeholder, AI Manager dan Worker AI dijadikan actor
  untuk memperlihatkan hierarki "AI sebagai manager dan bawahan": AIOS dipandang
  seperti organisasi dengan 9 cabang bidang (modul ERP), tiap cabang dikepalai
  AI Manager yang memimpin Worker AI (job role spesifik). Komponen internal lain
  (Plugin Manager, Database Adapter, AI Schema Analyzer, AIOS Internal Database,
  pipeline RAG, Ollama) tetap bukan actor.
- Use case tidak dibuat per komponen teknis; misalnya tidak ada use case
  terpisah untuk "menggunakan Ollama", "menjalankan Database Adapter", atau
  "Plugin Manager mendaftarkan plugin". Peran tersebut termasuk dalam alur
  internal use case yang relevan (UC-02, UC-03, UC-07).
- Database adaptation (UC-04, UC-05, UC-06) dieksekusi otomatis oleh AIOS saat
  integrasi/setup dan saat perubahan skema terdeteksi, bukan dari nol untuk
  setiap request (DS-09, DS-11, IDB-11). Karena bersifat otomatis, use case ini
  tidak memiliki actor inisiator manusia; pemicunya didokumentasikan pada bagian
  *Trigger* masing-masing.
- Tidak ada use case khusus untuk pipeline RAG karena `AGENTS.md` dan
  `REQUIREMENTS.md` tidak mendefinisikan aktor yang menyuplai/mengunggah dokumen.
  Proses RAG (termasuk retrieval dokumen) berjalan internal di AIOS dan dipakai
  oleh Worker AI pada alur UC-02/UC-09 (RAG-01, RAG-02, RAG-03).
- Business data tidak disalin ke AIOS Internal Database; Client Database tetap
  menjadi source of truth (IDB-14 s.d. IDB-21).
- Sumber data job role Worker AI: hasil riset struktur organisasi departemen
  (Finance, HR, Sales/CRM, Procurement, Inventory, Production, Logistics,
  Maintenance, Reporting/BI). Daftar bersifat contoh & modular dan dapat
  disesuaikan pada implementasi melalui konfigurasi (UC-07).
