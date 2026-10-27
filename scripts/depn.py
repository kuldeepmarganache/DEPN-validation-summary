#!/usr/bin/env python3
"""
DEPN: Dialect-Neutral Execution Plan Normalizer.

A real implementation of the mapping specified in Table 3 of the manuscript
(QuerySage_AIR_Springer_submission_Final.docx), covering the two engines
actually tested in this experiment (PostgreSQL 16, MySQL 8.0). Oracle 21c's
column exists in Table 3 as a design target but is not exercised here --
no Oracle instance is available in this environment.

For each node in a captured EXPLAIN plan, DEPN looks up the engine-specific
operator name against the canonical type table and returns the canonical
type, or None if the operator isn't one of the ten canonical types the
manuscript defines. "Correct" in this experiment means: a node whose
engine-specific operator appears in Table 3 is normalized to the matching
canonical type (this is a deterministic lookup, not a judgment call); a
node whose operator is outside Table 3's ten types is counted as unmapped.
Accuracy = (nodes normalized) / (total nodes seen) -- i.e. does this
10-type taxonomy actually cover what real query plans contain.
"""

# Table 3 of the manuscript, transcribed exactly.
# Postgres "Node Type" strings and MySQL EXPLAIN FORMAT=JSON access_type /
# operation strings, each mapped to one of the ten canonical types.

POSTGRES_MAP = {
    "Seq Scan":        "Seq Scan",
    "Index Scan":      "Index Scan",
    "Index Only Scan": "Index Scan",
    "Bitmap And":       "BitmapAnd/Or",
    "BitmapAnd":       "BitmapAnd/Or",
    "Bitmap Or":       "BitmapAnd/Or",
    "BitmapOr":        "BitmapAnd/Or",
    "Bitmap Heap Scan": "BitmapAnd/Or",
    "Bitmap Index Scan": "BitmapAnd/Or",
    "Hash Join":       "Hash Join",
    "Nested Loop":     "Nested Loop",
    "Merge Join":      "Merge Join",
    "Sort":            "Sort",
    "Aggregate":       "Aggregate",
    "HashAggregate":   "Aggregate",
    "GroupAggregate":  "Aggregate",
    "Subquery Scan":   "Subquery Scan",
    "Gather":          "Gather",
    "Gather Merge":    "Gather",
}

# MySQL's EXPLAIN FORMAT=JSON doesn't use PostgreSQL-style node-type labels;
# it nests dicts with access_type / using_* keys. depn_mysql_node_type()
# below derives the operator label from the node's shape, then this table
# maps that derived label onto the canonical type, matching Table 3's
# MySQL 8.0 column.
MYSQL_MAP = {
    "ALL":             "Seq Scan",
    "ref":             "Index Scan",
    "eq_ref":          "Index Scan",
    "range":           "Index Scan",
    "const":           "Index Scan",
    "index_merge":     "BitmapAnd/Or",
    "hash_join":        "Hash Join",
    "nested_loop":      "Nested Loop",
    "filesort":        "Sort",
    "grouping_operation": "Aggregate",
    "materialized_derived_table": "Subquery Scan",
}

CANONICAL_TYPES = [
    "Seq Scan", "Index Scan", "BitmapAnd/Or", "Hash Join", "Nested Loop",
    "Merge Join", "Sort", "Aggregate", "Subquery Scan", "Gather",
]


def normalize_postgres_node(node_type: str):
    """node_type: the raw 'Node Type' string from a Postgres EXPLAIN (FORMAT JSON) node."""
    return POSTGRES_MAP.get(node_type)


def _walk_postgres(plan_node, out):
    nt = plan_node.get("Node Type")
    if nt:
        out.append(nt)
    for child in plan_node.get("Plans", []):
        _walk_postgres(child, out)


def postgres_plan_node_types(explain_json):
    """explain_json: the parsed JSON from EXPLAIN (FORMAT JSON) ... -> list of raw node-type strings."""
    out = []
    root = explain_json[0]["Plan"] if isinstance(explain_json, list) else explain_json["Plan"]
    _walk_postgres(root, out)
    return out


def _walk_mysql(node, out):
    """MySQL's EXPLAIN FORMAT=JSON nests under keys like table/query_block/
    nested_loop/grouping_operation/ordering_operation etc. We detect the
    operator present at each nesting level and record a label from
    MYSQL_MAP's key space."""
    if not isinstance(node, dict):
        return
    if "query_block" in node:
        _walk_mysql(node["query_block"], out)
        return
    if "grouping_operation" in node:
        out.append("grouping_operation")
        _walk_mysql(node["grouping_operation"], out)
        return
    if "ordering_operation" in node:
        out.append("filesort")
        _walk_mysql(node["ordering_operation"], out)
        return
    if "duplicates_removal" in node:
        _walk_mysql(node["duplicates_removal"], out)
        return
    if "nested_loop" in node:
        if len(node["nested_loop"]) > 1:
            out.append("nested_loop")
        for child in node["nested_loop"]:
            _walk_mysql(child, out)
        return
    if "materialized_from_subquery" in node:
        out.append("materialized_derived_table")
        inner = node["materialized_from_subquery"].get("query_block")
        if inner:
            _walk_mysql(inner, out)
        return
    if "table" in node:
        t = node["table"]
        access_type = t.get("access_type")
        if access_type:
            out.append(access_type)
        if "attached_subqueries" in t:
            for sq in t["attached_subqueries"]:
                _walk_mysql(sq, out)
        return
    # fallback: recurse into any nested dict/list values
    for v in node.values():
        if isinstance(v, dict):
            _walk_mysql(v, out)
        elif isinstance(v, list):
            for item in v:
                _walk_mysql(item, out)


def mysql_plan_node_types(explain_json):
    out = []
    _walk_mysql(explain_json, out)
    return out


def normalize_mysql_node(raw_label: str):
    return MYSQL_MAP.get(raw_label)


def evaluate_plan(engine: str, explain_json):
    """Returns (n_normalized, n_total, [unmapped raw labels]) for one plan."""
    if engine == "postgres":
        raw_nodes = postgres_plan_node_types(explain_json)
        normalize = normalize_postgres_node
    elif engine == "mysql":
        raw_nodes = mysql_plan_node_types(explain_json)
        normalize = normalize_mysql_node
    else:
        raise ValueError(engine)

    unmapped = []
    n_ok = 0
    for raw in raw_nodes:
        canon = normalize(raw)
        if canon is not None:
            n_ok += 1
        else:
            unmapped.append(raw)
    return n_ok, len(raw_nodes), unmapped
