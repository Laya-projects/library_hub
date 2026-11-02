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

-- Q5: Which items have never been borrowed?
-- Join: LEFT JOIN items -> loans. LEFT keeps every item even when no loan matches,
-- and those rows have NULL in the loan columns. An INNER JOIN would drop exactly
-- the items I am looking for.
SELECT i.title
FROM items AS i
LEFT JOIN loans AS l ON l.isbn = i.isbn
WHERE l.loan_id IS NULL
ORDER BY i.title;

-- Q6: Which members have no loan in the last 90 days (since 2026-07-14)?
-- Join: LEFT JOIN members -> recent loans. The date test sits in the ON clause,
-- not in WHERE, so a member with only old loans still appears with NULLs.
-- Putting it in WHERE would remove those rows and turn this into an INNER JOIN.
SELECT m.name
FROM members AS m
LEFT JOIN loans AS l
       ON l.member_id = m.member_id
      AND l.issue_date >= date('2026-10-12', '-90 days')
WHERE l.loan_id IS NULL
ORDER BY m.name;

-- Q8: How much in fines has been paid, and how much is still pending?
-- Join: none. Fines already hold the amount and the paid flag, so one table is
-- enough. CASE turns the 1 and 0 flag into the words Paid and Pending.
SELECT CASE paid WHEN 1 THEN 'Paid' ELSE 'Pending' END AS status,
       SUM(amount) AS total
FROM fines
GROUP BY paid
ORDER BY paid DESC;

-- Q11: How many copies of each title are available right now?
-- Join: LEFT JOIN items -> open loans. Items with no open loan must stay in the
-- result with a count of 0. The open-loan test is in the ON clause for the same
-- reason as Q6. COUNT(l.loan_id) counts only real matches, never the NULL rows.
-- Reference items are not borrowable (R1) but the sample shows them with 1, so I
-- show total_copies minus open loans for every item (see DECISIONS.md D23).
SELECT i.title, i.total_copies - COUNT(l.loan_id) AS available
FROM items AS i
LEFT JOIN loans AS l ON l.isbn = i.isbn AND l.return_date IS NULL
GROUP BY i.isbn, i.title, i.total_copies
ORDER BY i.isbn;


-- Q7: What are the total fines per membership type per month (month the item was returned)?
-- Join: INNER JOIN fines -> loans -> members. A fine always belongs to a loan and a
-- loan to a member, and only loans that have a fine should appear.
-- strftime cuts the return date down to year and month.
SELECT m.membership_type,
       strftime('%Y-%m', l.return_date) AS month,
       SUM(f.amount) AS total_fines
FROM fines AS f
INNER JOIN loans AS l ON l.loan_id = f.loan_id
INNER JOIN members AS m ON m.member_id = l.member_id
GROUP BY m.membership_type, month
ORDER BY m.membership_type, month;

-- Q9: Which members borrowed from at least 3 different categories?
-- Join: INNER JOIN members -> loans -> items. COUNT(DISTINCT ...) counts each
-- category once however many times it was borrowed. HAVING filters after grouping,
-- which WHERE cannot do.
SELECT m.name, COUNT(DISTINCT i.category) AS categories
FROM members AS m
INNER JOIN loans AS l ON l.member_id = m.member_id
INNER JOIN items AS i ON i.isbn = l.isbn
GROUP BY m.member_id, m.name
HAVING COUNT(DISTINCT i.category) >= 3
ORDER BY m.name;

-- Q10: Which categories have an average loan length above 25 days (returned loans only)?
-- Join: INNER JOIN loans -> items. Only returned loans have a length, so the
-- WHERE removes open loans before the average is taken.
SELECT i.category,
       ROUND(AVG(julianday(l.return_date) - julianday(l.issue_date)), 1) AS avg_days
FROM loans AS l
INNER JOIN items AS i ON i.isbn = l.isbn
WHERE l.return_date IS NOT NULL
GROUP BY i.category
HAVING AVG(julianday(l.return_date) - julianday(l.issue_date)) > 25
ORDER BY avg_days DESC;

-- Q12: Which pair of titles is most often borrowed by the same member?
-- Join: SELF JOIN of the member-and-title list with itself, on the same member.
-- The condition a.title < b.title keeps each pair once and never pairs a title
-- with itself. DISTINCT first, so a member who borrowed a title twice counts once.
WITH member_titles AS (
    SELECT DISTINCT l.member_id, i.title
    FROM loans AS l
    INNER JOIN items AS i ON i.isbn = l.isbn
)
SELECT a.title AS title_a, b.title AS title_b, COUNT(*) AS members
FROM member_titles AS a
INNER JOIN member_titles AS b
        ON b.member_id = a.member_id AND a.title < b.title
GROUP BY a.title, b.title
ORDER BY members DESC, title_a, title_b
LIMIT 1;










