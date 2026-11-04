"""950PR development comparison: frozen retained pipeline versus GE TopKV2."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import traceback

COMMIT = "5eb130eff798e06341d67fd6899f67a9f66ffb20"
TOOL = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check_device(root, label):
    text = subprocess.check_output(["npu-smi", "info"], text=True, timeout=30)
    (root / (label + "-npu-smi.txt")).write_text(text)
    section = text.split("Process id", 1)
    assert len(section) == 2, "Unrecognized npu-smi process table"
    own = {os.getpid()}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("NSpid:"):
            own.update(map(int, line.split()[1:]))
    seen = []
    for line in section[1].splitlines():
        cells = [v.strip() for v in line.split("|")[1:-1]]
        if len(cells) >= 3 and cells[0].split() and cells[0].split()[0].isdigit():
            device = int(cells[0].split()[0])
            if device == 0:
                assert cells[1].isdigit(), "Unknown device-0 process row: " + line
                pid = int(cells[1])
                seen.append(pid)
                assert pid in own, "Device 0 has another process; stop without killing it: " + line
    assert seen or "No running processes" in section[1], "Cannot confirm process table"
    return {"sha256": sha(text.encode()), "device0_pids": seen, "allowed_pids": sorted(own)}


def execute(args, report, root):
    report["occupancy"] = [check_device(root, "preflight")]
    identity = json.loads((TOOL / "identity.json").read_text())
    for name, expected in identity["tools"].items():
        assert sha((TOOL / name).read_bytes()) == expected, name
    report["identity"] = identity
    report["source_commit"] = COMMIT
    sources = {}
    for suffix in ["probe", "pipeline"]:
        path = "src/tileops/_kernels/attention/topk_select_decode_" + suffix + "_ascend.py"
        raw = subprocess.check_output(["git", "-C", args.repo, "show", COMMIT + ":" + path])
        assert sha(raw) == identity["sources"][path], "Frozen source mismatch"
        target = root / (suffix + ".py")
        target.write_bytes(raw)
        sources[suffix] = target
    # Cache changes are confined to this run; never mutate shared toolchain settings.
    for name, sub in [("TILELANG_CACHE_DIR", "tilelang-cache"), ("TMPDIR", "tmp"),
                      ("ASCEND_CACHE_PATH", "ascend-cache"), ("ASCEND_WORK_PATH", "work")]:
        target = root / sub
        target.mkdir()
        os.environ[name] = str(target)
    import torch
    import torch_npu
    import tilelang
    from ge_model import GeTopK
    from profile_support import read_profile, names_for
    from tilelang.ascend.callback import register_ascend_postproc_callback
    from tilelang.profiler.msprof import get_msprof_cache_flush_kernel
    torch.npu.set_device(0)
    report["runtime"] = {"python": sys.version, "torch": torch.__version__, "torch_npu": torch_npu.__version__,
                         "tilelang": tilelang.__version__, "device": torch.npu.get_device_name(0),
                         "cann_home": os.environ["ASCEND_HOME_PATH"],
                         "guard": "occupancy monitoring plus private cooperative flock; not host guard certification"}
    assert "950" in report["runtime"]["device"]
    probe = load(sources["probe"], "frozen_probe")
    pipeline = load(sources["pipeline"], "frozen_pipeline")
    def capture(code, target):
        (root / (report["stage"] + "-precompile.cpp")).write_text(str(code))
        return str(code)
    register_ascend_postproc_callback(capture, override=True)
    programs = {}
    builders = [("hist", lambda: probe.decode_histogram(16384, 4, STAGE_INPUT=True)),
                ("prepare", lambda: pipeline.decode_prepare(4, 2048, GROUPED_OFFSETS=True)),
                ("compact", lambda: pipeline.decode_compact(4, STAGE_INPUT=True)),
                ("finish", lambda: pipeline.decode_finish(ADAPTIVE_TIE=True, EARLY_EXIT=True,
                    STAGE_OVERFLOW=True, CACHE_OVERFLOW_KEYS=True))]
    for name, build in builders:
        report["stage"] = name
        print("COMPILE", name, flush=True)
        fd = os.dup(2)
        try:
            with (root / (name + ".stderr.log")).open("w") as log:
                sys.stderr.flush()
                os.dup2(log.fileno(), 2)
                programs[name] = build()
        finally:
            sys.stderr.flush()
            os.dup2(fd, 2)
            os.close(fd)
        assert "ThreadSync" not in (root / (name + ".stderr.log")).read_text(), "ThreadSync diagnostic"
        (root / (name + ".cpp")).write_text(programs[name].get_kernel_source())
    seed = int.from_bytes(hashlib.sha256(b"TopKSelectFwdOp::ds-v32-topk-decode-b1").digest()[:4], "little")
    torch.manual_seed(seed)
    x = torch.randn(1, 1, 16384, 1, dtype=torch.float32, device="npu").flatten()
    cpu = x.cpu()
    report["input"] = {"seed": seed, "sha256": sha(cpu.numpy().tobytes()),
        "index_score": [1, 1, 16384, 1], "starts": [[0]], "ends": [[16384]],
        "indexes": [1, 1, 1, 2048], "dtype": "float32", "distribution": "NPU torch.randn, target workload generation"}
    starts = torch.zeros(1, dtype=torch.int32, device="npu")
    ends = torch.full_like(starts, 16384)
    outputs = {name: torch.empty(2048, dtype=torch.int32, device="npu") for name in ["ours", "topkv2"]}
    w = {"partial": torch.empty((4,256), dtype=torch.int32, device="npu"),
         "higher": torch.empty(256, dtype=torch.int32, device="npu"),
         "meta": torch.empty(4, dtype=torch.int32, device="npu"),
         "offsets": torch.empty((4,2), dtype=torch.int32, device="npu"),
         "scores": torch.empty(2048, dtype=torch.float32, device="npu"),
         "indices": torch.empty(2048, dtype=torch.int32, device="npu"),
         "final": torch.empty(2, dtype=torch.int32, device="npu")}
    report["stage"] = "build-ge"
    import shutil
    model = root / "ge"
    model.mkdir()
    for name in ["build.cpp", "top_k_v2_proto.h"]:
        shutil.copyfile(TOOL / "cann" / name, model / name)
    home = Path(os.environ["ASCEND_HOME_PATH"])
    os.environ.setdefault("TOPK_SOC", "Ascend950PR_9579")
    report["soc"] = os.environ["TOPK_SOC"]
    cmd = ["g++", "-std=c++17", "-D_GLIBCXX_USE_CXX11_ABI=" + os.environ.get("TOPK_CXX11_ABI", "0"),
           "build.cpp", "-I"+str(home/"include"), "-I"+str(home/"include/external"),
           "-I"+str(home/"include/external/graph"), "-I.", "-L"+str(home/"lib64"),
           "-lge_compiler", "-lgraph", "-lgraph_base", "-lge_runner", "-o", "build"]
    for name, command in [("ge-compiler", cmd), ("ge-build", [str(model/"build"), "1", "16384", "2048", "decode"])]:
        result = subprocess.run(command, cwd=model, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (root / (name + ".log")).write_text(result.stdout)
        assert result.returncode == 0, name + " failed; inspect log"
    values = torch.empty((1,2048), dtype=torch.float32, device="npu")
    ge = GeTopK(model/"decode.om", x.view(1,16384), values, outputs["topkv2"].view(1,2048))
    report["ge"] = {"description": ge.description, "om_sha256": sha((model/"decode.om").read_bytes()),
        "largest": True, "sorted": False, "indices": "int32", "extra_values_output": True}
    def invoke(name):
        if name == "topkv2":
            ge.run()
            return
        programs["hist"](x, starts, ends, w["partial"])
        programs["prepare"](w["partial"], w["higher"], w["meta"], outputs[name], w["offsets"])
        programs["compact"](x, starts, ends, w["meta"], w["offsets"], w["scores"], w["indices"], outputs[name])
        programs["finish"](x, starts, ends, w["meta"], w["scores"], w["indices"], outputs[name], w["final"])
    def validate(label):
        for name in outputs:
            invoke(name)
            torch.npu.synchronize()
            ids = outputs[name].cpu().long()
            assert bool(((ids >= 0) & (ids < 16384)).all()) and ids.unique().numel() == 2048
            assert torch.equal(cpu[ids].sort().values, cpu.sort(descending=True).values[:2048].sort().values)
            if name == "ours":
                assert torch.equal(ids.sort().values, cpu.argsort(descending=True, stable=True)[:2048].sort().values)
                assert w["final"].cpu().tolist() == [0,2048]
            else:
                assert torch.equal(cpu[ids], values.cpu().flatten())
        assert torch.equal(x.cpu(), cpu) and starts.cpu().tolist() == [0] and ends.cpu().tolist() == [16384]
        report.setdefault("validation", []).append({"label": label, "passed": True, "meta": w["meta"].cpu().tolist()})
    validate("before")
    report["stage"] = "flush-compile"
    flush = get_msprof_cache_flush_kernel((1<<30)//4, "int32")
    buffer = torch.empty((1<<30)//4, dtype=torch.int32, device="npu")
    def isolate():
        flush(buffer)
        torch.npu.synchronize()
    for _ in range(3):
        for name in outputs:
            isolate()
            invoke(name)
            torch.npu.synchronize()
    def profile(fn, label):
        profile_dir = root / ("profile-" + label)
        profile_dir.mkdir()
        os.environ["ASCEND_WORK_PATH"] = str(profile_dir)
        with torch_npu.profiler.profile(
            activities=[torch_npu.profiler.ProfilerActivity.NPU],
            schedule=torch_npu.profiler.schedule(wait=0, warmup=0, active=1, repeat=1, skip_first=0),
            on_trace_ready=lambda prof: None,
            experimental_config=torch_npu.profiler._ExperimentalConfig(
                profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
                aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,
                l2_cache=False, data_simplification=False)) as prof:
            fn()
            torch.npu.synchronize()
            prof.step()
        return Path(prof.prof_if.prof_path)
    # Verify name resolution against the real flush before trusting its absence.
    flush_path = profile(lambda: flush(buffer), "flush-selftest")
    assert any("_tilelang_profiler_cache_flush" in n for n in names_for(flush_path).values()), "Flush marker unresolved"
    report["samples"] = []
    for sample in range(15):
        order = ["ours", "topkv2"] if (sample + args.repeat) % 2 else ["topkv2", "ours"]
        for name in order:
            label = str(sample) + "-" + name
            report["stage"] = label
            report["occupancy"].append(check_device(root, label))
            isolate()
            path = profile(lambda: invoke(name), label)
            record = read_profile(path, 4 if name == "ours" else 1)
            record.update(implementation=name, sample=sample)
            report["samples"].append(record)
            print("SAMPLE", name, sample, record["latency_ms"]*1000, "us", flush=True)
    validate("after")
    report["occupancy"].append(check_device(root, "final"))
    report["summary"] = {}
    for name in outputs:
        samples = [v["latency_ms"]*1000 for v in report["samples"] if v["implementation"] == name]
        report["summary"][name] = {"samples_us": samples, "mean_us": statistics.mean(samples),
            "stdev_us": statistics.stdev(samples), "min_us": min(samples), "max_us": max(samples)}
    report["speedup_x_topkv2"] = report["summary"]["topkv2"]["mean_us"] / report["summary"]["ours"]["mean_us"]
    report["status"] = "complete"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()
    root = Path(args.output).resolve()
    root.mkdir()
    report = {"status": "failed", "repeat": args.repeat, "stage": "preflight",
        "protocol": "950PR-development-isolated-device-task-sum-v1",
        "scope": "Same-environment comparison, not server2 acceptance or historical ops-math reproduction"}
    try:
        execute(args, report, root)
    except Exception:
        report["error"] = traceback.format_exc()
        print(report["error"], file=sys.stderr)
    finally:
        # Preserve raw evidence and compiler diagnostics even on failure.
        report["evidence"] = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            name = path.name
            if name.endswith((".cpp", ".log", ".txt")) or any(k in name for k in ["ffts_profile", "hash_dic", "task_track", "stars_soc.data", "info.json"]):
                if not name.endswith((".done", ".complete")):
                    raw = path.read_bytes()
                    report["evidence"][str(path.relative_to(root))] = {"sha256": sha(raw), "base64": base64.b64encode(raw).decode()}
        (root / "device-return.json").write_text(json.dumps(report, indent=2))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
