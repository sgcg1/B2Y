"""Strict fresh-profile parser; chronological tail, per-call sums and envelopes."""
import csv
from decimal import Decimal
import statistics


def summarize_rows(rows, kernels_per_call, samples=50, launched=60):
    assert kernels_per_call in [1, 4]
    assert samples * kernels_per_call <= len(rows) <= launched * kernels_per_call, len(rows)
    assert len(rows) % kernels_per_call == 0, "Partial pipeline capture"
    rows = sorted(rows, key=lambda r: Decimal(r["Start Time(us)"].strip()))
    selected = rows[-samples * kernels_per_call:]
    streams = {r["Stream Id"] for r in selected if "Stream Id" in r}
    assert len(streams) <= 1, ("Review multiple streams", streams)
    groups = []
    labels = ["hist", "prepare", "compact", "finish"] if kernels_per_call == 4 else ["kernel"]
    for i in range(samples):
        group = selected[i * kernels_per_call:(i + 1) * kernels_per_call]
        if kernels_per_call == 4 and all("Block Num" in r for r in group):
            assert [int(r["Block Num"].strip()) for r in group] == [4, 1, 4, 1], "Unexpected P4 task order"
        starts = [Decimal(r["Start Time(us)"].strip()) for r in group]
        durations = [Decimal(r["Duration(us)"].strip()) for r in group]
        assert all(d > 0 for d in durations)
        gaps = [starts[j + 1] - (starts[j] + durations[j]) for j in range(kernels_per_call - 1)]
        assert all(g >= 0 for g in gaps), "Overlapping tasks: positional grouping not accepted"
        envelope = starts[-1] + durations[-1] - starts[0]
        assert envelope == sum(durations) + sum(gaps)
        groups.append({"durations_us": dict(zip(labels, map(float, durations))),
                       "gaps_us": list(map(float, gaps)), "gap_sum_us": float(sum(gaps)), "sum_kernel_us": float(sum(durations)),
                       "envelope_us": float(envelope)})
    return {"captured_records": len(rows), "selected_records": selected,
            "selection": "last 50 complete calls in chronological device order, never fastest",
            "calls": groups,
            "stage_median_us": {label: statistics.median(g["durations_us"][label] for g in groups) for label in labels},
            "sum_kernel_median_us": statistics.median(g["sum_kernel_us"] for g in groups),
            "gap_sum_median_us": statistics.median(g["gap_sum_us"] for g in groups),
            "envelope_median_us": statistics.median(g["envelope_us"] for g in groups)}


def summarize_profile(root, kernels_per_call):
    files = list(root.rglob("kernel_details.csv"))
    assert len(files) == 1, ("Expected one fresh profile", files)
    with files[0].open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    names = {r["Name"] for r in rows}
    if kernels_per_call == 4:
        assert all("main_kernel" in name for name in names), names
    else:
        assert all("main_kernel" in name for name in names) or names == {"TopKV2"}, names
    task_files = list(root.rglob("task_time.csv"))
    assert task_files, "Missing underlying task_time.csv"
    tasks = []
    for path in task_files:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            tasks.extend(csv.DictReader(handle))
    assert tasks
    task_types = {r.get("kernel_type", r.get("Task Type", "unknown")) for r in tasks}
    assert not any("AICPU" in kind.upper() for kind in task_types), task_types
    compute = [r for r in tasks if r.get("kernel_type", r.get("Task Type", "")).startswith("KERNEL")]
    assert len(compute) >= len(rows), "Underlying computation task records incomplete"
    streams = {r["stream_id"] for r in compute if "stream_id" in r}
    assert len(streams) <= 1, ("Multiple underlying streams need explicit grouping", streams)
    result = summarize_rows(rows, kernels_per_call)
    result.update(kernel_names=sorted(names), task_types=sorted(task_types), task_records=tasks,
                  grouping="Four sequential kernels per r3 call on one stream; hist, prepare, compact, finish")
    return result
