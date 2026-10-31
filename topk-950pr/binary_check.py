"""Record the actual loaded/cached host library and device cache provenance."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path

import tilelang
from tilelang.cache.ascend_binary_cache import AscendBinaryCache
from tilelang.contrib import bisheng
from tilelang.env import TILELANG_TEMPLATE_PATH

from tileops._kernels.attention.topk_select_ascend import topk_select_ascend

root = Path(os.environ["EVIDENCE"])
spec = importlib.util.spec_from_file_location(
    "v2_fingerprint", root / "control-decode-1/kernel-v0.1.2.py"
)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
programs = {
    "v2": old.topk_select_ascend(1, 16384, 2048, 1, 1),
    "candidate-h128": topk_select_ascend(1, 16384, 2048, 1, 1, COARSE=True, H=128),
}
report = {}
for name, program in programs.items():
    source = program.get_kernel_source()
    arch = bisheng.get_target_npu_arch(program.target)
    cfg = program.pass_configs or {}
    flags = bisheng.normalize_options(cfg.get(tilelang.PassConfigKey.TL_DEVICE_COMPILE_FLAGS))
    options = bisheng.get_bisheng_compile_options(arch, ["-I" + TILELANG_TEMPLATE_PATH, *flags])
    linker = bisheng.get_aibin_linker_options()
    key = AscendBinaryCache.make_key(
        code=source,
        target_kind=program.target.kind.name,
        target_arch=arch,
        compile_format="aibin",
        options=options,
        linker_options=linker,
    )
    binary_path = Path(AscendBinaryCache.get_path(key, "aibin"))
    host_path = getattr(program.adapter, "libpath", None)
    exported = root / (name + "-runtime.so")
    program.export_library(str(exported))
    report[name] = {
        "generated_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "execution_backend": program.execution_backend,
        "pass_configs": {str(k): str(v) for k, v in cfg.items()},
        "target": str(program.target),
        "compiler_options": options,
        "linker_options": linker,
        "device_cache_key": key,
        "device_cache_path": str(binary_path),
        "device_cache_exists": binary_path.exists(),
        "device_binary_sha256": hashlib.sha256(binary_path.read_bytes()).hexdigest()
        if binary_path.exists()
        else None,
        "host_library_path": str(host_path),
        "host_library_sha256": hashlib.sha256(Path(host_path).read_bytes()).hexdigest()
        if host_path
        else None,
        "exported_runtime_sha256": hashlib.sha256(exported.read_bytes()).hexdigest(),
    }
report["same_program_object"] = programs["v2"] is programs["candidate-h128"]
(root / "binary-fingerprint.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2), flush=True)
