"""Read-only audit: fixed kernel source, real generated code, CPU logical work."""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
B2Y = Path("D:/04_Project/B2Y")
COMMIT = "5eb130eff798e06341d67fd6899f67a9f66ffb20"
REPORT = B2Y / "experiments/topk/20261104-950pr-device-compare-r1-113714/raw/topk-950pr-device-compare-r1-20261104-113714-178290-repeat-1.json"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    path = "src/tileops/_kernels/attention/topk_select_decode_pipeline_ascend.py"
    raw = subprocess.check_output(["git", "-C", str(ROOT), "show", COMMIT + ":" + path])
    assert hashlib.sha256(raw).hexdigest() == report["identity"]["sources"][path]
    model = load(ROOT / "artifacts/topk_algorithm_audit.py", "work_model")
    tree = ast.parse(raw)
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "decode_finish")
    fn = next(n for n in func.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    model.code = compile(ast.fix_missing_locations(model.Lower().visit(ast.Module(body=fn.body, type_ignores=[]))), "fixed-5eb-finish", "exec")
    # Same coarse metadata as the real case, intentionally NOT its unreturned values.
    case = {"label":"synthetic-same-coarse-counts-not-real-input", "window":[0,16384],
            "values":[2.0]*1744 + [1+i/4096 for i in range(894)] + [0.0]*(16384-1744-894)}
    work = model.simulate(case)
    assert work["coarse_boundary"] == 894 and work["pending_quota"] == 304
    generated = {}
    for name in ("hist", "prepare", "compact", "finish"):
        item = report["evidence"][name+".cpp"]
        code = base64.b64decode(item["base64"])
        assert hashlib.sha256(code).hexdigest() == item["sha256"]
        lines = code.decode().splitlines()
        markers = [(i+1,line.strip()) for i,line in enumerate(lines)
                   if "for (int32_t round" in line or "bool __cond_2" in line or
                   "asc_sync_wait(PIPE_V, PIPE_S, static_cast<event_t>(0))" in line or
                   "asc_atomic_add" in line]
        generated[name] = {"sha256":item["sha256"], "simt_vf_definitions":code.count(b"__simt_vf__"),
                           "static_vf_call_sites":code.count(b"asc_vf_call"), "markers":markers}
    # All FP32 encodings in the RNE preimage of FP16 coarse bucket 188.
    low = (struct.unpack("e",struct.pack("H",0x3bff))[0]+1.0)/2
    high = (struct.unpack("e",struct.pack("H",0x3cff))[0]+struct.unpack("e",struct.pack("H",0x3d00))[0])/2
    lo,hi = [struct.unpack("I",struct.pack("f",v))[0] for v in (low,high)]
    checked = 0
    for bits in range(lo,hi):
        value = struct.unpack("f",struct.pack("I",bits))[0]
        assert model.helpers.coarse(value) == 188
        assert model.helpers.score(value) >> 24 == 0xbf
        checked += 1
    proof = {"model":"CPU IEEE RNE, same coarse helper as prior oracle; not a new device experiment",
             "lower_inclusive":low,"upper_exclusive":high,"fp32_encodings_checked":checked,
             "full_key_high_byte":191,"finding":"first full-FP32-byte round cannot distinguish bucket-188 members"}
    output = {"kernel_commit":COMMIT,"source_path":path,"source_sha256":hashlib.sha256(raw).hexdigest(),
              "real_meta":report["validation"][0]["meta"],
              "real_case_source_semantic_counts":{"hist_atomic_updates":16384,"coarse_computations_hist_and_compact":32768,
                 "compact_returning_atomics":1744+894,"remaining_quota":304,"boundary_count":894},
              "generated_code":generated,"coarse_prefix_proof":proof,"synthetic_finish_work":work}
    (ROOT/"artifacts/topk_overall_audit_20261104.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"proof":proof,"synthetic_rounds":work["rounds"],"generated":generated},indent=2))

if __name__ == "__main__":
    main()
