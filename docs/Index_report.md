# Index report (Phase 3, Step 7)

## 1. Summary

Two indexes were added to `loans`. **Q5** (items never borrowed) became about 6 times
faster (about 140 times faster compared with having no index at all). **Q12** (pairs of
titles borrowed by the same member) changed its query plan but only improved by about 13%,
because its cost comes from the number of pairs, not from finding rows. At 10 million loans
Q12 is the query I would not run live.

## 2. Test data and method

- 100,010 loans (the 10 starter loans plus 100,000 generated), 1,000 members and 1,000
  items, built by `sql/gen_bench.sql`.
- Timings come from `benchmarks/index_bench.py`: each time is the median of 3 runs on an
  in-memory SQLite database.
- Plans come from `EXPLAIN QUERY PLAN`.
- "Before" and "after" are always compared within the same run (see section 6).

## 3. The slowest queries (before any new index)

| Rank | Query | Time (ms) |
|---|---|---|
| 1 | **Q12** pair of titles borrowed by the same member | 12,342.1 |
| 2 | **Q5** items never borrowed | 220.8 |
| 3 | Q9 members with 3+ categories | 107.2 |
| 4 | Q4 top 3 titles | 76.9 |
| 5 | Q10 average loan length | 74.2 |
| 6 | Q6 members with no recent loan | 23.0 |
| 7 | Q2 items on loan | 11.1 |
| 8 | Q3 overdue loans | 8.7 |
| 9 | Q11 availability | 7.4 |
| - | Q1, Q7, Q8 | 0.0 |

Q12 and Q5 are the two slowest, so they are the ones I worked on.

## 4. Indexes added

```sql
CREATE INDEX idx_loans_isbn        ON loans (isbn);
CREATE INDEX idx_loans_member_isbn ON loans (member_id, isbn);
```

**Why these.** SQLite does not create an index for a foreign key, so `loans.isbn` and
`loans.member_id` had none.

- `idx_loans_isbn` serves Q5, which joins `loans` to `items` on `isbn`.
- `idx_loans_member_isbn` serves Q12, which joins `loans` to itself by member and reads only
  the ISBN. Both columns are in the index, so it is a **covering index**: the query never
  touches the table.

The second index does not make the first redundant: `(member_id, isbn)` cannot answer a
search on `isbn` alone.

## 5. Results

| Query | Before | After | Change |
|---|---|---|---|
| **Q5** | 217.2 ms, `SEARCH l USING AUTOMATIC COVERING INDEX (isbn=?)` | **36.3 ms**, `SEARCH l USING INDEX idx_loans_isbn (isbn=?)` | about 6 times faster |
| **Q12** | 4,823.0 ms, `SCAN l` | 4,209.3 ms, `SCAN l USING COVERING INDEX idx_loans_member_isbn` | about 13% faster |

**Q5.** Before the index, SQLite built a temporary index on `loans.isbn` every time the
query ran and threw it away. The permanent index pays that cost once. To see the cost of
having no index at all, I switched automatic indexes off (`PRAGMA automatic_index = OFF`):
the query took 4,261.5 ms without the index and 30.4 ms with it, about 140 times faster.

**Q12.** The plan changed from a table scan to a covering index scan, but the time barely
moved. The cost is the number of title pairs, not finding rows. Each member borrowed about
100 different titles, which gives about 5,000 pairs per member, or about 5 million pair rows
for 1,000 members. An index cannot reduce the rows that the self-join has to produce, group
and sort.

## 6. A note on the numbers

The ranking run measured Q12 at 12.3 s, while the before and after runs measured 4.8 s and
4.2 s, because the machine was busy during the ranking run. Absolute times therefore vary
from run to run. The conclusions rest on comparisons made inside one run, and Q12 is by far
the slowest query in both.

## 7. An index I decided not to create

`items (category)`. The `items` table is small and a category has only a few distinct
values, so the index would not narrow the search much. Every index also makes each insert
and update slower and takes up space, and this one would only help queries that already run
in a fraction of a millisecond.

## 8. Which query worries me at 10 million loans?

**Q12.** Its work grows with the square of the number of titles each member has borrowed,
and indexes do not change that. At 10 million loans I would not compute it live. Options:

- count pairs only over recent loans,
- keep a summary table of pair counts that is updated when a loan is made, or
- run the query as a scheduled report.

Q5 is already about 36 ms with the index and scales with an index lookup per item. Q9 (107.2
ms before the indexes) should be measured again with them before I claim it is fine at that
size.