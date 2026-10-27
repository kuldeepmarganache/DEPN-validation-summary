-- TPC-H-shaped schema (8 standard tables), PostgreSQL dialect.
-- Not the official dbgen-generated TPC-H dataset -- a structurally
-- equivalent schema populated with synthetic data for the purpose of
-- generating real, varied execution plans to validate DEPN's node-type
-- mapping (Table 3 of the manuscript). This distinction is reported
-- honestly in the final write-up.

DROP TABLE IF EXISTS lineitem, orders, partsupp, part, customer, supplier, nation, region CASCADE;

CREATE TABLE region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name      VARCHAR(25) NOT NULL,
    r_comment   VARCHAR(152)
);

CREATE TABLE nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name      VARCHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL REFERENCES region(r_regionkey),
    n_comment   VARCHAR(152)
);

CREATE TABLE supplier (
    s_suppkey   INTEGER PRIMARY KEY,
    s_name      VARCHAR(25) NOT NULL,
    s_address   VARCHAR(40),
    s_nationkey INTEGER NOT NULL REFERENCES nation(n_nationkey),
    s_phone     VARCHAR(15),
    s_acctbal   NUMERIC(12,2),
    s_comment   VARCHAR(101)
);

CREATE TABLE customer (
    c_custkey    INTEGER PRIMARY KEY,
    c_name       VARCHAR(25) NOT NULL,
    c_address    VARCHAR(40),
    c_nationkey  INTEGER NOT NULL REFERENCES nation(n_nationkey),
    c_phone      VARCHAR(15),
    c_acctbal    NUMERIC(12,2),
    c_mktsegment VARCHAR(10),
    c_comment    VARCHAR(117)
);

CREATE TABLE part (
    p_partkey     INTEGER PRIMARY KEY,
    p_name        VARCHAR(55) NOT NULL,
    p_mfgr        VARCHAR(25),
    p_brand       VARCHAR(10),
    p_type        VARCHAR(25),
    p_size        INTEGER,
    p_container   VARCHAR(10),
    p_retailprice NUMERIC(12,2),
    p_comment     VARCHAR(23)
);

CREATE TABLE partsupp (
    ps_partkey    INTEGER NOT NULL REFERENCES part(p_partkey),
    ps_suppkey    INTEGER NOT NULL REFERENCES supplier(s_suppkey),
    ps_availqty   INTEGER,
    ps_supplycost NUMERIC(12,2),
    ps_comment    VARCHAR(199),
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

CREATE TABLE orders (
    o_orderkey      INTEGER PRIMARY KEY,
    o_custkey       INTEGER NOT NULL REFERENCES customer(c_custkey),
    o_orderstatus   VARCHAR(1),
    o_totalprice    NUMERIC(12,2),
    o_orderdate     DATE NOT NULL,
    o_orderpriority VARCHAR(15),
    o_clerk         VARCHAR(15),
    o_shippriority  INTEGER,
    o_comment       VARCHAR(79)
);

CREATE TABLE lineitem (
    l_orderkey      INTEGER NOT NULL REFERENCES orders(o_orderkey),
    l_partkey       INTEGER NOT NULL REFERENCES part(p_partkey),
    l_suppkey       INTEGER NOT NULL REFERENCES supplier(s_suppkey),
    l_linenumber    INTEGER,
    l_quantity      NUMERIC(12,2),
    l_extendedprice NUMERIC(12,2),
    l_discount      NUMERIC(12,2),
    l_tax           NUMERIC(12,2),
    l_returnflag    VARCHAR(1),
    l_linestatus    VARCHAR(1),
    l_shipdate      DATE NOT NULL,
    l_commitdate    DATE,
    l_receiptdate   DATE,
    l_shipinstruct  VARCHAR(25),
    l_shipmode      VARCHAR(10),
    l_comment       VARCHAR(44),
    PRIMARY KEY (l_orderkey, l_linenumber)
);

-- indexes: deliberately partial, so some filters hit Seq Scan and others
-- hit Index Scan -- matters for exercising DEPN's full node-type coverage
CREATE INDEX idx_lineitem_shipdate ON lineitem(l_shipdate);
CREATE INDEX idx_lineitem_suppkey ON lineitem(l_suppkey);
CREATE INDEX idx_orders_custkey ON orders(o_custkey);
CREATE INDEX idx_orders_orderdate ON orders(o_orderdate);
CREATE INDEX idx_customer_nationkey ON customer(c_nationkey);
CREATE INDEX idx_partsupp_partkey ON partsupp(ps_partkey);
