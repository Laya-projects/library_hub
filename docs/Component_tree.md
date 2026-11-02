# Component tree and state

App
├─ MemberProvider        (context: members, currentMember)
├─ BasketProvider        (context: basket reducer)
└─ Router
   └─ Layout             (toast message)
      ├─ Navbar
      └─ pages: CataloguePage, BookDetailsPage, MyLoansPage,
                BasketPage, AddItemPage, NotFoundPage

| Component | State it owns | Props it receives |
|---|---|---|
| App | nothing (wraps providers and router) | none |
| MemberProvider | members, currentMember | children |
| BasketProvider | the basket (a reducer) | children |
| Layout | the toast message | children |
| Navbar | nothing | basket count, member list and selection (from context) |
| CataloguePage | books, loading, error (via useBooks) | none; search, category and sort live in the URL |
| SearchBar, CategoryFilter, SortSelect | nothing | value, onChange |
| BookList | nothing | books |
| BookCard | nothing | book, onAdd |
| AvailabilityBadge | nothing | available, total, itemType |
| BookDetailsPage | book, loading, error | route parameter isbn |
| MyLoansPage | loans, loading, error | none (member from context) |
| BasketPage | submitting, results | none (basket from context) |
| AddItemForm | field values, touched fields, submitting | onCreated |

## Where each piece of state lives
- Search text, category, sort: the URL query string, so "Back to results" works.
- Current member: MemberContext, because the navbar, loans and basket all need it.
- Basket: BasketContext with useReducer, because the navbar count and the basket page need it.
- Fetched data (books, loans): inside the page that shows it, never in a global store.