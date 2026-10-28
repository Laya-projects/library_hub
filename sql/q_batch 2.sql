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