"""Record local-only runtime provenance before any NPU experiment."""

import faulthandler
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    faulthandler.enable()
    faulthandler.dump_traceback_later(120, repeat=True)
    repo = Path(os.environ["TOPK_REPO"])
    evidence = Path(os.environ["EVIDENCE"])
    assert sys.version_info >= (3, 12), "TileOPs requires Python >=3.12"
    assert repo.is_dir(), repo
    data = {"python": sys.executable, "modules": {}}
    for name in [
        "torch",
        "torch_npu",
        "tilelang",
        "tilelang.ascend.language",
        "tilelang.ascend.backend",
        "tileops.ascend.topk_select",
        "tileops._kernels.attention.topk_select_ascend",
        "pytest",
        "pytest_timeout",
    ]:
        print("IMPORT", name, flush=True)
        module = importlib.import_module(name)
        path = Path(module.__file__).resolve()
        if name.startswith("tileops."):
            assert path.is_relative_to(repo.resolve()), (name, path)
        data["modules"][name] = {
            "path": str(path),
            "version": str(getattr(module, "__version__", "")),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    import torch

    version = tuple(int(part) for part in torch.__version__.split("+")[0].split(".")[:2])
    assert version == (2, 13), (
        "This TileOPs checkout declares torch>=2.13,<2.14; use a compatible private environment"
    )
    assert torch.npu.is_available()
    torch.npu.set_device(0)
    properties = torch.npu.get_device_properties(0)
    assert "950" in torch.npu.get_device_name(0)
    assert torch.npu.get_device_name(0) == os.environ["TOPK_SOC"], (
        "Confirm the chip and set TOPK_SOC before building models"
    )
    data["device"] = str(properties)
    data["vector_cores"] = properties.vector_core_num
    data["free_total_memory"] = torch.npu.mem_get_info()
    a = torch.tensor([1.0, 2.0], device="npu")
    assert (a + a).cpu().tolist() == [2.0, 4.0]
    print("TRANSFER_CHECK_BEGIN", flush=True)
    host = torch.arange(131072, dtype=torch.float32)
    assert torch.equal(host.npu().cpu(), host)
    print("TRANSFER_CHECK_OK", flush=True)
    data["cpu_threads"] = torch.get_num_threads()
    reference = json.loads((Path(os.environ["TOPK_TOOLS"]) / "SOURCE.json").read_text())
    data["matches_kit_reference_source"] = all(
        hashlib.sha256((repo / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == expected
        for name, expected in reference["source_sha256"].items()
    )
    data["environment"] = {
        k: os.environ.get(k)
        for k in [
            "ASCEND_RT_VISIBLE_DEVICES",
            "ASCEND_HOME_PATH",
            "LD_LIBRARY_PATH",
            "TASK_QUEUE_ENABLE",
            "TILELANG_CACHE_DIR",
        ]
    }
    data["tools"] = {name: shutil.which(name) for name in ["bisheng", "g++", "git", "npu-smi"]}
    assert data["tools"]["bisheng"], "CANN device compiler bisheng is missing"
    cann = Path(os.environ["ASCEND_HOME_PATH"])
    architecture = os.uname().machine + "-linux"
    data["cann_installation_info"] = {}
    for path in [
        cann / architecture / "ascend_toolkit_install.info",
        cann / "ascend_toolkit_install.info",
        cann / "version.cfg",
    ]:
        if path.is_file():
            data["cann_installation_info"][str(path)] = path.read_text()
    for name, args in {
        "tileops_commit": ["rev-parse", "HEAD"],
        "tileops_status": ["status", "--porcelain"],
    }.items():
        data[name] = subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    data["loaded_libraries"] = sorted(
        {
            line.split()[-1]
            for line in Path("/proc/self/maps").read_text().splitlines()
            if ".so" in line
            and any(t in line.lower() for t in ["ascend", "runtime", "tilelang", "tvm"])
        }
    )
    # Mapped host libraries are not the executed device kernel binary.
    data["library_sha256"] = {}
    for name in data["loaded_libraries"]:
        path = Path(name)
        if path.is_file():
            data["library_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with (evidence / "environment.json").open("x") as handle:
        handle.write(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2), flush=True)
    faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
