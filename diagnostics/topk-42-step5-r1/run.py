"""Prevalidate bounded decode configs, then invoke the real TileLang AutoTuner."""
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
    root=Path('/home/y00937463')/('topk-42-step5-r1-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid()))
    root.mkdir();source=Path(os.environ.get('TILEOPS_REPO','/home/y00937463/TileOPs')).resolve()
    report={'status':'failed','scope':'yjl development public API correctness; no shared host reservation or formal receipt',
            'step2':'CPU passed; remainder explicitly deferred by user','step3':'previously_passed','step4':'previously_passed_c70ffa3a','timing':'autotuner_selection_only_no_formal_profiler'}
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
        import inspect
        import math
        from tilelang.autotuner import AutoTuner
        from tileops.kernels.ascend.attention.tuning import decode_select_prim, TUNING_CONFIGS, DEFAULT_CONFIG
        from workloads.numerics import Request, verify
        tuning_source=Path(inspect.getfile(AutoTuner));raw=tuning_source.read_bytes()
        (root/'installed-autotuner.py').write_bytes(raw)
        report['autotuner_api']={'path':str(tuning_source),'sha256':hashlib.sha256(raw).hexdigest(),
            'compile_signature':str(inspect.signature(AutoTuner.set_compile_args)),
            'profile_signature':str(inspect.signature(AutoTuner.set_profile_args)),
            'run_signature':str(inspect.signature(AutoTuner.run))}
        from tileops.kernels.ascend.attention.radix_select import topk_select_ascend
        assert callable(getattr(topk_select_ascend,'get_tir',None))
        profile_keys=inspect.signature(AutoTuner.set_profile_args).parameters
        assert {'warmup','rep','supply_prog','skip_check','backend'}<=set(profile_keys),'Unsupported installed AutoTuner profile contract'
        configs=kernel.tuning_candidates(TUNING_CONFIGS,DEFAULT_CONFIG)
        assert len(configs)==4 and DEFAULT_CONFIG in configs
        report['search_space']=configs;report['default_config']=DEFAULT_CONFIG
        fixtures=load(source/'tests/ops/test_topk_select_ascend_decode.py','decode_candidate_fixtures')
        test=fixtures.test_topk_select_ascend_decode_boundaries
        marks=next(m for m in test.pytestmark if m.name=='parametrize');rows=marks.args[1];assert len(rows)==12
        report['candidate_validation_scope']='Direct compiled candidate with shared source test body/public workload validator; public default dispatch checked separately'
        def validate_candidate(program):
            def make_op(topk):
                assert topk==2048
                def run(scores,starts,ends):
                    return program(scores.reshape(1,16384,1),starts.reshape(1),ends.reshape(1)).reshape(1,1,1,2048)
                return run
            previous=fixtures.TopKSelectFwdOp;fixtures.TopKSelectFwdOp=make_op
            passed=[]
            try:
                for row in rows:
                    report['active_fixture']=row.id
                    test(*row.values);passed.append(row.id)
            finally:fixtures.TopKSelectFwdOp=previous
            return passed
        accepted=[];report['candidates']=[]
        for index,cfg in enumerate(configs):
            report['stage']='candidate-'+str(index)
            rec={'config':cfg,'status':'compile_started'};report['candidates'].append(rec)
            report['health'].append(helper.check_device(root,report['stage']))
            saved=os.dup(2)
            try:
                with (root/(report['stage']+'.stderr.log')).open('w') as log:
                    sys.stderr.flush();os.dup2(log.fileno(),2)
                    program=tilelang.compile(decode_select_prim(**cfg),target='ascend',out_idx=[3])
            except Exception:
                rec.update(status='compile_failed',error=traceback.format_exc());continue
            finally:
                sys.stderr.flush();os.dup2(saved,2);os.close(saved)
            diagnostic=(root/(report['stage']+'.stderr.log')).read_text()
            if 'ThreadSync' in diagnostic:rec['status']='rejected_sync_diagnostic';continue
            code=str(program.get_kernel_source());(root/(report['stage']+'.cpp')).write_text(code)
            rec['source_sha256']=hashlib.sha256(code.encode()).hexdigest()
            report['active_candidate']=cfg;rec['status']='validating'
            rec['fixtures']=validate_candidate(program);rec['repeats_per_fixture']=3
            rec['status']='12_boundary_cases_passed';accepted.append(cfg)
            print('CANDIDATE_VALIDATED',cfg,flush=True)
        assert DEFAULT_CONFIG in accepted,'Default config failed; no tuning allowed'
        assert len(accepted)>=2,'Fewer than two validated configs; no meaningful search'
        torch.manual_seed(20261105)
        supplied=[torch.randn((1,16384,1),device='npu',dtype=torch.float32),
                  torch.zeros(1,device='npu',dtype=torch.int32),torch.full((1,),16384,device='npu',dtype=torch.int32)]
        protected=[x.clone() for x in supplied]
        report['tuning_inputs']={'seed':20261105,'starts':[0],'ends':[16384],
            'sha256':[hashlib.sha256(x.cpu().numpy().tobytes()).hexdigest() for x in supplied]}
        def supply(params):return supplied
        report['stage']='autotuner-search';report['trials']=[]
        report['search_protocol']={'warmup_argument':25,'rep_argument':100,'backend':'event',
            'validation':'All admitted configs validated externally with public workload before search; no elementwise comparison of unordered indices',
            'score_scope':'TileLang config-selection latency only; not formal profiler samples or TopKV2 comparison'}
        tuner=AutoTuner.from_kernel(decode_select_prim,accepted)
        tuner.set_compile_args(out_idx=[3],target='ascend')
        # Unordered index outputs need the public set/value validator above; never use allclose on indices.
        tuner.set_profile_args(warmup=25,rep=100,supply_prog=supply,skip_check=True,backend='event')
        options={'warmup':25,'rep':100};run_params=inspect.signature(tuner.run).parameters
        if 'on_trial' in run_params:options['on_trial']=lambda event:report['trials'].append(event)
        if 'benchmark_multi_gpu' in run_params:options['benchmark_multi_gpu']=False
        if 'use_pipeline' in run_params:options['use_pipeline']=False
        artifact=tuner.run(**options)
        assert artifact.config in accepted,artifact.config
        assert math.isfinite(float(artifact.latency)) and float(artifact.latency)>0
        torch.npu.synchronize()
        for a,b in zip(supplied,protected):assert torch.equal(a.view(torch.int32),b.view(torch.int32)),'Tuning input modified'
        report['stage']='winner-revalidation';report['active_candidate']=artifact.config
        report['winner']={'config':artifact.config,'selection_latency_ms':float(artifact.latency),
                          'fixtures':validate_candidate(artifact.kernel),'repeats_per_fixture':3}
        (root/'winner.cpp').write_text(str(artifact.kernel.get_kernel_source()))
        report['step5']='search_and_winner_boundary_revalidation_complete_pending_review'
        report['status']='development_autotuner_search_complete'
        report['health'].append(helper.check_device(root,'final'))
        return 0
    except Exception:
        report['error']=traceback.format_exc();return 1
    finally:
        report['evidence']={}
        for p in root.rglob('*'):
            if p.is_file() and p.relative_to(root).parts[0]!='TileOPs' and p.suffix in ('.log','.json','.xml','.cpp','.txt','.py'):
                raw=p.read_bytes();report['evidence'][str(p.relative_to(root))]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
        output=HERE.parents[1]/'AAA_Results'/(root.name+'.json');output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report,indent=2,default=str)+'\n');print('STATUS',report['status']);print('UPLOAD_RESULT',output)
        subprocess.run([sys.executable,str(HERE/'pack.py'),str(output)],check=False)


if __name__=='__main__':sys.exit(main())
