-- Phase 3 Step 6: borrow as one transaction, then break it on purpose.
-- Run on a freshly built database (schema.sql + seed.sql), today = 2026-10-12.

-- Before: nothing exists yet
SELECT COUNT(*) AS loans_with_L011 FROM loans WHERE loan_id = 'L011';
SELECT COUNT(*) AS audit_rows FROM audit_log;

-- Attempt 1: the audit insert breaks NOT NULL on purpose (action is NULL).
BEGIN;
  -- Check availability and insert the loan in one statement.
  -- The loan is inserted only if total copies minus open loans is above 0.
  INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date)
  SELECT 'L011', 'M001', '9780000000011', '2026-10-12', '2026-10-26'
  WHERE (SELECT i.total_copies - COUNT(l.loan_id)
         FROM items AS i
         LEFT JOIN loans AS l ON l.isbn = i.isbn AND l.return_date IS NULL
         WHERE i.isbn = '9780000000011') > 0;
  INSERT INTO audit_log (action, details)
  VALUES (NULL, 'M001 borrowed 9780000000011 as L011');
ROLLBACK;

-- After the rollback: the loan must be gone too
SELECT COUNT(*) AS loans_with_L011 FROM loans WHERE loan_id = 'L011';
SELECT COUNT(*) AS audit_rows FROM audit_log;

-- Attempt 2: the same two statements, written correctly.
BEGIN;
  INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date)
  SELECT 'L011', 'M001', '9780000000011', '2026-10-12', '2026-10-26'
  WHERE (SELECT i.total_copies - COUNT(l.loan_id)
         FROM items AS i
         LEFT JOIN loans AS l ON l.isbn = i.isbn AND l.return_date IS NULL
         WHERE i.isbn = '9780000000011') > 0;
  INSERT INTO audit_log (action, details)
  VALUES ('BORROW', 'M001 borrowed 9780000000011 as L011');
COMMIT;

-- After the commit: both rows exist
SELECT COUNT(*) AS loans_with_L011 FROM loans WHERE loan_id = 'L011';
SELECT COUNT(*) AS audit_rows FROM audit_log;
SELECT loan_id, member_id, isbn, issue_date, due_date FROM loans WHERE loan_id = 'L011';