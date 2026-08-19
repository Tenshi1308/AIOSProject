# Hasil Mentah — Client A (Northwind) — Prompt v2 — RUN #2 (repeat)

Run ulang determinisme dengan prompt v2 **identik** dengan run #1
(prompt_a_v2.txt, `hermes -z ... --yolo`, device idle — tidak ada
intervensi).

## Output Model (verbatim)

```text
Konsep: Product.name
ditemukan: false
source: tidak ditemukan
confidence: rendah
alasan: Nama kolom "Product.name" tidak ditemukan dalam file skema.

Konsep: Product.price
ditemukan: false
source: tidak ditemukan
confidence: rendah
alasan: Nama kolom "Product.price" tidak ditemukan dalam file skema.

Konsep: Product.stock
ditemukan: false
source: tidak ditemukan
confidence: rendah
alasan: Nama kolom "Product.stock" tidak ditemukan dalam file skema.
```

## Kontras dengan Run #1 (prompt identik)

| Konsep | Run #1 | Run #2 |
|---|---|---|
| Product.name | ditemukan: true (`products.product_name`) ✓ | **ditemukan: false** ✗ |
| Product.price | ditemukan: false ✗ | **ditemukan: false** ✗ |
| Product.stock | ditemukan: true (`products.units_in_stock`) ✓ | **ditemukan: false** ✗ |

Skor: 2/3 (run#1) vs **0/3** (run#2). Prompt dan lingkungan sama.

## Temuan Kunci

1. **Non-determinisme ekstrem**: prompt, model, dan environment identik,
   namun hasil berubah dari 2/3 benar menjadi 0/3 salah total.
2. **Pola salah run #2 bermakna**: model mencari kolom **literal bernama
   "Product.name / Product.price / Product.stock"** dan menjawab
   "Nama kolom ... tidak ditemukan dalam file skema". Ini menunjukkan
   model dalam run ini **mengartikan nama konsep canonical sebagai nama
   kolom literal dan tidak membaca/memahami isi skema yang sebenarnya**
   (yang memuat `product_name`, `unit_price`, `units_in_stock`).
3. **Vonis**: keandalan Qwen2.5-3B untuk semantic schema mapping tidak
   konsisten — satu run bisa lolos 2/3, run berikut 0/3. Ini menjabarkan
   bahwa masalah **bukan murni prompting**: perbaikan prompt menaikkan
   potensi (run #1) tapi model tetap tidak andal (run #2 masih bisa jatuh
   ke jawaban salah total).

## Catatan

- Ini run mentah; interpretasi penuh di dokumen evaluasi akhir eksperimen.