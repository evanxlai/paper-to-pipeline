-- sqlite_bench script: an order-processing database built, queried and
-- changed in memory. It runs the SQLite parts that real applications use:
-- the parser and planner, B-tree inserts through three indexes, joins,
-- grouping and sorting, window functions, string matching, and updates
-- and deletes that rebalance the trees.
--
-- Size: p2p_param.n (the N argument of sqlite_bench) is the number of
-- order lines. There is one customer for every 8 lines. The work grows a
-- little faster than N, because the B-tree depth grows with log N.
--
-- Determinism: all data comes from the recursive CTEs below, which step
-- the ANSI C rand() LCG in integer SQL. The script never calls random(),
-- randomblob() or a date function with 'now'. Every ORDER BY that reaches
-- the output breaks ties on a unique column.
--
-- Checks: each row whose first column is 'ok' or 'FAIL' compares two ways
-- of computing one answer. The driver fails the run on any 'FAIL'.

CREATE TABLE customer(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  region INTEGER NOT NULL,
  credit INTEGER NOT NULL
);
CREATE TABLE line(
  id INTEGER PRIMARY KEY,
  customer INTEGER NOT NULL,
  product INTEGER NOT NULL,
  qty INTEGER NOT NULL,
  price INTEGER NOT NULL,
  note TEXT NOT NULL
);
CREATE INDEX line_customer ON line(customer);
CREATE INDEX line_product ON line(product, qty);
CREATE INDEX customer_region ON customer(region, credit);

-- The indexes exist before the inserts on purpose: every row then goes
-- through three B-tree insertions, the branchy part of a write.
WITH RECURSIVE gen(i, x) AS (
  SELECT 1, 42
  UNION ALL
  SELECT i + 1, (x * 1103515245 + 12345) % 2147483648 FROM gen
  WHERE i < (SELECT n FROM p2p_param) / 8 + 1
)
INSERT INTO customer
SELECT i, printf('cust%06d', (x >> 8) % 1000000), (x >> 4) % 16,
       (x >> 10) % 100000
FROM gen;

WITH RECURSIVE gen(i, x) AS (
  SELECT 1, 7
  UNION ALL
  SELECT i + 1, (x * 1103515245 + 12345) % 2147483648 FROM gen
  WHERE i < (SELECT n FROM p2p_param)
)
INSERT INTO line
SELECT i,
       1 + (x >> 5) % ((SELECT n FROM p2p_param) / 8 + 1),
       (x >> 3) % 97,
       1 + (x >> 11) % 9,
       100 + (x >> 13) % 9900,
       substr('abcdefghijklmnopqrstuvwxyz', 1 + (x >> 7) % 20,
              1 + (x >> 17) % 7)
FROM gen;

SELECT CASE WHEN (SELECT count(*) FROM line) = (SELECT n FROM p2p_param)
            THEN 'ok' ELSE 'FAIL' END, 'line_count';

-- Revenue by region: a join, a GROUP BY and an ORDER BY.
SELECT 'region', c.region, count(*), sum(l.qty * l.price)
FROM line l JOIN customer c ON c.id = l.customer
GROUP BY c.region
ORDER BY c.region;

-- The five biggest customers, ranked with a window function.
SELECT 'top', id, spend, rnk FROM (
  SELECT c.id AS id, sum(l.qty * l.price) AS spend,
         rank() OVER (ORDER BY sum(l.qty * l.price) DESC, c.id) AS rnk
  FROM customer c JOIN line l ON l.customer = c.id
  GROUP BY c.id
)
WHERE rnk <= 5
ORDER BY rnk;

-- String matching over every note.
SELECT 'notes', count(*), sum(length(note)), sum(note LIKE '%e%'),
       sum(note GLOB '[a-f]*'), count(DISTINCT note)
FROM line;

-- A moving sum over the whole table in id order.
SELECT 'moving', max(m), min(m) FROM (
  SELECT sum(qty) OVER (ORDER BY id ROWS BETWEEN 7 PRECEDING
                        AND CURRENT ROW) AS m
  FROM line
);

-- Changes that rewrite and rebalance the B-trees.
UPDATE line SET qty = qty + 1 WHERE product % 7 = 0;
DELETE FROM line WHERE price < 1000;
UPDATE customer SET credit = credit - 500
WHERE id IN (SELECT customer FROM line WHERE qty > 8);

-- Check: an index lookup and a full scan must count the same rows.
SELECT CASE WHEN (SELECT count(*) FROM line WHERE product = 13)
               = (SELECT count(*) FROM line NOT INDEXED WHERE product = 13)
            THEN 'ok' ELSE 'FAIL' END, 'index_vs_scan';

-- Check: per-product totals must add up to the grand total.
SELECT CASE WHEN (SELECT sum(s) FROM (SELECT sum(qty * price) AS s
                                      FROM line GROUP BY product))
               = (SELECT sum(qty * price) FROM line)
            THEN 'ok' ELSE 'FAIL' END, 'group_sum';

-- Check: the rows left after the DELETE are exactly those it kept.
SELECT CASE WHEN (SELECT count(*) FROM line WHERE price < 1000) = 0
            THEN 'ok' ELSE 'FAIL' END, 'delete';

-- Customers with no order lines left: a correlated NOT EXISTS.
SELECT 'idle', count(*) FROM customer c
WHERE NOT EXISTS (SELECT 1 FROM line l WHERE l.customer = c.id);

-- One number over every surviving row and every customer.
SELECT 'checksum',
       (SELECT sum(id * 31 + customer * 7 + product * 3 + qty * price)
               % 1000000007 FROM line),
       (SELECT sum(credit + region) FROM customer);
