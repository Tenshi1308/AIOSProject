-- ============================================================================
-- CLIENT B : EAV + JSONB (pemodelan pola, arsitektur sangat berbeda)
-- Berdasar : pola EAV (Wikipedia) + JSONB (PostgreSQL docs)
-- Status   : modeling (BUKAN salinan DB produksi; pemodelan berdasar pola)
-- Tujuan   : input eksperimen AI Schema Analyzer (research spike)
-- Catatan  : nama item ('Teh Botol', 'Kecap Manis') disembunyikan di
--            BARIS EAV (attr_value_text), BUKAN sebagai kolom bernama jela
-- ============================================================================

DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS attr_value_date;
DROP TABLE IF EXISTS attr_value_num;
DROP TABLE IF EXISTS attr_value_text;
DROP TABLE IF EXISTS attribute_definitions;
DROP TABLE IF EXISTS objects;

-- objek generik: entitas bisnis dari jenis berapa pun disimpan di satu tabel
CREATE TABLE objects (
    object_id     SERIAL PRIMARY KEY,
    object_type   VARCHAR(30) NOT NULL,          -- 'product', 'customer', ...
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    meta          JSONB NOT NULL DEFAULT '{}'
);

-- definisi atribut tersedia (nama kolom apa pun boleh ada di sini)
CREATE TABLE attribute_definitions (
    attribute_id  SERIAL PRIMARY KEY,
    attribute_code VARCHAR(40) NOT NULL UNIQUE,  -- mis. 'name', 'price', 'stock'
    attribute_domain VARCHAR(10) NOT NULL DEFAULT 'text'  -- text | num | date
);

-- nilai atribut disimpan sebagai BARIS (satu baris per atribut)
CREATE TABLE attr_value_text (
    object_id     INTEGER NOT NULL REFERENCES objects(object_id),
    attribute_id  INTEGER NOT NULL REFERENCES attribute_definitions(attribute_id),
    attr_value_text VARCHAR(255),
    PRIMARY KEY (object_id, attribute_id)
);

CREATE TABLE attr_value_num (
    object_id     INTEGER NOT NULL REFERENCES objects(object_id),
    attribute_id  INTEGER NOT NULL REFERENCES attribute_definitions(attribute_id),
    attr_value_num NUMERIC(15,2),
    PRIMARY KEY (object_id, attribute_id)
);

CREATE TABLE attr_value_date (
    object_id     INTEGER NOT NULL REFERENCES objects(object_id),
    attribute_id  INTEGER NOT NULL REFERENCES attribute_definitions(attribute_id),
    attr_value_date DATE,
    PRIMARY KEY (object_id, attribute_id)
);

-- versi 'orders' Client B (juga EAV/JSONB)
CREATE TABLE orders (
    order_id      SERIAL PRIMARY KEY,
    order_json    JSONB NOT NULL            -- seluruh isi order sebagai JSONB
);

CREATE TABLE order_lines (
    line_id       SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    object_id     INTEGER REFERENCES objects(object_id),  -- barang yang dibeli
    qty_json      JSONB NOT NULL                           -- mis. {"qty": 5}
);

-- --- Sampel data (kecil) ----------------------------------------------------
-- Nama produk HANYA ada di baris EAV attr_value_text, bukan kolom berjela.

INSERT INTO attribute_definitions (attribute_code, attribute_domain) VALUES
    ('name',  'text'),
    ('price', 'num'),
    ('stock', 'num');

INSERT INTO objects (object_id, object_type, meta) VALUES
    (1, 'product', '{"brand":"Sariwangi"}'),
    (2, 'product', '{"brand":"Indofood"}');

-- produk 1: 'Teh Botol'  (nama di baris text, harga & stok di baris num)
INSERT INTO attr_value_text (object_id, attribute_id, attr_value_text) VALUES
    (1, 1, 'Teh Botol'),
    (2, 1, 'Kecap Manis');
INSERT INTO attr_value_num (object_id, attribute_id, attr_value_num) VALUES
    (1, 2, 3500.00),  -- price
    (1, 3, 120.00),   -- stock
    (2, 2, 8000.00),  -- price
    (2, 3, 45.00);    -- stock

-- order versi EAV/JSONB: seluruh detail order berupa JSON
INSERT INTO orders (order_id, order_json) VALUES
    (1, '{"order_date":"2024-05-01","customer":"Toko Maju","status":"paid"}'),
    (2, '{"order_date":"2024-05-02","customer":"Minimarket Sejahtera","status":"pending"}');

INSERT INTO order_lines (line_id, order_id, object_id, qty_json) VALUES
    (1, 1, 1, '{"qty":10}'),
    (2, 1, 2, '{"qty":5}'),
    (3, 2, 1, '{"qty":3}');