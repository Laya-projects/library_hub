# Phase 2 benchmarks

Median of several runs, in milliseconds, on fake books sorted by title
(7 runs for `sorted()`, 21 for the searches, 3 for the hand-written sorts).
The searches look for the **last** book, which is the worst case for linear
search. Binary search runs on a list of ISBNs that is already in order.

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

No. Sorting 10,000 books takes ~5.3 ms while a single linear search takes ~1 ms, making linear search faster for a one-off query. However, binary search eliminates nearly the entire search cost afterward. In practice, sorting pays off after about 5 searches (or ~13 searches theoretically, based on a \(\log n\) break-even point). These savings hold only if the data remains sorted; frequent additions require repeated sorting or continuous list maintenance.

**Which of the three sorts is best for a list that is already almost sorted, and
why?**

Insertion sort. Each item is already close to its place, so it only shifts past a
few items and the whole sort is close to O(n). Bubble sort with the early exit
is also fast when the list is nearly sorted, but an item that is far to the right
of its place moves left only one step per pass. Selection sort does the same
O(n squared) work whatever the order.

## 5. Conclusions

- `sorted()` is hundreds to thousands of times faster than the hand-written
  sorts at 10,000 books, so in the library code I should use `sorted()` and keep
  the hand-written sorts for learning.
- Searching by ISBN with binary search is effectively instant, but only if the
  list is kept sorted, and it needs a sort first if the data is not.
- The numbers for searches under 1 ms are noisy. The shape (flat, linear,
  quadratic) is reliable. The exact ratios are not.