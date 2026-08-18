-- ============================================================================
-- CLIENT A : NORTHWIND (normalisasi klasik, relasional)
-- Berdasar : pthom/northwind_psql (github.com/pthom/northwind_psql)
-- Status   : verified (skema riil, disederhanakan untuk eksperimen)
-- Tujuan   : input eksperimen AI Schema Analyzer (research spike)
-- Catatan  : hanya subset tabel (categories, products, suppliers,
--            orders, order_details) + sampel kecil. Bukan DB penuh.
-- ============================================================================

DROP TABLE IF EXISTS order_details;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS suppliers;

CREATE TABLE categories (
    category_id     SMALLINT PRIMARY KEY,
    category_name   VARCHAR(15) NOT NULL,
    description     TEXT
);

CREATE TABLE suppliers (
    supplier_id     SMALLINT PRIMARY KEY,
    company_name    VARCHAR(40) NOT NULL,
    contact_name    VARCHAR(30),
    contact_title   VARCHAR(30),
    address         VARCHAR(60),
    city            VARCHAR(15),
    postal_code     VARCHAR(10),
    country         VARCHAR(15),
    phone           VARCHAR(24)
);

CREATE TABLE products (
    product_id      SMALLINT PRIMARY KEY,
    product_name    VARCHAR(40) NOT NULL,
    supplier_id     SMALLINT REFERENCES suppliers(supplier_id),
    category_id     SMALLINT REFERENCES categories(category_id),
    quantity_per_unit VARCHAR(20),
    unit_price      REAL,
    units_in_stock  SMALLINT,
    units_on_order  SMALLINT,
    reorder_level   SMALLINT,
    discontinued    SMALLINT NOT NULL
);

CREATE TABLE orders (
    order_id        SMALLINT PRIMARY KEY,
    customer_id     VARCHAR(5),
    employee_id     SMALLINT,
    order_date      DATE,
    required_date   DATE,
    shipped_date    DATE,
    ship_via        SMALLINT,
    freight         REAL,
    ship_name       VARCHAR(40)
);

CREATE TABLE order_details (
    order_id        SMALLINT REFERENCES orders(order_id),
    product_id      SMALLINT REFERENCES products(product_id),
    unit_price      REAL,
    quantity        SMALLINT,
    discount        REAL,
    PRIMARY KEY (order_id, product_id)
);

-- --- Sampel data (kecil, cukup untuk validasi konsep) -----------------------

INSERT INTO categories (category_id, category_name, description) VALUES
    (1, 'Beverages', 'Soft drinks, coffees, teas, beers and ales'),
    (2, 'Condiments', 'Sweet and savory sauces, relishes, spreads, and seasonings');

INSERT INTO suppliers (supplier_id, company_name, contact_name, contact_title,
                       address, city, postal_code, country, phone) VALUES
    (1, 'Exotic Liquids', 'Charlotte Cooper', 'Purchasing Manager',
     '49 Gilbert St.', 'London', 'EC1 4SD', 'UK', '(171) 555-2222'),
    (2, 'New Orleans Cajun Delights', 'Shelley Burke', 'Order Administrator',
     'P.O. Box 78934', 'New Orleans', '70117', 'USA', '(100) 555-4822');

INSERT INTO products (product_id, product_name, supplier_id, category_id,
                      quantity_per_unit, unit_price, units_in_stock,
                      units_on_order, reorder_level, discontinued) VALUES
    (1,  'Chai',                   1, 1, '10 boxes x 20 bags',             18.0,  39,  0, 10, 0),
    (2,  'Chang',                  1, 1, '24 - 12 oz bottles',             19.0,  17, 40, 25, 0),
    (3,  'Aniseed Syrup',          1, 2, '12 - 550 ml bottles',            10.0,  13, 70, 25, 0),
    (4,  'Chef Anton''s Cajun Seasoning', 2, 2, '48 - 6 oz jars',          22.0,  53,  0,  0, 0);

INSERT INTO orders (order_id, customer_id, employee_id, order_date,
                    required_date, shipped_date, ship_via, freight, ship_name) VALUES
    (10248, 'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.38, 'Vins et alcools Chevalier'),
    (10249, 'TOMSP', 6, '1996-07-05', '1996-08-16', '1996-07-10', 1, 11.61, 'Toms Spezialitaten'),
    (10250, 'HANAR', 4, '1996-07-08', '1996-08-05', '1996-07-12', 2, 65.83, 'Hanari Carnes');

INSERT INTO order_details (order_id, product_id, unit_price, quantity, discount) VALUES
    (10248, 11, 14.0, 12, 0),
    (10248, 42, 9.8,  10, 0),
    (10248, 72, 34.8, 5,  0),
    (10249, 14, 18.6, 9,  0),
    (10249, 51, 42.4, 40, 0),
    (10250, 41, 7.7,  10, 0);