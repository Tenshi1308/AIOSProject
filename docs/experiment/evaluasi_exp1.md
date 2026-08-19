# Evaluasi Eksperimen 1 — Perbaikan Prompting (Qwen2.5-3B)

Eksperimen lanjutan dari baseline v1 untuk memisahkan penyebab kegagalan
semantic schema mapping: **apakah masalah prompting, atau kapasitas
model `/ keandalan`?**

## Metode

- Model: Qwen2.5-3B-Instruct-Q4_K_M (CPU-only, llama.cpp) — **tetap**,
  tidak diganti.
- Perbaikan prompt v2 (lihat `prompt_evaluasi_v2.md`): few-shot, format
  kaku (kata kunci `ditemukan/source/confidence/alasan`), hapus bias
  "bisa tersembunyi", anti-ragu.
- Client A (Northwind, kolom eksplisit — kasus termudah) diuji **dua
  kali berturut-turut** dengan prompt identik.

## Hasil

### Run #1 (prompt v2)

| Konsep | Hasil | Ground truth (skema) |
|---|---|---|
| Product.name | ditemukan: true, `products.product_name`, tinggi | ✓ benar |
| Product.price | ditemukan: false | ✗ salah (`products.unit_price`) |
| Product.stock | ditemukan: true, `products.units_in_stock`, tinggi | ✓ benar |

→ **2/3** (v1 baseline: 0/3)

### Run #2 (prompt v2 pun, identik)

| Konsep | Hasil |
|---|---|
| Product.name | ditemukan: false (alasan: nama kolom "Product.name" tidak ditemukan) ✗ |
| Product.price | ditemukan: false ✗ |
| Product.stock | ditemukan: false ✗ |

→ **0/3** (regresi total)

## Kesimpulan (berbasis bukti)

### 1. Prompting adalah faktor nyata (v2 > v1)
v1 peling semua TIDAK TERSEDIA (0/3). v2 memperoleh 2/3 pada run#1.
Few-shot + format kaku + anti-ragu **menaikkan kesediaan** model
menyimpulkan mapping. Ini membuktikan **kualitas prompt berpengaruh besar**.

### 2. Tetapi prompting SAJA tidak cukup — keandalan 3B rendah
Bukti kunci: run #2 dengan prompt **identik** jatuh ke 0/3, dan -- kritikal --
**mengartikan nama canonical sebagai nama kolom literal** ("Product.name
tidak ditemukan dalam file skema"), menunjukkan run tersebut
**tidak memahami isi skema** (yang memuat `product_name`). Non-determinisme
ini tidak dapat diperbaiki oleh prompt.

### 3. Absen: tidak ada fabrikasi nilai
Kedua run tidak menebak angka/nama nilai (source benar/kosong), konsisten
dengan instruksi anti-fabrikasi. Positif.

## Verdict untuk fase #11 (patokan)

| Pertanyaan | Jawaban berdasarkan bukti |
|---|---|
| Perbaikan prompting membantu? | **Ya** — v2 nyata menaikkan (0/3 → 2/3 pada best run). |
| Prompting saja cukup? | **Tidak** — non-determinisme run#2 (0/3) membuktikan model tidak andal. |
| Perlu model lebih besar / lebih andal? | **Indikasi kuat ya** — keandalan, bukan sekadar bias. Perlu cross-check sedangkan saat menguji model lebih besar. |

**Kesimpulan balanced**: masalahnya **keduanya bertumpuk** — (a) prompt
mentah memang buruk (v1), dan (b) Qwen2.5-3B membantu tidak andal untuk
penalaran semantic-schema (run#2). Untuk fase #11 patokan: **jangan**
mengandalkan 3B murni; gunakan model lebih capable ATAU pendekatan
hibrida (ekstraksi metadata ber-kode + format kaku + retry/validasi
otomatis) untuk meraik keandalan.

## Keterbatasan eksperimen

- 2 run saja; CPU determinisme TIDAK dijamin (temperature sampling).
  Kesimpulan "non-determinisme" berdasarkan run#1 vs run#2, bukan set
  statistik besar — tetap pola yang jelas (satu run lolos, satu run salah
  total pada prompt sama).
- Client B (EAV, kasus tersulit) belum diuji ulang v2 — tapi mengingat
  Client A (termudah) saja gagal andal, penarikan ke EAV dianggap
  redundan untuk pertanyaan "apakah 3B andal". Opsional dilanjut bila
  mau bukti di kasus sulit.

## Data pendukung
- `hasil_client_a_v2.md` (run#1, verbatim)
- `hasil_client_a_v2_run2.md` (run#2, verbatim)
- `usage_a_v2.json` (usage run#1)
- `prompt_evaluasi_v2.md` (prompt v2 + kriteria)
- baseline: `hasil_client_a.md` (v1)