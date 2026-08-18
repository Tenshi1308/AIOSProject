# Use Case Description — AIOS Plugin Platform

**Proyek:** Prototype AIOS Plugin Platform (Immersion Program)
**Pelaksana:** Samuel Karel Augusta / 233016011
**Mitra:** Ekasa Technology (software house)
**Status:** Draft — berdasarkan `AGENTS.md` dan `REQUIREMENTS.md` serta keputusan
stakeholder pada sesi perancangan.

---

## 1. Pendahuluan

Dokumen ini mendeskripsikan use case AIOS berdasarkan kebutuhan pada
`AGENTS.md` dan `REQUIREMENTS.md` saja. Tidak ada fitur atau requirement baru
yang ditambahkan kecuali yang telah disepakati pada sesi perancangan
(keputusan stakeholder).

Prinsip yang menjadi dasar:

- AIOS adalah **plugin** yang menempel pada sistem client; sistem client tetap
  (**CLIENT SYSTEM STAYS. AIOS ADAPTS.**).
- AIOS adalah **multi-tenant SaaS** yang di-host Ekasa. Setiap perusahaan
  client login ke workspace-nya sendiri; data, percakapan, dan mapping
  antar perusahaan terisolasi.
- Terdapat **2 role eksternal**: **Client** (perusahaan pemakai AIOS) dan
  **Developer Ekasa** (internal Ekasa yang hanya memantau pemakaian).
- Portal Client dan portal monitoring Developer Ekasa berada di **domain
  terpisah** (mis. `client.aios.*` dan `developer.aios.*`); role ditentukan
  dari domain portal dan diverifikasi server-side, tanpa menu pilih role.
  Kedua portal berbagi satu backend dan satu AIOS Internal Database.
- AIOS dipandang seperti organisasi dengan **9 cabang bidang (modul ERP)**.
  Setiap cabang dikepalai satu **AI Primary Agent**, dan di bawahnya terdapat
  **sub-agents domain** yang meniru job role spesifik pada bidang tersebut.
- AIOS **bukan chatbot umum**; user memilih AI Manager/kapabilitas terlebih
  dahulu di interface.
- **Client Database** tetap menjadi source of truth business data. AIOS
  Internal Database hanya menyimpan metadata, mapping, konfigurasi,
  percakapan, dan state.
- Database adaptation berlangsung saat **integrasi/setup**, bukan per request.
- Pada prototype ini, penanganan dokumen (RAG) **di-defer** / berada di luar
  scope. Prototype fokus pada data terstruktur dari Client Database.
- Produk diukur terhadap 4 prinsip inti (keputusan stakeholder): **Cost
  Efficient**, **User Friendly**, **Plug and Go**, dan **Fast**.

---

## 2. Actor

| Actor | Peran | Use case terkait |
|---|---|---|
| **Client** | Perusahaan pemakai AIOS (satu role). Registrasi, login, membayar, menghubungkan database, memilih bidang ERP, chat dengan AI Primary Agent, dan memvalidasi mapping. | C1–C9 |
| **Developer Ekasa** | Internal Ekasa. Hanya memantau pemakaian token per akun client; tidak memiliki akses ke data atau percakapan bisnis client. Akses melalui portal monitoring di domain terpisah (`developer.aios.*`). | D1–D2 |
| **AI Primary Agent** (9 cabang) | "Manager bidang" di AIOS. Setiap cabang (modul ERP) dikepalai satu AI Primary Agent. Menerima pertanyaan dari Client, mendelegasikan ke sub-agent yang sesuai, dan menyusun respons. | C8–C10, C12–C13 |
| **Sub-agents domain** | "Bawahan" AI Primary Agent yang meniru job role spesifik pada bidangnya dan menjawab sesuai spesialisasinya. | C11 |
| **Data Access Agent** | Satu per tenant. Memahami struktur database client (database adaptation), menyimpan mapping, menyediakan data aktual, dan re-adaptasi saat skema berubah. | C4–C7, C12, C14 |
| **Memory Agent** | Satu per AI Manager. Merangkum percakapan agar AI Primary Agent mengingat konteks chat sebelumnya. | C13 |
| **Client System** | Sistem existing milik client (aplikasi, autentikasi, database). Tetap menjadi sistem utama dan sumber business data; tidak dimodifikasi. Actor sekunder. | C4, C5, C7, C12, C14 |

### 9 Cabang Bidang (Modul ERP) dan Job Role Sub-agents

| # | Cabang (AI Primary Agent) | Contoh Job Role / Sub-agents |
|---|---|---|
| 1 | Strategic and Operational Planning | BI Analyst, Report Developer, Data Steward |
| 2 | Finance | Finance Staff, Financial Analyst, Budgeting Staff, Treasurer, CFO |
| 3 | Human Resource | HR Staff, Recruiter, Payroll Officer, Training Specialist, HR Manager |
| 4 | Logistic Management | Logistics Coordinator, Shipping & Receiving Clerk, Fleet Manager |
| 5 | Maintenance Management | Maintenance Planner, Reliability Engineer, Maintenance Technician |
| 6 | Sales and Distribution | Sales Representative, Customer Service, Sales Data Analyst, Marketing Specialist |
| 7 | Quality Management | Quality Inspector, Quality Engineer, Quality Auditor, Quality Control Officer |
| 8 | Material Management | Procurement Staff, Senior Procurement Specialist, Purchasing Officer, Inventory Control Manager, Warehouse Inventory Manager, Retail Inventory Manager |
| 9 | Manufacturing | Production Planner, Production Scheduler, Production Supervisor |

> Semua 9 bidang selalu tersedia untuk setiap client. Jawaban sub-agents
> menyesuaikan data yang benar-benar tersedia pada database client.
>
> Daftar job role bersifat contoh & modular dan dapat disesuaikan pada
> implementasi melalui konfigurasi (Plugin Manager).

---

## 3. Ringkasan Use Case

| ID | Nama | Kelompok | Actor utama | Actor sekunder |
|---|---|---|---|---|
| C1 | Registrasi Akun | Onboarding & Auth | Client | – |
| C2 | Login (Role dari Domain) | Onboarding & Auth | Client / Developer Ekasa | – |
| C3 | Pembayaran | Onboarding & Auth | Client | – |
| C4 | Menghubungkan Database Perusahaan | Onboarding Data | Client | Client System |
| C5 | Menganalisis Skema & Membuat Mapping (Database Adaptation) | Onboarding Data | – (otomatis oleh AIOS) | Client System |
| C6 | Memvalidasi Hasil Mapping | Onboarding Data | Client | – |
| C7 | Mengedit Koneksi Database | Onboarding Data | Client | Client System |
| C8 | Memilih Bidang ERP | Penggunaan | Client | – |
| C9 | Chat dengan AI Primary Agent | Penggunaan | Client | AI Primary Agent |
| C10 | AI Primary Mendelegasikan Pertanyaan | Internal AI | AI Primary Agent | Sub-agents domain |
| C11 | Sub-agents Menjawab Tugas Domain | Internal AI | Sub-agents domain | – |
| C12 | Data Access Agent Menyediakan Data Client | Internal AI | Data Access Agent | Client System |
| C13 | Memory Agent Merangkum Percakapan | Internal AI | Memory Agent | – |
| C14 | Re-adaptasi Mapping saat Skema Berubah | Internal AI | – (otomatis oleh AIOS) | Client System |
| D1 | Dashboard Pemakaian Token per Client | Monitoring | Developer Ekasa | – |
| D2 | Analisis Penggunaan AI Manager | Monitoring | Developer Ekasa | – |

---

## 4. Deskripsi Use Case

### C1 — Registrasi Akun

- **Tujuan:** Client membuat akun AIOS sebelum dapat login.
- **Actor:** Client (utama).
- **Deskripsi:** Sebelum melakukan login, client melakukan registrasi terlebih
  dahulu untuk membuat akun perusahaannya.
- **Pre-condition:** – (belum memiliki akun).
- **Alur utama:**
  1. Client membuka domain portal client (`client.aios.*`).
  2. Client memilih opsi registrasi.
  3. Client mengisi data registrasi akun perusahaan.
  4. Sistem membuat akun client.
- **Post-condition:** Akun client terdaftar dan siap login.
- **Referensi:** FR-27, FR-28, SEC-01.

---

### C2 — Login (Role dari Domain)

- **Tujuan:** Client atau Developer Ekasa mengakses workspace-nya.
- **Actor:** Client (utama); Developer Ekasa (utama).
- **Deskripsi:** Setiap role login melalui portal pada **domain terpisah**:
  Client membuka domain portal client (`client.aios.*`) dan Developer Ekasa
  membuka domain portal monitoring (`developer.aios.*`). Role ditentukan oleh
  domain portal dan diverifikasi server-side; tidak ada menu pilih role.
  Client masuk ke workspace perusahaannya; Developer Ekasa masuk ke dashboard
  monitoring.
- **Pre-condition:** Akun sudah terdaftar (C1).
- **Alur utama:**
  1. Client membuka domain portal client (`client.aios.*`), ATAU Developer
     Ekasa membuka domain portal monitoring (`developer.aios.*`).
  2. User memasukkan kredensial.
  3. Sistem memverifikasi kredensial dan role sesuai domain portal.
  4. Sistem membuka workspace yang sesuai dengan role.
- **Alur alternatif:**
  - Kredensial salah atau role tidak sesuai dengan domain → sistem menampilkan
    pesan kesalahan login.
  - Pengguna mengakhiri sesi → pengguna memilih opsi keluar (logout); sistem
    mengakhiri sesi aktif dan mengembalikan ke halaman login.
- **Post-condition:** Client masuk ke workspace perusahaannya, atau Developer
  Ekasa masuk ke dashboard monitoring. Sesi tetap berjalan hingga pengguna
  keluar (logout).
- **Referensi:** FR-27, FR-28, SEC-01, SEC-03.

---

### C3 — Pembayaran

- **Tujuan:** Client membayar untuk mengaktifkan penggunaan fitur AIOS.
- **Actor:** Client (utama).
- **Deskripsi:** Client melakukan pembayaran melalui payment gateway pada
  umumnya. Setelah pembayaran berhasil, akun client aktif otomatis dan dapat
  menggunakan kapabilitas AIOS.
- **Pre-condition:** Client telah login (C2).
- **Alur utama:**
  1. Client memilih opsi pembayaran.
  2. Sistem mengarahkan ke payment gateway.
  3. Client menyelesaikan pembayaran.
  4. Payment gateway mengonfirmasi keberhasilan.
  5. Sistem mengaktifkan akses kapabilitas client secara otomatis.
- **Alur alternatif:**
  - Pembayaran gagal/dibatalkan → sistem menampilkan status pembayaran belum
    selesai; akses kapabilitas belum aktif.
- **Post-condition:** Akun client aktif dan dapat menggunakan kapabilitas AIOS.
- **Referensi:** FR-29, AC-18.

---

### C4 — Menghubungkan Database Perusahaan

- **Tujuan:** Client menghubungkan database perusahaannya agar AIOS dapat
  mengakses business data.
- **Actor:** Client (utama); Client System (sekunder).
- **Deskripsi:** Setelah akun aktif, client menghubungkan database perusahaan
  melalui form koneksi (gate wajib sebelum menggunakan AI Manager). Kredensial
  koneksi disimpan aman pada AIOS Internal Database (connection metadata).
- **Pre-condition:** Akun client aktif (C3).
- **Alur utama:**
  1. Client membuka menu menghubungkan database.
  2. Client memilih jalur koneksi: **masukkan kredensial** database perusahaan
     yang sudah ada, atau **buat database baru** (disediakan Ekasa).
  3. Sistem menyimpan metadata koneksi dan memvalidasi koneksi.
  4. Koneksi berhasil; sistem melanjutkan ke database adaptation (C5).
- **Alur alternatif:**
  - Koneksi gagal (kredensial salah/server tidak terjangkau) → sistem
    menampilkan pesan kesalahan; client dapat memperbaiki dan mencoba lagi.
  - Client memilih **buat database baru** (tidak memiliki database):
    1. Client memilih mode pembuatan: **template standar** Ekasa (skema + data
       contoh siap pakai) atau **buat sendiri** (menentukan tabel dan
       variabel/kolom yang dibutuhkan).
    2. Sistem membuat database baru; karena kredensial dibuat oleh AIOS sendiri,
       client tidak perlu mengisi form kredensial.
    3. Sistem menandai database baru tersebut sebagai Client Database (source
       of truth) yang di-host Ekasa dan melanjutkan ke database adaptation (C5).
- **Post-condition:** Koneksi ke Client Database tersimpan dan valid.
- **Referensi:** FR-32, FR-32A, FR-32B, FR-32C, IR-01 s.d. IR-09, DS-12, DS-13, SEC-03, IDB-01, IDB-02, AC-01, AC-15.

---

### C5 — Menganalisis Skema & Membuat Mapping (Database Adaptation)

- **Tujuan:** Data Access Agent memahami struktur database client secara
  semantik dan membuat mapping ke konsep canonical.
- **Actor:** – (dieksekusi otomatis oleh AIOS); Client System (sekunder).
- **Trigger:** Dijalankan otomatis oleh AIOS setelah koneksi database berhasil
  (setelah C4) dan setelah koneksi diedit (C7). Tidak dijalankan dari nol pada
  setiap request user (DS-09, DS-11).
- **Deskripsi:** Data Access Agent (1 per tenant) mengekstrak metadata skema
  melalui Database Adapter, menganalisisnya secara semantik (tabel, kolom,
  tipe data, relasi, constraint, sample values, naming pattern, makna semantik),
  lalu memetakannya ke Canonical Data Model. Hasil mapping beserta
  versi/status/confidence disimpan di AIOS Internal Database.
- **Pre-condition:** Koneksi database tersedia (C4).
- **Alur utama:**
  1. Sistem mengekstrak metadata skema melalui Database Adapter.
  2. Data Access Agent menganalisis skema secara semantik.
  3. Sistem membuat semantic mapping ke Canonical Data Model.
  4. Sistem menyimpan mapping dan metadata (versi/status/confidence) di AIOS
     Internal Database.
  5. Hasil mapping siap divalidasi oleh client (C6).
- **Post-condition:** Mapping tersimpan di AIOS Internal Database dan siap
  digunakan.
- **Catatan:** Database yang dibuat melalui opsi "buat database baru" pada C4
  (provisioning Ekasa) tetap melalui pipeline adaptasi yang sama persis seperti
  Client Database biasa (FR-32A s.d. FR-32C).
- **Referensi:** DS-01 s.d. DS-11, LLM-03, FR-37, IDB-03 s.d. IDB-06, IDB-10, IDB-26,
  AC-06, AC-07, AC-08.

---

### C6 — Memvalidasi Hasil Mapping

- **Tujuan:** Client mengonfirmasi kebenaran hasil mapping skema agar
  pemahaman data client dapat dipercaya.
- **Actor:** Client (utama).
- **Deskripsi:** Setelah Data Access Agent selesai memahami skema, sistem
  menampilkan UI validasi mapping: tingkat confidence hasil analisis, daftar
  pemetaan konsep, opsi konfirmasi, dan opsi edit manual oleh client. Hasil
  konfirmasi/editan disimpan di AIOS Internal Database.
- **Pre-condition:** Mapping telah dibuat (C5).
- **Alur utama:**
  1. Sistem menampilkan hasil mapping beserta tingkat confidence.
  2. Client memeriksa kebenaran pemetaan konsep.
  3. Client mengonfirmasi mapping yang benar, dan/atau melakukan edit manual
     pada mapping yang kurang tepat.
  4. Sistem menyimpan hasil validasi/editan di AIOS Internal Database.
- **Alur alternatif:**
  - Confidence rendah → sistem menandai mapping sebagai low-confidence dan
    meminta konfirmasi/editan manual oleh client.
- **Post-condition:** Mapping tervalidasi dan digunakan untuk interaksi AI.
- **Catatan (TBD):** Low-confidence terjadi pada konteks database adaptation
  (saat onboarding & perubahan skema), bukan saat chat dengan AI Manager.
  Mekanisme penanganan low-confidence yang user-friendly (tanpa memunculkan
  istilah teknis, sesuai prinsip User Friendly) masih **open discussion**.
- **Referensi:** FR-34, DS-06, DS-07, IDB-05, IDB-06, AC-19.

---

### C7 — Mengedit Koneksi Database

- **Tujuan:** Client memperbaiki atau mengganti koneksi database perusahaannya.
- **Actor:** Client (utama); Client System (sekunder).
- **Deskripsi:** Client dapat mengedit koneksi database dari menu kapan saja
  (misalnya kredensial salah, pindah database/server). Perubahan koneksi
  memicu database adaptation ulang (C5) dan validasi mapping ulang (C6).
- **Pre-condition:** Koneksi pernah dibuat (C4).
- **Alur utama:**
  1. Client membuka menu koneksi database.
  2. Client mengubah informasi koneksi.
  3. Sistem memvalidasi koneksi baru.
  4. Sistem menyimpan koneksi baru dan memicu database adaptation ulang (C5).
  5. Client melakukan validasi mapping ulang (C6).
- **Alur alternatif:**
  - Koneksi baru gagal → sistem menampilkan pesan kesalahan; koneksi lama tetap
    berlaku.
- **Post-condition:** Koneksi baru berlaku dan mapping diperbarui.
- **Referensi:** FR-33, IR-01 s.d. IR-09, IDB-01, IDB-02.

---

### C8 — Memilih Bidang ERP

- **Tujuan:** Client memilih salah satu dari 9 bidang ERP untuk berinteraksi
  dengan AI Primary Agent-nya.
- **Actor:** Client (utama).
- **Deskripsi:** Semua 9 bidang selalu tersedia untuk setiap client. Client
  memilih satu bidang dari home (9 bidang mengelilingi hub AIOS); sistem
  membuka workspace AI Primary Agent bidang tersebut.
- **Pre-condition:** Akun aktif dan database terhubung (C4 selesai).
- **Alur utama:**
  1. Client membuka home AIOS.
  2. Interface menampilkan 9 bidang yang mengelilingi hub AIOS.
  3. Client memilih salah satu bidang.
  4. Interface membuka workspace chat AI Primary Agent bidang tersebut.
- **Post-condition:** Workspace AI Primary Agent terbuka dan siap digunakan.
- **Referensi:** FR-01, FR-02, FR-03, FR-04, OS-01.

---

### C9 — Chat dengan AI Primary Agent

- **Tujuan:** Client bertanya/memberi tugas dan menerima respons dari AI
  Primary Agent beserta sub-agents-nya.
- **Actor:** Client (utama); AI Primary Agent (sekunder).
- **Deskripsi:** Workspace chat menampilkan panel kiri (placeholder) dan kolom
  chat di kanan. Client mengirimkan pertanyaan; AI Primary Agent mengelola dan
  mengoordinasikan sub-agents yang relevan (C10–C13) lalu menyusun respons.
- **Pre-condition:** Workspace AI Primary Agent terbuka (C8).
- **Alur utama:**
  1. Client mengirimkan pertanyaan/tugas pada kolom chat.
  2. AI Primary Agent menerima pertanyaan.
  3. AI Primary Agent mendelegasikan ke sub-agent yang sesuai (C10).
  4. Respons disusun dan ditampilkan kepada client.
- **Alur alternatif:**
  - Konsep/kapabilitas yang diminta tidak tersedia pada database client →
    sistem menginformasikan keterbatasan data, tidak mengarang data.
- **Post-condition:** Client menerima respons.
- **Referensi:** FR-04 s.d. FR-07, FR-31, LLM-02, LLM-03, AC-12.

---

### C10 — AI Primary Mendelegasikan Pertanyaan

- **Tujuan:** AI Primary Agent menugaskan pertanyaan/tugas ke sub-agent yang
  sesuai pada bidangnya.
- **Actor:** AI Primary Agent (utama); Sub-agents domain (sekunder).
- **Deskripsi:** AI Primary Agent adalah agent primary bidangnya. Ia
  mengidentifikasi sub-agent yang relevan dengan pertanyaan, mengoordinasikan
  konteks dan tools yang dibutuhkan, lalu mengarahkan sub-agent untuk
  mengeksekusi tugas. Delegasi bersifat transparan di interface.
- **Pre-condition:** AI Primary Agent menerima pertanyaan dari client (C9).
- **Alur utama:**
  1. AI Primary Agent menganalisis pertanyaan client.
  2. AI Primary Agent mengidentifikasi sub-agent yang relevan pada bidangnya.
  3. AI Primary Agent mendelegasikan tugas beserta konteks yang dibutuhkan.
- **Alur alternatif:**
  - Tidak ada sub-agent yang sesuai → AI Primary Agent menginformasikan
    keterbatasan kapabilitas.
- **Post-condition:** Tugas didelegasikan ke sub-agent yang tepat.
- **Referensi:** FR-08 s.d. FR-16, FR-31, OS-10, PW-04.

---

### C11 — Sub-agents Menjawab Tugas Domain

- **Tujuan:** Sub-agents domain mengeksekusi tugas sesuai spesialisasinya dan
  mengembalikan hasil ke AI Primary Agent.
- **Actor:** Sub-agents domain (utama).
- **Deskripsi:** Sub-agents meniru job role spesifik pada bidangnya (mis.
  Finance Staff, Inventory Control Manager, BI Analyst). Sub-agent menjawab
  menggunakan canonical model, abstraksi data AIOS, dan Local LLM; tidak
  bergantung langsung pada skema raw client.
- **Pre-condition:** Tugas didelegasikan oleh AI Primary Agent (C10); data
  yang dibutuhkan tersedia melalui abstraksi AIOS.
- **Alur utama:**
  1. Sub-agent menerima tugas dari AI Primary Agent.
  2. Sub-agent menggunakan tools dan data yang tersedia (via canonical model;
    termasuk data dari Data Access Agent bila diperlukan).
  3. Local LLM menghasilkan respons/hasil.
  4. Sub-agent mengembalikan hasil kepada AI Primary Agent.
- **Alur alternatif:**
  - Konsep yang diminta tidak tersedia pada database client → sub-agent tidak
    mengarang data; hasil mencerminkan keterbatasan data yang tersedia.
- **Post-condition:** Hasil tugas diserahkan ke AI Primary Agent.
- **Referensi:** FR-17 s.d. FR-22, LLM-02, LLM-03, AC-04.

---

### C12 — Data Access Agent Menyediakan Data Client

- **Tujuan:** Data Access Agent menyediakan business data aktual dari Client
  Database kepada sub-agents tanpa menduplikasi data ke AIOS Internal Database.
- **Actor:** Data Access Agent (utama); Client System (sekunder).
- **Deskripsi:** Data Access Agent (1 per tenant, dipakai bersama semua AI
  Primary Agent) menerjemahkan kebutuhan data konsep (canonical) menjadi akses
  ke Client Database melalui AIOS Data Layer / Database Adapter. Business data
  tetap bersumber dari Client Database.
- **Pre-condition:** Mapping tervalidasi (C6); data diminta oleh sub-agent.
- **Alur utama:**
  1. Sub-agent meminta data konsep tertentu.
  2. Data Access Agent menerjemahkan konsep ke struktur client melalui mapping.
  3. Database Adapter mengambil data dari Client Database.
  4. Data disediakan kepada sub-agent.
- **Alur alternatif:**
  - Koneksi DB gagal/down → sistem menginformasikan bahwa data sementara tidak
    dapat diambil (bukan error mentah).
  - Konsep tidak tersedia pada client → menginformasikan bahwa data tidak
    tersedia, tidak mengarang.
- **Post-condition:** Data aktual client tersedia bagi sub-agent; Client
  Database tetap source of truth.
- **Referensi:** DS-12 s.d. DS-15, SEC-05, IDB-14 s.d. IDB-21, FR-36, FR-38, AC-20.

---

### C13 — Memory Agent Merangkum Percakapan

- **Tujuan:** AI Primary Agent mengingat konteks percakapan client sebelumnya.
- **Actor:** Memory Agent (utama).
- **Deskripsi:** Memory Agent (1 per AI Manager) merangkum percakapan yang
  telah dilakukan. Riwayat percakapan (full messages) dan ringkasan (summary)
  disimpan di AIOS Internal Database, di-tag per bidang. AI Primary Agent
  menggunakan ringkasan ini sebagai konteks pada interaksi selanjutnya.
- **Pre-condition:** Terdapat percakapan yang telah berlangsung (C9).
- **Alur utama:**
  1. Memory Agent membaca riwayat percakapan bidang terkait.
  2. Memory Agent membuat/memperbarui ringkasan percakapan.
  3. Ringkasan disimpan di AIOS Internal Database.
  4. AI Primary Agent menggunakan ringkasan sebagai konteks percakapan
     selanjutnya.
- **Post-condition:** Konteks percakapan terjaga pada AI Primary Agent bidang
  tersebut.
- **Referensi:** FR-39, FR-40, FR-11 (pengelolaan konteks oleh AI Manager), IDB-09, AC-21.

---

### C14 — Re-adaptasi Mapping saat Skema Berubah

- **Tujuan:** Menjaga mapping tetap sesuai ketika skema database client
  berubah.
- **Actor:** – (dieksekusi otomatis oleh AIOS); Client System (sekunder).
- **Trigger:** Perubahan skema terdeteksi pada Client Database.
- **Deskripsi:** Jika skema client berubah, Data Access Agent mendeteksi
  perubahan, melakukan re-analysis, dan memperbarui mapping. Sistem menampilkan
  pop-up yang menjelaskan bahwa skema database berubah, lalu meminta konfirmasi
  dan memberikan opsi edit manual kepada client (alur validasi ulang seperti
  C6).
- **Pre-condition:** Mapping pernah dibuat (C5/C6).
- **Alur utama:**
  1. Sistem mendeteksi perubahan skema client.
  2. Data Access Agent melakukan re-analysis skema.
  3. Sistem memperbarui mapping yang terdampak di AIOS Internal Database.
  4. Sistem menampilkan pop-up perubahan skema dan meminta konfirmasi client.
  5. Client mengonfirmasi dan/atau mengedit mapping secara manual.
- **Post-condition:** Mapping diperbarui dan konsisten dengan skema terbaru.
- **Referensi:** FR-35, IDB-11, AC-20.

---

### D1 — Dashboard Pemakaian Token per Client

- **Tujuan:** Developer Ekasa memantau pemakaian token setiap akun client.
- **Actor:** Developer Ekasa (utama).
- **Deskripsi:** Developer Ekasa membuka domain portal monitoring
  (`developer.aios.*`) dan login sebagai developer. Dashboard menampilkan kolom
  input token, consumed token, dan metrik pemakaian lainnya dari tiap akun
  client (perusahaan yang memakai AIOS).
- **Pre-condition:** Developer Ekasa login (C2).
- **Alur utama:**
  1. Developer Ekasa masuk ke dashboard monitoring.
  2. Dashboard menampilkan pemakaian token (input dan consumed) per akun
     client.
- **Post-condition:** Developer Ekasa dapat memantau penggunaan client.
- **Referensi:** FR-30, IDB-27, AC-17.

---

### D2 — Analisis Penggunaan AI Manager

- **Tujuan:** Developer Ekasa melihat pola penggunaan AI Manager oleh client.
- **Actor:** Developer Ekasa (utama).
- **Deskripsi:** Dashboard menampilkan analisis penggunaan AI Manager terbanyak
  beserta persentasenya, dengan drill-down per bidang dan per worker.
- **Pre-condition:** Developer Ekasa login (C2); data pemakaian tercatat.
- **Alur utama:**
  1. Developer Ekasa membuka analisis penggunaan pada dashboard (portal
     monitoring `developer.aios.*`).
  2. Sistem menampilkan AI Manager yang paling banyak dipakai beserta
     persentasenya.
  3. Developer Ekasa dapat melakukan drill-down per bidang dan per worker.
- **Post-condition:** Developer Ekasa memperoleh gambaran penggunaan per
  bidang/worker.
- **Referensi:** FR-30, IDB-27, AC-17.

---

## 5. Proses Pendukung Internal (Bukan Use Case)

Proses berikut berjalan internal oleh sistem dan mendukung use case di atas:

1. **Pencatatan pemakaian token** — pada setiap pemanggilan LLM, sistem
   mencatat input token dan consumed token per tenant, per bidang, dan per
   worker untuk mendukung dashboard D1–D2 (IDB-27).
2. **Penyimpanan percakapan & memory** — riwayat percakapan dan ringkasan
   disimpan di AIOS Internal Database, di-tag per bidang (mendukung C13).
3. **Isolasi tenant** — data, percakapan, dan mapping milik Client A tidak
   pernah diakses oleh Client B (SEC-03).
4. **Keamanan kredensial** — kredensial koneksi database client disimpan aman
   pada AIOS Internal Database (connection metadata) dan tidak terekspos.
5. **Batasan akses Developer Ekasa** — Developer Ekasa hanya memiliki akses ke
   metrik pemakaian token; tidak memiliki akses ke data atau percakapan bisnis
   client.

---

## 6. Catatan

- **9 bidang selalu tersedia** untuk setiap client; jawaban sub-agents
  menyesuaikan data yang benar-benar tersedia pada database client.
- **RAG / dokumen di-defer** — penanganan dokumen (unggah file, sub-agent
  pembaca dokumen, tombol attach pada chat) berada di luar scope prototype ini
  dan dapat menjadi fase berikutnya.
- **Reset percakapan/memori** — mekanisme penghapusan riwayat chat dan memory
  belum tersedia pada prototype ini.
- **Pembayaran** dilakukan melalui payment gateway pada umumnya dan
  pengaktifan bersifat otomatis setelah pembayaran berhasil.
- **Portal terpisah** — Portal Client (`client.aios.*`) dan portal monitoring
  Developer Ekasa (`developer.aios.*`) berada di domain terpisah; role
  ditentukan oleh domain portal dan diverifikasi server-side, tanpa menu pilih
  role. Pemisahan domain tidak memisahkan database: AIOS Internal Database
  tetap satu (multi-tenant).
- **Business data tidak disalin** ke AIOS Internal Database; Client Database
  tetap menjadi source of truth (IDB-14 s.d. IDB-21). Database yang dibuat
  melalui opsi "buat database baru" (provisioning Ekasa) berperan sebagai
  Client Database, BUKAN bagian dari IDB, walau di-host di server Ekasa.
- **Caching query berulang** (keputusan sementara) — query identik berulang
  direncanakan memanfaatkan cache ber-TTL pendek per (tenant, bidang, hash
  pertanyaan); detail implementasi masih open discussion dan dapat berubah.
- **Low-confidence sub-agent analisis database** — terjadi pada konteks
  database adaptation (onboarding & perubahan skema); mekanisme penanganan
  yang user-friendly masih open discussion (lihat C6).
- Daftar job role sub-agents bersifat contoh & modular dan dapat disesuaikan
  melalui konfigurasi (Plugin Manager, FR-23 s.d. FR-26).
