#!/usr/bin/env python3
"""
Loads the generated TPC-H-shaped data into PostgreSQL and MySQL, then runs
every query in queries.sql against both with EXPLAIN (FORMAT JSON), saving
the raw captured plans. This is the actual data-collection step -- every
plan written to output/ came from a real query against a real, running
engine.

    python load_and_run.py --engine postgres   (or --engine mysql, or --engine both)
"""
import argparse, csv, json, pathlib, sys, time

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)

TABLES_IN_ORDER = ["region", "nation", "supplier", "customer", "part",
                    "partsupp", "orders", "lineitem"]


def load_postgres(dsn):
    import psycopg2
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    print("[postgres] applying schema...")
    cur.execute(open(HERE / "sql" / "schema_postgres.sql").read())
    for t in TABLES_IN_ORDER:
        path = DATA / f"{t}.csv"
        print(f"[postgres] loading {t} from {path} ...")
        with open(path) as f:
            cur.copy_expert(f"COPY {t} FROM STDIN WITH CSV HEADER", f)
    cur.execute("ANALYZE;")
    conn.close()
    print("[postgres] load complete.")


def load_mysql(host, user, password, db):
    import pymysql
    conn = pymysql.connect(host=host, user=user, password=password, local_infile=True)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {db}")
    cur.execute(f"CREATE DATABASE {db}")
    cur.execute(f"USE {db}")
    print("[mysql] applying schema...")
    for stmt in open(HERE / "sql" / "schema_mysql.sql").read().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)
    for t in TABLES_IN_ORDER:
        path = DATA / f"{t}.csv"
        print(f"[mysql] loading {t} from {path} ...")
        cur.execute(
            f"LOAD DATA LOCAL INFILE '{path}' INTO TABLE {t} "
            f"FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' "
            f"LINES TERMINATED BY '\\n' IGNORE 1 LINES"
        )
    cur.execute("ANALYZE TABLE region, nation, supplier, customer, part, partsupp, orders, lineitem")
    conn.commit()
    conn.close()
    print("[mysql] load complete.")


def run_postgres(dsn, queries):
    import psycopg2
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    plans = []
    errors = 0
    t0 = time.time()
    for i, q in enumerate(queries):
        try:
            cur.execute("EXPLAIN (FORMAT JSON) " + q)
            plan = cur.fetchone()[0]
            plans.append({"query": q, "plan": plan})
        except Exception as e:
            errors += 1
        if (i + 1) % 100 == 0:
            print(f"[postgres] {i+1}/{len(queries)} ({time.time()-t0:.0f}s, {errors} errors)")
    with open(OUT / "postgres_plans.json", "w") as f:
        json.dump(plans, f)
    print(f"[postgres] done: {len(plans)} plans captured, {errors} errors")


def run_mysql(host, user, password, db, queries):
    import pymysql
    conn = pymysql.connect(host=host, user=user, password=password, database=db)
    cur = conn.cursor()
    plans = []
    errors = 0
    t0 = time.time()
    for i, q in enumerate(queries):
        try:
            cur.execute("EXPLAIN FORMAT=JSON " + q)
            raw = cur.fetchone()[0]
            plan = json.loads(raw)
            plans.append({"query": q, "plan": plan})
        except Exception as e:
            errors += 1
        if (i + 1) % 100 == 0:
            print(f"[mysql] {i+1}/{len(queries)} ({time.time()-t0:.0f}s, {errors} errors)")
    with open(OUT / "mysql_plans.json", "w") as f:
        json.dump(plans, f)
    print(f"[mysql] done: {len(plans)} plans captured, {errors} errors")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["postgres", "mysql", "both"], required=True)
    ap.add_argument("--load", action="store_true", help="load schema+data first")
    ap.add_argument("--pg-dsn", default="dbname=depn_exp host=localhost")
    ap.add_argument("--mysql-host", default="127.0.0.1")
    ap.add_argument("--mysql-user", default="root")
    ap.add_argument("--mysql-password", default="")
    ap.add_argument("--mysql-db", default="depn_exp")
    args = ap.parse_args()

    queries = [l.strip().rstrip(";") for l in open(HERE / "queries.sql")
               if l.strip() and not l.startswith("--")]
    print(f"{len(queries)} queries loaded")

    if args.engine in ("postgres", "both"):
        if args.load:
            load_postgres(args.pg_dsn)
        run_postgres(args.pg_dsn, queries)

    if args.engine in ("mysql", "both"):
        if args.load:
            load_mysql(args.mysql_host, args.mysql_user, args.mysql_password, args.mysql_db)
        run_mysql(args.mysql_host, args.mysql_user, args.mysql_password, args.mysql_db, queries)
