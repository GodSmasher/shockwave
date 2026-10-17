"""Evaluate Shockwave's reverse-mode SPOF detection against ground-truth.

Metrics:
  - Recall@K: did the expected SPOF appear in the top-K hidden_spofs result?
  - Hidden Recall@K: same but only counting min_hops >= 2 (true hidden)

Prints a table + headline numbers.
"""
import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.graph.reverse import find_hidden_spofs

GT_PATH = Path(__file__).resolve().parents[1] / "data" / "ground_truth_spofs.csv"


def slug(s: str) -> str:
    return hashlib.md5(s.lower().strip().encode()).hexdigest()[:12]


def evaluate(k_values: list[int] = [5, 10]) -> dict:
    with GT_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    hits = {k: 0 for k in k_values}
    hidden_hits = {k: 0 for k in k_values}
    total = len(rows)
    total_hidden = sum(1 for r in rows if int(r["min_hops"]) >= 2)

    print(f"Evaluating {total} ground-truth SPOFs ({total_hidden} truly hidden ≥2-hop)...\n")
    print(f"{'Target':<22} {'Expected SPOF':<22} {'Hops':<5} {'Found@':<8} {'Rank':<6}")
    print("-" * 70)

    for row in rows:
        target = row["target"].strip()
        expected = row["expected_spof"].strip()
        gt_hops = int(row["min_hops"])
        tid = slug(target)

        spofs = find_hidden_spofs(tid, max_hops=4, limit=20)
        names = [s["name"] for s in spofs]

        rank = None
        for i, name in enumerate(names):
            # Match on normalized name — case-insensitive, strip punctuation
            if name.lower().strip() == expected.lower().strip():
                rank = i + 1
                break
            # Also allow partial match if GT name is contained
            if expected.lower() in name.lower() or name.lower() in expected.lower():
                if rank is None:
                    rank = i + 1

        found_at = max(k_values) + 1 if rank is None else rank
        results.append({
            "target": target,
            "expected": expected,
            "gt_hops": gt_hops,
            "rank": rank,
            "found_in_top": [k for k in k_values if rank is not None and rank <= k],
        })

        for k in k_values:
            if rank is not None and rank <= k:
                hits[k] += 1
                if gt_hops >= 2:
                    hidden_hits[k] += 1

        rank_str = str(rank) if rank is not None else "—"
        top_str = ",".join(str(k) for k in k_values if rank is not None and rank <= k) or "—"
        print(f"{target:<22} {expected:<22} {gt_hops:<5} {top_str:<8} {rank_str:<6}")

    print()
    print("=" * 70)
    print("SHOCKWAVE DETECTION METRICS")
    print("=" * 70)
    for k in k_values:
        pct = 100 * hits[k] / total
        hidden_pct = 100 * hidden_hits[k] / total_hidden if total_hidden else 0
        print(f"  Recall@{k:<3}         {hits[k]:>2}/{total}  ({pct:5.1f}%)")
        print(f"  Hidden Recall@{k:<3}  {hidden_hits[k]:>2}/{total_hidden}  ({hidden_pct:5.1f}%)   [SPOFs ≥2 hops away]")
    print()
    print(f"HEADLINE: Shockwave findet {hits[k_values[-1]]}/{total} dokumentierter SPOFs.")
    return {
        "total": total,
        "total_hidden": total_hidden,
        "hits": hits,
        "hidden_hits": hidden_hits,
        "details": results,
    }


if __name__ == "__main__":
    evaluate()
