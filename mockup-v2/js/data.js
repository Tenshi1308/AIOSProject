// Data 9 bidang AIOS (dari AGENTS.md / REQUIREMENTS.md)
const BRANCHES = [
  {
    id: 'strategic',
    icon: '📊',
    name: 'Strategic & Operational Planning',
    manager: 'AI Manager Strategic & Operational Planning',
    workers: ['BI Analyst', 'Report Developer', 'Data Steward']
  },
  {
    id: 'finance',
    icon: '💰',
    name: 'Finance',
    manager: 'AI Manager Finance',
    workers: ['Finance Staff', 'Financial Analyst', 'Budgeting Staff', 'Treasurer', 'CFO']
  },
  {
    id: 'hr',
    icon: '👥',
    name: 'Human Resource',
    manager: 'AI Manager HR',
    workers: ['HR Staff', 'Recruiter', 'Payroll Officer', 'Training Specialist', 'HR Manager']
  },
  {
    id: 'logistic',
    icon: '🚚',
    name: 'Logistic Management',
    manager: 'AI Manager Logistic Management',
    workers: ['Logistics Coordinator', 'Shipping & Receiving Clerk', 'Fleet Manager']
  },
  {
    id: 'maintenance',
    icon: '🔧',
    name: 'Maintenance Management',
    manager: 'AI Manager Maintenance Management',
    workers: ['Maintenance Planner', 'Reliability Engineer', 'Maintenance Technician']
  },
  {
    id: 'sales',
    icon: '📈',
    name: 'Sales and Distribution',
    manager: 'AI Manager Sales',
    workers: ['Sales Representative', 'Customer Service', 'Sales Data Analyst', 'Marketing Specialist']
  },
  {
    id: 'quality',
    icon: '✅',
    name: 'Quality Management',
    manager: 'AI Manager Quality Management',
    workers: ['Quality Inspector', 'Quality Engineer', 'Quality Auditor', 'Quality Control Officer']
  },
  {
    id: 'material',
    icon: '📦',
    name: 'Material Management',
    manager: 'AI Manager Material Management',
    workers: ['Procurement Staff', 'Senior Procurement Specialist', 'Purchasing Officer', 'Inventory Control Manager', 'Warehouse Inventory Manager', 'Retail Inventory Manager']
  },
  {
    id: 'manufacturing',
    icon: '🏭',
    name: 'Manufacturing',
    manager: 'AI Manager Manufacturing',
    workers: ['Production Planner', 'Production Scheduler', 'Production Supervisor']
  }
];

function getBranch(id) {
  return BRANCHES.find(b => b.id === id);
}

// ------------------------------------------------------------
// Demo onboarding data (mockup)
// ------------------------------------------------------------

// Contoh koneksi + struktur database yang SANGAT BERBEDA per client,
// untuk mendemonstrasikan "Client system stays. AIOS adapts."
const DEMO_COMPANIES = {
  'pt-alpha': {
    name: 'PT Alpha',
    pillar: 'Manufacturing',
    connection: { engine: 'PostgreSQL', host: 'db.ptalpha.co.id', port: '5432', name: 'alpha_erp', user: 'aios_reader' },
    schema: ['products (product_id, product_name, price, stock)', 'suppliers (kode, nama_supplier)', 'sales_orders (so_no, tanggal, total)'],
    mapping: [
      { concept: 'Product.id',      source: 'products.product_id',    confidence: 0.97, flag: 'ok' },
      { concept: 'Product.name',    source: 'products.product_name',  confidence: 0.96, flag: 'ok' },
      { concept: 'Product.price',   source: 'products.price',         confidence: 0.91, flag: 'ok' },
      { concept: 'Product.stock',   source: 'products.stock',         confidence: 0.93, flag: 'ok' },
      { concept: 'Supplier.name',   source: 'suppliers.nama_supplier',confidence: 0.84, flag: 'ok' },
      { concept: 'Order.number',    source: 'sales_orders.so_no',     confidence: 0.62, flag: 'low' }
    ]
  },
  'pt-beta': {
    name: 'PT Beta',
    pillar: 'Retail',
    connection: { engine: 'MySQL', host: 'db.ptbeta.co.id', port: '3306', name: 'beta_toko', user: 'aios_reader' },
    schema: ['barang (kode, nama, harga, tersedia)', 'supplier (kd_sp, nama)', 'jual (no_jual, tgl, total)'],
    mapping: [
      { concept: 'Product.id',      source: 'barang.kode',        confidence: 0.95, flag: 'ok' },
      { concept: 'Product.name',    source: 'barang.nama',        confidence: 0.97, flag: 'ok' },
      { concept: 'Product.price',   source: 'barang.harga',       confidence: 0.94, flag: 'ok' },
      { concept: 'Product.stock',   source: 'barang.tersedia',    confidence: 0.90, flag: 'ok' },
      { concept: 'Supplier.name',   source: 'supplier.nama',      confidence: 0.88, flag: 'ok' },
      { concept: 'Order.number',    source: 'jual.no_jual',       confidence: 0.58, flag: 'low' }
    ]
  },
  'pt-gamma': {
    name: 'PT Gamma',
    pillar: 'F&B',
    connection: { engine: 'SQL Server', host: 'db.ptgamma.co.id', port: '1433', name: 'gamma_fnb', user: 'aios_reader' },
    schema: ['menu (menu_id, nama_menu, harga)', 'stok (menu_id, jumlah)', 'transaksi (no_trans, tgl, subtotal)'],
    mapping: [
      { concept: 'Product.id',    source: 'menu.menu_id',    confidence: 0.98, flag: 'ok' },
      { concept: 'Product.name',  source: 'menu.nama_menu',  confidence: 0.96, flag: 'ok' },
      { concept: 'Product.price', source: 'menu.harga',      confidence: 0.92, flag: 'ok' },
      { concept: 'Product.stock', source: 'stok.jumlah',     confidence: 0.71, flag: 'ok' },
      { concept: 'Order.number',  source: 'transaksi.no_trans', confidence: 0.55, flag: 'low' },
      { concept: 'Order.amount',  source: 'transaksi.subtotal', confidence: 0.49, flag: 'low' }
    ]
  }
};

// Koneksi default saat user baru daftar (belum punya profil demo)
const DEMO_FALLBACK = DEMO_COMPANIES['pt-alpha'];

function getDemoCompany(id) {
  return DEMO_COMPANIES[id] || DEMO_FALLBACK;
}

// ------------------------------------------------------------
// Database "buat database baru" (disediakan Ekasa) — FR-32A/B/C
// ------------------------------------------------------------
// Template standar Ekasa: skema + data contoh. Client yang tidak memiliki
// database menggunakan jalur ini; hasil provisioning berperan sebagai
// Client Database (source of truth) yang di-host di server Ekasa — BUKAN
// bagian dari AIOS Internal Database (boundary IDB-14 s.d. IDB-21).
const EKASA_TEMPLATE = {
  engine: 'PostgreSQL',
  host: 'db.ekasa.internal',
  port: '5432',
  name: 'aios_<company>',
  user: 'aios_admin',
  schema: [
    'products (id, name, price, stock)',
    'suppliers (id, name, phone)',
    'orders (id, ordered_at, total)',
    'order_items (id, order_id, product_id, qty, unit_price)'
  ],
  mapping: [
    { concept: 'Product.id',      source: 'products.id',          confidence: 0.98, flag: 'ok' },
    { concept: 'Product.name',    source: 'products.name',        confidence: 0.97, flag: 'ok' },
    { concept: 'Product.price',   source: 'products.price',       confidence: 0.96, flag: 'ok' },
    { concept: 'Product.stock',   source: 'products.stock',       confidence: 0.95, flag: 'ok' },
    { concept: 'Supplier.id',     source: 'suppliers.id',         confidence: 0.96, flag: 'ok' },
    { concept: 'Supplier.name',   source: 'suppliers.name',       confidence: 0.97, flag: 'ok' },
    { concept: 'Order.number',    source: 'orders.id',            confidence: 0.92, flag: 'ok' },
    { concept: 'Order.date',      source: 'orders.ordered_at',    confidence: 0.93, flag: 'ok' },
    { concept: 'Order.amount',    source: 'orders.total',         confidence: 0.94, flag: 'ok' }
  ]
};

function getEkasaTemplate() {
  return EKASA_TEMPLATE;
}
