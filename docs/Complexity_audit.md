# Complexity audit (Phase 2, task 2.1)

Predictions were written first, before any measurement. The measurements are added at the bottom.

## Variables

- **n**: number of items (books)
- **L**: number of loans, open and returned
- **F**: number of fines (at most one per loan, so F ≤ L)
- **q**: length of one waiting queue (small)
- **k**: number of overdue loans (k ≤ open loans ≤ L)

Titles, author lists and ISBNs are short strings, so I treat comparing them as O(1).

## What each repository call costs

I read `repositories.py` and checked every call.

| Call | What it does | Time |
|---|---|---|
| `items.get(isbn)` | dict lookup | O(1) |
| `items.list_all()` | copies the dict values into a new list | O(n) |
| `members.get(member_id)` | dict lookup | O(1) |
| `loans.get(loan_id)` | scans the list for the ID | O(L) |
| `loans.add(loan)` | calls `get` to refuse a repeated ID, then appends | O(L) |
| `loans.update(loan)` | scans the list for the ID, then replaces | O(L) |
| `loans.list_all()` | copies the list | O(L) |
| `loans.list_open()` | scans every loan, keeps the open ones | O(L) |
| `loans.list_for_member(id)` | scans every loan | O(L) |
| `loans.list_for_isbn(isbn)` | scans every loan | O(L) |
| `fines.add(fine)` | scans fines to refuse a second fine for one loan | O(F) |
| `fines.list_all()` | copies the list | O(F) |

Only `get` on items and members is a real lookup. Every loan call is a scan.

## Predictions

| Method | Predicted time | Predicted space | Why (one line) |
|---|---|---|---|
| `list_items` | O(n) | O(n) | `list_all` copies the item dict into a new list and nothing else happens |
| `search_items` | O(n) | O(n) | `list_all` copy, one pass over the items, and a result list that can hold up to n |
| `borrow` | O(L) | O(L) | items are only looked up in dicts, but about six passes over the loans happen per call (see below) |
| `return_item` | O(L) | O(1) | `loans.get` scans, `loans.update` scans again, and a fine `add` scans the fines; no new collection is built |
| `overdue_report` | O(L + k log k), worst case O(L log L) | O(L) | `list_open` scans all loans, the loop does O(1) work per open loan, then `sorted` sorts the k overdue lines |

## How I read each method

**`list_items`.** One call to `items.list_all()`, which copies the dict values. No loop of its own.

**`search_items`.** Strip and casefold the text, copy the items with `list_all`, then one list comprehension over n items. Each item check compares short strings. The result list can be as long as n if the text matches everything.

**`borrow`.** `get_member` and `get_item` are dict lookups, so n does not appear at all. The loan scans add up:
1. `unpaid_fines_for` copies all loans, builds a dict of all loans, and walks the fines (O(L + F), and the copies and the dict cost O(L) space).
2. `_check_limit` calls `list_for_member`.
3. `_check_no_duplicate` calls `list_for_member` again.
4. `_check_available` calls `list_for_isbn`.
5. `loans.add` calls `get`, which scans for a repeated loan ID.

That is about six passes over L loans plus one over F. The queue checks cost O(q). Total O(L), since F ≤ L and q is small.

**`return_item`.** `get_loan` scans once (O(L)). `get_member` and `get_item` are lookups. `days_late` and `fine` are O(1). `fines.add` scans the fines (O(F)). `loans.update` scans again (O(L)). Peeking at the queue is O(1). No list is built, so extra space is O(1).

**`overdue_report`.** `iter_overdue` starts with `loans.list_open()`, a full scan that builds a list. The loop is O(1) work per open loan. `overdue_report` then calls `sorted`, which reads every overdue line, so the generator's laziness is used up. Sorting k lines costs O(k log k). In the starter data k is tiny, so it looks like O(L). It is O(L log L) only if almost every loan is open and overdue.

In my benchmark every loan is open and overdue, so k = L. That is the worst case.

## What I expect to see when I measure

- `list_items` and `search_items` grow with n and do not change when L grows.
- `borrow` grows with L and does not change when n grows. Doubling L should roughly double the time.
- `return_item` also grows with L, but with a smaller constant than `borrow`, because it makes about three passes and not six.
- `overdue_report` grows with L. The sort should only matter when many loans are overdue.

## Measured results

## Measured results (median of 7 runs, ms)

| method | n=1,000 | n=5,000 | n=10,000 | n=50,000 |
|---|---|---|---|---|
| list_items | 0.011 | 0.017 | 0.060 | 0.651 |
| search_items | 0.369 | 2.041 | 6.565 | 23.224 |
| borrow | 0.051 | 0.063 | 0.066 | 0.119 |
| return_item | 0.051 | 0.051 | 0.056 | 0.064 |
| overdue_report | 0.265 | 1.589 | 4.720 | 12.403 |

In this table L is 0 for borrow and return_item, and L = n / 10 for overdue_report.

| method | 1k to 5k | 10k to 50k |
|---|---|---|
| list_items | 1.5x | 10.9x |
| search_items | 5.5x | 3.5x |
| borrow | 1.2x | 1.8x |
| return_item | 1.0x | 1.1x |
| overdue_report | 6.0x | 2.6x |

### Predicted vs measured

**search_items (predicted O(n)): matches.** Time grows about 5x for 5x more books, because every title and author is checked. The 3.5x at the top is noise.

**list_items (predicted O(n)): a surprise.** I expected steady growth, but it was nearly flat at small sizes (1.5x) and jumped 10.9x at 50,000. A list copy is so fast that the cost of calling the method dominates at small sizes, and at 50,000 the copy probably no longer fits in the CPU cache.

**borrow and return_item (predicted O(L)): flat, but this is expected.** I predicted that n does not appear in their cost, and that is what the table shows. The benchmark has no loans (L = 0), so the loan scans cost almost nothing. The O(L) prediction needs a second measurement where L varies (see below).

**overdue_report (predicted O(L + k log k)): matches the shape.** It grows with the number of loans (L = n / 10 here). Here k = L, so this is the worst case, but the sort's log factor is hidden by the per-loan Python work, so it looks linear. The 10,000 value looks noisy and is worth re-measuring.

## Second measurement: vary L, keep n fixed

| method | L=1,000 | L=2,000 | L=5,000 | L=10,000 |
|---|---|---|---|---|
| borrow | 0.460 | 0.699 | 1.695 | 3.204 |
| return_item | 0.162 | 0.488 | 0.761 | 1.390 |