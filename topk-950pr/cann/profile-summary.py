"""Select 50 chronological real TopKV2 records from one fresh case directory."""

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path


def summarize(root, name):
    profiles = list(root.glob("profile-final-" + name + "/**/kernel_details.csv"))
    assert len(profiles) == 1, (name, "Expected one fresh profile", profiles)
    with profiles[0].open() as handle:
        captured = list(csv.DictReader(handle))
    assert 50 <= len(captured) <= 60, (name, len(captured))
    assert {row["Name"] for row in captured} == {"TopKV2"}
    captured.sort(key=lambda row: float(row["Start Time(us)"].strip()))
    selected = captured[-50:]
    tasks = []
    for path in root.glob("profile-final-" + name + "/**/task_time.csv"):
        with path.open() as handle:
            tasks.extend(csv.DictReader(handle))
    assert tasks, "Missing task_time.csv"
    task_types = Counter(row.get("kernel_type", row.get("Task Type", "unknown")) for row in tasks)
    assert not any("AICPU" in kind.upper() for kind in task_types), (
        "Unexpected AICPU task: review baseline route"
    )
    compute_types = sorted(kind for kind in task_types if kind.startswith("KERNEL"))
    assert compute_types, "No underlying computation tasks found"
    result = {
        "case": name,
        "kernel_records": selected,
        "task_records": tasks,
        "profile_captured_records": len(captured),
        "profile_launched_records": 60,
        "profile_selection": "last 50 records in device timestamp order",
        "kernel_samples_us": [float(r["Duration(us)"]) for r in selected],
        "kernel_median_us": statistics.median(float(r["Duration(us)"]) for r in selected),
        "task_types": dict(task_types),
        "compute_task_types": compute_types,
        "expected_vector_route": set(compute_types) <= {"KERNEL_MIX_AIV", "KERNEL_AIV"},
    }
    (root / "profile-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        name,
        "selected",
        50,
        "median_us",
        result["kernel_median_us"],
        "task_types",
        dict(task_types),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case", required=True, choices=["decode", "prefill-k1024", "prefill-k2048"]
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    summarize(args.root, args.case)
