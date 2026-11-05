"""Interleaved raw-device comparison of default and AutoTuner winner; no default change."""
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
CANDIDATE='8b277187'


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    root=Path('/home/y00937463')/('topk-42-step6-compare-r1-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid()))
    root.mkdir();source=Path(os.environ.get('TILEOPS_REPO','/home/y00937463/TileOPs')).resolve()
    report={'status':'failed','scope':'yjl development public API correctness; no shared host reservation or formal receipt',
            'step2':'CPU passed; remainder explicitly deferred by user','step3':'previously_passed','step4':'previously_passed_c70ffa3a','timing':'raw_device_development_no_shared_guard','round':int(os.environ['TOPK_COMPARE_ROUND'])}
    try:
        identity=json.loads((HERE/'identity.json').read_text())
        for name,digest in identity.items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
        report['tool_identity']=identity
        assert (source/'.git').exists(),'TileOPs checkout not found; set TILEOPS_REPO'
        sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        assert sha=='8b27718757f42175dc940326a1278be22bf97c3d','Pull the documented candidate branch before running'
        subprocess.run(['git','diff','--exit-code','HEAD','--'],cwd=source,check=True)
        report['source_checkout']=str(source)
        report['source_sha']=sha
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
            (root/(report.get('stage','base')+'-precompile.cpp')).write_text(str(code));return str(code)
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
        import statistics
        from tileops.kernels.ascend.attention.tuning import decode_select_prim
        from workloads.numerics import Request, verify
        from tilelang.profiler.msprof import get_msprof_cache_flush_kernel
        shared=HERE.parent/'topk-950pr-device-compare-r1'
        sys.path.insert(0,str(shared))
        from profile_support import read_profile,names_for
        configs={'default':{'H':128,'PARALLEL_SCAN':True},'candidate':{'H':256,'PARALLEL_SCAN':False}}
        programs={};report['configs']=configs;report['candidate_validation']={}
        fixtures=load(source/'tests/ops/test_topk_select_ascend_decode.py','compare_fixtures')
        test=fixtures.test_topk_select_ascend_decode_boundaries
        rows=next(m for m in test.pytestmark if m.name=='parametrize').args[1]
        assert len(rows)==12
        def validate_program(program):
            previous=fixtures.TopKSelectFwdOp
            def make_op(topk):
                assert topk==2048
                def run(scores,starts,ends):
                    out=torch.empty((1,2048),dtype=torch.int32,device=scores.device)
                    program(scores.reshape(1,16384,1),starts.reshape(1),ends.reshape(1),out)
                    return out.reshape(1,1,1,2048)
                return run
            fixtures.TopKSelectFwdOp=make_op;passed=[]
            try:
                for row in rows:
                    report['active_fixture']=row.id;test(*row.values);passed.append(row.id)
            finally:fixtures.TopKSelectFwdOp=previous
            return passed
        for name,cfg in configs.items():
            report['stage']='compile-'+name;saved=os.dup(2)
            try:
                with (root/(name+'.stderr.log')).open('w') as log:
                    sys.stderr.flush();os.dup2(log.fileno(),2)
                    program=tilelang.compile(decode_select_prim(**cfg),target='ascend',out_idx=[])
            finally:
                sys.stderr.flush();os.dup2(saved,2);os.close(saved)
            assert 'ThreadSync' not in (root/(name+'.stderr.log')).read_text(),'Rejected sync diagnostic'
            code=str(program.get_kernel_source());(root/(name+'.cpp')).write_text(code)
            if name=='default':
                report['default_cpp_matches_public_kernel']=code==str(kernel.program.get_kernel_source())
                assert report['default_cpp_matches_public_kernel'],'Default wrapper changed generated code'
            programs[name]=program
            report['candidate_validation'][name]={'fixtures':validate_program(program),'repeats_per_fixture':3}
        def profile(fn,label):
            directory=root/('profile-'+label);directory.mkdir();os.environ['ASCEND_WORK_PATH']=str(directory)
            with torch_npu.profiler.profile(activities=[torch_npu.profiler.ProfilerActivity.NPU],
                schedule=torch_npu.profiler.schedule(wait=0,warmup=0,active=1,repeat=1,skip_first=0),on_trace_ready=lambda prof:None,
                experimental_config=torch_npu.profiler._ExperimentalConfig(profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
                    aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,l2_cache=False,data_simplification=False)) as prof:
                fn();torch.npu.synchronize();prof.step()
            return Path(prof.prof_if.prof_path)
        report['stage']='flush-selftest'
        flush=get_msprof_cache_flush_kernel((1<<30)//4,'int32')
        buffer=torch.empty((1<<30)//4,dtype=torch.int32,device='npu')
        trace=profile(lambda:flush(buffer),'flush-selftest')
        assert any('_tilelang_profiler_cache_flush' in name for name in names_for(trace).values())
        def isolate():flush(buffer);torch.npu.synchronize()
        scores,starts,ends=inputs
        outputs={name:torch.empty((1,2048),device='npu',dtype=torch.int32) for name in configs}
        report['scenarios']={};torch.manual_seed(20261105)
        random_values=torch.randn(16384,dtype=torch.float32)
        scenario_values={'random':random_values,'equal':torch.ones(16384),
            'adjacent':(torch.arange(16384,dtype=torch.int32)+0x3F800000).view(torch.float32)}
        for scenario,cpu in scenario_values.items():
            scores.copy_(cpu.reshape(1,1,16384,1));starts.fill_(0);ends.fill_(16384);torch.npu.synchronize()
            evidence=case.workload.verification(*inputs);expected=case.workload.ref_program(*inputs)
            score_bits=scores.view(torch.int32).clone()
            record={'score_sha256':hashlib.sha256(cpu.numpy().tobytes()).hexdigest(),'profiles':[],
                    'starts':0,'ends':16384,'warmup_calls_per_method':3}
            report['scenarios'][scenario]=record
            args={name:(scores.reshape(1,16384,1),starts.reshape(1),ends.reshape(1),out) for name,out in outputs.items()}
            def invoke(name):programs[name](*args[name])
            def check(name):
                evidence.validator(outputs[name].reshape(1,1,1,2048),expected)
                assert torch.equal(scores.view(torch.int32),score_bits),'Scores changed'
                assert starts.item()==0 and ends.item()==16384,'Window changed'
            for name in configs:
                for _ in range(3):isolate();invoke(name);torch.npu.synchronize();check(name)
            for pair in range(5):
                order=['default','candidate'] if (pair+report['round'])%2==0 else ['candidate','default']
                for name in order:
                    report['stage']=scenario+'-'+str(pair)+'-'+name
                    report['health'].append(helper.check_device(root,report['stage']))
                    isolate();trace=profile(lambda:invoke(name),report['stage'])
                    decoded=read_profile(trace,1);check(name)
                    record['profiles'].append({'pair':pair,'method':name,'decoded':decoded})
                    print('DEVICE_SAMPLE',scenario,pair,name,decoded['latency_ms']*1000,'us',flush=True)
            record['summary_us']={}
            for name in configs:
                values=[row['decoded']['latency_ms']*1000 for row in record['profiles'] if row['method']==name]
                assert len(values)==5
                record['summary_us'][name]={'samples':values,'mean':statistics.mean(values),'stdev':statistics.stdev(values),
                    'min':min(values),'max':max(values)}
            record['inputs_preserved']=True
        report['status']='development_raw_device_compare_complete'
        report['default_changed']=False
        report['health'].append(helper.check_device(root,'final'))
        return 0
    except Exception:
        report['error']=traceback.format_exc();return 1
    finally:
        report['evidence']={}
        for p in root.rglob('*'):
            if p.is_file() and p.relative_to(root).parts[0]!='TileOPs' and (p.suffix in ('.log','.json','.xml','.cpp','.txt','.py') or any(key in p.name for key in ('ffts_profile','hash_dic','task_track','stars_soc.data','info.json'))):
                raw=p.read_bytes();report['evidence'][str(p.relative_to(root))]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
        output=HERE.parents[1]/'AAA_Results'/(root.name+'.json');output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report,indent=2,default=str)+'\n');print('STATUS',report['status']);print('UPLOAD_RESULT',output)
        subprocess.run([sys.executable,str(HERE/'pack.py'),str(output)],check=False)


if __name__=='__main__':sys.exit(main())
