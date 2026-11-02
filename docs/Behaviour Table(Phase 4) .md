# Behaviour table (Phase 4)

Start the API with `TODAY=2026-10-12` and the site with `npm run dev`, then go through
the rows one at a time. Tick the **Done** column (change `☐` to `✅`) when the site
does what the table says. If a row does not work yet, write why in **Notes**.

## Catalogue

| # | What you do | What you should see | Done | Notes |
|---|---|---|---|---|
| 1 | Open `/` | "Loading catalogue...", then 7 cards, "7 results", and an availability badge on each | ✅ | |
| 2 | Type `py` and pause | "1 result" and one card | ✅ | |
| 3 | Type `zzz` | "No items match 'zzz'. Try a different word." | ✅ | |
| 4 | Clear the search box | All 7 cards come back | ✅ | |
| 5 | Choose a category | Only books of that category; `?category=` appears in the address | ✅ | |
| 6 | Sort by Pages, then Category | The order changes; `?sort=` appears in the address | ✅ | |
| 7 | Network tab on "Slow 3G", type quickly | An old response never replaces a newer one | ✅ | |
| 8 | Stop the API and open `/` | "Can't reach the library server." with a Retry button; Retry works once the API is back | ✅ | |

## Book cards and details

| # | What you do | What you should see | Done | Notes |
|---|---|---|---|---|
| 9 | Look at The Alchemist (every copy is out) | "0 of N available" and a **Join waiting list** button instead of Add to basket | ✅ | |
| 10 | Click **Join waiting list** | A toast: "<member> is #1 on the waiting list for 'The Alchemist'." | ✅ | |
| 11 | Look at the Encyclopaedia (reference item) | "Reference item: read in the library only" and no borrow button | ✅ | |
| 12 | Click a book title | The details page: title, authors, category, type, pages, ISBN and availability | ✅ | |
| 13 | Search `py`, open the book, click **Back to results** | `py` is still in the search box and the results are filtered | ✅ | |
| 14 | Do the same with the browser's back button | The same result | ✅ | |
| 15 | Open `/books/123` | The server's message (not found), a **Back to results** link, and no crash | ✅ | |

## My loans

| # | What you do | What you should see | Done | Notes |
|---|---|---|---|---|
| 16 | Pick Rahul Mehta (M002) and open **My loans** | L001 The Alchemist, due 2026-09-22, "OVERDUE (20 days)"; "Active loans: 1 of 5"; "Unpaid fines: ₹0" | ✅ | |
| 17 | Pick a member with no loans | "You have no active loans." | ✅ | |
| 18 | Stop the API and open **My loans** | The error message with a Retry button | ✅ | |

## Basket and checkout

| # | What you do | What you should see | Done | Notes |
|---|---|---|---|---|
| 19 | Click **Add to basket** on a book | The navbar shows "Basket (1)" and the button says "In basket" | ✅ | |
| 20 | As a Student, add a 4th item | "Basket full: Students can borrow 3 items." and the Add buttons are disabled | ✅ | |
| 21 | Change the member in the navbar | The basket is emptied | ✅ | |
| 22 | Open an empty basket | "Your basket is empty." with a link to the catalogue | ✅ | |
| 23 | Basket with a valid book (for example Wings of Fire as Asha Raman), click **Borrow** | "Borrowing...", then "Borrowed Wings of Fire. Due 2026-10-26." as a toast and under the list; the item leaves the basket | ✅ | |
| 24 | Go back to the catalogue after borrowing | The availability of that book has gone down by one | ✅ | |
| 25 | Borrow as Karthik (owes ₹120) | The R4 message under the item, exactly as the server sent it (including `₹`), and the item stays in the basket | ✅ | |

## Add item (librarian)

| # | What you do | What you should see | Done | Notes |
|---|---|---|---|---|
| 26 | Type ISBN `123` and leave the field | "ISBN must be exactly 13 digits." under the field; **Add item** is disabled | ✅ | |
| 27 | Leave the title empty and leave the field | "Title is required." | ✅ | |
| 28 | Type `0` in Copies | "Copies must be a whole number, at least 1." | ✅ | |
| 29 | Fill in a valid form and submit | "Adding...", then "Added '<title>' to the catalogue." and the form resets; the book appears in the catalogue | ✅ | |
| 30 | Add the same ISBN again | The server's message, shown unchanged | ✅ | |

## Whole site

| # | What you do | What you should see | Done | Notes |
|---|---|---|---|---|
| 31 | Open `/xyz` | "Page not found" with a link back to the catalogue | ✅ | |
| 32 | Set the browser width to 360 px and visit every screen | One column, nothing cut off, no sideways scrolling of the page | ✅ | |

