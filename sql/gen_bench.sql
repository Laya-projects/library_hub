-- Phase 3 Step 7: make a big test database. Run on a fresh database that already
-- has schema.sql and seed.sql loaded. It adds members, items and 100000 loans.

-- 995 extra members with IDs M006 .. M1000 (the IDs are only text)
WITH RECURSIVE n(i) AS (SELECT 6 UNION ALL SELECT i + 1 FROM n WHERE i < 1000)
INSERT INTO members (member_id, name, email, membership_type)
SELECT 'M' || printf('%03d', i), 'Member ' || i, 'member' || i || '@example.com',
       CASE i % 3 WHEN 0 THEN 'Student' WHEN 1 THEN 'Regular' ELSE 'Premium' END
FROM n;

-- 993 extra books, spread over the existing categories
WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 993)
INSERT INTO items (isbn, title, item_type, category, pages, price, total_copies)
SELECT CAST(9781000000000 + i AS TEXT), 'Bench Book ' || i, 'Book',
       CASE i % 4 WHEN 0 THEN 'Fiction' WHEN 1 THEN 'History'
                  WHEN 2 THEN 'Programming' ELSE 'Biography' END,
       100 + i % 400, 100 + i % 500, 5
FROM n;

-- 100000 loans. Member and item are picked by simple arithmetic, so every run
-- gives the same data. Every 30th loan stays open, the rest are returned.
WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 100000)
INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date, return_date)
SELECT 'B' || printf('%06d', i),
       'M' || printf('%03d', 6 + (i * 7) % 995),
       CAST(9781000000000 + 1 + (i * 13) % 993 AS TEXT),
       date('2025-01-01', '+' || (i % 600) || ' days'),
       date('2025-01-01', '+' || ((i % 600) + 14) || ' days'),
       CASE WHEN i % 30 = 0 THEN NULL
            ELSE date('2025-01-01', '+' || ((i % 600) + 10 + i % 20) || ' days') END
FROM n;

SELECT COUNT(*) AS loans FROM loans;
SELECT COUNT(*) AS open_loans FROM loans WHERE return_date IS NULL;