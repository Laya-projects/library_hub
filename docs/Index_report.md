# Index report (Phase 3, Step 7)

## Test data

100,010 loans (the 10 starter loans plus 100,000 generated), 1,000 members and
1,000 items. They are built by `sql/gen_bench.sql`, and the timings come from
`benchmarks/index_bench.py`. Each time is the median of 3 runs on an in-memory
SQLite database.

## The 12 queries, slowest first

| Query | Time (ms) |
|---|---|
| **Q12** pair of titles borrowed by the same member | 12,342.1 |
| **Q5** items never borrowed | 220.8 |
| Q9 members with 3+ categories | 107.2 |
| Q4 top 3 titles | 76.9 |
| Q10 average loan length | 74.2 |
| Q6 members with no recent loan | 23.0 |
| Q2 items on loan | 11.1 |
| Q3 overdue loans | 8.7 |
| Q11 availability | 7.4 |
| Q1, Q7, Q8 | 0.0 |

The 2 slowest are **Q12** and **Q5**.

## Indexes added

```sql
CREATE INDEX idx_loans_isbn ON loans (isbn);
CREATE INDEX idx_loans_member_isbn ON loans (member_id, isbn);
```

SQLite does not create an index for a foreign key, so `loans.isbn` and
`loans.member_id` had none.

## Q5: items never borrowed

| | Time | EXPLAIN QUERY PLAN |
|---|---|---|
| Before | 217.2 ms | `SCAN i` then `SEARCH l USING AUTOMATIC COVERING INDEX (isbn=?) LEFT-JOIN` |
| After | **36.3 ms** | `SCAN i` then `SEARCH l USING INDEX idx_loans_isbn (isbn=?) LEFT-JOIN` |

About 6 times faster. Before the index, SQLite built a temporary index on
`loans.isbn` every time the query ran and threw it away afterwards. The permanent
index pays that cost once.

With automatic indexes switched off (`PRAGMA automatic_index = OFF`), which shows
the real cost of having no index at all: **4,261.5 ms without the index, 30.4 ms
with it**, about 140 times faster. Without any index, SQLite scans the whole
loans table once for every item.

## Q12: pair of titles borrowed by the same member

| | Time | EXPLAIN QUERY PLAN |
|---|---|---|
| Before | 4,823.0 ms | `SCAN l`, then `SEARCH b USING AUTOMATIC COVERING INDEX (member_id=?)` |
| After | 4,209.3 ms | `SCAN l USING COVERING INDEX idx_loans_member_isbn`, same `SEARCH b` |

Only about 13% faster. The plan changed from a table scan to a covering index
scan, but the time barely moved.

**Why the index does not fix Q12:** the cost is the number of title pairs, not
finding rows. Each member borrowed about 100 different titles, which is about
5,000 pairs per member, or about 5 million pair rows for 1,000 members. An
index helps SQLite find rows faster. It cannot reduce the number of rows the
self-join has to produce, group and sort.

**Note on the numbers:** the first run (the ranking) measured Q12 at 12.3 s and
the later before and after runs at 4.8 s and 4.2 s. The machine was busy in
between, so I compare before and after within the same run only. The ranking
and the conclusion are the same in both runs: Q12 is by far the slowest.

## An index I decided not to create

`items (category)`. The items table is small, and a category has only a few
distinct values, so the index would not narrow the search much. Every index
also makes each insert and update slower and takes up space, and it would
only help queries that already run in a fraction of a millisecond.

## Which query worries me at 10 million loans?

Q12. Its work grows with the square of the number of titles each member has
borrowed, and indexes do not change that. At 10 million loans I would not
compute it live. I would either count pairs only over recent loans, or keep a
summary table of pair counts that is updated when a loan is made, or run the
query as a scheduled report. Q5 and Q9 would be fine with the indexes above.