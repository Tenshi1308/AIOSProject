# Hasil Mentah — Client A (Northwind) — Prompt v2

Run: `hermes -z <prompt_evaluasi_v2> --yolo` (file tool), Qwen2.5-3B
CPU-only. Output asli model (disalin utuh dari run yang tampil langsung;
run pertama dengan `*>` redirect menghasilkan `(empty)` — artefak
redirect, model sebenarnya tidak kosong).

## Output Model (verbatim)

```text
konsep: Product.name
ditemukan: true
source: products.product_name
confidence: tinggi
alasan: kolom product_name dalam tabel products

konsep: Product.price
ditemukan: false
source:
confidence: rendah
alasan: data harga produk tidak disajikan dalam skema

konsep: Product.stock
ditemukan: true
source: products.units_in_stock
confidence: tinggi
alasan: kolom units_in_stock dalam tabel products
```

## Skor vs Ketentuan

| Konsep | v1 (baseline) | v2 (ini) | Di skema? (ground truth) |
|---|---|---|---|
| Product.name | TIDAK TERSEDIA | **ditemukan: true** ✓ | Ya — `products.product_name` |
| Product.price | TIDAK TERSEDIA | **ditemukan: false** ✗ | Ya — `products.unit_price` |
| Product.stock | TIDAK TERSEDIA | **ditemukan: true** ✓ | Ya — `products.units_in_stock` |

Gate fase B (lanjut Client B): Ketiga konsep `ditemukan: true` dgn source
benar. → **TIDAK lolos** (price salah).

## Analisis

- **Perbaikan prompting sangat berdampak**: dari 0/3 → 2/3 benar.
  Few-shot + format kaku + kalimat anti-"ragu" menaikkan kesediaan model
  menyimpulkan mapping.
- **Kasus price menarik**: `products.unit_price` jelas dan mengandung kata
  "price", tetapi model menulis `ditemukan: false` dengan alasan "data
  harga produk tidak disajikan dalam skema" — **kontradiksi dengan isi
  skema yang dibacanya sendiri**. Ini menandakan **inkonsistensi /
  ketidakmampuan penuh** pada Qwen2.5-3B, bukan sekadar bias keamanan
  (karena price mengandung substring "price" seperti stock mengandung
  "stock" — satu sukses, satu gagal).
- Tidak memfabrikasi nilai (tidak menebak harga), source kosong saat false.

## Catatan

- Evidence usage: `usage_a_v2.json` (input 642, output 85, cache 20098,
  4 api calls, cost $0, completed).
- Ini hasil **mentah**; analisis reflektif di dokumen evaluasi akhir
  eksperimen.