#!/usr/bin/env python3
"""
Runs DEPN against every captured plan in output/{postgres,mysql}_plans.json
and reports the real resulting accuracy -- whatever it turns out to be.

    python evaluate.py
"""
import json, pathlib, collections, csv, datetime
import depn

HERE = pathlib.Path(__file__).parent
OUT = HERE / "output"

total_ok = 0
total_nodes = 0
per_engine = {}
unmapped_counter = collections.Counter()
plan_rows = []  # for the supplementary CSV: one row per captured plan

for engine, fname in [("postgres", "postgres_plans.json"), ("mysql", "mysql_plans.json")]:
    path = OUT / fname
    if not path.exists():
        print(f"[skip] {path} not found")
        continue
    plans = json.load(open(path))
    e_ok, e_total = 0, 0
    for rec in plans:
        ok, n, unmapped = depn.evaluate_plan(engine, rec["plan"])
        e_ok += ok
        e_total += n
        for u in unmapped:
            unmapped_counter[(engine, u)] += 1
        plan_rows.append({
            "engine": engine,
            "query": rec["query"][:200],
            "nodes_total": n,
            "nodes_normalized": ok,
            "nodes_unmapped": n - ok,
        })
    per_engine[engine] = (e_ok, e_total, len(plans))
    total_ok += e_ok
    total_nodes += e_total

print()
print("=" * 70)
for engine, (ok, total, n_plans) in per_engine.items():
    pct = 100 * ok / total if total else 0
    print(f"{engine:10s}: {n_plans:5d} plans, {total:6d} nodes, {ok:6d} normalized ({pct:.1f}%)")

overall_pct = 100 * total_ok / total_nodes if total_nodes else 0
total_plans = sum(n for _, _, n in per_engine.values())
print("-" * 70)
print(f"{'TOTAL':10s}: {total_plans:5d} plans, {total_nodes:6d} nodes, {total_ok:6d} normalized ({overall_pct:.2f}%)")
print("=" * 70)

if unmapped_counter:
    print("\nUnmapped node types (not in Table 3's ten canonical types):")
    for (engine, label), count in unmapped_counter.most_common(20):
        print(f"  {engine:10s} {label:30s} {count:5d}")

# write the supplementary CSV (per-plan records) and a summary JSON
with open(OUT / "depn_validation_plans.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["engine", "query", "nodes_total", "nodes_normalized", "nodes_unmapped"])
    w.writeheader()
    w.writerows(plan_rows)

summary = {
    "generated": datetime.datetime.now().isoformat(),
    "engines_tested": list(per_engine.keys()),
    "oracle_tested": False,
    "oracle_note": "Oracle 21c has no macOS distribution; not empirically tested in this experiment. Table 3's Oracle column remains a documented design target.",
    "schema_note": "Synthetic TPC-H-shaped data (not official dbgen), scale ~1x (~600k lineitem rows).",
    "per_engine": {e: {"plans": n, "nodes_total": t, "nodes_normalized": ok, "pct": round(100*ok/t, 2) if t else None}
                   for e, (ok, t, n) in per_engine.items()},
    "overall": {"plans": total_plans, "nodes_total": total_nodes, "nodes_normalized": total_ok,
                "pct": round(overall_pct, 2)},
    "unmapped_node_types": {f"{e}:{l}": c for (e, l), c in unmapped_counter.items()},
}
with open(OUT / "depn_validation_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"\nWrote {OUT / 'depn_validation_plans.csv'}")
print(f"Wrote {OUT / 'depn_validation_summary.json'}")
