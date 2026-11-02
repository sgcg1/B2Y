"""Export an existing failed probe's source; no device or TileLang imports."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def describe_source(raw):
    code = raw.decode("utf-8")
    tokens = [
        "tileops_probe_clock",
        "tileops_probe_fence",
        "asc_vf_call",
        "GetSystemCycle",
        "PipeBarrier",
    ]
    clocks = [m.start() for m in re.finditer(r"tileops_probe_clock\(", code)]
    fences = [m.start() for m in re.finditer(r"tileops_probe_fence\(", code)]
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "line_count": len(code.splitlines()),
        "clock_occurrence_offsets": clocks,
        "fence_occurrence_offsets": fences,
        "legacy_positional_order_check": (
            fences[1] < clocks[1] < fences[2] < clocks[2]
            if len(clocks) == len(fences) == 3
            else None
        ),
        "marker_lines": [
            {"line": number, "text": line}
            for number, line in enumerate(code.splitlines(), 1)
            if any(token in line for token in tokens)
        ],
        "interpretation": "Occurrences are not classified as declarations, definitions or calls. No order is accepted by this exporter.",
    }


def collect(root):
    summary_path = root / "probe-summary.txt"
    assert summary_path.resolve().is_relative_to(root.resolve()), "Unexpected summary symlink"
    summary_raw = summary_path.read_bytes()
    summary = json.loads(summary_raw.decode("utf-8"))
    timed = root / "r1-timed.cpp"
    assert timed.is_file(), "Expected r1-timed.cpp in the original failed probe directory"
    report = {
        "inspector_version": "20261102-source1",
        "run_directory": str(root),
        "probe_summary_sha256": hashlib.sha256(summary_raw).hexdigest(),
        "original_probe_summary": summary,
        "source_order_root_cause_established": False,
        "note": "Read-only snapshot of existing source files; no compilation, counter calls or NPU execution.",
        "sources": {},
    }
    for name in ["r1-plain.cpp", "r1-fenced.cpp", "r1-timed.cpp"]:
        path = root / name
        if path.is_file():
            assert path.resolve().is_relative_to(root.resolve()), "Unexpected source symlink"
            report["sources"][name] = describe_source(path.read_bytes())
        else:
            report["sources"][name] = {"missing": True}
    code = timed.read_text(encoding="utf-8")
    lines = [f"{number:04d}: {line}" for number, line in enumerate(code.splitlines(), 1)]
    return (
        json.dumps(report, ensure_ascii=False, indent=2)
        + "\n\n===== r1-timed.cpp (numbered source) =====\n"
        + "\n".join(lines)
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.run.resolve()
    private = Path("/home/y00937463").resolve()
    assert root.is_dir() and root.is_relative_to(private) and root != private
    output = args.output.resolve()
    assert output.is_relative_to(root), (
        "Write the new inspection text inside the selected run directory"
    )
    text = collect(root)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(text)
    print("INSPECTION_OUTPUT", output)
    print("INSPECTION_BYTES", len(text.encode("utf-8")))


if __name__ == "__main__":
    main()
