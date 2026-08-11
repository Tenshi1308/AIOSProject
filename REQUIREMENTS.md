# REQUIREMENTS.md — AIOS Plugin Platform

Sumber utama: `AGENTS.md`. Dokumen ini hanya berisi konsep yang didukung oleh
`AGENTS.md`. Kebutuhan yang tidak dapat ditentukan dari `AGENTS.md` ditandai
**TBD**.

---

## 1. Project Overview

AIOS adalah platform AI lokal yang dirancang untuk diintegrasikan ke dalam
sistem perangkat lunak perusahaan yang sudah ada (client) sebagai **plugin**.

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

## 2. System Scope

AIOS dipandang seperti organisasi/perusahaan dengan 9 cabang bidang (modul
ERP): Finance, Human Resources, Sales / CRM, Procurement, Inventory,
Production, Logistics, Maintenance, Reporting / BI. Setiap cabang dikepalai
oleh satu AI Manager yang mengelola dan mengoordinasikan Worker AI (job role)
pada bidangnya.

Model interaksi: AIOS **bukan** chatbot umum tunggal. Pengguna memilih
AI Manager/kapabilitas terlebih dahulu, kemudian berinteraksi dengan AI
Manager beserta Worker AI-nya.

Alur umum:

```
User → AIOS Interface → Select Capability (AI Manager) → AI Manager
      → Selected Worker (Worker AI) → Tools / Data / RAG → Response
```

Dalam lingkup sistem:

1. Pengguna dapat memilih AI Manager / kapabilitas spesifik dari AIOS
   Interface.
2. AI Manager mengelola dan mengoordinasikan Worker AI yang dipilih beserta
   kapabilitas yang dibutuhkan.
3. Worker AI melaksanakan tugas domain-spesifik.
4. Worker menggunakan tools dan data melalui abstraksi AIOS.
5. AIOS menggunakan Local LLM (Ollama).
6. AIOS terhubung ke database client melalui Database Adapter.
7. AIOS menganalisis skema database client secara semantik dan memetakannya ke
   Canonical Data Model.
8. Worker beroperasi melalui Canonical Data Model, bukan skema raw client.
9. AIOS menangani pengetahuan berbasis dokumen (PDF/dokumen) melalui RAG.
10. Alur lengkap dapat didemonstrasikan melalui interface.

Di luar lingkup awal: pengoptimalan model tingkat produksi, serta infrastruktur
tingkat produksi yang tidak mendukung prototype secara langsung.

---

## 3. Actors

- **User** — pengguna akhir yang memilih kapabilitas dan berinteraksi dengan
  worker melalui AIOS Interface. Pengguna tidak perlu memahami detail
  implementasi internal (database adapter, schema analyzer, canonical model,
  vector database, tools internal).
- **AI Manager** — "manager bidang" di AIOS. AIOS dipandang seperti organisasi
  dengan 9 cabang bidang (modul ERP), dan setiap cabang dikepalai oleh satu AI
  Manager: Finance, Human Resources, Sales / CRM, Procurement, Inventory,
  Production, Logistics, Maintenance, Reporting / BI. AI Manager mengelola dan
  mengoordinasikan Worker AI pada bidangnya. Actor pada use case yang
  menggambarkan pengelolaan/koordinasi worker.
- **Worker AI** — "bawahan" AI Manager yang meniru job role spesifik pada
  bidangnya (contoh Finance: Finance Staff, Financial Analyst, Budgeting Staff,
  Treasurer, CFO). Mengeksekusi tugas domain melalui abstraksi AIOS. Actor pada
  use case yang menggambarkan eksekusi tugas domain oleh worker.
- **Client System** — sistem existing milik client (aplikasi, database,
  autentikasi, logika bisnis) yang tetap menjadi sistem utama dan tidak
  dimodifikasi.
- **AIOS System** — platform plugin AIOS (AI Manager, Plugin Manager, Workers,
  Tools, Data Layer, RAG, Local LLM) yang menempel di atas sistem client.
- **Developer / Intern** — pelaksana pengembangan yang bekerja secara
  bertahap dengan persetujuan sebelum setiap tahap.

---

## 4. Functional Requirements

### 4.1 Interface & User Interaction

- **FR-01** — AIOS harus menyediakan interface yang mengekspos kapabilitas/
  *workspace* yang berbeda-beda (bukan satu chatbot generik tunggal).
- **FR-02** — Interface harus menyajikan entry AI Manager/kapabilitas yang
  berbeda, misalnya Finance, Human Resources, Sales / CRM, Procurement,
  Inventory, Production, Logistics, Maintenance, Reporting / BI.
- **FR-03** — Pengguna harus memilih kapabilitas/worker terlebih dahulu sebelum
  berinteraksi.
- **FR-04** — Setelah memilih kapabilitas, interface harus membuka workspace
  worker yang sesuai sehingga pengguna dapat berinteraksi dengan worker tersebut.
- **FR-05** — Interface harus memperjelas tujuan dari setiap worker.
- **FR-06** — Detail implementasi internal (database adapter, schema analyzer,
  canonical model, vector database, tools internal) harus tersembunyi dari
  pengguna kecuali diperlukan untuk administrasi/debugging.
- **FR-07** — Alur lengkap (pemilihan kapabilitas → AI Manager → worker →
  respons) harus dapat didemonstrasikan melalui interface.

### 4.2 AI Manager

AIOS dipandang seperti organisasi dengan 9 cabang bidang (modul ERP). Setiap
cabang dikepalai oleh satu AI Manager yang mengelola dan mengoordinasikan
Worker AI (job role) pada bidangnya: Finance, Human Resources, Sales / CRM,
Procurement, Inventory, Production, Logistics, Maintenance, Reporting / BI.

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

### 4.3 Specialized Workers

- **FR-17** — Worker AI harus merupakan komponen AI domain-spesifik dengan
  tanggung jawab yang jelas.
- **FR-18** — Worker AI tidak boleh mengandung logika bisnis yang tidak
  berkaitan.
- **FR-19** — Worker AI dikelompokkan per cabang bidang dan meniru job role
  spesifik pada bidangnya (contoh, bukan daftar wajib; modular dan dapat
  disesuaikan melalui konfigurasi):
  - **Finance**: Finance Staff, Financial Analyst, Budgeting Staff, Treasurer,
    CFO.
  - **Human Resources**: HR Staff, Recruiter, Payroll Officer, Training
    Specialist, HR Manager.
  - **Sales / CRM**: Sales Representative, Customer Service, Sales Data
    Analyst, Marketing Specialist.
  - **Procurement**: Procurement Staff, Senior Procurement Specialist,
    Purchasing Officer.
  - **Inventory**: Inventory Control Manager, Warehouse Inventory Manager,
    Retail Inventory Manager.
  - **Production**: Production Planner, Production Scheduler, Production
    Supervisor.
  - **Logistics**: Logistics Coordinator, Shipping & Receiving Clerk, Fleet
    Manager.
  - **Maintenance**: Maintenance Planner, Reliability Engineer, Maintenance
    Technician.
  - **Reporting / BI**: BI Analyst, Report Developer, Data Steward.
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

---

## 5. Non-Functional Requirements

- **NFR-01** — Eksekusi lokal: AIOS harus berjalan sepenuhnya secara lokal
  (tanpa ketergantungan cloud).
- **NFR-02** — Model sederhana: prototype harus memakai model AI yang sederhana.
  (Model LLM spesifik: **TBD**.)
- **NFR-03** — Performa wajar: prototype harus memberikan performa yang wajar.
  (Target performa spesifik: **TBD**.)
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
- **C-02** — AI lokal: gunakan Ollama sebagai runtime model lokal kecuali ada
  kebutuhan proyek yang secara eksplisit mengubahnya.
- **C-03** — Jangan over-engineer model AI; pengoptimalan model tingkat produksi
  berada di luar scope awal.
- **C-04** — AIOS tidak boleh mengharuskan client mengubah sistemnya.
- **C-05** — Jangan memperkenalkan lapisan autentikasi JWT terpisah untuk AIOS
  kecuali diminta eksplisit oleh kebutuhan di masa depan.
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

- **IR-01** — AIOS harus dirancang sebagai plugin; aplikasi client tetap menjadi
  sistem utama.
- **IR-02** — AIOS tidak boleh mengharuskan client mengganti aplikasi existing.
- **IR-03** — AIOS tidak boleh mengharuskan client mendesain ulang database.
- **IR-04** — AIOS tidak boleh mengharuskan client mengganti nama tabel.
- **IR-05** — AIOS tidak boleh mengharuskan client mengganti nama kolom.
- **IR-06** — AIOS tidak boleh mengharuskan client mengganti sistem autentikasi.
- **IR-07** — AIOS tidak boleh mengharuskan client migrasi logika bisnis ke AIOS.
- **IR-08** — AIOS harus terintegrasi dengan environment client yang sudah
  terautentikasi.
- **IR-09** — Prototype harus menunjukkan bahwa AIOS dapat diintegrasikan ke
  sistem-sistem existing yang berbeda dengan modifikasi minimal.

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

- **LLM-01** — AIOS harus menggunakan arsitektur AI lokal untuk prototype karena
  data perusahaan dapat bersifat sensitif.
- **LLM-02** — AIOS harus menggunakan Ollama sebagai runtime model lokal.
- **LLM-03** — AI Manager, Workers, dan AI Schema Analyzer harus menggunakan
  Local LLM.
- **LLM-04** — Prototype harus memprioritaskan: eksekusi lokal, model sederhana,
  performa wajar, setup mudah, dan demonstrabilitas.
- **LLM-05** — Model LLM spesifik yang digunakan: **TBD** (runtime ditetapkan
  Ollama; nama model belum ditetapkan oleh `AGENTS.md`).

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

- **SEC-01** — Autentikasi pengguna tetap menjadi tanggung jawab sistem
  autentikasi existing milik client.
- **SEC-02** — AIOS harus terintegrasi dengan environment client yang sudah
  terautentikasi.
- **SEC-03** — AIOS tidak boleh memperkenalkan lapisan autentikasi JWT terpisah
  kecuali diminta eksplisit oleh kebutuhan di masa depan.
- **SEC-04** — AIOS harus berjalan lokal untuk menjaga keamanan/privasi data
  perusahaan yang sensitif.
- **SEC-05** — Worker tidak boleh mengakses database langsung; akses data harus
  melalui AIOS Data Layer / Database Adapter / canonical model.
- **SEC-06** — Detail autentikasi integrasi spesifik dengan system client:
  **TBD**.

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

---

## 14. Out of Scope / Non-Goals

- **OS-01** — Bukan chatbot generik umum; AIOS mengekspos kapabilitas/worker
  spesifik.
- **OS-02** — Bukan pengganti sistem client (aplikasi, database, autentikasi,
  logika bisnis tetap milik client).
- **OS-03** — Tidak mengharuskan client mengganti aplikasi, mendesain ulang
  database, mengganti nama tabel/kolom, mengganti autentikasi, atau memigrasi
  logika bisnis.
- **OS-04** — Bukan sistem autentikasi baru (tanpa lapisan JWT terpisah).
- **OS-05** — Bukan AI yang bergantung pada cloud untuk data sensitif.
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

---

## 15. Acceptance Criteria

Prototype AIOS dinyatakan berhasil jika seluruh kriteria berikut dapat
ditunjukkan:

- **AC-01** — AIOS dapat diintegrasikan sebagai plugin.
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

---

## 16. Referensi Use Case

Pemetaan use case (sesuai `docs/use-case-description.md`) terhadap requirement
di atas. Referensi use case tidak menambah requirement baru; ia hanya mengikat
requirement yang sudah ada ke use case yang menggambarkannya.

| Use Case | Nama | Requirement terkait |
|---|---|---|
| UC-01 | Memilih AI Manager / Kapabilitas | FR-01, FR-02, FR-03, FR-04, OS-01, OS-10 |
| UC-02 | Berinteraksi dengan AI Manager dan Worker | FR-04, FR-05, FR-06, FR-07, FR-08 s.d. FR-16, FR-20, FR-21, FR-22, RAG-03, LLM-02, LLM-03, SEC-05, IDB-14 s.d. IDB-21, AC-04, AC-12 |
| UC-03 | Mendaftarkan Integrasi Client (Plugin Setup) | IR-01 s.d. IR-09, PW-01, SEC-01, SEC-02, SEC-03, IDB-01, IDB-02, IDB-22, IDB-23, IDB-24, AC-01, AC-15 |
| UC-04 | Menganalisis Skema Database Client | DS-01, DS-02, DS-03, DS-04, DS-05, LLM-03, IDB-03, IDB-04, AC-06, AC-07 |
| UC-05 | Memetakan Skema ke Canonical Data Model | DS-06, DS-07, DS-08, DS-09, DS-10, DS-11, DS-14, DS-15, DS-16, IDB-05, IDB-06, IDB-10, IDB-26, AC-08, AC-09 |
| UC-06 | Memperbarui Mapping saat Skema Berubah | IDB-11 |
| UC-07 | Mengonfigurasi Plugin dan Worker | FR-23, FR-24, FR-25, FR-26, PW-02, PW-03, PW-04, PW-05, PW-07, IDB-07, IDB-08 |
| UC-08 | AI Manager Mengelola & Mengkoordinasikan Worker | FR-04, FR-05, FR-06, FR-07, FR-08 s.d. FR-16, OS-10, PW-04 |
| UC-09 | Worker AI Mengeksekusi Tugas Domain | FR-04, FR-06, FR-20, FR-21, FR-22, RAG-01, RAG-03, LLM-02, LLM-03, AC-04, AC-12 |