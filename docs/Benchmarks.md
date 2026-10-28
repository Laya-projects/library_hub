# Phase 2 benchmarks

Median of several runs, in milliseconds, on fake books sorted by title
(7 runs for `sorted()`, 21 for the searches, 3 for the hand-written sorts).
The searches look for the **last** book, which is the worst case for linear
search. Binary search runs on a list of ISBNs that is already in order.
The Library audit (section 5 onwards) uses the median of 7 runs, and the queue
test the median of 5, both from `benchmarks.py`.

## 1. Searching and sorting (the brief's table)

| n | linear_search_ms | binary_search_ms | sorted_key_ms | insertion_sort_ms |
|---|---|---|---|---|
| 1,000 | 0.0820 | 0.0012 | 0.1754 | 29.9389 |
| 5,000 | 0.7411 | 0.0029 | 1.8479 | 930.5347 |
| 10,000 | 1.0000 | 0.0029 | 5.2902 | 4,411.2932 |

## 2. All three hand-written sorts against sorted()

| n | bubble_sort_ms | insertion_sort_ms | selection_sort_ms | sorted_key_ms |
|---|---|---|---|---|
| 1,000 | 66.28 | 29.94 | 50.50 | 0.18 |
| 5,000 | 2,324.51 | 930.53 | 1,896.14 | 1.85 |
| 10,000 | 9,652.47 | 4,411.29 | 6,594.71 | 5.29 |

At 10,000 books, `sorted()` is about 830 times faster than insertion sort,
about 1,250 times faster than selection sort and about 1,820 times faster than
bubble sort.

## 3. Growth when n doubles (5,000 to 10,000)

| column | time ratio |
|---|---|
| linear_search_ms | 1.3x |
| binary_search_ms | 1.0x |
| bubble_sort_ms | 4.2x |
| insertion_sort_ms | 4.7x |
| selection_sort_ms | 3.5x |
| sorted_key_ms | 2.9x |

### What the shape says

- **Barely moves: binary search.** It went from 0.0012 ms at 1,000 books to
  0.0029 ms at 10,000, which is 10 times more books for about 2.4 times the
  time. Each step halves the remaining range, so the work grows with log n (about
  10 steps for 1,000 books, about 14 for 10,000).
- **Roughly doubles when n doubles: linear search, and `sorted()` a little
  above.** Linear search looks at every book until it finds the last one, so it
  is O(n). My measured ratio (1.3x) is lower than 2x and the 1,000 to 5,000 jump
  was larger than 5x, because these times are tiny (under 1 ms), so cache effects
  and timer noise matter. The overall trend is still linear. `sorted()` is
  O(n log n), so it grows a little faster than 2x (2.9x measured).
- **Roughly quadruples when n doubles: bubble, insertion and selection sort.**
  The measured ratios are 4.2x, 4.7x and 3.5x. All three compare items in two
  nested loops, so they are O(n squared): double the books and the work is four
  times bigger.

### Why insertion sort is the fastest of the three

On random data insertion sort moves each item only as far as it needs to, about
half the sorted part on average, so it does roughly n squared / 4 shifts. Bubble
sort compares and swaps neighbours in every pass (about n squared / 2 each, and
swaps are slower than shifts). Selection sort does about n squared / 2
comparisons, but only n swaps, which puts it in the middle.

## 4. Questions

**Binary search needs sorted data. If someone searches only once, is sorting
first worth it? After how many searches does it pay off?**

No. Sorting 10,000 books takes about 5.3 ms, while one linear search takes about
1 ms, so for a single search linear search wins. Each later search saves about
1 ms (1.0 ms linear minus 0.003 ms binary), so the break-even point is the sort
cost divided by the saving per search: 5.3 / 1.0, about 5.3. Sorting pays off from
the 6th search on. This only holds while the data stays sorted. If books are
added often, each addition either needs a re-sort or must be inserted in the
right place.

**Which of the three sorts is best for a list that is already almost sorted, and
why?**

Insertion sort. Each item is already close to its place, so it only shifts past a
few items and the whole sort is close to O(n). Bubble sort with the early exit
is also fast when the list is nearly sorted, but an item that is far to the right
of its place moves left only one step per pass. Selection sort does the same
O(n squared) work whatever the order.

## 5. Complexity audit: predictions (written BEFORE measuring)

n = number of books, L = number of loans, F = number of fines, k = results. The
audit world has n // 10 loans (two thirds open, one third returned with a fine),
so L = n / 10 and F is about L / 3.

| Method | Predicted time | Predicted extra space | Why |
|---|---|---|---|
| `list_items` | O(n) | O(n) | `list(dict.values())` copies every item |
| `search_items` | O(n) | O(k) | looks at each title and authors once; keeps the k matches |
| `borrow` | O(L + F) | O(L + F) | `get_member` and `get_item` are dictionary lookups, but the rule checks scan the loan list several times (`list_for_member` twice, `list_for_isbn`), `loans.add` scans once more for a duplicate ID, and `unpaid_total` reads every fine and loan |
| `return_item` | O(L + F) | O(1) | `get` and `update` each scan the loan list; `fines.add` scans the fines for a duplicate |
| `overdue_report` | O(L + k log k) | O(L + k) | `list_open` copies and scans the loans, then k overdue lines are sorted |
| `list.pop(0)`, serving n entries | O(n squared) in total | O(1) | every remaining entry shifts one place left |
| `deque.popleft()`, serving n entries | O(n) in total | O(1) | only the front pointer moves |

## 6. Audit: measured

| n books | loans | fines | list_items_ms | search_items_ms | borrow_ms | return_item_ms | overdue_report_ms |
|---|---|---|---|---|---|---|---|
| 1,000 | 100 | 33 | 0.004 | 0.436 | 0.038 | 0.015 | 0.077 |
| 5,000 | 500 | 166 | 0.018 | 2.1 | 0.100 | 0.038 | 0.366 |
| 10,000 | 1,000 | 333 | 0.082 | 4.4 | 0.385 | 0.210 | 0.976 |
| 50,000 | 5,000 | 1,666 | 0.656 | 47.1 | 2.0 | 1.1 | 5.9 |

When the library grows 5 times (10,000 to 50,000 books, so 1,000 to 5,000 loans),
the time grew by:

| method | predicted | measured |
|---|---|---|
| list_items | 5x (O(n)) | 8.0x |
| search_items | 5x (O(n)) | 10.7x |
| borrow | 5x (O(L + F)) | 5.2x |
| return_item | 5x (O(L + F)) | 5.2x |
| overdue_report | a little over 5x (O(L + k log k)) | 6.0x |

**Held.** `borrow` and `return_item` grew 5.2x for 5 times more loans, so both are
linear in the loan list, and `unpaid_total` building a dict first kept `borrow` from
becoming quadratic. `overdue_report` grew 6.0x, a little over 5x, as its extra sort predicts.

**Surprise 1: `search_items` (10.7x) and `list_items` (8.0x) grew faster than the
predicted 5x.** The cost per book roughly doubled (0.44 to 0.94 microseconds for
`search_items`), which probably means the books no longer fit in the processor's
cache. Big-O counts steps, not how long each step takes.

**Surprise 2: the jump from 5,000 to 10,000 books** (`return_item` 5.5x, `borrow`
3.9x, instead of 2x). These calls take well under a millisecond, so one slow moment
changes the median a lot; from 10,000 to 50,000 the ratios settle near 5x.

**Surprise 3: `overdue_report` (5.9 ms) is slower than `borrow` (2.0 ms)** although it
passes over the loans once. It does real work for every overdue loan (two lookups, a
fine calculation, a result object), about 3.5 microseconds each, so fewer steps can
still cost more. Big-O hides these constants.

## 7. pop(0) against popleft()

## Serving everybody from the front: pop(0) against popleft() (median ms)

| n | list.pop(0)_ms | deque.popleft()_ms | list is slower by |
|---|---|---|---|
| 10,000 | 7.2 | 1.4 | 5x |
| 50,000 | 185.0 | 7.9 | 23x |
| 100,000 | 850.3 | 58.0 | 15x |

## 8. Conclusions

- `sorted()` is hundreds to thousands of times faster than the hand-written
  sorts at 10,000 books, so in the library code I should use `sorted()` and keep
  the hand-written sorts for learning.
- Searching by ISBN with binary search is effectively instant, but only if the
  list is kept sorted, and it needs a sort first if the data is not.
- The numbers for searches under 1 ms are noisy. The shape (flat, linear,
  quadratic) is reliable. The exact ratios are not.