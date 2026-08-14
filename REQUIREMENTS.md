# REQUIREMENTS.md — AIOS Plugin Platform

Sumber utama: `AGENTS.md`. Dokumen ini hanya berisi konsep yang didukung oleh
`AGENTS.md`. Kebutuhan yang tidak dapat ditentukan dari `AGENTS.md` ditandai
**TBD**.

---

## 1. Project Overview

AIOS adalah platform AI standalone (multi-tenant SaaS) yang di-host oleh Ekasa.
Setiap perusahaan client login ke workspace AIOS-nya sendiri; tidak ada yang
perlu dipasang atau di-embed di aplikasi client.

"Plugin" berarti AIOS beradaptasi ke sistem client yang sudah ada tanpa
mengharuskan client mengubah sistemnya.

Tujuannya adalah memberikan kemampuan AI khusus tanpa mengharuskan client untuk
memodifikasi atau membangun ulang aplikasi, database, autentikasi, atau logika
bisnis mereka.

Prinsip utama:

> **CLIENT SYSTEM STAYS. AIOS ADAPTS.**
> Piranti: Plug in → Adapt → Understand → Use

Proyek ini adalah **prototype** untuk memvalidasi konsep produk dan arsitektur
teknis. Prototype yang fungsional dan dapat didemonstrasikan secara end-to-end
lebih diprioritaskan daripada kompleksitas tingkat produksi.

AIOS terdiri dari komponen berikut:

- AIOS Interface
- AI Manager
- Plugin Manager
- Specialized Workers
- Tools
- Database Adapter
- Schema Extraction
- AI Schema Analyzer
- Canonical Data Model
- AIOS Data Layer
- AIOS Internal Database
- RAG / Document Pipeline
- Local LLM

---

## 1.5 Product Core Principles

Produk diukur terhadap empat prinsip inti (keputusan stakeholder; sumber:
`AGENTS.md` "Product Core Principles"):

- **Cost Efficient** — meminimalkan biaya operasional: satu model lokal yang
  dibagikan untuk semua cabang/worker, model tetap kecil, menghindari komputasi
  mahal yang berulang melalui caching ber-TTL pendek, dan tidak pernah
  menduplikasi business data client di AIOS Internal Database.
- **User Friendly** — client tidak perlu menangani detail teknis; interaksi
  menggunakan bahasa alami dan guided onboarding, serta langkah internal
  (adapter, analisis skema, mapping) tetap tersembunyi.
- **Plug and Go** — beradaptasi ke sistem existing client dengan usaha setup
  minimal; client yang tidak memiliki database mendapatkan database yang
  disediakan oleh Ekasa.
- **Fast** — database adaptation terjadi sekali saat integrasi/setup (bukan
  per request), query berulang memanfaatkan hasil cache, dan respons cepat.

Kaitan dengan requirements:

| Prinsip | Requirement terkait |
|---|---|
| Cost Efficient | NFR-02, NFR-03, IDB-14 s.d. IDB-21, DS-09, DS-11, LLM-04 |
| User Friendly | FR-06, FR-34, NFR-04, DS-10 |
| Plug and Go | FR-32A s.d. FR-32C, IR-01 s.d. IR-09, NFR-04, AC-01, AC-15 |
| Fast | DS-09, DS-11, DS-12, NFR-03 |

---

## 2. System Scope

AIOS dipandang seperti organisasi/perusahaan dengan 9 cabang bidang (modul
ERP): Strategic and Operational Planning, Finance, Human Resource, Logistic
Management, Maintenance Management, Sales and Distribution, Quality
Management, Material Management, Manufacturing. Setiap cabang dikepalai
oleh satu AI Manager yang mengelola dan mengoordinasikan Worker AI (job role)
pada bidangnya.

Model interaksi: AIOS **bukan** chatbot umum tunggal. Pengguna memilih
bidang (kapabilitas) terlebih dahulu, kemudian berinteraksi dengan AI
Manager (agent primary) beserta Worker AI-nya.

Alur umum:

```
User → Login (SaaS per perusahaan) → Home (9 bidang mengelilingi hub AIOS)
     → Pilih Bidang → AI Manager (agent primary) → Delegasi ke Worker (sub-agent)
     → Tools / Data / RAG → Response
```

Dalam lingkup sistem:

1. Pengguna login ke tenant perusahaannya (multi-tenant SaaS).
2. Pengguna dapat memilih AI Manager / kapabilitas spesifik dari AIOS
   Interface (Home: 9 bidang mengelilingi hub AIOS; hover menampilkan preview
   worker, bukan untuk diklik).
3. AI Manager mengelola dan mengoordinasikan Worker AI yang dipilih beserta
   kapabilitas yang dibutuhkan.
4. Worker AI melaksanakan tugas domain-spesifik.
5. AI Manager (agent primary) mendelegasikan tugas ke worker (sub-agent);
   proses delegasi transparan di interface.
6. Worker menggunakan tools dan data melalui abstraksi AIOS.
7. AIOS menggunakan Ollama sebagai runtime LLM (di server Ekasa pada
   prototype).
8. AIOS terhubung ke database client melalui Database Adapter.
9. AIOS menganalisis skema database client secara semantik dan memetakannya ke
   Canonical Data Model.
10. Worker beroperasi melalui Canonical Data Model, bukan skema raw client.
11. AIOS menangani pengetahuan berbasis dokumen (PDF/dokumen) melalui RAG.
12. Pengguna perusahaan harus menyelesaikan pembayaran sebelum dapat
    menggunakan kapabilitas AIOS (via payment gateway, aktivasi otomatis).
13. Ekasa Developer dapat memantau pemakaian token per perusahaan dengan
    drill-down per bidang dan per worker.
14. Alur lengkap dapat didemonstrasikan melalui interface.

Di luar lingkup awal: pengoptimalan model tingkat produksi, serta infrastruktur
tingkat produksi yang tidak mendukung prototype secara langsung.

---

## 3. Actors

- **Client** — perusahaan yang memakai AIOS (satu role; tidak ada pemisahan
  user/admin di dalam perusahaan). Registrasi akun, login, pembayaran,
  menghubungkan database perusahaannya, memilih bidang, berinteraksi dengan AI
  Manager dan worker melalui AIOS Interface, serta memvalidasi mapping
  perusahaannya sendiri. Tidak perlu memahami detail implementasi internal
  (database adapter, schema analyzer, canonical model, vector database, tools
  internal).
- **Ekasa Developer** — internal Ekasa yang hanya memantau pemakaian token per
  perusahaan (input dan consumed) dengan drill-down per bidang/worker. Tidak
  mengakses data bisnis atau percakapan client.
- **AI Manager** — "manager bidang" di AIOS. AIOS dipandang seperti organisasi
  dengan 9 cabang bidang (modul ERP), dan setiap cabang dikepalai oleh satu AI
  Manager: Strategic and Operational Planning, Finance, Human Resource,
  Logistic Management, Maintenance Management, Sales and Distribution, Quality
  Management, Material Management, Manufacturing. AI Manager mengelola dan
  mengoordinasikan Worker AI pada bidangnya. Actor pada use case yang
  menggambarkan pengelolaan/koordinasi worker.
- **Worker AI** — "bawahan" AI Manager yang meniru job role spesifik pada
  bidangnya (contoh Finance: Finance Staff, Financial Analyst, Budgeting Staff,
  Treasurer, CFO). Mengeksekusi tugas domain melalui abstraksi AIOS. Actor pada
  use case yang menggambarkan eksekusi tugas domain oleh worker.
- **Client System** — sistem existing milik client (aplikasi, database,
  autentikasi, logika bisnis) yang tetap menjadi sistem utama dan tidak
  dimodifikasi.
- **AIOS System** — platform AIOS standalone (SaaS) yang di-host Ekasa,
  terdiri dari AI Manager, Plugin Manager, Workers, Tools, Data Layer, RAG,
  dan runtime LLM (Ollama).
- **Developer / Intern** — pelaksana pengembangan yang bekerja secara
  bertahap dengan persetujuan sebelum setiap tahap.

---

## 4. Functional Requirements

### 4.1 Interface & User Interaction

- **FR-01** — AIOS harus menyediakan interface yang mengekspos kapabilitas/
  *workspace* yang berbeda-beda (bukan satu chatbot generik tunggal).
- **FR-02** — Home harus menyajikan 9 bidang yang mengelilingi hub "AIOS" di
  tengah: Strategic and Operational Planning, Finance, Human Resource, Logistic
  Management, Maintenance Management, Sales and Distribution, Quality
  Management, Material Management, Manufacturing.
- **FR-03** — Pengguna harus memilih bidang (kapabilitas) terlebih dahulu
  sebelum berinteraksi; hover pada sebuah bidang menampilkan preview daftar
  worker bidang tersebut (informasi saja, worker pada preview tidak dapat
  diklik).
- **FR-04** — Setelah memilih bidang, interface harus membuka tampilan chat
  dengan AI Manager bidang tersebut (agent primary), termasuk kotak saran dan
  panel kiri placeholder (mis. revenue, growth).
- **FR-05** — Interface harus memperjelas tujuan dari setiap bidang dan worker.
- **FR-06** — Detail implementasi internal (database adapter, schema analyzer,
  canonical model, vector database, tools internal) harus tersembunyi dari
  pengguna kecuali diperlukan untuk administrasi/debugging.
- **FR-07** — Alur lengkap (pemilihan kapabilitas → AI Manager → worker →
  respons) harus dapat didemonstrasikan melalui interface.

### 4.2 AI Manager

AIOS dipandang seperti organisasi dengan 9 cabang bidang (modul ERP). Setiap
cabang dikepalai oleh satu AI Manager yang mengelola dan mengoordinasikan
Worker AI (job role) pada bidangnya: Strategic and Operational Planning,
Finance, Human Resource, Logistic Management, Maintenance Management, Sales
and Distribution, Quality Management, Material Management, Manufacturing.

- **FR-08** — Setiap AI Manager harus menjadi orkestrator pusat untuk
  cabangnya dan mengelola Worker AI yang dipilih beserta kapabilitas yang
  dibutuhkannya.
- **FR-09** — AI Manager harus mengelola eksekusi worker.
- **FR-10** — AI Manager harus mengoordinasikan tools.
- **FR-11** — AI Manager harus mengelola konteks.
- **FR-12** — AI Manager harus berkomunikasi dengan Local LLM.
- **FR-13** — AI Manager harus mengoordinasikan banyak kapabilitas bila
  diperlukan.
- **FR-14** — AI Manager harus mengelola alur kerja AIOS secara keseluruhan.
- **FR-15** — AI Manager tidak boleh menebak/memilih worker sendiri; pilihan
  AI Manager/kapabilitas berasal dari pilihan pengguna di interface.
- **FR-16** — AI Manager tidak boleh menggantikan Worker AI; Worker AI tetap
  bertanggung jawab atas tugas domain-spesifik.

Catatan: AI Manager bertindak sebagai agent primary pada bidangnya — ia
berkomunikasi dengan pengguna dan mendelegasikan tugas domain-spesifik ke
worker (sub-agent). Proses delegasi transparan: interface dapat menampilkan
worker mana yang sedang dikonsultasikan.

### 4.3 Specialized Workers

- **FR-17** — Worker AI harus merupakan komponen AI domain-spesifik dengan
  tanggung jawab yang jelas.
- **FR-18** — Worker AI tidak boleh mengandung logika bisnis yang tidak
  berkaitan.
- **FR-19** — Worker AI dikelompokkan per cabang bidang dan meniru job role
  spesifik pada bidangnya (contoh, bukan daftar wajib; modular dan dapat
  disesuaikan melalui konfigurasi):
  - **Strategic and Operational Planning**: BI Analyst, Report Developer, Data
    Steward.
  - **Finance**: Finance Staff, Financial Analyst, Budgeting Staff, Treasurer,
    CFO.
  - **Human Resource**: HR Staff, Recruiter, Payroll Officer, Training
    Specialist, HR Manager.
  - **Logistic Management**: Logistics Coordinator, Shipping & Receiving
    Clerk, Fleet Manager.
  - **Maintenance Management**: Maintenance Planner, Reliability Engineer,
    Maintenance Technician.
  - **Sales and Distribution**: Sales Representative, Customer Service, Sales
    Data Analyst, Marketing Specialist.
  - **Quality Management**: Quality Inspector, Quality Engineer, Quality
    Auditor, Quality Control Officer.
  - **Material Management**: Procurement Staff, Senior Procurement Specialist,
    Purchasing Officer, Inventory Control Manager, Warehouse Inventory
    Manager, Retail Inventory Manager.
  - **Manufacturing**: Production Planner, Production Scheduler, Production
    Supervisor.
  - Daftar final worker dapat berubah selama pengembangan (**TBD**).
- **FR-20** — Worker AI harus menggunakan tools dan data melalui abstraksi
  AIOS.
- **FR-21** — Worker AI tidak boleh bergantung langsung pada skema database
  spesifik milik client.

### 4.4 Tools

- **FR-22** — Worker harus dapat menggunakan tools melalui abstraksi AIOS.

### 4.5 Plugin Manager

- **FR-23** — Plugin Manager harus mengelola plugin AIOS beserta kapabilitasnya.
- **FR-24** — Plugin Manager harus mendukung arsitektur modular agar worker dan
  kapabilitas dapat ditambahkan tanpa mendesain ulang inti AIOS.
- **FR-25** — Harus ada interface/kontrak yang jelas antara AI Manager, Plugin
  Manager, Workers, Tools, dan Data Layer.
- **FR-26** — Worker tidak boleh terkait erat (tight coupling) dengan
  implementasi AI Manager.

### 4.6 Autentikasi, Role, Pembayaran & Monitoring

- **FR-27** — AIOS adalah SaaS multi-tenant: setiap perusahaan login ke
  workspace-nya sendiri; data, metadata, dan mapping antar perusahaan harus
  terisolasi (tenant isolation).
- **FR-28** — Client harus registrasi akun sebelum login. AIOS harus memiliki
  autentikasi login sendiri (mis. email + password) dengan role: **Client** dan
  **Ekasa Developer**. AIOS harus menyediakan opsi keluar (logout) untuk
  mengakhiri sesi login Client maupun Developer Ekasa.
- **FR-29** — Client harus menyelesaikan pembayaran via payment gateway
  sebelum dapat menggunakan kapabilitas AIOS; aktivasi akun bersifat otomatis
  setelah pembayaran berhasil.
- **FR-30** — Ekasa Developer harus dapat memantau pemakaian token per
  perusahaan (input dan consumed) dengan drill-down per bidang dan per worker.
  Ekasa Developer tidak mengakses data bisnis atau percakapan client.
- **FR-31** — AI Manager bertindak sebagai agent primary pada bidangnya dan
  mendelegasikan tugas ke worker (sub-agent); proses delegasi transparan di
  interface.

### 4.7 Onboarding Data Client

- **FR-32** — Sebelum client dapat menggunakan AI Manager, database
  perusahaannya harus dihubungkan terlebih dahulu (onboarding gate).
- **FR-32A** — Koneksi database harus menyediakan 2 jalur pilihan: (1) client
  memasukkan kredensial database perusahaannya yang sudah ada, atau (2) client
  memilih opsi **buat database baru** yang disediakan oleh Ekasa (untuk client
  yang tidak memiliki database).
- **FR-32B** — Database yang dibuat melalui opsi "buat database baru"
  (provisioning) berperan sebagai **Client Database** (source of truth business
  data) meskipun di-host di server Ekasa; karena kredensialnya dibuat oleh AIOS
  sendiri, client tidak perlu mengisi form kredensial pada jalur ini.
- **FR-32C** — Opsi "buat database baru" harus mendukung 2 mode: (1) **template
  standar** Ekasa (skema + data contoh siap pakai), dan (2) **buat sendiri** di
  mana client menentukan tabel dan variabel/kolom yang dibutuhkannya.
- **FR-33** — Client harus dapat mengedit koneksi database perusahaannya dari
  menu kapan saja; perubahan koneksi memicu database adaptation ulang.
- **FR-34** — Hasil mapping skema harus ditampilkan kepada client di UI beserta
  tingkat confidence; client dapat mengonfirmasi mapping yang benar dan
  mengedit mapping secara manual. Mapping low-confidence ditandai untuk
  konfirmasi.
- **FR-35** — Jika skema client berubah, AIOS harus mendeteksi perubahan,
  melakukan re-adaptasi, dan menampilkan pop-up penjelasan perubahan skema
  dengan permintaan konfirmasi serta opsi edit manual.

> Catatan (TBD) — low-confidence pada analisis database (misalnya oleh AI
> Schema Analyzer / Data Access Agent) terjadi pada konteks **database
> adaptation saat onboarding dan saat perubahan skema**, bukan saat user
> sedang chat dengan AI Manager. Mekanisme penanganannya agar tetap
> user-friendly (tanpa memunculkan istilah teknis) masih **TBD / open
> discussion**.

### 4.8 Data Access Agent

- **FR-36** — Data Access Agent adalah specialized worker yang dibagikan per
  tenant (bukan per bidang); semua AI Manager pada tenant yang sama memakai
  Data Access Agent yang sama.
- **FR-37** — Data Access Agent harus menghubungkan dan memahami skema database
  client (database adaptation), serta membangun dan mempersistenkan semantic
  mapping di AIOS Internal Database (termasuk mapping version, confidence, dan
  validation status).
- **FR-38** — Data Access Agent harus menyediakan business data aktual kepada
  worker lain melalui AIOS Data Layer / Canonical Data Model, menjaga Client
  Database sebagai source of truth, dan melakukan re-adaptasi ketika skema
  client berubah.

### 4.9 Memory Agent

- **FR-39** — Setiap AI Manager memiliki Memory Agent (satu per bidang) yang
  merangkum percakapan sebelumnya dengan client.
- **FR-40** — Pesan percakapan dan ringkasan disimpan di AIOS Internal
  Database, di-tag per bidang, sehingga AI Manager mempertahankan konteks
  lintas sesi chat.

---

## 5. Non-Functional Requirements

- **NFR-01** — SaaS: AIOS berjalan di server Ekasa (multi-tenant); data
  perusahaan mengalir ke server Ekasa pada prototype.
- **NFR-02** — Model sederhana: prototype harus memakai model AI yang sederhana.
  (Model LLM spesifik: **TBD**.)
- **NFR-03** — Performa wajar: prototype harus memberikan performa yang wajar.
  (Target performa spesifik: **TBD**.)
  - Keputusan sementara (dapat berubah): query berulang memanfaatkan **cache
    ber-TTL pendek** yang dikunci per (tenant, bidang, hash pertanyaan) —
    mendukung prinsip Cost Efficient dan Fast. Detail implementasi masih **TBD**.
- **NFR-04** — Setup mudah: setup/instalasi harus mudah dilakukan.
- **NFR-05** — Dapat didemonstrasikan: alur end-to-end harus mudah
  didemonstrasikan.
- **NFR-06** — Modularitas: komponen (AI Manager, Plugin Manager, Worker, Tool,
  Data Layer) harus modular dan dapat dipisahkan.
- **NFR-07** — Maintainability: prototype harus readable, maintainable,
  menghindari abstraksi yang tidak perlu, dan menghindari premature
  optimization.
- **NFR-08** — Extensibility: worker dan kapabilitas baru harus dapat ditambahkan
  tanpa mendesain ulang inti AIOS.
- **NFR-09** — Adaptability: AIOS tidak boleh memiliki asumsi hardcoded tentang
  struktur database client; harus bekerja pada berbagai struktur yang sangat
  berbeda.

---

## 6. System Constraints

- **C-01** — Lingkup prototype: utamakan prototype fungsional yang
  dapat didemonstrasikan end-to-end di atas kompleksitas tingkat produksi.
- **C-02** — Runtime LLM: gunakan Ollama sebagai runtime model; pada prototype
  berjalan di server Ekasa.
- **C-03** — Jangan over-engineer model AI; pengoptimalan model tingkat produksi
  berada di luar scope awal.
- **C-04** — AIOS tidak boleh mengharuskan client mengubah sistemnya.
- **C-05** — AIOS memiliki autentikasi sendiri (login per perusahaan dengan
  role) karena deployment SaaS; ini merupakan kebutuhan eksplisit, bukan
  pengganti autentikasi aplikasi client.
- **C-06** — Jangan melewatkan dependensi arsitektural demi mencapai UI lebih
  cepat.
- **C-07** — Urutan pengembangan mengikuti prioritas: AIOS Core, AI Manager,
  Plugin Manager, Worker architecture, Local LLM integration, Database Adapter,
  Schema Extraction, AI Schema Analyzer, Canonical Data Model, AIOS Data Layer,
  Worker-to-data integration, RAG / Document Worker, Interface, Multi-client
  simulation, End-to-end testing, Optimization and documentation.
- **C-08** — Metode kerja: selalu minta persetujuan sebelum tahap/tugas baru;
  bekerja inkremental; selesaikan satu tahap lalu laporkan sebelum tahap
  berikutnya.

---

## 7. Integration Requirements

- **IR-01** — AIOS harus beradaptasi ke sistem client (aspek "plugin"); aplikasi
  dan database client tetap tidak dimodifikasi. Deployment AIOS adalah SaaS
  standalone dengan domain dan login sendiri.
- **IR-02** — AIOS tidak boleh mengharuskan client mengganti aplikasi existing.
- **IR-03** — AIOS tidak boleh mengharuskan client mendesain ulang database.
- **IR-04** — AIOS tidak boleh mengharuskan client mengganti nama tabel.
- **IR-05** — AIOS tidak boleh mengharuskan client mengganti nama kolom.
- **IR-06** — AIOS tidak boleh mengharuskan client mengganti sistem autentikasi.
- **IR-07** — AIOS tidak boleh mengharuskan client migrasi logika bisnis ke AIOS.
- **IR-08** — AIOS memiliki autentikasi sendiri (login per perusahaan) karena
  deployment SaaS; hal ini tidak menggantikan sistem autentikasi aplikasi
  client itu sendiri.
- **IR-09** — Prototype harus menunjukkan bahwa AIOS dapat beradaptasi ke
  sistem-sistem existing yang berbeda dengan modifikasi minimal pada sistem
  client.

---

## 8. Data & Schema Adaptation Requirements

- **DS-01** — AIOS harus mendukung client database dengan struktur yang sangat
  berbeda, termasuk perbedaan nama tabel, nama kolom, tipe kolom, relasi,
  organisasi tabel, konvensi penamaan, representasi data, engine database
  (**TBD**: engine spesifik), dan makna semantik field.
- **DS-02** — AIOS tidak boleh mengasumsikan adaptasi database hanya sebatas
  memetakan nama kolom yang berbeda.
- **DS-03** — Schema Extraction harus mengekstrak metadata skema dari database
  client.
- **DS-04** — AI Schema Analyzer harus menganalisis skema client secara
  semantik, bukan hanya berdasarkan nama.
- **DS-05** — AI Schema Analyzer harus mempertimbangkan tables, columns, data
  types, relationships, constraints, sample values, naming patterns, dan
  semantic meaning.
- **DS-06** — Sistem harus memetakan pemahaman skema client ke Canonical Data
  Model secara semantik (semantic mapping).
- **DS-07** — Canonical Data Model harus menyediakan representasi semantik yang
  ternormalisasi sehingga worker bekerja dengan konsep, bukan nama
  tabel/kolom spesifik client.
- **DS-08** — Konsep setara dari client yang berbeda (contoh: `products`
  (`product_name`, `stock`) vs `barang` (`kode`, `nama`, `tersedia`)) harus
  dipetakan ke konsep canonical yang sama (contoh: `Product.name`,
  `Product.stock`).
- **DS-09** — Database adaptation harus terutama terjadi saat integrasi/setup
  AIOS, bukan dari nol untuk setiap query pengguna.
- **DS-10** — Sistem harus menghasilkan pemahaman/pemetaan client database yang
  dapat digunakan ulang.
- **DS-11** — Analisis skema lengkap tidak boleh diulang untuk setiap permintaan
  user normal kecuali diminta eksplisit.
- **DS-12** — Database Adapter harus menyediakan cara yang konsisten bagi AIOS
  untuk berinteraksi dengan sistem database yang berbeda.
- **DS-13** — Database Adapter harus menyembunyikan detail implementasi spesifik
  database dari worker apabila praktis.
- **DS-14** — Worker harus beroperasi terutama melalui canonical model atau
  abstraksi data AIOS.
- **DS-15** — Worker tidak boleh bergantung langsung pada struktur database raw
  client.
- **DS-16** — Sistem harus dapat mendemonstrasikan adaptasi terhadap beberapa
  struktur database client yang berbeda.

---

## 9. RAG Requirements

> **Prototype scope:** RAG / document handling is deferred in the prototype.
> The prototype focuses on structured data from the Client Database; document
> handling (RAG) may be added in a later phase. Requirements RAG-01 s.d.
> RAG-03 below describe the target design and do not block the prototype.

- **RAG-01** — AIOS harus menyediakan pipeline RAG untuk dokumen tak
  terstruktur (PDF/Dokumen) dengan alur: Parser → Chunking → Embedding →
  Vector Store → Retrieval → Document Worker.
- **RAG-02** — Pipeline RAG harus terpisah secara konseptual dari database
  schema adaptation; keduanya tidak boleh dicampur menjadi satu proses
  konseptual.
- **RAG-03** — Sebuah worker harus dapat menggunakan data terstruktur dan
  dokumen sekaligus bila tugas membutuhkan keduanya.
- **RAG-04** — Detail implementasi vector store/embedding: **TBD**.

---

## 10. AI / Local LLM Requirements

- **LLM-01** — Prototype menggunakan Ollama sebagai runtime LLM; pada deployment
  SaaS, Ollama berjalan di server Ekasa sehingga data perusahaan mengalir ke
  server Ekasa (trade-off yang diterima untuk prototype).
- **LLM-02** — AIOS harus menggunakan Ollama sebagai runtime model.
- **LLM-03** — AI Manager, Workers, dan AI Schema Analyzer harus menggunakan
  Local LLM.
- **LLM-04** — Prototype harus memprioritaskan: model sederhana, performa wajar,
  setup mudah, dan demonstrabilitas.
- **LLM-05** — Model LLM spesifik yang digunakan: **TBD** (runtime ditetapkan
  Ollama; nama model belum ditetapkan oleh `AGENTS.md`).
  - Catatan diskusi: keluarga **Hermes** (Nous Research) dapat berjalan lokal via
    Ollama (mis. `hermes3`; varian Hermes 4/4-Pro juga tersedia). Banyak token
    tidak menjadi masalah biaya pada model lokal; kendala utama adalah
    **memori/VRAM model yang mengendap saat tersimpan di RAM** dan dampaknya ke
    server (prinsip Cost Efficient → utamakan satu model kecil bersama untuk
    semua cabang/worker). Keputusan final tetap **TBD**, ditentukan pada tahap
    Local LLM integration.

---

## 11. Plugin & Worker Requirements

- **PW-01** — AIOS harus dirancang sebagai plugin; aplikasi client tetap menjadi
  sistem utama.
- **PW-02** — Plugin Manager harus mengelola plugin AIOS dan kapabilitasnya.
- **PW-03** — Plugin Manager harus mendukung arsitektur modular sehingga worker
  dan kapabilitas dapat ditambahkan tanpa mendesain ulang inti AIOS.
- **PW-04** — Worker tidak boleh terkait erat dengan implementasi AI Manager.
- **PW-05** — Harus ada interface/kontrak yang jelas antara AI Manager, Plugin
  Manager, Workers, Tools, dan Data Layer.
- **PW-06** — Worker harus domain-spesifik, memiliki tanggung jawab jelas, dan
  tidak mengandung logika bisnis yang tidak berkaitan.
- **PW-07** — Worker harus menggunakan tools dan data melalui abstraksi AIOS,
  bukan akses database langsung.
- **PW-08** — Worker tidak boleh bergantung pada skema database spesifik client.

---

## 12. Authentication & Security Boundary

- **SEC-01** — AIOS memiliki autentikasi login sendiri (per perusahaan) dengan
  role: Client dan Ekasa Developer. Siklus sesi mencakup login dan logout.
- **SEC-02** — Autentikasi AIOS tidak menggantikan sistem autentikasi aplikasi
  client; sistem client tetap berfungsi seperti sebelumnya.
- **SEC-03** — Data, metadata, dan mapping antar perusahaan harus terisolasi
  (tenant isolation); akses hanya dalam lingkup tenant yang sedang login.
- **SEC-04** — Pada prototype, data perusahaan mengalir ke server Ekasa (SaaS);
  kebijakan privasi/keamanan produksi: **TBD**.
- **SEC-05** — Worker tidak boleh mengakses database langsung; akses data harus
  melalui AIOS Data Layer / Database Adapter / canonical model.
- **SEC-06** — Detail autentikasi SaaS (login, sesi, role, dan tenant
  isolation): **TBD**.

---

## 13. Internal Database Requirements

Internal Database (IDB) adalah persistent storage milik AIOS untuk metadata,
konfigurasi, mapping, dan state yang diperlukan AIOS. IDB memungkinkan AIOS
menyimpan pengetahuan tentang setiap integrasi client dan menghindari analisis
skema lengkap yang berulang.

Alur utama:

```
Client DB → Schema Extraction → AI Schema Analyzer → Semantic Mapping
         → Internal DB → AIOS Data Layer / Canonical Model → Worker
```

### 13.1 Fungsi Persistent Storage

IDB berfungsi sebagai persistent storage AIOS untuk 4 kategori:

1. **Client / Integration**
   - client metadata
   - integration & connection metadata

2. **Schema Intelligence**
   - schema metadata
   - hasil analisis Schema Extraction / AI Schema Analyzer
   - semantic/schema mapping
   - mapping configuration
   - version/status/confidence (bila diperlukan)

3. **Plugin / Worker**
   - plugin metadata
   - worker/tool configuration

4. **AIOS Persistent State**
   - configuration dan state AIOS yang memang membutuhkan persistence

### 13.2 Functional Requirements

- **IDB-01** — IDB harus menyimpan client metadata untuk setiap integrasi
  client.
- **IDB-02** — IDB harus menyimpan integration & connection metadata.
- **IDB-03** — IDB harus menyimpan schema metadata.
- **IDB-04** — IDB harus menyimpan hasil analisis Schema Extraction / AI Schema
  Analyzer bila berguna.
- **IDB-05** — IDB harus menyimpan semantic/schema mapping dan mapping
  configuration.
- **IDB-06** — IDB harus mendukung penyimpanan mapping version, mapping status,
  dan mapping confidence bila diperlukan.
- **IDB-07** — IDB harus menyimpan plugin metadata.
- **IDB-08** — IDB harus menyimpan worker/tool configuration.
- **IDB-09** — IDB harus menyimpan configuration dan state AIOS yang memang
  membutuhkan persistence.
- **IDB-10** — IDB harus mendukung persistence schema mapping sehingga AIOS tidak
  perlu melakukan analisis skema lengkap ulang setiap restart atau request
  normal.
- **IDB-11** — Jika skema client berubah, AIOS harus dapat mendeteksi perubahan,
  melakukan re-analysis, atau memperbarui mapping yang terdampak.
- **IDB-12** — Skema IDB harus diturunkan dari kebutuhan fungsional aktual;
  tidak boleh membuat tabel/entitas yang tidak perlu.
- **IDB-13** — Implementasi teknis IDB (engine, ERD, tabel, migration): **TBD**.

### 13.3 Data Boundary

- **IDB-14** — Client Database tetap menjadi source of truth untuk business data
  client.
- **IDB-15** — IDB TIDAK boleh menyimpan atau menyalin seluruh business data
  client; IDB bukan pengganti Client Database.
- **IDB-16** — IDB hanya menyimpan metadata, mapping, configuration, dan state
  yang diperlukan AIOS.
- **IDB-17** — IDB tidak boleh menjadi salinan (copy) dari business database
  client.
- **IDB-18** — Business data tidak boleh disimpan di IDB hanya untuk mempermudah
  implementasi worker.
- **IDB-19** — Canonical Data Model bukan database bisnis; ia merupakan lapisan
  abstraksi, bukan salinan database client.
- **IDB-20** — Worker mengambil business data dari Client Database melalui AIOS
  Data Layer / Database Adapter, bukan dari IDB.
- **IDB-21** — IDB tidak digunakan sebagai sumber utama business data client.

> Catatan boundary provisioning (FR-32A s.d. FR-32C) — Database yang dibuat
> melalui opsi "buat database baru" oleh Ekasa berperan sebagai **Client
> Database** (source of truth business data), BUKAN bagian dari AIOS Internal
> Database. IDB-14 s.d. IDB-21 tetap berlaku penuh untuk database tersebut.
> Secara implementasi, database provisioning boleh berjalan pada engine/mesin
> yang sama dengan IDB (misal di server Ekasa), tetapi keduanya tetap
> merupakan database/schema yang terpisah secara logis.

### 13.4 Multi-Client Requirements

- **IDB-22** — IDB harus mendukung beberapa konfigurasi client secara independen.
- **IDB-23** — Metadata dan mapping milik tiap client harus terisolasi secara
  logis.
- **IDB-24** — Mapping yang dimiliki Client A tidak boleh digunakan untuk
  mengakses Client B.
- **IDB-25** — Setiap client dapat memiliki skema yang sangat berbeda; IDB harus
  menyimpan pemahaman/mapping yang spesifik untuk masing-masing client.
- **IDB-26** — Mapping yang sudah dianalisis dapat digunakan kembali tanpa
  analisis ulang setiap request.
- **IDB-27** — IDB harus menyimpan data pemakaian (usage/token metering) per
  perusahaan, bidang, dan worker untuk mendukung dashboard Ekasa Developer.

---

## 14. Out of Scope / Non-Goals

- **OS-01** — Bukan chatbot generik umum; AIOS mengekspos kapabilitas/worker
  spesifik.
- **OS-02** — Bukan pengganti sistem client (aplikasi, database, autentikasi,
  logika bisnis tetap milik client).
- **OS-03** — Tidak mengharuskan client mengganti aplikasi, mendesain ulang
  database, mengganti nama tabel/kolom, mengganti autentikasi, atau memigrasi
  logika bisnis.
- **OS-04** — Autentikasi AIOS (login per perusahaan) bukan pengganti sistem
  autentikasi aplikasi client; aplikasi client tetap memakai autentikasinya
  sendiri.
- **OS-05** — Prototype menerima trade-off data perusahaan mengalir ke server
  Ekasa (SaaS); opsi LLM/deployment per perusahaan menjadi pertimbangan fase
  berikutnya.
- **OS-06** — Bukan worker yang bergantung langsung pada skema database client
  atau akses database langsung.
- **OS-07** — Bukan pengoptimalan/perawatan model tingkat produksi.
- **OS-08** — Tidak menambahkan infrastruktur tingkat produksi kecuali
  mendukung prototype secara langsung.
- **OS-09** — Tidak melakukan analisis skema lengkap berulang untuk setiap
  permintaan user normal.
- **OS-10** — AI Manager tidak menebak/memilih worker sendiri.
- **OS-11** — Proyek adalah prototype untuk validasi konsep, bukan produk
  production-ready.
- **OS-12** — RAG / penanganan dokumen di-defer pada prototype; prototype fokus
  pada data terstruktur dari Client Database.

---

## 15. Acceptance Criteria

Prototype AIOS dinyatakan berhasil jika seluruh kriteria berikut dapat
ditunjukkan:

- **AC-01** — AIOS dapat beradaptasi ke sistem client existing (aspek plugin)
  sebagai SaaS standalone tanpa mengubah sistem client.
- **AC-02** — Pengguna dapat memilih kapabilitas AI yang spesifik melalui
  interface.
- **AC-03** — AI Manager dapat mengelola worker yang dipilih.
- **AC-04** — Worker dapat melaksanakan tugas domain-spesifik.
- **AC-05** — AIOS dapat menggunakan Local LLM melalui Ollama.
- **AC-06** — AIOS dapat terhubung ke database client melalui adapter.
- **AC-07** — AI dapat menganalisis skema database client.
- **AC-08** — Struktur database yang berbeda dapat dipetakan ke canonical model.
- **AC-09** — Worker dapat beroperasi melalui canonical model, bukan skema raw
  client.
- **AC-10** — AIOS dapat menangani pengetahuan berbasis dokumen melalui RAG.
  (Deferred pada prototype; prototype fokus pada data terstruktur.)
- **AC-11** — Beberapa struktur database client dapat didemonstrasikan.
- **AC-12** — Alur lengkap dapat didemonstrasikan melalui interface.
- **AC-13** — Testing menggunakan beberapa simulated client system dengan skema
  yang sangat berbeda (meliputi nama tabel, nama kolom, relasi, representasi
  data, dan engine database bila praktis).
- **AC-14** — Testing mencakup schema understanding, semantic mapping, canonical
  model generation, worker queries, incorrect/ambiguous mappings, dan error
  handling.
- **AC-15** — Sistem client tidak perlu didesain ulang agar AIOS dapat bekerja
  (sistem client tetap, AIOS beradaptasi).
- **AC-16** — Pengguna dapat registrasi dan login per perusahaan (multi-tenant)
  dengan role-based access (Client dan Ekasa Developer); data antar perusahaan
  terisolasi.
- **AC-17** — Ekasa Developer dapat memantau pemakaian token per perusahaan
  dengan drill-down per bidang dan per worker.
- **AC-18** — Client harus menyelesaikan pembayaran sebelum menggunakan
  kapabilitas AIOS (via payment gateway, aktivasi otomatis).
- **AC-19** — Sebelum menggunakan AI Manager, client harus menghubungkan
  database perusahaannya dan memvalidasi hasil mapping di UI (confidence,
  konfirmasi, edit manual).
- **AC-20** — Data Access Agent (per tenant) menyediakan business data aktual
  kepada worker lain melalui canonical model, dan melakukan re-adaptasi saat
  skema berubah (dengan pop-up konfirmasi).
- **AC-21** — Memory Agent (per bidang) menyimpan percakapan dan ringkasan di
  AIOS Internal Database sehingga AI Manager mempertahankan konteks lintas sesi.

---

## 16. Referensi Use Case

Pemetaan use case (sesuai `docs/use-case-description.md`) terhadap requirement
di atas. Referensi use case tidak menambah requirement baru; ia hanya mengikat
requirement yang sudah ada ke use case yang menggambarkannya.

| Use Case | Nama | Requirement terkait |
|---|---|---|
| C1 | Registrasi Akun | FR-27, FR-28, SEC-01, SEC-03, AC-16 |
| C2 | Login (Pilih Role) | FR-27, FR-28, SEC-01, SEC-03, AC-16 |
| C3 | Pembayaran | FR-29, AC-18 |
| C4 | Menghubungkan Database Perusahaan | FR-32, FR-32A, FR-32B, FR-32C, IR-01 s.d. IR-09, SEC-03, IDB-01, IDB-02, AC-01, AC-15 |
| C5 | Menganalisis Skema & Membuat Mapping | DS-01 s.d. DS-11, LLM-03, FR-37, IDB-03 s.d. IDB-06, IDB-10, IDB-26, AC-06, AC-07, AC-08 |
| C6 | Memvalidasi Hasil Mapping | FR-34, DS-06, DS-07, IDB-05, IDB-06, AC-19 |
| C7 | Mengedit Koneksi Database | FR-33, IR-01 s.d. IR-09, IDB-01, IDB-02 |
| C8 | Memilih Bidang ERP | FR-01, FR-02, FR-03, FR-04, OS-01, OS-10 |
| C9 | Chat dengan AI Primary Agent | FR-04 s.d. FR-07, FR-31, LLM-02, LLM-03, AC-12 |
| C10 | AI Primary Mendelegasikan Pertanyaan | FR-08 s.d. FR-16, FR-31, OS-10, PW-04 |
| C11 | Sub-agents Menjawab Tugas Domain | FR-17 s.d. FR-22, LLM-02, LLM-03, AC-04 |
| C12 | Data Access Agent Menyediakan Data Client | FR-36, FR-38, DS-12 s.d. DS-15, SEC-05, IDB-14 s.d. IDB-21, AC-20 |
| C13 | Memory Agent Merangkum Percakapan | FR-39, FR-40, IDB-09, AC-21 |
| C14 | Re-adaptasi Mapping saat Skema Berubah | FR-35, IDB-11, AC-20 |
| D1 | Dashboard Pemakaian Token per Client | FR-30, IDB-27, AC-17 |
| D2 | Analisis Penggunaan AI Manager | FR-30, IDB-27, AC-17 |