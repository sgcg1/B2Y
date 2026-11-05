"""Development-only public TopK integration check in original yjl; no timing."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import datetime
HERE=Path(__file__).resolve().parent
BASE='4409536e1f0dba8dca7141d6aee6fc6677afa9ce'
CANDIDATE='727132f7'


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    root=Path('/home/y00937463')/('topk-42-step3-r1-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid()))
    root.mkdir();source=Path(os.environ.get('TILEOPS_REPO','/home/y00937463/TileOPs')).resolve()
    report={'status':'failed','scope':'yjl development public API correctness; no shared host reservation or formal receipt',
            'step2':'CPU passed; remainder explicitly deferred by user','step3':'pending','step4':'pending','timing':'not_requested'}
    try:
        identity=json.loads((HERE/'identity.json').read_text())
        for name,digest in identity.items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
        report['tool_identity']=identity
        assert (source/'.git').exists(),'TileOPs checkout not found; set TILEOPS_REPO'
        sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        assert sha=='727132f7dc387cdc6c56eec2400e42d038245b1c','Pull the documented candidate branch before running'
        subprocess.run(['git','diff','--exit-code','HEAD','--'],cwd=source,check=True)
        report['source_checkout']=str(source)
        report['source_sha']=sha
        env=dict(os.environ,TORCH_DEVICE_BACKEND_AUTOLOAD='0',PYTHONDONTWRITEBYTECODE='1')
        with (root/'cpu.log').open('w') as log:
            cpu=subprocess.run([sys.executable,'scripts/ci/ascend950.py','--phase','cpu','--output',str(root/'cpu')],cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT)
        if cpu.returncode:report['status']='cpu_gate_failed';return 1
        report['cpu_receipt']=json.loads((root/'cpu/receipt.json').read_text());assert report['cpu_receipt']['status']=='passed'
        helper=load(HERE.parent/'topk-950pr-device-compare-r1/run.py','topk_integration_health')
        report['health']=[helper.check_device(root,'preflight')];helper.configure_temp(report)
        for key,name in [('TILELANG_CACHE_DIR','tl-cache'),('ASCEND_CACHE_PATH','cann-cache'),('ASCEND_WORK_PATH','work')]:
            (root/name).mkdir();os.environ[key]=str(root/name)
        sys.path[:0]=[str(source/'src'),str(source)]
        import torch
        import torch_npu
        import tilelang
        torch.npu.set_device(0)
        report['environment']={'torch':torch.__version__,'torch_npu':torch_npu.__version__,'tilelang':tilelang.__version__,'device':torch.npu.get_device_name(0)}
        assert '950PR' in report['environment']['device']
        import tileops.ascend  # Explicit source backend load; no editable install or entry-point claim.
        from tileops.attention import TopKSelectFwdOp
        from tileops.kernels.attention.topk_select import TopKSelectCall
        from benchmarks.api import cases
        from benchmarks._cases import entry
        from benchmarks.ascend.runner import benchmark_case
        from workloads.device import set_run_device
        from tilelang.ascend.callback import register_ascend_postproc_callback
        def capture(code,target):
            (root/'precompile.cpp').write_text(str(code));return str(code)
        register_ascend_postproc_callback(capture,override=True)
        set_run_device('npu')
        selected=[c for c in cases('TopKSelectFwdOp') if c.id=='ds-v32-topk-decode-b1'];assert len(selected)==1
        case=selected[0];torch.manual_seed(20261105);inputs=case.inputs
        assert [list(x.shape) for x in inputs]==[[1,1,16384,1],[1,1],[1,1]]
        assert [x.dtype for x in inputs]==[torch.float32,torch.int32,torch.int32]
        assert inputs[1].item()==0 and inputs[2].item()==16384
        op=TopKSelectFwdOp(**case.arguments)
        call=TopKSelectCall(batch=1,seq_len=1,seq_len_kv=16384,kv_group=1,topk=2048,
                           dtype=torch.float32,out_dtype=torch.int32,device=inputs[0].device)
        saved=os.dup(2)
        try:
            with (root/'compile.stderr.log').open('w') as log:
                sys.stderr.flush();os.dup2(log.fileno(),2)
                kernel=op.kernel_for('topk_select',call)
        finally:
            sys.stderr.flush();os.dup2(saved,2);os.close(saved)
        assert type(kernel).__name__=='AscendTopKSelectKernel',type(kernel).__name__
        report['selected_kernel']=type(kernel).__module__+'.'+type(kernel).__name__
        assert 'ThreadSync' not in (root/'compile.stderr.log').read_text(),'ThreadSync guard rejected execution'
        (root/'kernel.cpp').write_text(str(kernel.program.get_kernel_source()))
        report['step3']='public_dispatch_and_compile_passed'
        report['checks']=benchmark_case(case,{'tileops':entry('TopKSelectFwdOp').binder(op,case)},None,
                                        name='TopKSelectFwdOp/ds-v32-topk-decode-b1',verify_only=True)
        torch.npu.synchronize()
        report['step4']='decode_manifest_correctness_passed_boundaries_pending'
        report['status']='development_decode_correctness_passed'
        report['health'].append(helper.check_device(root,'final'))
        return 0
    except Exception:
        report['error']=traceback.format_exc();return 1
    finally:
        report['evidence']={}
        for p in root.rglob('*'):
            if p.is_file() and p.relative_to(root).parts[0]!='TileOPs' and p.suffix in ('.log','.json','.xml','.cpp','.txt'):
                raw=p.read_bytes();report['evidence'][str(p.relative_to(root))]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
        output=HERE.parents[1]/'AAA_Results'/(root.name+'.json');output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report,indent=2,default=str)+'\n');print('STATUS',report['status']);print('UPLOAD_RESULT',output)
        subprocess.run([sys.executable,str(HERE/'pack.py'),str(output)],check=False)


if __name__=='__main__':sys.exit(main())
