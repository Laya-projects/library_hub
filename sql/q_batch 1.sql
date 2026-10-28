-- Q1: Which books are in the category Biography, and who wrote them?
-- Join: INNER JOIN items -> item_authors -> authors. Every item here has at least
-- one author, and I only want pairs that exist, so nothing needs to be kept
-- when there is no match.
SELECT i.title, a.name AS author
FROM items AS i
INNER JOIN item_authors AS ia ON ia.isbn = i.isbn
INNER JOIN authors AS a ON a.author_id = ia.author_id
WHERE i.category = 'Biography'
ORDER BY i.title, a.name;

-- Q2: Which items are on loan right now, and who has them?
-- Join: INNER JOIN loans -> members and items. An open loan always has a member
-- and an item (foreign keys guarantee it), so INNER loses nothing.
SELECT l.loan_id, m.name AS member, i.title
FROM loans AS l
INNER JOIN members AS m ON m.member_id = l.member_id
INNER JOIN items AS i ON i.isbn = l.isbn
WHERE l.return_date IS NULL
ORDER BY l.loan_id;

-- Q3: Which open loans are overdue as of 2026-10-12, and by how many days?
-- Join: INNER JOIN, same reason as Q2. The date is written in the query because
-- today is fixed for the project (date('now') would change the answer).
SELECT m.name AS member, i.title, l.due_date,
       CAST(julianday('2026-10-12') - julianday(l.due_date) AS INTEGER) AS days_overdue
FROM loans AS l
INNER JOIN members AS m ON m.member_id = l.member_id
INNER JOIN items AS i ON i.isbn = l.isbn
WHERE l.return_date IS NULL
  AND l.due_date < '2026-10-12'
ORDER BY days_overdue DESC;

-- Q4: Which 3 titles have the most loans? Ties are broken by title.
-- Join: INNER JOIN loans -> items. Titles with no loans may drop out here,
-- which is fine because the top 3 all have loans.
SELECT i.title, COUNT(*) AS loans
FROM loans AS l
INNER JOIN items AS i ON i.isbn = l.isbn
GROUP BY i.isbn, i.title
ORDER BY loans DESC, i.title
LIMIT 3;













