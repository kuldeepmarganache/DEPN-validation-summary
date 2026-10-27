#!/usr/bin/env python3
"""
Generates a large, varied set of SELECT queries against the TPC-H-shaped
schema, parameterized to produce genuinely distinct execution plans (not
the same query run 2,400 times). Covers scans with and without usable
indexes, 2- and 3-way joins, sorts, aggregates, and correlated/derived
subqueries -- enough to exercise all ten of Table 3's canonical node types
across both engines' planners.

    python generate_queries.py > queries.sql   (one query per line, ';'-terminated)
"""
import random

random.seed(20261026)

MKTSEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "HOUSEHOLD", "MACHINERY"]
SHIPMODES = ["AIR", "FOB", "MAIL", "RAIL", "REG AIR", "SHIP", "TRUCK"]
PRIORITIES = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
RETURNFLAGS = ["A", "N", "R"]

queries = []

def add(q):
    # collapse to a single line -- the loader reads one query per line
    flat = " ".join(q.split())
    queries.append(flat.rstrip(";") + ";")

# 1. Seq Scan: filters on a non-indexed, low-selectivity column
for seg in MKTSEGMENTS:
    add(f"SELECT c_custkey, c_name FROM customer WHERE c_mktsegment = '{seg}'")
for i in range(0, 150000, 750):
    add(f"SELECT o_orderkey, o_totalprice FROM orders WHERE o_totalprice > {i}")

# 2. Index Scan: filters on indexed, high-selectivity columns
for y in range(2015, 2026):
    for m in range(1, 13, 3):
        add(f"SELECT l_orderkey, l_quantity FROM lineitem WHERE l_shipdate = '{y}-{m:02d}-15'")
for s in range(0, 1000, 10):
    add(f"SELECT o_orderkey FROM orders WHERE o_custkey = {s}")

# 3. Hash Join: equi-join on non-indexed/large-cardinality combos
for seg in MKTSEGMENTS:
    add(f"""SELECT c_name, o_orderkey, o_totalprice
            FROM customer JOIN orders ON c_custkey = o_custkey
            WHERE c_mktsegment = '{seg}'""")
for mode in SHIPMODES:
    add(f"""SELECT l_orderkey, p_name FROM lineitem JOIN part ON l_partkey = p_partkey
            WHERE l_shipmode = '{mode}'""")

# 4. Nested Loop: joins on indexed small-cardinality keys
for i in range(0, 500, 5):
    add(f"""SELECT o_orderkey, l_linenumber FROM orders JOIN lineitem
            ON o_orderkey = l_orderkey WHERE o_custkey = {i}""")

# 5. Merge Join hint via sorted-key joins (optimizer may or may not pick merge;
#    still a real, distinct plan either way)
for y in range(2015, 2026):
    add(f"""SELECT o_orderkey, c_name FROM orders JOIN customer
            ON o_custkey = c_custkey
            WHERE o_orderdate >= '{y}-01-01' AND o_orderdate < '{y+1}-01-01'
            ORDER BY o_orderkey""")

# 6. Sort: explicit ORDER BY on non-indexed columns
for seg in MKTSEGMENTS:
    add(f"SELECT c_custkey, c_acctbal FROM customer WHERE c_mktsegment = '{seg}' ORDER BY c_acctbal DESC")
for p in PRIORITIES:
    add(f"SELECT o_orderkey, o_totalprice FROM orders WHERE o_orderpriority = '{p}' ORDER BY o_totalprice")

# 7. Aggregate: GROUP BY with aggregation functions
for flag in RETURNFLAGS:
    add(f"""SELECT l_linestatus, COUNT(*), SUM(l_quantity), AVG(l_extendedprice)
            FROM lineitem WHERE l_returnflag = '{flag}' GROUP BY l_linestatus""")
for i in range(0, 25):
    add(f"""SELECT o_custkey, COUNT(*), SUM(o_totalprice) FROM orders
            WHERE o_custkey BETWEEN {i*500} AND {i*500+499} GROUP BY o_custkey""")

# 8. Subquery Scan: derived tables / IN subqueries
for seg in MKTSEGMENTS:
    add(f"""SELECT * FROM (
                SELECT c_custkey, c_name FROM customer WHERE c_mktsegment = '{seg}'
            ) AS seg_customers WHERE c_custkey < 5000""")
for y in range(2015, 2026):
    add(f"""SELECT c_name FROM customer WHERE c_custkey IN (
                SELECT o_custkey FROM orders
                WHERE o_orderdate >= '{y}-01-01' AND o_orderdate < '{y+1}-01-01'
            )""")

# 9. Multi-way joins (3+ tables): exercises join-order choice and mixed
#    scan/join node combinations across the plan tree
for mode in SHIPMODES:
    add(f"""SELECT c_name, o_orderkey, l_quantity, p_name
            FROM customer
            JOIN orders ON c_custkey = o_custkey
            JOIN lineitem ON o_orderkey = l_orderkey
            JOIN part ON l_partkey = p_partkey
            WHERE l_shipmode = '{mode}'""")
for nat in range(0, 25):
    add(f"""SELECT s_name, n_name, COUNT(*) FROM supplier
            JOIN nation ON s_nationkey = n_nationkey
            JOIN partsupp ON s_suppkey = ps_suppkey
            WHERE n_nationkey = {nat}
            GROUP BY s_name, n_name""")

# 10. Larger, multi-clause queries mixing several node types at once
for seg in MKTSEGMENTS:
    for p in PRIORITIES:
        add(f"""SELECT c_name, o_orderpriority, SUM(l_extendedprice * (1 - l_discount)) AS revenue
                FROM customer
                JOIN orders ON c_custkey = o_custkey
                JOIN lineitem ON o_orderkey = l_orderkey
                WHERE c_mktsegment = '{seg}' AND o_orderpriority = '{p}'
                GROUP BY c_name, o_orderpriority
                ORDER BY revenue DESC""")

# pad with further parameter sweeps over quantity/discount/tax thresholds to
# reach good coverage without repeating identical queries
for q in range(1, 50):
    for disc_x100 in range(0, 10, 2):
        add(f"""SELECT l_orderkey, l_quantity, l_discount FROM lineitem
                WHERE l_quantity > {q} AND l_discount > {disc_x100/100:.2f}""")

random.shuffle(queries)
print(f"-- {len(queries)} generated queries", flush=True)
for q in queries:
    print(q)
