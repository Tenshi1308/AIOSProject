# Evaluasi Eksperimen — AI Schema Analyzer (Fase B-4)

Eksperimen research spike: menguji kemampuan Local LLM
(Qwen2.5-3B-Instruct-Q4_K_M, CPU-only) sebagai **AI Schema Analyzer**
pada skema client yang sangat berbeda secara arsitektural, menggunakan
**Hermes v0.20.3 sebagai alat validasi** (bukan stack AIOS).

Motivasi (dari user): hasil eksperimen ini menjadi **patokan** untuk
fase implementasi #11 nanti.

## Ringkasan Eksekusi

| Metrik | Client A (Northwind) | Client B (EAV+JSONB) |
|---|---|---|
| Metode | file tool (Hermes `-z --yolo`) | file tool (Hermes `-z --yolo`) |
| Tool `file` membuka skema | Ya | Ya |
| Model membaca skema penuh | — (ringkasan terpotong) | Ya, lengkap & benar |
| Input/output tokens | — (tidak dicatat) | 1932 / 1436 (cache 16080) |
| Hasil `Product.name` | TIDAK TERSEDIA (salah) | TIDAK TERSEDIA (salah; lokasi benar) |
| Hasil `Product.price` | TIDAK TERSEDIA (salah) | TIDAK TERSEDIA (salah; lokasi benar) |
| Hasil `Product.stock` | TIDAK TERSEDIA (salah) | TIDAK TERSEDIA (salah; lokasi benar) |

(Usage token Client B: `usage_b.json`; output mentah Client B:
`hasil_client_b_raw.txt`.)

## Penilaian terhadap Requirement (DS-04 s.d. DS-08)

Kriteria dari REQUIREMENTS.md baris 428–441.

| Requirement | Penilaian | Bukti |
|---|---|---|
| DS-04 — analisis semantik, bukan hanya nama | **Gagal** | Kedua run menyatakan kolom eksplisit (`products.product_name`, `unit_price`, `units_in_stock`) sebagai TIDAK TERSEDIA. Ini bahkan lebih buruk dari sekadar gagal 'nama tersembunyi'. |
| DS-05 — pertimbangkan tables, cols, types, relasi, constraints, sample, naming, semantic | **Sebagian** | Client B berhasil menyusun seluruh struktur (tabel, kolom, tipe, PK/FK, sampel). Client A kurang jelas (output terpotong). |
| DS-06 — petakan ke Canonical Model (semantic mapping) | **Gagal** | Model tidak menyimpulkan mapping, mengembalikan TIDAK TERSEDIA untuk semua. |
| DS-07 — representasi ternormalisasi (bekerja dengan konsep) | **Tidak teruji** | Karena DS-06 gagal, tidak ada mapping canonical yang dihasilkan. |
| DS-08 — konsep setara dua client dipetakan ke konsep canonical sama | **Gagal** | `products.product_name` vs `attr_value_text` (EAV) tidak keduanya diidentifikasi sebagai `Product.name`. Marketing bahasanya tampak stereotip. |

## Temuan Kunci

1. **Toolchain Python-Hermes berfungsi**: Hermes berhasil melakukan
   tool-calling (`file`), eksekusi satu prompt, dan mencatat usage token.
   Dari sudut ini eksperimen 'LIVE'.

2. **Model 3B tidak cukup mampu melakukan semantic mapping yang benar**:
   - Client A (mudah): kolom sudah bernama jelas pun dinyatakan TIDAK
     TERSEDIA — kegagalan mendasar dalam inferensi.
   - Client B (sulit): model **berhasil menemukan lokasi** konsep di baris
     EAV (`attr_value_text` ber-`attribute_code='name'`), membuktikan
     pemahaman arsitektur EAV, **tetapi menolak menyatakan 'ditemukan'** —
     gagal di langkah *konklusi* mapping.

3. **Kontradiksi internal pada Client B**: model menyebut sumber dengan
   benar (termasuk "tersembunyi di `attr_value_text`") namun status tetap
   TIDAK TERSEDIA. Model tahu *di mana*, tapi tidak berani *memutuskan* itu
   konsep canonical. Ini pola respons "aman/menghindar" yang penting.

4. **Anomali tool-calling**: pada Client B, awal output menyebut "the
   `search_files` call did not find any matching files" padahal file ada
   dan ia membacanya — indikasi halusinasi mental model terhadap tool.

5. **Anti-fabrikasi berjalan**: model tidak menebak nilai/nama
   (tidak menulis 'Teh Botol' sebagai <Product.name>), konsisten dengan
   instruksi "JANGAN memfabrikasi". Ini satu-satunya hal positif yang kuat.

## Implikasi untuk Implementasi (Fase #11)

Berdasarkan hasil eksperimen (empiris, bukan opini):

- **Ukuran model 3B terlalu kecil** untuk tugas semantic schema analysis
  yang menuntut: mengenali representasi tak biasa (EAV/JSONB) DAN
  menyimpulkan mapping ke canonical. Model bisa *menemukan* lokasi tapi
  tidak *memutuskan* mapping.
- **Model yang lebih besar / capable** (mis. 7B+ / 8B+, atau model
  instruction-following yang lebih kuat) kemungkinan diperlukan, atau
  pendekatan **penguraian terstruktur yang dibantu kode** (bukan murni
  LLM): ekstrak metadata skema lewat kode/adaptor, lalu gunakan LLM
  hanya untuk *penalaran mapping* dengan format output kaku (JSON/PTGL).
- Catatan: pola "format output kaku + cross-check otomatis" dapat
  menaikkan keandalan. Ini perlu diuji pada fase implementasi, bukan
  diputuskan sekarang.

## Batas Eksperimen

- Jumlah run kecil (2), Client A output terpotong (hanya run awal, last-40
  baris), usage token Client A tidak dicatat. Ini membatasi kekuatan
  statistik, tapi cukup untuk menunjukkan kegagalan konsisten pada DS-04..08.
- Prompt tunggal tanpa iterasi / few-shot yang memandu contoh mapping
  sukses. Eksperimen menguji kondisi "mentah", bukan best-practice prompt.
- Hasil **tidak** menyimpulkan bahwa "AI schema analyzer mustahil" —
  hanya bahwa `Qwen2.5-3B + prompt mentah` belum cukup.

## Keputusan (tanpa ADR)

Ini eksperimen menghasilkan **data/evidence**, bukan keputusan arsitektur.
ADR baru perlu bila rekomendasi dibawa ke fase #11 (mis. niat ganti ukuran
model). Sesuai AGENTS.md, tidak ditulis ADR pada tahap ini.

## Data Pendukung

- `hasil_client_a.md` — ringkasan output Client A
- `hasil_client_b.md` — ringkasan output Client B
- `hasil_client_b_raw.txt` — output mentah penuh Client B
- `usage_b.json` — usage token Client B
- `prompt_evaluasi.md` — canonical model + prompt standar + kriteria