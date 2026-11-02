"""Export existing probe2 samples and C++ as one text; no device imports."""

import argparse
import hashlib
import json
from pathlib import Path


def snapshot(root, name, expected=None):
    path = root / name
    assert path.resolve().is_relative_to(root.resolve()), "Unexpected file symlink"
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert expected is None or digest == expected, f"Source SHA mismatch: {name}"
    return {"sha256": digest, "bytes": len(raw), "text": raw.decode("utf-8")}


def collect(root):
    report_file = snapshot(root, "probe-report.json")
    report = json.loads(report_file["text"])
    assert report["version"] == "20261102-probe2", "Select the existing probe2 run"
    assert report["status"] == "completed", "This export expects a completed probe2 run"
    names = [f"r{r}-{m}" for r in (1, 16, 64) for m in ("plain", "fenced", "timed")]
    names += ["r0-timed"]
    assert set(report["cases"]) == set(report["postproc_captures"]) == set(names)
    files = {"probe-report.json": report_file}
    api_sources = {}
    for name in names:
        capture = report["postproc_captures"][name]
        case = report["cases"][name]
        assert len(case["event_samples_us"]) == 50, f"Missing event samples: {name}"
        expected_count = 50 if case["mode"] == 2 else 0
        assert len(case["counter_samples"]) == expected_count, f"Missing counter samples: {name}"
        for suffix, key in (
            ("-original.cpp", "original_source_sha256"),
            ("-postproc.cpp", "postproc_source_sha256"),
        ):
            files[name + suffix] = snapshot(root, name + suffix, capture[key])
        api = snapshot(root, name + ".cpp", case["api_source_sha256"])
        api_sources[name] = {"sha256": api["sha256"], "same_text_as": None}
        for suffix in ("-original.cpp", "-postproc.cpp"):
            if api["sha256"] == files[name + suffix]["sha256"]:
                api_sources[name]["same_text_as"] = name + suffix
                break
        if api_sources[name]["same_text_as"] is None:
            files[name + ".cpp"] = api
    return {
        "export_version": "20261102-probe2-export1",
        "run_directory": str(root),
        "note": "Existing files only; no compilation or NPU execution. Text fields reconstruct original UTF-8 bytes.",
        "api_sources": api_sources,
        "files": files,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.run.resolve(), args.output.resolve()
    private = Path("/home/y00937463").resolve()
    assert root.is_dir() and root.is_relative_to(private) and root != private
    assert output.is_relative_to(root), "Write the new export in the selected run directory"
    text = json.dumps(collect(root), ensure_ascii=False, indent=2) + "\n"
    with output.open("x", encoding="utf-8") as handle:
        handle.write(text)
    print("EXPORT_OUTPUT", output)
    print("EXPORT_BYTES", len(text.encode("utf-8")))


if __name__ == "__main__":
    main()
