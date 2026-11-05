"""GPU-produced exact merge outputs and multi-batch cursors, with scoped device timing."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
import traceback

HERE=Path(__file__).resolve().parent


def sha(raw):return hashlib.sha256(raw).hexdigest()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def execute(root,report):
    identity=json.loads((HERE/"identity.json").read_text())
    for name,digest in identity.items():assert sha((HERE/name).read_bytes())==digest,name
    report["tool_identity"]=identity
    shared=HERE.parent/"topk-950pr-device-compare-r1"
    assert sha((shared/"run.py").read_bytes().replace(b"\r\n",b"\n"))=="6453592e4b324c5a0da4e619fbdae19f51deda54a1f746b9577cc95b4813439d"
    report["shared_helper_sha256"]={name:sha((shared/name).read_bytes().replace(b"\r\n",b"\n")) for name in ("run.py","profile_support.py","kernel_task_profile.py")}
    helper=load(shared/"run.py","merge_device_preflight")
    report["health"]=[helper.check_device(root,"preflight")]
    helper.configure_temp(report)
    for name,folder in [("TILELANG_CACHE_DIR","tl-cache"),("ASCEND_CACHE_PATH","cann-cache"),("ASCEND_WORK_PATH","work")]:
        target=root/folder;target.mkdir();os.environ[name]=str(target)
    from check_cpu import validate
    report["cpu_kernel_ast_validation"]=validate()
    import torch
    import torch_npu
    import tilelang
    from tilelang.ascend.callback import register_ascend_postproc_callback
    from tilelang.profiler.msprof import get_msprof_cache_flush_kernel
    from cases import build_cases,expected,signed,L,K
    from kernels import merge_batches
    sys.path.insert(0,str(shared))
    from profile_support import read_profile,names_for
    torch.npu.set_device(0)
    report["runtime"]={"python":sys.executable,"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                       "tilelang":tilelang.__version__,"device":torch.npu.get_device_name(0),"cann_home":os.environ.get("ASCEND_HOME_PATH")}
    assert "950" in report["runtime"]["device"]
    def capture(code,target):
        (root/(report["stage"]+"-precompile.cpp")).write_text(str(code))
        return str(code)
    register_ascend_postproc_callback(capture,override=True)
    cases=build_cases();B=len(cases)
    report["fixtures"]=[{"name":c["name"],"left":len(c["left"]),"right":len(c["right"]),"limit":c["limit"]} for c in cases]
    cpu_inputs=[torch.tensor(x,dtype=torch.int32) for x in [
        [[[signed(k) for k,i in c[side]]+[0]*(L-len(c[side])) for side in ("left","right")] for c in cases],
        [[[i for k,i in c[side]]+[0]*(L-len(c[side])) for side in ("left","right")] for c in cases],
        [[len(c["left"]),len(c["right"])] for c in cases],[c["limit"] for c in cases]]]
    inputs=[x.to("npu") for x in cpu_inputs]
    report["input_sha256"]=sha(b"".join(x.numpy().tobytes() for x in cpu_inputs))
    report["variants"]={}
    flush=None;buffer=None
    def compile_program(R,count,record):
        report["stage"]=f"compile-R{R}-B{count}"
        print(report["stage"],flush=True)
        saved=os.dup(2)
        try:
            with (root/(report["stage"]+".stderr.log")).open("w") as log:
                sys.stderr.flush();os.dup2(log.fileno(),2)
                program=merge_batches(count,R)
        except Exception:
            record.update(status="compile_failed",error=traceback.format_exc())
            return None
        finally:
            sys.stderr.flush();os.dup2(saved,2);os.close(saved)
        code=str(program.get_kernel_source());(root/(report["stage"]+".cpp")).write_text(code)
        record["source_sha256"]=sha(code.encode())
        record["atomic_marker_present"]="atomic" in code.lower()
        record["cumsum_marker_present"]="cumsum" in code.lower()
        diagnostic=(root/(report["stage"]+".stderr.log")).read_text()
        if "ThreadSync" in diagnostic:
            record.update(status="rejected_sync_diagnostic",error=diagnostic)
            return None
        return program
    def profile(fn,label):
        folder=root/("profile-"+label);folder.mkdir();os.environ["ASCEND_WORK_PATH"]=str(folder)
        with torch_npu.profiler.profile(activities=[torch_npu.profiler.ProfilerActivity.NPU],
            schedule=torch_npu.profiler.schedule(wait=0,warmup=0,active=1,repeat=1,skip_first=0),
            on_trace_ready=lambda prof:None,
            experimental_config=torch_npu.profiler._ExperimentalConfig(
                profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
                aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,l2_cache=False,data_simplification=False)) as prof:
            fn();torch.npu.synchronize();prof.step()
        return Path(prof.prof_if.prof_path)
    for R in (128,256):
        record=report["variants"][str(R)]={"status":"started","validation":{},"single_case":{}}
        report["health"].append(helper.check_device(root,f"R{R}-begin"))
        program=compile_program(R,B,record["validation"])
        if program is None:
            record["status"]="validation_compile_failed"
            continue
        wanted=[expected(c,R) for c in cases]
        want=[torch.tensor(x,dtype=torch.int32) for x in [[ [signed(k) for k in v[0]] for v in wanted], [v[1] for v in wanted], [v[2] for v in wanted]]]
        outputs=[torch.empty(x.shape,dtype=torch.int32,device="npu") for x in want]
        report["stage"]=f"validate-R{R}"
        for repeat in range(3):
            for tensor in outputs:tensor.fill_(-777)
            program(*inputs,*outputs);torch.npu.synchronize()
            actual=[x.cpu() for x in outputs]
            for name,got,ref in zip(("keys","ids","trace"),actual,want):
                if not torch.equal(got,ref):
                    record.update(status="wrong_result",failed_output=name,repeat=repeat,
                                  mismatches=(got!=ref).nonzero()[:20].tolist())
                    raise AssertionError(f"R{R}: wrong {name}")
        record["validation"].update(status="passed",cases=B,repeats=3,
            output_sha256=sha(b"".join(x.numpy().tobytes() for x in actual)),
            final_trace=[v[-1] for v in actual[2].tolist()],
            all_batch_traces=actual[2].tolist())
        assert all(torch.equal(x.cpu(),y) for x,y in zip(inputs,cpu_inputs)),"Input modified"
        print("VALIDATION_PASSED",R,B,"cases x 3",flush=True)
        single=compile_program(R,1,record["single_case"])
        if single is None:
            record["status"]="correctness_passed_single_compile_failed"
            continue
        single_inputs=[x[:1].contiguous() for x in inputs]
        single_outputs=[torch.empty(x[:1].shape,dtype=torch.int32,device="npu") for x in want]
        if flush is None:
            report["stage"]="compile-flush"
            flush=get_msprof_cache_flush_kernel((1<<30)//4,"int32")
            buffer=torch.empty((1<<30)//4,dtype=torch.int32,device="npu")
            path=profile(lambda:flush(buffer),"flush-selftest")
            assert any("_tilelang_profiler_cache_flush" in n for n in names_for(path).values()),"Unresolved flush marker"
        def isolate():flush(buffer);torch.npu.synchronize()
        def invoke():single(*single_inputs,*single_outputs)
        for _ in range(3):isolate();invoke();torch.npu.synchronize()
        record["timing_scope"]={"case":cases[0]["name"],"left":L,"right":L,"output_limit":K,
            "blocks":1,"batch_size":R,"batches":K//R,"samples":5,"includes":"merge, cursor updates, output initialization and trace stores",
            "excludes":"local sorting and other nodes of full M"}
        record["profiles"]=[]
        for sample in range(5):
            report["stage"]=f"measure-R{R}-{sample}"
            report["health"].append(helper.check_device(root,report["stage"]))
            isolate();path=profile(invoke,f"R{R}-{sample}")
            try:result=read_profile(path,1)
            except Exception:
                record["timing_parse_error"]=traceback.format_exc()
                break
            record["profiles"].append(result)
            print("DEVICE_SAMPLE",R,sample,result["latency_ms"]*1000,"us",flush=True)
        actual_single=[x.cpu() for x in single_outputs]
        assert all(torch.equal(x,y[:1]) for x,y in zip(actual_single,want)),"Timed single-case result mismatch"
        record["single_case"]["status"]="correctness_passed_after_timing"
        vals=[p["latency_ms"]*1000 for p in record["profiles"]]
        if len(vals)==5:
            record["timing_us"]={"samples":vals,"mean":statistics.mean(vals),"stdev":statistics.stdev(vals),"min":min(vals),"max":max(vals)}
            record["status"]="correctness_and_timing_complete"
        else:record["status"]="correctness_passed_timing_unavailable"
    assert all(torch.equal(x.cpu(),y) for x,y in zip(inputs,cpu_inputs)),"Input modified"
    report["inputs_preserved"]=True
    report["health"].append(helper.check_device(root,"final"))
    report["status"]="complete" if all(v["status"]=="correctness_and_timing_complete" for v in report["variants"].values()) else "partial"


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);args=p.parse_args()
    root=Path(args.output).resolve();root.mkdir()
    report={"status":"failed","stage":"preflight","protocol":"isolated-one-block-rank-merge-device-task-sum-v1",
        "limits":["GPU performs exact merge; CPU only supplies sorted inputs and independent expected outputs",
        "This is a two-list merge node, not the N16384 complete TopK operator",
        "SIMT per-element binary ranking is a capability candidate, not a native SIMD merge claim",
        "No full-M speedup or target attainment can be inferred from these times"]}
    try:execute(root,report)
    except Exception:report["error"]=traceback.format_exc();print(report["error"],file=sys.stderr)
    finally:
        report["evidence"]={}
        for path in sorted(root.rglob("*")):
            if path.is_file() and (path.suffix in (".cpp",".log",".txt") or any(s in path.name for s in ("ffts_profile","hash_dic","task_track","stars_soc.data","info.json"))):
                if not path.name.endswith((".done",".complete")):
                    raw=path.read_bytes();report["evidence"][str(path.relative_to(root))]={"sha256":sha(raw),"base64":base64.b64encode(raw).decode()}
        (root/"merge-return.json").write_text(json.dumps(report,indent=2)+"\n")
    print("RUN_STATUS",report["status"],flush=True)
    return 0 if report["status"]=="complete" else 1


if __name__=="__main__":sys.exit(main())
