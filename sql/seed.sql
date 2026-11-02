-- LibraryHub Mini, Phase 3: starter data
-- Run after schema.sql. Order matters: parents before children.

-- Membership types (limits come from the Python member classes)
INSERT INTO membership_types (type, borrow_limit, loan_days, fine_per_day) VALUES
    ('Student', 3, 14, 2),
    ('Regular', 5, 21, 5),
    ('Premium', 10, 30, 3);

-- Members (members.csv)
INSERT INTO members (member_id, name, email, membership_type) VALUES
    ('M001', 'Asha Raman',  'asha@example.com',   'Student'),
    ('M002', 'Rahul Mehta', 'rahul@example.com',  'Regular'),
    ('M003', 'Sneha Iyer',  'sneha@example.com',  'Premium'),
    ('M004', 'Karthik N',   'karthik@example.com','Student'),
    ('M005', 'Divya Rao',   'divya@example.com',  'Regular');

-- Categories: Technology first, because two categories point to it as their parent
INSERT INTO categories (name, parent) VALUES
    ('Technology', NULL),
    ('Biography', NULL),
    ('Fiction', NULL),
    ('History', NULL),
    ('Reference', NULL),
    ('Magazines', NULL),
    ('Software Engineering', 'Technology'),
    ('Programming', 'Technology');

-- Items (books.csv)
INSERT INTO items (isbn, title, item_type, category, pages, price, total_copies) VALUES
    ('9780000000011', 'Wings of Fire',          'Book',      'Biography',            180,  250, 2),
    ('9780000000028', 'The Alchemist',          'Book',      'Fiction',              208,  300, 1),
    ('9780000000035', 'Clean Code',             'Book',      'Software Engineering', 464,  900, 1),
    ('9780000000042', 'Python Crash Course',    'Book',      'Programming',          544,  700, 2),
    ('9780000000059', 'Sapiens',                'Book',      'History',              512,  600, 1),
    ('9780000000066', 'Encyclopaedia of Science','Reference','Reference',           1200, 2500, 1),
    ('9780000000073', 'India Today (Oct 2026)', 'Magazine',  'Magazines',             90,   80, 3);

-- Authors: the multi-author cell in books.csv is split here, one row per person
INSERT INTO authors (name) VALUES
    ('A.P.J. Abdul Kalam'),
    ('Arun Tiwari'),
    ('Paulo Coelho'),
    ('Robert C. Martin'),
    ('Eric Matthes'),
    ('Yuval Noah Harari'),
    ('Various');

-- Item and author pairs (the junction table): Wings of Fire has two authors
INSERT INTO item_authors (isbn, author_id) VALUES
    ('9780000000011', (SELECT author_id FROM authors WHERE name = 'A.P.J. Abdul Kalam')),
    ('9780000000011', (SELECT author_id FROM authors WHERE name = 'Arun Tiwari')),
    ('9780000000028', (SELECT author_id FROM authors WHERE name = 'Paulo Coelho')),
    ('9780000000035', (SELECT author_id FROM authors WHERE name = 'Robert C. Martin')),
    ('9780000000042', (SELECT author_id FROM authors WHERE name = 'Eric Matthes')),
    ('9780000000059', (SELECT author_id FROM authors WHERE name = 'Yuval Noah Harari')),
    ('9780000000066', (SELECT author_id FROM authors WHERE name = 'Various')),
    ('9780000000073', (SELECT author_id FROM authors WHERE name = 'Various'));

-- Loans (loans.csv): an empty return_date in the CSV becomes NULL here
INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date, return_date) VALUES
    ('L001', 'M002', '9780000000028', '2026-09-01', '2026-09-22', NULL),
    ('L002', 'M004', '9780000000042', '2026-09-21', '2026-10-05', NULL),
    ('L003', 'M003', '9780000000059', '2026-09-20', '2026-10-20', NULL),
    ('L004', 'M001', '9780000000011', '2026-09-10', '2026-09-24', '2026-09-24'),
    ('L005', 'M001', '9780000000042', '2026-08-01', '2026-08-15', '2026-08-20'),
    ('L006', 'M003', '9780000000035', '2026-08-05', '2026-09-04', '2026-09-02'),
    ('L007', 'M002', '9780000000042', '2026-07-10', '2026-07-31', '2026-07-31'),
    ('L008', 'M002', '9780000000011', '2026-06-01', '2026-06-22', '2026-06-30'),
    ('L009', 'M004', '9780000000073', '2026-07-01', '2026-07-08', '2026-09-06'),
    ('L010', 'M004', '9780000000011', '2026-07-20', '2026-08-03', '2026-08-23');

-- Fines (fines.csv): paid is yes or no in the CSV, 1 or 0 here
INSERT INTO fines (loan_id, amount, paid) VALUES
    ('L005', 10, 1),
    ('L008', 40, 1),
    ('L009', 80, 0),
    ('L010', 40, 0);