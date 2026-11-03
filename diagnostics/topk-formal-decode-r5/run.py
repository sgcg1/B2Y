"""Experimental full Decode pipeline screening; production route remains unchanged."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import traceback


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def execute(report, repo, root):
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    import torch
    import torch_npu
    import tilelang
    from itertools import permutations
    import shutil
    from ge_model import GeTopK
    from profile_records import summarize_profile
    from tilelang.ascend.callback import register_ascend_postproc_callback

    report["stage"] = "provenance"
    report["configuration"] = {"N": 16384, "K": 2048, "P": [4], "threads": 128,
                               "kernels_per_pipeline": 4, "boundary_capacity": 2048, "compact_scan_width": {"previous": 128, "new": 128}, "compact_stage_input": {"previous": False, "new": True}}
    identity = json.loads((Path(__file__).parent / "identity.json").read_text())
    for path, expected in identity["tool_files"].items():
        assert digest((Path(__file__).parent / path).read_bytes()) == expected, path
    report["commit"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    report["source_checks"] = {}
    for path, expected in identity["sources"].items():
        actual = (repo / path).read_bytes()
        head = subprocess.check_output(["git", "-C", str(repo), "show", "HEAD:" + path])
        report["source_checks"][path] = {"expected_sha256": expected,
            "working_sha256": digest(actual), "head_blob_sha256": digest(head),
            "working_lf_sha256": digest(actual.replace(b"\r\n", b"\n")),
            "matches": digest(actual) == expected}
    assert all(v["matches"] for v in report["source_checks"].values()), "Source identity mismatch; see source_checks and commit in formal-return.txt. Follow SOURCE_RECOVERY.md; do not bypass identity checks."
    assert digest(Path(__file__).read_bytes()) == identity["run_sha256"]
    assert not subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"]).strip()
    report["commit"] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    raw = subprocess.check_output(["git", "-C", str(repo), "show", identity["baseline_commit"] + ":src/tileops/_kernels/attention/topk_select_ascend.py"])
    assert digest(raw) == identity["baseline_sha256"]
    (root / "baseline.py").write_bytes(raw)
    frozen_raw = subprocess.check_output(["git", "-C", str(repo), "show", identity["r3_commit"] + ":src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py"])
    assert digest(frozen_raw) == identity["r3_pipeline_sha256"]
    (root / "frozen-r3.py").write_bytes(frozen_raw)
    report["identity"] = identity
    report["runtime"] = {"python": sys.executable, "torch": torch.__version__, "torch_npu": torch_npu.__version__,
                         "tilelang": tilelang.__version__, "tilelang_path": tilelang.__file__,
                         "cann_home": os.environ.get("ASCEND_HOME_PATH")}
    report["compiler"] = subprocess.check_output(["bisheng", "--version"], text=True, timeout=30)
    report["health_begin"] = subprocess.check_output(["npu-smi", "info"], text=True)
    torch.npu.set_device(0)
    assert "950" in torch.npu.get_device_name(0)
    report["generated"] = {}

    def capture(code, target):
        name = report["stage"].split(":")[-1]
        text = str(code)
        (root / (name + "-precompile.cpp")).write_text(text)
        return text

    register_ascend_postproc_callback(capture, override=True)
    baseline_module = load(root / "baseline.py", "full_decode_baseline")
    hist_module = load(repo / "src/tileops/_kernels/attention/topk_select_decode_probe_ascend.py", "full_decode_hist")
    module = load(repo / "src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py", "full_decode_pipeline")
    frozen_module = load(root / "frozen-r3.py", "formal_frozen_r3")
    builders = [("prepare-r3", lambda: frozen_module.decode_prepare(4, 2048, GROUPED_OFFSETS=True)),
                ("prepare-control", lambda: module.decode_prepare(4, 2048, GROUPED_OFFSETS=True)),
                ("baseline", lambda: baseline_module.topk_select_ascend(1, 16384, 2048, 1, 1, COARSE=True, H=128, PARALLEL_SCAN=True)),
                ("finish-previous", lambda: frozen_module.decode_finish(ADAPTIVE_TIE=True, EARLY_EXIT=True)),
                ("finish-control", lambda: module.decode_finish(ADAPTIVE_TIE=True, EARLY_EXIT=True)),
                ("finish", lambda: module.decode_finish(ADAPTIVE_TIE=True, EARLY_EXIT=True))]
    for p in [4]:
        builders.extend([(f"hist-p{p}", lambda p=p: hist_module.decode_histogram(16384, p)),
                         (f"prepare-p{p}", lambda p=p: module.decode_prepare(p, 2048, GROUPED_OFFSETS=True)),
                         ("compact-previous", lambda p=p: frozen_module.decode_compact(p)),
                         ("compact-control", lambda p=p: module.decode_compact(p)),
                         (f"compact-p{p}", lambda p=p: module.decode_compact(p, STAGE_INPUT=True))])
    programs = {}
    for name, build in builders:
        report["stage"] = "compile:" + name
        print("COMPILE_BEGIN", name, flush=True)
        stderr_path = root / (name + ".stderr.log")
        saved = os.dup(2)
        try:
            with stderr_path.open("w") as log:
                sys.stderr.flush()
                os.dup2(log.fileno(), 2)
                program = build()
        finally:
            sys.stderr.flush()
            os.dup2(saved, 2)
            os.close(saved)
            report.setdefault("compile_stderr", {})[name] = stderr_path.read_text()
            print(report["compile_stderr"][name], file=sys.stderr, flush=True)
        code = program.get_kernel_source()
        (root / (name + ".cpp")).write_text(code)
        report["generated"][name] = digest(code.encode())
        assert "ThreadSync" not in report["compile_stderr"][name], "Unresolved sync diagnostic"
        programs[name] = program
        print("COMPILE_END", name, flush=True)
    assert report["generated"]["finish-control"] == report["generated"]["finish-previous"], "Unchanged finish differs"
    assert report["generated"]["prepare-control"] == report["generated"]["prepare-r3"], "Default prepare changed"
    assert report["generated"]["compact-control"] == report["generated"]["compact-previous"], "Default compact changed"
    for name, expected in identity["unchanged_generated"].items():
        assert report["generated"][name] == expected, (name, "R3 or baseline identity changed")
    x = torch.empty(16384, dtype=torch.float32, device="npu")
    starts = torch.zeros(1, dtype=torch.int32, device="npu")
    ends = torch.full_like(starts, 16384)
    out = {name: torch.empty(2048, dtype=torch.int32, device="npu") for name in ["baseline", "previous", "new", "cann"]}
    work = {name: {"partial": torch.empty((4, 256), dtype=torch.int32, device="npu"),
                "higher": torch.empty(256, dtype=torch.int32, device="npu"),
                "meta": torch.empty(4, dtype=torch.int32, device="npu"),
                "offsets": torch.empty((4, 2), dtype=torch.int32, device="npu"),
                "scores": torch.empty(2048, dtype=torch.float32, device="npu"),
                "indices": torch.empty(2048, dtype=torch.int32, device="npu"),
                "final": torch.empty(2, dtype=torch.int32, device="npu")}
            for name in ["previous", "new"]}

    report["stage"] = "build-ge-model"
    model_dir = root / "ge-model"
    model_dir.mkdir()
    tool_root = Path(__file__).resolve().parent
    for filename in ["build.cpp", "top_k_v2_proto.h"]:
        shutil.copyfile(tool_root / "cann" / filename, model_dir / filename)
    home = Path(os.environ["ASCEND_HOME_PATH"])
    os.environ.setdefault("TOPK_SOC", "Ascend950PR_9579")
    report["ge_soc_version"] = os.environ["TOPK_SOC"]
    command = ["g++", "-std=c++17", "-D_GLIBCXX_USE_CXX11_ABI=" + os.environ.get("TOPK_CXX11_ABI", "0"),
               "build.cpp", "-I" + str(home / "include"), "-I" + str(home / "include/external"),
               "-I" + str(home / "include/external/graph"), "-I.", "-L" + str(home / "lib64"),
               "-lge_compiler", "-lgraph", "-lgraph_base", "-lge_runner", "-o", "build"]
    for label_build, cmd in [("ge-compiler", command), ("ge-build", [str(model_dir / "build"), "1", "16384", "2048", "decode"])]:
        result = subprocess.run(cmd, cwd=model_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        report[label_build] = {"command": cmd, "returncode": result.returncode, "log": result.stdout}
        print(label_build, result.stdout, flush=True)
        assert result.returncode == 0, label_build
    model_path = model_dir / "decode.om"
    report["om"] = {"sha256": digest(model_path.read_bytes()), "bytes": model_path.stat().st_size,
                    "largest": True, "sorted": False, "indices_dtype": "INT32", "sort_policy": 0,
                    "precision": "must_keep_origin_dtype", "shape": [1, 16384], "K": 2048}
    cann_values = torch.empty((1, 2048), dtype=torch.float32, device="npu")
    ge = GeTopK(model_path, x.view(1, 16384), cann_values, out["cann"].view(1, 2048))
    report["acl_model_description"] = ge.description

    def invoke(name):
        if name == "cann":
            ge.run()
        elif name == "baseline":
            programs[name](x.view(1, 16384, 1), starts, ends, out[name].view(1, 2048))
        else:
            p = 4
            w = work[name]
            programs[f"hist-p{p}"](x, starts, ends, w["partial"])
            programs["prepare-r3" if name == "previous" else f"prepare-p{p}"](w["partial"], w["higher"], w["meta"], out[name], w["offsets"])
            programs["compact-previous" if name == "previous" else f"compact-p{p}"](x, starts, ends, w["meta"], w["offsets"], w["scores"], w["indices"], out[name])
            programs["finish-previous" if name == "previous" else "finish"](x, starts, ends, w["meta"], w["scores"], w["indices"], out[name], w["final"])

    report["validation"] = []

    def validate(cpu, start, stop, label):
        report["stage"] = "validate:" + label
        x.copy_(cpu)
        starts.fill_(start)
        ends.fill_(stop)
        bits = cpu.view(torch.int32).long() & 0xffffffff
        mag = bits & 0x7fffffff
        ordered = torch.where((bits & 0x80000000) != 0, (~bits) & 0xffffffff, bits | 0x80000000)
        keys = torch.where(mag > 0x7f800000, 0xffffffff, torch.where(mag == 0, 0x80000000, ordered))
        valid = max(0, stop - start)
        selected = keys[start:stop].argsort(descending=True, stable=True)[:2048] + start if valid else torch.empty(0, dtype=torch.int64)
        reference = torch.cat((selected, torch.full((2048 - min(valid, 2048),), 16384, dtype=torch.int64))).sort().values
        item = {"label": label, "window": [start, stop], "input_sha256": digest(cpu.numpy().tobytes()), "metadata": {}}
        report["validation"].append(item)
        for name in out:
            out[name].fill_(-1)
            invoke(name)
            torch.npu.synchronize()
            if name == "cann":
                ids = out[name].cpu().long()
                vals = cann_values.cpu().flatten()
                assert bool(((ids >= 0) & (ids < 16384)).all())
                assert ids.unique().numel() == 2048
                assert torch.equal(cpu[ids], vals), "CANN values differ from FP32 gather"
                assert torch.equal(vals.sort().values, cpu.sort(descending=True).values[:2048].sort().values), "CANN wrong score multiset"
            else:
                assert torch.equal(out[name].cpu().long().sort().values, reference), (name, label, "Wrong selected set")
            if name in ["previous", "new"]:
                assert work[name]["final"].cpu().tolist() == [0, min(valid, 2048)], (name, label, "Unfinished quota")
                item["metadata"][name] = work[name]["meta"].cpu().tolist()
                assert item["metadata"][name][3] == valid
        item["passed"] = True

    small = torch.zeros(16384, dtype=torch.float32)
    small[:2047] = 1000.
    small[2047:2147] = 100.
    report["cases"] = []
    names = list(out)
    orders = list(permutations(names))
    for label, seed in [("random-20261030", 20261030), ("random-20261102", 20261102),
                        ("all-equal-overflow", None), ("small-boundary-tie", None)]:
        if seed is not None:
            torch.manual_seed(seed)
            torch.npu.manual_seed_all(seed)
            cpu = torch.randn((1, 16384, 1), dtype=torch.float32, device="npu").reshape(-1).cpu()
        else:
            cpu = torch.ones(16384, dtype=torch.float32) if label == "all-equal-overflow" else small
        validate(cpu, 0, 16384, label)
        case = {"label": label, "seed": seed, "input_sha256": digest(cpu.numpy().tobytes()), "event_samples_us": {n: [] for n in names}}
        report["cases"].append(case)
        for name in names:
            for _ in range(5):
                invoke(name)
        torch.npu.synchronize()
        begin, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
        for _ in range(5):
            begin.record(); end.record(); end.synchronize()
        for iteration in range(50):
            for name in orders[iteration % len(orders)]:
                report["stage"] = f"sample:{label}:{iteration}:{name}"
                begin.record()
                invoke(name)
                end.record()
                end.synchronize()
                case["event_samples_us"][name].append(begin.elapsed_time(end) * 1000)
        case["median_us"] = {n: statistics.median(v) for n, v in case["event_samples_us"].items()}
        validate(cpu, 0, 16384, "post-sample-" + label)
        case["event_x_ascend_c"] = {name: case["median_us"]["cann"] / case["median_us"][name] for name in ["baseline", "previous", "new"]}
        case["profile"] = {}
        # Independent profile sessions; no events, validation or allocations inside.
        for name in names:
            report["stage"] = "profile:" + label + ":" + name
            profile_root = root / ("profile-" + label + "-" + name)
            with torch_npu.profiler.profile(
                activities=[torch_npu.profiler.ProfilerActivity.CPU, torch_npu.profiler.ProfilerActivity.NPU],
                schedule=torch_npu.profiler.schedule(wait=0, warmup=1, active=1, repeat=1),
                on_trace_ready=torch_npu.profiler.tensorboard_trace_handler(str(profile_root)),
            ) as prof:
                invoke(name)
                torch.npu.synchronize()
                prof.step()
                for iteration in range(60):
                    invoke(name)
                    torch.npu.synchronize()
                prof.step()
            torch.npu.synchronize()
            case["profile"][name] = summarize_profile(profile_root, 4 if name in ["previous", "new"] else 1)
        case["event_x_ascend_c"] = {name: case["median_us"]["cann"] / case["median_us"][name] for name in ["baseline", "previous", "new"]}
        cann_device = case["profile"]["cann"]["envelope_median_us"]
        device_ratios = {name: cann_device / case["profile"][name]["envelope_median_us"] for name in ["baseline", "previous", "new"]}
        partial = any(z.get("leading_partial_records") for z in case["profile"].values())
        if partial:
            report["profile_review_required"] = True
            print("PROFILE_BOUNDARY_REVIEW_REQUIRED", label, flush=True)
        case["device_ratio_status"] = "review_required_partial_capture" if partial else "complete_selected_calls"
        case["provisional_device_x_ascend_c" if partial else "device_envelope_x_ascend_c"] = device_ratios
    ge.close()
    report["health_end"] = subprocess.check_output(["npu-smi", "info"], text=True)
    report.update(status="completed_with_profile_review" if report.get("profile_review_required") else "completed",
                  stage="review_required", accepted=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default=0, type=int)
    args = parser.parse_args()
    root = args.output.resolve()
    assert root.is_relative_to(Path("/home/y00937463")) and root != Path("/home/y00937463")
    assert args.device >= 0
    root.mkdir(parents=True, exist_ok=False)
    for key, relative in {"TMPDIR": "tmp", "XDG_CACHE_HOME": "cache", "TILELANG_CACHE_DIR": "cache/tilelang",
                          "ASCEND_CACHE_PATH": "cache/cann", "ASCEND_WORK_PATH": "cache/work",
                          "ASCEND_PROCESS_LOG_PATH": "logs", "TORCH_EXTENSIONS_DIR": "cache/torch"}.items():
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(ASCEND_RT_VISIBLE_DEVICES=str(args.device), TASK_QUEUE_ENABLE="0",
                      PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True
    report = {"version": "20261103-formal-decode-r5", "status": "incomplete",
              "physical_device": args.device, "accepted": False,
              "scope": "Same-stream events and independent profiler device envelopes, CANN vs baseline vs r3"}
    try:
        execute(report, args.repo.resolve(), root)
    except Exception:
        report.update(status="failed", traceback=traceback.format_exc())
        raise
    finally:
        sources = {p.name: p.read_text() for p in root.glob("*.cpp")}
        profile_csv = {}
        for filename in ["kernel_details.csv", "task_time.csv"]:
            for path in root.rglob(filename):
                raw = path.read_bytes()
                profile_csv[str(path.relative_to(root))] = {"sha256": digest(raw), "bytes": len(raw), "text": raw.decode("utf-8")}
        (root / "formal-return.txt").write_text(json.dumps({"report": report, "sources": sources, "profile_csv": profile_csv}, indent=2) + "\n")
        print("FORMAL_OUTPUT", root, flush=True)


if __name__ == "__main__":
    main()
