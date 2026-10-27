#!/usr/bin/env python3
"""
Generates synthetic TPC-H-shaped CSV data for the DEPN validation experiment.
Not the official dbgen tool -- a from-scratch generator producing structurally
realistic data (real skew in nation/region distribution, real date ranges,
real foreign-key integrity) at a modest scale, enough to give both query
planners genuine cardinality signal to choose varied plan shapes from.

    python generate_data.py [scale]   # scale = lineitem row count / 100000, default 1.0
"""
import csv, random, sys, pathlib, datetime

random.seed(20261026)  # reproducible
SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
OUT = pathlib.Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

N_REGION = 5
N_NATION = 25
N_SUPPLIER = int(1000 * SCALE)
N_CUSTOMER = int(15000 * SCALE)
N_PART = int(20000 * SCALE)
N_ORDERS = int(150000 * SCALE)
N_LINEITEM_TARGET = int(600000 * SCALE)  # ~4 lines/order average

REGIONS = ["AFRICA", "AMERICA", "ASIA", "EUROPE", "MIDDLE EAST"]
NATIONS = [f"NATION_{i}" for i in range(N_NATION)]
MKTSEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "HOUSEHOLD", "MACHINERY"]
PRIORITIES = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
RETURNFLAGS = ["A", "N", "R"]
LINESTATUS = ["O", "F"]
SHIPMODES = ["AIR", "FOB", "MAIL", "RAIL", "REG AIR", "SHIP", "TRUCK"]
CONTAINERS = ["SM BOX", "SM CASE", "LG BOX", "LG CASE", "JUMBO PKG", "WRAP BAG"]
BRANDS = [f"Brand#{i}" for i in range(1, 26)]


def write_csv(name, header, rows):
    path = OUT / f"{name}.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name}: {len(rows):,} rows -> {path}")


def rand_date(start, end):
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, delta))


print(f"Generating at scale {SCALE} (lineitem target ~{N_LINEITEM_TARGET:,} rows)")

region_rows = [(i, REGIONS[i], f"comment for region {i}") for i in range(N_REGION)]
write_csv("region", ["r_regionkey", "r_name", "r_comment"], region_rows)

nation_rows = [(i, NATIONS[i], i % N_REGION, f"comment for nation {i}") for i in range(N_NATION)]
write_csv("nation", ["n_nationkey", "n_name", "n_regionkey", "n_comment"], nation_rows)

supplier_rows = []
for i in range(N_SUPPLIER):
    supplier_rows.append((
        i, f"Supplier#{i:09d}", f"{random.randint(1,999)} Main St",
        random.randint(0, N_NATION - 1), f"555-{random.randint(1000,9999)}",
        round(random.uniform(-999, 9999), 2), f"supplier comment {i}"
    ))
write_csv("supplier", ["s_suppkey","s_name","s_address","s_nationkey","s_phone","s_acctbal","s_comment"], supplier_rows)

customer_rows = []
for i in range(N_CUSTOMER):
    customer_rows.append((
        i, f"Customer#{i:09d}", f"{random.randint(1,999)} Oak Ave",
        random.randint(0, N_NATION - 1), f"555-{random.randint(1000,9999)}",
        round(random.uniform(-999, 9999), 2), random.choice(MKTSEGMENTS),
        f"customer comment {i}"
    ))
write_csv("customer", ["c_custkey","c_name","c_address","c_nationkey","c_phone","c_acctbal","c_mktsegment","c_comment"], customer_rows)

part_rows = []
for i in range(N_PART):
    part_rows.append((
        i, f"part name {i}", f"Manufacturer#{(i % 5) + 1}", random.choice(BRANDS),
        f"type {i % 150}", random.randint(1, 50), random.choice(CONTAINERS),
        round(random.uniform(1, 2000), 2), f"part comment {i}"
    ))
write_csv("part", ["p_partkey","p_name","p_mfgr","p_brand","p_type","p_size","p_container","p_retailprice","p_comment"], part_rows)

partsupp_rows = []
for p in range(N_PART):
    suppliers_for_part = random.sample(range(N_SUPPLIER), k=min(4, N_SUPPLIER))
    for s in suppliers_for_part:
        partsupp_rows.append((
            p, s, random.randint(1, 9999), round(random.uniform(1, 1000), 2),
            f"partsupp comment {p}-{s}"
        ))
write_csv("partsupp", ["ps_partkey","ps_suppkey","ps_availqty","ps_supplycost","ps_comment"], partsupp_rows)

DATE_START = datetime.date(2015, 1, 1)
DATE_END = datetime.date(2025, 12, 31)

orders_rows = []
for i in range(N_ORDERS):
    odate = rand_date(DATE_START, DATE_END)
    orders_rows.append((
        i, random.randint(0, N_CUSTOMER - 1), random.choice(["O", "F", "P"]),
        round(random.uniform(100, 500000), 2), odate.isoformat(),
        random.choice(PRIORITIES), f"Clerk#{random.randint(1,1000):09d}",
        random.randint(0, 1), f"order comment {i}"
    ))
write_csv("orders", ["o_orderkey","o_custkey","o_orderstatus","o_totalprice","o_orderdate","o_orderpriority","o_clerk","o_shippriority","o_comment"], orders_rows)

lineitem_rows = []
ln_per_order = max(1, N_LINEITEM_TARGET // N_ORDERS)
for o in orders_rows:
    orderkey, odate = o[0], datetime.date.fromisoformat(o[4])
    n_lines = random.randint(1, max(1, ln_per_order * 2 - 1))
    for ln in range(1, n_lines + 1):
        shipdate = odate + datetime.timedelta(days=random.randint(1, 121))
        commitdate = odate + datetime.timedelta(days=random.randint(1, 121))
        receiptdate = shipdate + datetime.timedelta(days=random.randint(1, 30))
        lineitem_rows.append((
            orderkey, random.randint(0, N_PART - 1), random.randint(0, N_SUPPLIER - 1), ln,
            random.randint(1, 50), round(random.uniform(100, 100000), 2),
            round(random.uniform(0, 0.1), 2), round(random.uniform(0, 0.08), 2),
            random.choice(RETURNFLAGS), random.choice(LINESTATUS),
            shipdate.isoformat(), commitdate.isoformat(), receiptdate.isoformat(),
            random.choice(["DELIVER IN PERSON", "COLLECT COD", "NONE", "TAKE BACK RETURN"]),
            random.choice(SHIPMODES), f"lineitem comment {orderkey}-{ln}"
        ))
write_csv("lineitem", ["l_orderkey","l_partkey","l_suppkey","l_linenumber","l_quantity",
    "l_extendedprice","l_discount","l_tax","l_returnflag","l_linestatus","l_shipdate",
    "l_commitdate","l_receiptdate","l_shipinstruct","l_shipmode","l_comment"], lineitem_rows)

print("done.")
