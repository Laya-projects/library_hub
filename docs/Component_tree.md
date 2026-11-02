# Component tree and state

## Tree

```
BrowserRouter (main.jsx)
└─ App
   └─ MemberProvider         members, currentMember
      └─ BasketProvider      basket (useReducer)
         └─ AppShell
            └─ Layout        toast (ToastContext)
               ├─ Navbar
               └─ Routes
                  ├─ /            CataloguePage
                  │                SearchBar, CategoryFilter, SortSelect
                  │                BookList > BookCard > AvailabilityBadge, BookActions
                  ├─ /books/:isbn BookDetailsPage (AvailabilityBadge, BookActions)
                  ├─ /me          MyLoansPage
                  ├─ /basket      BasketPage
                  ├─ /admin/add   AddItemPage > AddItemForm
                  └─ *            NotFoundPage
```

## State and props

| Component | State it owns | Props |
|---|---|---|
| MemberProvider | members, currentId, loading, error | children |
| BasketProvider | items, message (reducer) | children |
| Layout | toast | navbar, children |
| Navbar | nothing | basketCount, members, membersLoading, currentMemberId, onMemberChange |
| CataloguePage | categories; books, loading, error (useBooks) | none (search, category, sort are in the URL) |
| BookDetailsPage | book, loading, error | none (isbn from the route) |
| MyLoansPage | data, loading, error | none (member from context) |
| BasketPage | submitting, results | none (basket from context) |
| AddItemForm | values, touched, submitting, serverError, success | onCreated |
| SearchBar, CategoryFilter, SortSelect | nothing | value, onChange (and categories) |
| BookList | nothing | books, search |
| BookCard | nothing | book, to |
| BookActions | nothing | book (reads member, basket, toast from context) |
| AvailabilityBadge | nothing | available, total, itemType |

## Where each piece of state lives

- **Search, category, sort:** the URL query string, so "Back to results" and the browser's back button work.
- **Current member:** `MemberContext`, because the navbar, loans, basket and `BookActions` all need it.
- **Basket:** `BasketContext` with `useReducer` (`ADD`, `REMOVE`, `CLEAR`). It is cleared when the member changes. The limit check here is for comfort only; the server's rule is the one that must stay.
- **Toast:** `Layout`, shared through `ToastContext`.
- **Fetched data (books, one book, loans):** inside the page that shows it, never in a global store.
- **Old responses:** every fetch uses an `AbortController`, so a late response never overwrites a newer one.
