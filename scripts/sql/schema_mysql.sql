-- TPC-H-shaped schema (8 standard tables), MySQL 8.0 dialect.
-- See schema_postgres.sql for the scope note (synthetic data, real schema,
-- real engine, real plans -- not the official dbgen TPC-H dataset).

DROP TABLE IF EXISTS lineitem, orders, partsupp, part, customer, supplier, nation, region;

CREATE TABLE region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name      VARCHAR(25) NOT NULL,
    r_comment   VARCHAR(152)
) ENGINE=InnoDB;

CREATE TABLE nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name      VARCHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment   VARCHAR(152),
    FOREIGN KEY (n_regionkey) REFERENCES region(r_regionkey)
) ENGINE=InnoDB;

CREATE TABLE supplier (
    s_suppkey   INTEGER PRIMARY KEY,
    s_name      VARCHAR(25) NOT NULL,
    s_address   VARCHAR(40),
    s_nationkey INTEGER NOT NULL,
    s_phone     VARCHAR(15),
    s_acctbal   DECIMAL(12,2),
    s_comment   VARCHAR(101),
    FOREIGN KEY (s_nationkey) REFERENCES nation(n_nationkey)
) ENGINE=InnoDB;

CREATE TABLE customer (
    c_custkey    INTEGER PRIMARY KEY,
    c_name       VARCHAR(25) NOT NULL,
    c_address    VARCHAR(40),
    c_nationkey  INTEGER NOT NULL,
    c_phone      VARCHAR(15),
    c_acctbal    DECIMAL(12,2),
    c_mktsegment VARCHAR(10),
    c_comment    VARCHAR(117),
    FOREIGN KEY (c_nationkey) REFERENCES nation(n_nationkey)
) ENGINE=InnoDB;

CREATE TABLE part (
    p_partkey     INTEGER PRIMARY KEY,
    p_name        VARCHAR(55) NOT NULL,
    p_mfgr        VARCHAR(25),
    p_brand       VARCHAR(10),
    p_type        VARCHAR(25),
    p_size        INTEGER,
    p_container   VARCHAR(10),
    p_retailprice DECIMAL(12,2),
    p_comment     VARCHAR(23)
) ENGINE=InnoDB;

CREATE TABLE partsupp (
    ps_partkey    INTEGER NOT NULL,
    ps_suppkey    INTEGER NOT NULL,
    ps_availqty   INTEGER,
    ps_supplycost DECIMAL(12,2),
    ps_comment    VARCHAR(199),
    PRIMARY KEY (ps_partkey, ps_suppkey),
    FOREIGN KEY (ps_partkey) REFERENCES part(p_partkey),
    FOREIGN KEY (ps_suppkey) REFERENCES supplier(s_suppkey)
) ENGINE=InnoDB;

CREATE TABLE orders (
    o_orderkey      INTEGER PRIMARY KEY,
    o_custkey       INTEGER NOT NULL,
    o_orderstatus   VARCHAR(1),
    o_totalprice    DECIMAL(12,2),
    o_orderdate     DATE NOT NULL,
    o_orderpriority VARCHAR(15),
    o_clerk         VARCHAR(15),
    o_shippriority  INTEGER,
    o_comment       VARCHAR(79),
    FOREIGN KEY (o_custkey) REFERENCES customer(c_custkey)
) ENGINE=InnoDB;

CREATE TABLE lineitem (
    l_orderkey      INTEGER NOT NULL,
    l_partkey       INTEGER NOT NULL,
    l_suppkey       INTEGER NOT NULL,
    l_linenumber    INTEGER,
    l_quantity      DECIMAL(12,2),
    l_extendedprice DECIMAL(12,2),
    l_discount      DECIMAL(12,2),
    l_tax           DECIMAL(12,2),
    l_returnflag    VARCHAR(1),
    l_linestatus    VARCHAR(1),
    l_shipdate      DATE NOT NULL,
    l_commitdate    DATE,
    l_receiptdate   DATE,
    l_shipinstruct  VARCHAR(25),
    l_shipmode      VARCHAR(10),
    l_comment       VARCHAR(44),
    PRIMARY KEY (l_orderkey, l_linenumber),
    FOREIGN KEY (l_orderkey) REFERENCES orders(o_orderkey),
    FOREIGN KEY (l_partkey) REFERENCES part(p_partkey),
    FOREIGN KEY (l_suppkey) REFERENCES supplier(s_suppkey)
) ENGINE=InnoDB;

CREATE INDEX idx_lineitem_shipdate ON lineitem(l_shipdate);
CREATE INDEX idx_lineitem_suppkey ON lineitem(l_suppkey);
CREATE INDEX idx_orders_custkey ON orders(o_custkey);
CREATE INDEX idx_orders_orderdate ON orders(o_orderdate);
CREATE INDEX idx_customer_nationkey ON customer(c_nationkey);
CREATE INDEX idx_partsupp_partkey ON partsupp(ps_partkey);
