"""Validate one Decode smoke result or all four matched-input results."""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize(root, scope="all"):
    names = (
        ["decode"] if scope == "decode" else ["decode", "small", "prefill-k1024", "prefill-k2048"]
    )
    cases = {
        name: json.loads((root / "candidate" / (name + ".json")).read_text()) for name in names
    }
    environment = json.loads((root / "environment.json").read_text())
    context = json.loads((root / "run-context.json").read_text())
    assert not environment["tileops_status"]
    suites = ET.parse(root / "candidate/tests.xml").getroot()
    suites = [suites] if suites.tag == "testsuite" else list(suites.iter("testsuite"))
    counts = {
        key: sum(int(s.attrib.get(key, 0)) for s in suites)
        for key in ["tests", "failures", "errors", "skipped"]
    }
    assert counts == {"tests": 14, "failures": 0, "errors": 0, "skipped": 0}, counts
    assert len({c["kernel_source_sha256"] for c in cases.values()}) == 1
    assert environment["tileops_commit"] == context["tileops_commit"]
    assert {c["tileops_commit"] for c in cases.values()} == {context["tileops_commit"]}
    report = {
        "scope": scope,
        "final_version_accepted": False,
        "tileops_commit": environment["tileops_commit"],
        "npu_tests": counts,
        "cases": {},
    }
    for name, case in cases.items():
        assert len(case["event_samples_us"]) == len(case["kernel_samples_us"]) == 50
        assert (
            case["kernel_source_sha256"]
            == context["source_sha256"]["src/tileops/_kernels/attention/topk_select_ascend.py"]
        )
        row = {
            k: case[k]
            for k in [
                "shape",
                "k",
                "workers",
                "threads",
                "coarse",
                "parallel_scan",
                "input_sha256",
                "kernel_source_sha256",
                "kernel_median_us",
                "event_median_us",
            ]
        }
        if name != "small":
            directory = root / "cann" / name
            baseline = json.loads((directory / (name + "-timing.json")).read_text())
            profile = json.loads((directory / "profile-summary.json").read_text())
            assert len(baseline["samples_ms"]) == len(profile["kernel_records"]) == 50
            assert profile["expected_vector_route"], (
                "CANN compute route changed: review task records"
            )
            assert baseline["input_sha256"] == case["input_sha256"], name
            assert baseline["shape"] == case["shape"] and baseline["k"] == case["k"]
            assert (
                str(baseline["physical_device"])
                == str(case["physical_device"])
                == context["physical_device"]
            )
            row["cann_kernel_median_us"] = profile["kernel_median_us"]
            row["performance_x_cann"] = profile["kernel_median_us"] / case["kernel_median_us"]
        report["cases"][name] = row
    (root / ("summary-" + scope + "-local.json")).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(
        "Local report: review device health, load telemetry, parser warnings and stability; this is not an automatic version acceptance."
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--scope", choices=["decode", "all"], default="all")
    args = parser.parse_args()
    summarize(args.evidence, args.scope)
