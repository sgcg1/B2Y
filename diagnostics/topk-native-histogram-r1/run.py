"""Direct native SIMD histogram contract, correctness and device timing probe."""
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
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def execute(root,report):
    identity=json.loads((HERE/'identity.json').read_text())
    for name,value in identity.items():assert sha((HERE/name).read_bytes())==value,name
    report['tool_identity']=identity
    shared=HERE.parent/'topk-950pr-device-compare-r1'
    assert sha((shared/'run.py').read_bytes().replace(b'\r\n',b'\n'))=='6453592e4b324c5a0da4e619fbdae19f51deda54a1f746b9577cc95b4813439d'
    helper=load(shared/'run.py','threshold_device_preflight')
    report['health']=[helper.check_device(root,'preflight')];helper.configure_temp(report)
    for name,folder in [('TILELANG_CACHE_DIR','tl-cache'),('ASCEND_CACHE_PATH','cann-cache'),('ASCEND_WORK_PATH','work')]:
        target=root/folder;target.mkdir();os.environ[name]=str(target)
    from check_cpu import validate
    report['cpu_oracle_validation']=validate()
    import torch
    import torch_npu
    import tilelang
    import tilelang.ascend.language as T
    from tilelang.ascend.callback import register_ascend_postproc_callback
    from tilelang.profiler.msprof import get_msprof_cache_flush_kernel
    from cases import build_cases,expected,N
    import inspect
    import tilelang.ascend.language.simd as simd
    source=Path(inspect.getfile(simd)).read_bytes()
    (root/"installed-simd.py").write_bytes(source)
    report["installed_simd"]={"path":inspect.getfile(simd),"sha256":sha(source),"definitions":{}}
    for key in ("dhistv2","chistv2","alloc_var","pset","vld","vsts","vdup","vcmp","_histogram"):
        fn=getattr(simd,key,None)
        assert callable(fn),"API_contract_unverified: "+key
        report["installed_simd"]["definitions"][key]=inspect.getsource(fn)
    for key in ("dhistv2","chistv2"):
        signature=inspect.signature(getattr(simd,key))
        assert list(signature.parameters)==["dst","src","mask","bin"],str(signature)
        assert signature.parameters["bin"].default==0,str(signature)
    backend=Path(tilelang.__file__).resolve().parent/'src/ascend/codegen/codegen_ascend.cc'
    if backend.is_file():
        raw=backend.read_bytes();lines=raw.decode('utf-8',errors='replace').splitlines()
        hits=set()
        for i,line in enumerate(lines):
            if 'histogram' in line.lower():hits.update(range(max(0,i-12),min(len(lines),i+24)))
        report['installed_codegen']={'path':str(backend),'sha256':sha(raw),'excerpts':[{'line':i+1,'text':lines[i]} for i in sorted(hits)]}
    from kernels import histogram
    sys.path.insert(0,str(shared));from profile_support import read_profile,names_for
    torch.npu.set_device(0)
    report['runtime']={'python':sys.executable,'torch':torch.__version__,'torch_npu':torch_npu.__version__,
                       'tilelang':tilelang.__version__,'device':torch.npu.get_device_name(0),'cann_home':os.environ.get('ASCEND_HOME_PATH')}
    assert '950' in report['runtime']['device']
    def capture(code,target):
        (root/(report['stage']+'-precompile.cpp')).write_text(str(code));return str(code)
    register_ascend_postproc_callback(capture,override=True)
    cases=build_cases();report['fixtures']=[{'name':c['name'],'digits_sha256':sha(bytes(c['digits'])),'tags_sha256':sha(bytes(c['tags']))} for c in cases]
    x=torch.empty(N,dtype=torch.uint8,device='npu');tags=torch.empty_like(x)
    report['methods']={};flush=None;buffer=None
    def prepare(c):
        cpu=torch.tensor(c['digits'],dtype=torch.uint8);mask=torch.tensor(c['tags'],dtype=torch.uint8)
        x.copy_(cpu);tags.copy_(mask);torch.npu.synchronize();return cpu,mask
    def profile(fn,label):
        directory=root/('profile-'+label);directory.mkdir();os.environ['ASCEND_WORK_PATH']=str(directory)
        with torch_npu.profiler.profile(activities=[torch_npu.profiler.ProfilerActivity.NPU],
            schedule=torch_npu.profiler.schedule(wait=0,warmup=0,active=1,repeat=1,skip_first=0),on_trace_ready=lambda prof:None,
            experimental_config=torch_npu.profiler._ExperimentalConfig(profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
                aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,l2_cache=False,data_simplification=False)) as prof:
            fn();torch.npu.synchronize();prof.step()
        return Path(prof.prof_if.prof_path)
    for name,masked,sf,sc in [('full_zero',False,0,0),('masked_zero',True,0,0),('masked_seeded',True,7,11)]:
        record=report['methods'][name]={'status':'compile_started'};report['stage']='compile-'+name
        report['health'].append(helper.check_device(root,name+'-begin'));print('COMPILE',name,flush=True)
        saved=os.dup(2)
        try:
            with (root/(name+'.stderr.log')).open('w') as log:
                sys.stderr.flush();os.dup2(log.fileno(),2);program=histogram(N,masked,sf,sc)
        except Exception:
            record.update(status='compile_failed',error=traceback.format_exc());continue
        finally:
            sys.stderr.flush();os.dup2(saved,2);os.close(saved)
        code=str(program.get_kernel_source());(root/(name+'.cpp')).write_text(code)
        record.update(source_sha256=sha(code.encode()),atomic_marker_present='atomic' in code.lower())
        diagnostic=(root/(name+'.stderr.log')).read_text()
        if 'ThreadSync' in diagnostic:record.update(status='rejected_sync_diagnostic',error=diagnostic);continue
        markers=['simd_inst::dhistv2','simd_inst::chistv2','Bin_N0','Bin_N1']
        record['native_markers']={m:m in code for m in markers}
        if not all(record['native_markers'].values()):
            record['status']='rejected_native_lowering_unverified';continue
        output=torch.empty((4,128),dtype=torch.int16,device='npu')
        def invoke():program(x,tags,output)
        def actual_values():return (output.cpu().to(torch.int32)&65535).tolist()
        record['validation']=[]
        for c in cases:
            report['stage']='validate-'+name+'-'+c['name'];cpu,mask=prepare(c)
            want=expected(c,masked,sf,sc)
            for repeat in range(3):
                output.fill_(-777);invoke();torch.npu.synchronize();actual=actual_values()
                if actual!=want:
                    record.update(status='wrong_result',case=c['name'],repeat=repeat,actual=actual,expected=want)
                    raise AssertionError(name+' output mismatch')
                assert torch.equal(x.cpu(),cpu) and torch.equal(tags.cpu(),mask),'Input modified'
            record['validation'].append({'case':c['name'],'passed':True,'repeats':3,'output':actual})
        print('VALIDATION_PASSED',name,len(cases),'x 3',flush=True);record['status']='correctness_passed';record['inputs_preserved']=True
        cpu,mask=prepare(cases[0])
        if flush is None:
            report['stage']='compile-flush';flush=get_msprof_cache_flush_kernel((1<<30)//4,'int32');buffer=torch.empty((1<<30)//4,dtype=torch.int32,device='npu')
            p=profile(lambda:flush(buffer),'flush-selftest')
            assert any('_tilelang_profiler_cache_flush' in v for v in names_for(p).values()),'Unresolved flush marker'
        def isolate():flush(buffer);torch.npu.synchronize()
        for _ in range(3):isolate();invoke();torch.npu.synchronize()
        record['profiles']=[]
        for sample in range(5):
            report['stage']=name+'-sample-'+str(sample);report['health'].append(helper.check_device(root,report['stage']))
            isolate();p=profile(invoke,name+'-'+str(sample))
            try:decoded=read_profile(p,1)
            except Exception:record['timing_parse_error']=traceback.format_exc();break
            record['profiles'].append(decoded);print('DEVICE_SAMPLE',name,sample,decoded['latency_ms']*1000,'us',flush=True)
        assert actual_values()==expected(cases[0],masked,sf,sc),'Post-timing output mismatch'
        assert torch.equal(x.cpu(),cpu) and torch.equal(tags.cpu(),mask),'Post-timing input modified'
        vals=[v['latency_ms']*1000 for v in record['profiles']]
        if len(vals)==5:record.update(status='correctness_and_timing_complete',timing_us={'samples':vals,'mean':statistics.mean(vals),'stdev':statistics.stdev(vals),'min':min(vals),'max':max(vals)})
        else:record['status']='correctness_passed_timing_unavailable'
    report['health'].append(helper.check_device(root,'final'))
    report['route_feasibility']='native_histogram_only_full_key_selection_and_collection_not_tested'
    report['status']='complete' if all(v['status']=='correctness_and_timing_complete' for v in report['methods'].values()) else 'partial'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();root=Path(args.output).resolve();root.mkdir()
    report={'status':'failed','stage':'preflight','protocol':'native-simd-histogram-v1', 'limits':[
        'One block, 16384 uint8 digits already supplied by CPU; not full FP32 TopK',
        '64 vectors; each uses two frequency and two cumulative native histogram instructions',
        'Cumulative bank1 oracle includes all lower-bank counts; device semantics remain to be verified',
        'No full-key conversion, threshold selection, native collect or TopKV2 comparison',
        'No whole-operator speedup or DT prediction from this microbenchmark']}
    try:execute(root,report)
    except Exception:report['error']=traceback.format_exc();print(report['error'],file=sys.stderr)
    finally:
        report['evidence']={}
        for path in sorted(root.rglob('*')):
            if path.is_file() and (path.suffix in ('.cpp','.log','.txt','.py') or any(s in path.name for s in ('ffts_profile','hash_dic','task_track','stars_soc.data','info.json'))):
                if not path.name.endswith(('.done','.complete')):
                    raw=path.read_bytes();report['evidence'][str(path.relative_to(root))]={'sha256':sha(raw),'base64':base64.b64encode(raw).decode()}
        (root/'native-hist-return.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RUN_STATUS',report['status'],'ROUTE_FEASIBILITY',report.get('route_feasibility','not_reached'),flush=True)
    return 0 if report['status']=='complete' else 1


if __name__=='__main__':sys.exit(main())
