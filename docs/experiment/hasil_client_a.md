# Hasil Mentah — Client A (Northwind)

Run: `hermes -z <prompt standar> --yolo` (file tool, membaca
`docs/experiment/client_a_northwind.sql`).

## Ringkasan Output

Model (Qwen2.5-3B-Instruct-Q4_K_M, CPU-only) **menyatakan hampir semua
konsep canonical "TIDAK TERSEDIA"**, meskipun skema memuat kolom jelas
seperti `product_name`, `unit_price`, `units_in_stock`.

Pernyataan kunci dari output:
- `Product.name` → **TIDAK TERSEDIA** — "Konsep produk memiliki kolom
  nama, namun tidak ada kolom spesifik untuk nama produk."
- `Product.price` → **TIDAK TERSEDIA** — "ada kolom harga unit, namun
  tidak ada kolom spesifik untuk harga produk."
- `Product.stock` → **TIDAK TERSEDIA** — "ada kolom inventaris ... tidak
  ada kolom spesifik untuk stock produk."
- Semua konsep lain (Order, Customer, Supplier, Categories) juga dinyatakan
  TIDAK TERSEDIA, dengan alasan berulang "tidak ada informasi spesifik".

## Penilaian Awal (vs DS-04..DS-08)

- Hermes **berhasil** menggunakan tool `file` dan menjalankan analisis
  (toolchain hidup, prompt dieksekusi).
- Namun kemampuan inferensi **semantic mapping model 3B gagal**: kolom
  sudah jelas namanya pun dinyatakan "tidak tersedia". Ini bukan hanya
  gagal soal 'nama tersembunyi' (kasus terberat Client B), melainkan gagal
  menemukan atribut yang bahkan sudah eksplisit bernama.
- Terindikasi model memberikan respons "aman" yang menghindar (semua
  TIDAK TERSEDIA) alih-alih memetakan — perilaku yang perlu didokumentasikan
  sebagai temuan penting.

## Catatan

- Output asli ditangkap sebagian (last 40 baris) pada run ini; akan
  dilengkapi bila run ulang penuh diperlukan untuk bukti deterministik.
- Ini hasil **mentah**, analisis reflektif ada di dokumen evaluasi
  (Fase B-4).