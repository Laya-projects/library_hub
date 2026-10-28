"""Phase 3 Step 7: find the 2 slowest queries on 100,000 loans, then add indexes.

Run from the project root:  python benchmarks/index_bench.py
Builds a throwaway database in memory, so nothing on disk changes.
"""

import re
import sqlite3
import statistics
import time

SQL_FILES = ["schema", "seed", "gen_bench"]
INDEXES = [
    "CREATE INDEX idx_loans_isbn ON loans (isbn)",
    "CREATE INDEX idx_loans_member_isbn ON loans (member_id, isbn)",
]


def build():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    for name in SQL_FILES:
        with open(f"sql/{name}.sql", encoding="utf-8") as file:
            conn.executescript(file.read())
    return conn


def load_queries():
    """Read sql/queries.sql and return {'Q1': sql, ...} using the '-- Qn:' comments."""
    with open("sql/queries.sql", encoding="utf-8") as file:
        text = file.read()
    queries = {}
    for statement in text.split(";\n"):
        match = re.search(r"-- (Q\d+):", statement)
        if match:
            queries[match.group(1)] = statement.strip()
    return queries


def median_ms(conn, sql, runs=3):
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        conn.execute(sql).fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)


def plan(conn, sql):
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql)]


def show(conn, label, name, sql):
    print(f"\n{name} {label}: {median_ms(conn, sql):.1f} ms")
    for line in plan(conn, sql):
        print("   ", line)


conn = build()
queries = load_queries()
print("loans:", conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0])

timings = {name: median_ms(conn, sql) for name, sql in queries.items()}
ranked = sorted(timings, key=timings.get, reverse=True)
print("\nAll queries, slowest first:")
for name in ranked:
    print(f"  {name:4} {timings[name]:8.1f} ms")

slowest_two = ranked[:2]
print("\nThe 2 slowest:", ", ".join(slowest_two))

for name in slowest_two:
    show(conn, "BEFORE", name, queries[name])

for statement in INDEXES:
    conn.execute(statement)
print("\nIndexes added:", *INDEXES, sep="\n  ")

for name in slowest_two:
    show(conn, "AFTER", name, queries[name])

# Extra: SQLite quietly builds a temporary index while a query runs, which hides
# the cost of having no index. Switch that off for Q5 only to see the real cost.
fresh = build()
fresh.execute("PRAGMA automatic_index = OFF")
before = median_ms(fresh, queries["Q5"], runs=1)
fresh.execute(INDEXES[0])
after = median_ms(fresh, queries["Q5"])
print(f"\nQ5 with automatic indexes OFF: {before:.1f} ms without idx_loans_isbn, "
      f"{after:.1f} ms with it")