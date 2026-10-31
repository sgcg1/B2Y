"""Validate complete matched-input evidence; emit a compact local report."""

import argparse
import json
from pathlib import Path


def summarize(root):
    names = ["decode", "small", "prefill-k1024", "prefill-k2048"]
    cases = {
        name: json.loads((root / "candidate" / (name + ".json")).read_text()) for name in names
    }
    environment = json.loads((root / "environment.json").read_text())
    assert not environment["tileops_status"], "Record a clean tested commit first"
    assert "14 passed" in (root / "candidate/tests.log").read_text()
    assert len({c["kernel_source_sha256"] for c in cases.values()}) == 1
    assert {c["tileops_commit"] for c in cases.values()} == {environment["tileops_commit"]}
    report = {"tileops_commit": environment["tileops_commit"], "npu_tests_passed": 14, "cases": {}}
    for name, case in cases.items():
        assert len(case["event_samples_us"]) == len(case["kernel_samples_us"]) == 50
        row = {
            k: case[k]
            for k in [
                "shape",
                "k",
                "workers",
                "threads",
                "coarse",
                "input_sha256",
                "kernel_source_sha256",
                "kernel_median_us",
                "event_median_us",
            ]
        }
        if name != "small":
            baseline = json.loads((root / "cann" / (name + "-timing.json")).read_text())
            profile = json.loads((root / "cann/profile-summary.json").read_text())[name]
            assert len(baseline["samples_ms"]) == len(profile["kernel_records"]) == 50
            assert baseline["input_sha256"] == case["input_sha256"], name
            assert baseline["shape"] == case["shape"] and baseline["k"] == case["k"]
            assert str(baseline["physical_device"]) == str(case["physical_device"])
            row["cann_kernel_median_us"] = profile["kernel_median_us"]
            row["performance_x_cann"] = profile["kernel_median_us"] / case["kernel_median_us"]
        report["cases"][name] = row
    (root / "summary-local.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("Inspect device health, raw task types and timing stability before accepting a version.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    summarize(parser.parse_args().evidence)
