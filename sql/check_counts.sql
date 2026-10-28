SELECT 'membership_types' AS tbl, COUNT(*) AS n FROM membership_types
UNION ALL SELECT 'members', COUNT(*) FROM members
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'items', COUNT(*) FROM items
UNION ALL SELECT 'authors', COUNT(*) FROM authors
UNION ALL SELECT 'item_authors', COUNT(*) FROM item_authors
UNION ALL SELECT 'loans', COUNT(*) FROM loans
UNION ALL SELECT 'fines', COUNT(*) FROM fines
UNION ALL SELECT 'open loans', COUNT(*) FROM loans WHERE return_date IS NULL;