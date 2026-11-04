"""Independent device validation of merge-consumption alternatives, not TopK timing."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

HERE=Path(__file__).resolve().parent


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def execute(root,report):
    identity=json.loads((HERE/"identity.json").read_text())
    for name,expected in identity.items():assert digest((HERE/name).read_bytes())==expected,name
    report["tool_identity"]=identity
    helper_path=HERE.parent/"topk-950pr-device-compare-r1/run.py"
    assert digest(helper_path.read_bytes().replace(b"\r\n",b"\n"))=="6453592e4b324c5a0da4e619fbdae19f51deda54a1f746b9577cc95b4813439d", "Shared preflight helper changed"
    helper=load(helper_path,"validated_device_preflight")
    report["health"]=[helper.check_device(root,"preflight")]
    helper.configure_temp(report)
    for key,folder in [("TILELANG_CACHE_DIR","tl-cache"),("ASCEND_CACHE_PATH","cann-cache"),("ASCEND_WORK_PATH","work")]:
        target=root/folder;target.mkdir();os.environ[key]=str(target)
    import torch
    import torch_npu
    import tilelang
    from tilelang.ascend.callback import register_ascend_postproc_callback
    from cases import build_cases,R
    from kernels import consume_binary,consume_tree,scan_control
    torch.npu.set_device(0)
    report["runtime"]={"python":sys.executable,"torch":torch.__version__,"torch_npu":torch_npu.__version__,
        "tilelang":tilelang.__version__,"device":torch.npu.get_device_name(0),"cann_home":os.environ.get("ASCEND_HOME_PATH")}
    assert "950" in report["runtime"]["device"]
    def capture(code,target):
        (root/(report["stage"]+"-precompile.cpp")).write_text(str(code))
        return str(code)
    register_ascend_postproc_callback(capture,override=True)
    cases=build_cases();B=len(cases)
    def signed(k):return k if k<(1<<31) else k-(1<<32)
    left_keys=[[signed(k) for k,i in case["left"]]+[0]*(R-len(case["left"])) for case in cases]
    left_ids=[[i for k,i in case["left"]]+[0]*(R-len(case["left"])) for case in cases]
    cpu_inputs=[torch.tensor(v,dtype=torch.int32) for v in [left_keys,left_ids,
        [len(c["left"]) for c in cases],[c["m"] for c in cases],
        [signed(c["last"][0]) for c in cases],[c["last"][1] for c in cases],
        [c["tags"]+[0]*(R-c["m"]) for c in cases]]]
    inputs=[v.to("npu") for v in cpu_inputs]
    expected=torch.tensor([c["expected"] for c in cases],dtype=torch.int32)
    report["input_sha256"]=digest(b"".join(v.numpy().tobytes() for v in cpu_inputs))
    report["fixtures"]=[{k:c[k] for k in ("name","m","expected")} | {"left_length":len(c["left"]),"right_length":len(c["right"])} for c in cases]
    scan_cpu=torch.tensor([(i%7)-3 for i in range(R)],dtype=torch.int32)
    scan_x=scan_cpu.to("npu");running=0;scan_expected=[]
    for value in scan_cpu.tolist():running+=value;scan_expected.append(running)
    candidates=[("binary_consumption",lambda:consume_binary(B),inputs[:6],expected),
                ("tree_consumption",lambda:consume_tree(B),[inputs[6],inputs[3]],expected),
                ("scan_control",lambda:scan_control(R),[scan_x],torch.tensor(scan_expected,dtype=torch.int32))]
    report["cases"]={}
    for name,build,args,want in candidates:
        report["stage"]="compile-"+name
        item=report["cases"][name]={"status":"compile_started"}
        report["health"].append(helper.check_device(root,name))
        print("COMPILE",name,flush=True)
        saved=os.dup(2)
        try:
            with (root/(name+".stderr.log")).open("w") as log:
                sys.stderr.flush();os.dup2(log.fileno(),2)
                program=build()
        except Exception:
            item.update(status="compile_failed",traceback=traceback.format_exc())
            print("COMPILE_FAILED",name,flush=True)
            continue
        finally:
            sys.stderr.flush();os.dup2(saved,2);os.close(saved)
        code=str(program.get_kernel_source());(root/(name+".cpp")).write_text(code)
        item.update(source_sha256=digest(code.encode()),source_bytes=len(code.encode()),
                    atomic_marker_present="atomic" in code.lower(),cumsum_marker_present="cumsum" in code.lower())
        log=(root/(name+".stderr.log")).read_text()
        assert "ThreadSync" not in log,"Unresolved synchronization diagnostic: "+name
        report["stage"]="validate-"+name
        result=torch.empty(want.shape,dtype=torch.int32,device="npu")
        for repeat in range(3):
            result.fill_(-123456)
            program(*args,result)
            torch.npu.synchronize()
            actual=result.cpu()
            if not torch.equal(actual,want):
                item.update(status="wrong_result",repeat=repeat,actual=actual.tolist(),expected=want.tolist())
                break
        else:
            item.update(status="passed",repeats=3,actual=actual.tolist())
        print("RESULT",name,item["status"],flush=True)
    torch.npu.synchronize()
    assert all(torch.equal(v.cpu(),original) for v,original in zip(inputs,cpu_inputs)),"Input modified"
    assert torch.equal(scan_x.cpu(),scan_cpu),"Scan input modified"
    report["inputs_preserved"]=True
    report["health"].append(helper.check_device(root,"final"))
    passed=[name for name in ("binary_consumption","tree_consumption") if report["cases"][name]["status"]=="passed" and not report["cases"][name]["atomic_marker_present"] and not report["cases"][name]["cumsum_marker_present"]]
    report["non_scan_methods_passed"]=passed
    report["verdict"]="non_scan_consumption_demonstrated" if passed else "no_non_scan_method_confirmed"
    report["status"]="complete"


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True);args=parser.parse_args()
    root=Path(args.output).resolve();root.mkdir()
    report={"status":"failed","stage":"preflight","purpose":"Independently distinguish scan from two aggregate merge-consumption methods",
        "limits":["CPU supplies correct merged-prefix labels and last item; does not validate a device merge implementation",
                  "No device timing; no claim about full M latency or stable TopK speedup",
                  "Private cooperative lock plus occupancy checks are not shared-host reservation"]}
    try:execute(root,report)
    except Exception:report["error"]=traceback.format_exc();print(report["error"],file=sys.stderr)
    finally:
        report["evidence"]={}
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in (".cpp",".log",".txt"):
                raw=path.read_bytes();report["evidence"][str(path.relative_to(root))]={"sha256":digest(raw),"base64":base64.b64encode(raw).decode()}
        (root/"probe-return.json").write_text(json.dumps(report,indent=2)+"\n")
    print("VERDICT",report.get("verdict",report["status"]),flush=True)
    return 0 if report["status"]=="complete" else 1


if __name__=="__main__":sys.exit(main())
