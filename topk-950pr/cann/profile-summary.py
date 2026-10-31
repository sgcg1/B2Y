"""Select a chronological tail of 50 real TopKV2 records per fresh run."""

import csv
import json
import statistics
from collections import Counter
from pathlib import Path

summary = {}
for name in ["decode", "prefill-k1024", "prefill-k2048"]:
    profiles = list(Path(".").glob("profile-final-" + name + "/**/kernel_details.csv"))
    assert len(profiles) == 1, (name, "Use a fresh directory; expected one profile", profiles)
    with profiles[0].open() as handle:
        captured = list(csv.DictReader(handle))
    assert 50 <= len(captured) <= 60, (name, len(captured))
    assert {row["Name"] for row in captured} == {"TopKV2"}
    captured.sort(key=lambda row: float(row["Start Time(us)"].strip()))
    selected = captured[-50:]
    tasks = []
    for path in Path(".").glob("profile-final-" + name + "/**/task_time.csv"):
        with path.open() as handle:
            tasks.extend(csv.DictReader(handle))
    assert tasks, "Missing task_time.csv: inspect profiler output"
    summary[name] = {
        "kernel_records": selected,
        "task_records": tasks,
        "profile_captured_records": len(captured),
        "profile_launched_records": 60,
        "profile_selection": "last 50 records in device timestamp order",
        "kernel_median_us": statistics.median(float(r["Duration(us)"]) for r in selected),
    }
    task_types = Counter(row.get("Task Type", row.get("kernel_type", "unknown")) for row in tasks)
    print(
        name,
        "n",
        len(selected),
        "median_us",
        summary[name]["kernel_median_us"],
        "task_types",
        dict(task_types),
    )
Path("profile-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
