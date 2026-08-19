# Fase B (v2) — Prompt Evaluasi Revisi — AI Schema Analyzer

Eksperimen lanjutan (Exp-1) untuk memisahkan penyebab kegagalan v1:
**prompting** vs **kapasitas model**. Tetap memakai Qwen2.5-3B
(CPU-only) + Hermes v0.20.3 sebagai alat validasi.

## Perbaikan vs v1

| Aspek | v1 (baseline) | v2 (ini) |
|---|---|---|
| Contoh | tidak ada (instruksi abstrak) | **few-shot 2 contoh mapping** |
| Format output | "ringkasan terstruktur" abstrak | **JSON kaku wajib** (`source`, `mapped`, `confidence`) |
| Bias "bisa tersembunyi" | eksplisit, memicu konservatif | **dihapus**, ganti "petakan berdasar makna + sampel" |
| Skala sumber | tidak tetap | **wajib nyebut sumber**; TIDAK ADA hanya bila benar-benar tiada |

Dasar: v1 cenderung menghindar (semua TIDAK TERSEDIA). v2 memaksa model
mengisi field konkret dan memberi contoh cara memetakan, agar dapat
menguji kemampuan sebenarnya, bukan bias konservatif.

## Prompt v2 (used untuk Client A dan B, beda path file)

```text
Anda adalah AI Schema Analyzer untuk platform AIOS yang beradaptasi pada
database client yang beragam. Tugas: petakan konsep bisnis yang ada di
skema ke "Canonical Model" berikut:
    Product.name   (string) — wajib cari
    Product.price  (number) — opsional
    Product.stock  (number) — opsional

LANGKAH:
1. Gunakan tool [file] untuk MEMBACA isi lengkap file skema: <PATH>
2. Analisis SEMANTIK: tabel, kolom, tipe data, relasi, constraints,
   DAN sampel data. Makna konsep bisa berasal dari kombinasi kolom,
   baris, atau representasi tidak biasa (mis. nilai dalam JSON/baris).
   Jangan hanya cocokkan nama kolom literal.
3. Untuk SETIAP konsep canonical di atas, keluarkan 4 item ini pada
   baris terpisah, diawali kata kunci:
       konsep:     (nama konsep)
       ditemukan:  (true atau false)
       source:     (tabel.kolom ATAU cara representasi)
       confidence: (tinggi / sedang / rendah)
       alasan:     (satu kalimat)
   - ditemukan: true HANYA bila anda yakin dari skema/ sampel bahwa
     data konsep itu tersedia.
   - ditemukan: false HANYA bila konsep tersebut benar-benar tidak ada
     di skema. JANGAN menulis false karena anda ragu atau tidak melihat
     nama kolom literal.
4. JANGAN menebak nilai data. Beri source atau cara representasi, bukan
   angka/nama tebakan.

Contoh output yang diharapkan (skema lain):
  konsep: Product.name
  ditemukan: true
  source: products.product_name
  confidence: tinggi
  alasan: kolom nama produk yang jelas

Jawab dengan blok di atas (kata kunci) untuk 3 konsep berikut
(Product.name, Product.price, Product.stock). Uraian bebas diletakkan
setelah blok tersebut.
```

## Kriteria Lolos (gate untuk lanjut ke Client B)

- `Product.name` → **ditemukan: true** dengan source benar, confidence
  ≥ sedang.
- `Product.price`, `Product.stock` → benar `ditemukan` per ketersediaan.
- Tidak ada mapping yang menujukkan source keliru.

Client A lolos bila minimal `Product.name` + `Product.price` + 
`Product.stock` semua `ditemukan: true` dgn source benar. Jika Client A
(termudah, kolom eksplisit) gagal, kita hentikan: menyimpulkan bahwa
3B + prompting saja belum cukup, dan masalah lebih pada kapasitas.