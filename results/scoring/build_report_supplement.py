"""Offline report appendix. Reads saved records only; never imports a provider.

Run from any directory:
  python results/scoring/build_report_supplement.py
Optional --output-dir writes a separate copy for verification.
The frozen scorer, references, reviews and original results remain unchanged.
"""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main(output_dir):
    manifest_path = ROOT / "config/basic-main-v1.json"
    manifest = read(manifest_path)
    labels_path = ROOT / "results/scoring/labels.json"
    reviews_path = ROOT / "results/scoring/reviews.jsonl"
    labels = read(labels_path)
    reviews = {}
    for line in reviews_path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            review = json.loads(line)
            reviews[review["run_id"]] = review
    csv_path = ROOT / "results/results.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = {r["run_id"]: r for r in csv.DictReader(handle)}

    all_records = []
    record_paths = {}
    for path in sorted((ROOT / "runs").rglob("*.json")):
        value = read(path)
        if value.get("run_kind") == "live_api" and "run_id" in value:
            require(value["run_id"] not in record_paths, "Duplicate live run ID")
            all_records.append(value)
            record_paths[value["run_id"]] = path
    formal = [r for r in all_records if r.get("experiment_id") == manifest["experiment_id"]]
    primary = [r for r in formal if r.get("is_primary")]
    expected = {j["job_id"] for j in manifest["jobs"]}
    require(len(primary) == len(expected) and {r["job_id"] for r in primary} == expected,
            "Missing, unexpected or duplicate primary jobs")
    for record in formal:
        require(record["run_id"] in rows, "Missing score row")
        require(record["run_id"] in reviews, "Missing review")
        require(record["source_hashes"] == manifest["source_hashes"], "Mixed source version")
        require(record["data_sha256"] == manifest["data_sha256"], "Mixed data version")
        require(record["config"] == manifest["config"], "Mixed configuration")
        row = rows[record["run_id"]]
        require(row["answer"] == (record["parsed_output"].get("answer") or ""),
                "Stale answer in score table")
        require(row["task_correct"] in ("True", "False"), "Unresolved score")
        require(row["semantic_support"] == reviews[record["run_id"]]["semantic_support"],
                "Stale semantic review")
        require(row["is_primary"] == str(record["is_primary"]), "Stale primary flag")
    require(set(rows) == {r["run_id"] for r in formal}, "Score rows do not match formal records")

    def group(record):
        return record["condition"] if record["variant"] == "baseline" else record["condition"] + "_improved"

    def correct(record):
        return rows[record["run_id"]]["task_correct"] == "True"

    def coverage(record, cited=False):
        label = labels[record["case_id"]]
        if label["answer_type"] == "insufficient":
            return None
        refs = set(label["reference_passages"])
        require(bool(refs), "Answerable task has no reference passages")
        ids = set(record["parsed_output"]["citations"] if cited else record["selected_passage_ids"])
        return len(refs & ids) / len(refs)

    pairs = []
    for cid in sorted({r["case_id"] for r in primary}):
        base = next(r for r in primary if r["case_id"] == cid and group(r) == "R0")
        improved = next(r for r in primary if r["case_id"] == cid and group(r) == "R0_improved")
        pair = {
            "case_id": cid,
            "reference_answer": labels[cid]["expected_answer"],
            "reference_passage_ids": labels[cid]["reference_passages"],
            "reference_requires_user_review": not labels[cid].get("reviewed_by_user", False),
            "coverage_applicability": "not_applicable_insufficient_task" if coverage(base) is None else "answerable_reference",
        }
        for prefix, record in (("baseline", base), ("improved", improved)):
            review = reviews[record["run_id"]]
            pair.update({prefix + "_" + key: value for key, value in {
                "run_id": record["run_id"],
                "record_path": record_paths[record["run_id"]].relative_to(ROOT).as_posix(),
                "answer": record["parsed_output"].get("answer"),
                "task_correct": correct(record),
                "api_status": record["api_status"],
                "format_status": record["format_status"],
                "locator_status": record["locator_status"],
                "semantic_support": review["semantic_support"],
                "input_reference_coverage": coverage(record),
                "cited_reference_coverage": coverage(record, cited=True) if record["api_status"] == "ok" else None,
                "elapsed_seconds": record["elapsed_seconds"],
                "preparation_ms": record.get("preparation_ms"),
                "call_count": record["call_count"],
                "citations": record["parsed_output"]["citations"],
                "judgment_source": review["judgment_source"],
            }.items()})
        pair.update(
            outcome="unchanged" if correct(base) == correct(improved) else ("improved" if correct(improved) else "worsened"),
            messages_identical=base["messages"] == improved["messages"],
            elapsed_delta_seconds=improved["elapsed_seconds"] - base["elapsed_seconds"],
            primary_extra_calls=improved["call_count"] - base["call_count"],
            baseline_retry_calls=sum(r["call_count"] for r in formal if r.get("retry_of") == base["run_id"]),
            improved_retry_calls=sum(r["call_count"] for r in formal if r.get("retry_of") == improved["run_id"]),
        )
        pairs.append(pair)

    conditions = {}
    for name in ("R0", "R1", "R2", "K", "R0_improved"):
        subset = [r for r in primary if group(r) == name]
        answerable = [r for r in subset if coverage(r) is not None]
        without_t01 = [r for r in subset if r["case_id"] != "T01"]
        t01 = next(r for r in subset if r["case_id"] == "T01")
        conditions[name] = {
            "primary_run_ids": [r["run_id"] for r in subset],
            "denominator": len(subset),
            "correct": sum(correct(r) for r in subset),
            "answerable_reference_denominator": len(answerable),
            "full_reference_in_input": sum(coverage(r) == 1 for r in answerable),
            "mean_input_reference_coverage": statistics.mean(coverage(r) for r in answerable),
            "t01_excluded": {"correct": sum(correct(r) for r in without_t01), "denominator": len(without_t01)},
            "t01_hypothetical_abstention_label": {
                "correct": sum(correct(r) for r in without_t01) + int(t01["parsed_output"].get("answer") == "证据不足"),
                "denominator": len(subset),
            },
        }

    failures = [{
        "run_id": r["run_id"],
        "record_path": record_paths[r["run_id"]].relative_to(ROOT).as_posix(),
        "case_id": r["case_id"], "purpose": r["purpose"],
        "status": r["status"], "http_status": r.get("http_status"),
        "error_code": r.get("error_code"), "elapsed_seconds": r["elapsed_seconds"],
        "response_raw_saved": r.get("response_raw") is not None,
        "call_count": r["call_count"],
        "evidence_limit": "Only recorded status/code/type and timing; detailed exception or HTTP error body was not preserved.",
    } for r in all_records if r["api_status"] != "ok"]

    sources = [manifest_path, labels_path, reviews_path, csv_path, Path(__file__)]
    sources.extend(record_paths.values())
    summary = {
        "artifact_kind": "post_hoc_offline_report_supplement",
        "experiment_id": manifest["experiment_id"],
        "model_calls_added": 0,
        "scoring_source": "Existing assistant references/reviews; user review pending; no relabeling.",
        "coverage_definition": "Reference ID intersection / reference IDs for currently answerable tasks; T05 excluded. Input and cited coverage are separate and do not establish semantic support.",
        "sensitivity_definition": "T01 exclusion and hypothetical abstention reference are descriptive post-hoc scenarios, not adopted labels. Other labels unchanged; semantic support is NOT recomputed.",
        "conditions": conditions,
        "pairs": {
            "count": len(pairs),
            "median_elapsed_delta_seconds": statistics.median(p["elapsed_delta_seconds"] for p in pairs),
            "slower": sum(p["elapsed_delta_seconds"] > 0 for p in pairs),
            "faster": sum(p["elapsed_delta_seconds"] < 0 for p in pairs),
            "primary_extra_calls": sum(p["primary_extra_calls"] for p in pairs),
            "improved_retry_calls": sum(p["improved_retry_calls"] for p in pairs),
            "messages_changed": sum(not p["messages_identical"] for p in pairs),
        },
        "call_accounting": {
            "total_calls": sum(r["call_count"] for r in all_records),
            "live_records": len(all_records),
            "formal_primary_calls": sum(r["call_count"] for r in primary),
            "formal_retry_calls": sum(r["call_count"] for r in formal if r.get("retry_of")),
            "failures": len(failures),
        },
        "failure_evidence": failures,
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(sources))},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "basic-pairs-detailed.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader()
        for pair in pairs:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v for k, v in pair.items()})
    (output_dir / "report-supplement.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"primary": len(primary), "pairs": len(pairs), "calls_added": 0,
                      "existing_calls": summary["call_accounting"]["total_calls"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    main(parser.parse_args().output_dir)
