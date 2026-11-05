"""Threshold-route fixed-expression costs plus read-only native-primitive discovery."""
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
    report['cpu_kernel_ast_validation']=validate()
    import torch
    import torch_npu
    import tilelang
    import tilelang.ascend.language as T
    from tilelang.ascend.callback import register_ascend_postproc_callback
    from tilelang.profiler.msprof import get_msprof_cache_flush_kernel
    from cases import build_cases,signed,N,K
    from kernels import encode_keys,collect_given_threshold
    from source_inventory import collect
    sys.path.insert(0,str(shared));from profile_support import read_profile,names_for
    torch.npu.set_device(0)
    report['runtime']={'python':sys.executable,'torch':torch.__version__,'torch_npu':torch_npu.__version__,
                       'tilelang':tilelang.__version__,'device':torch.npu.get_device_name(0),'cann_home':os.environ.get('ASCEND_HOME_PATH')}
    assert '950' in report['runtime']['device']
    report['stage']='backend-inventory';report['backend_inventory']=collect(T,tilelang)
    print('HISTOGRAM_STATUS',report['backend_inventory']['histogram_device_test'],flush=True)
    def capture(code,target):
        (root/(report['stage']+'-precompile.cpp')).write_text(str(code));return str(code)
    register_ascend_postproc_callback(capture,override=True)
    cases=build_cases();report['fixtures']=[]
    for c in cases:report['fixtures'].append({'name':c['name'],'start':c['start'],'end':c['end'],'threshold':c['threshold'],'expected_meta':c['meta'],'score_sha256':sha(torch.tensor(c['values'],dtype=torch.float32).numpy().tobytes())})
    x=torch.empty(N,dtype=torch.float32,device='npu')
    starts=torch.empty(1,dtype=torch.int32,device='npu');ends=torch.empty_like(starts);threshold=torch.empty_like(starts)
    report['methods']={};flush=None;buffer=None
    def prepare(c):
        cpu=torch.tensor(c['values'],dtype=torch.float32);x.copy_(cpu)
        starts.fill_(c['start']);ends.fill_(c['end']);threshold.fill_(signed(c['threshold']))
        torch.npu.synchronize();return cpu
    def profile(fn,label):
        directory=root/('profile-'+label);directory.mkdir();os.environ['ASCEND_WORK_PATH']=str(directory)
        with torch_npu.profiler.profile(activities=[torch_npu.profiler.ProfilerActivity.NPU],
            schedule=torch_npu.profiler.schedule(wait=0,warmup=0,active=1,repeat=1,skip_first=0),on_trace_ready=lambda prof:None,
            experimental_config=torch_npu.profiler._ExperimentalConfig(profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
                aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,l2_cache=False,data_simplification=False)) as prof:
            fn();torch.npu.synchronize();prof.step()
        return Path(prof.prof_if.prof_path)
    for name,build in [('encode_keys',lambda:encode_keys(N)),('collect_given_threshold',lambda:collect_given_threshold(N,K))]:
        record=report['methods'][name]={'status':'compile_started'};report['stage']='compile-'+name
        report['health'].append(helper.check_device(root,name+'-begin'));print('COMPILE',name,flush=True)
        saved=os.dup(2)
        try:
            with (root/(name+'.stderr.log')).open('w') as log:
                sys.stderr.flush();os.dup2(log.fileno(),2);program=build()
        except Exception:
            record.update(status='compile_failed',error=traceback.format_exc());continue
        finally:
            sys.stderr.flush();os.dup2(saved,2);os.close(saved)
        code=str(program.get_kernel_source());(root/(name+'.cpp')).write_text(code)
        record.update(source_sha256=sha(code.encode()),atomic_marker_present='atomic' in code.lower())
        diagnostic=(root/(name+'.stderr.log')).read_text()
        if 'ThreadSync' in diagnostic:record.update(status='rejected_sync_diagnostic',error=diagnostic);continue
        output=torch.empty(N if name=='encode_keys' else K,dtype=torch.int32,device='npu')
        meta=torch.empty(3,dtype=torch.int32,device='npu')
        args=[x,output] if name=='encode_keys' else [x,starts,ends,threshold,output,meta]
        def invoke():program(*args)
        record['validation']=[]
        for c in cases:
            report['stage']='validate-'+name+'-'+c['name'];cpu=prepare(c)
            want=torch.tensor(c['keys'] if name=='encode_keys' else c['ids'],dtype=torch.int32)
            for repeat in range(3):
                output.fill_(-777);meta.fill_(-777);invoke();torch.npu.synchronize();actual=output.cpu()
                if not torch.equal(actual,want):
                    record.update(status='wrong_result',case=c['name'],repeat=repeat,mismatches=(actual!=want).nonzero()[:20].tolist());raise AssertionError(name+' output mismatch')
                if name!='encode_keys':assert meta.cpu().tolist()==c['meta'],name+' meta mismatch'
                assert torch.equal(x.cpu().view(torch.int32),cpu.view(torch.int32)),'Input bits modified'
                assert starts.cpu().item()==c['start'] and ends.cpu().item()==c['end'] and threshold.cpu().item()==signed(c['threshold']),'Metadata inputs modified'
            record['validation'].append({'case':c['name'],'passed':True,'repeats':3,'output_sha256':sha(actual.numpy().tobytes())})
        print('VALIDATION_PASSED',name,len(cases),'x 3',flush=True);record['status']='correctness_passed';record['inputs_preserved']=True
        cpu=prepare(cases[0])
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
        want=torch.tensor(cases[0]['keys'] if name=='encode_keys' else cases[0]['ids'],dtype=torch.int32)
        assert torch.equal(output.cpu(),want),'Post-timing output mismatch'
        if name!='encode_keys':assert meta.cpu().tolist()==cases[0]['meta'],'Post-timing meta mismatch'
        assert torch.equal(x.cpu().view(torch.int32),cpu.view(torch.int32)),'Post-timing input modified'
        assert starts.cpu().item()==cases[0]['start'] and ends.cpu().item()==cases[0]['end'] and threshold.cpu().item()==signed(cases[0]['threshold']),'Post-timing metadata input modified'
        vals=[v['latency_ms']*1000 for v in record['profiles']]
        if len(vals)==5:record.update(status='correctness_and_timing_complete',timing_us={'samples':vals,'mean':statistics.mean(vals),'stdev':statistics.stdev(vals),'min':min(vals),'max':max(vals)})
        else:record['status']='correctness_passed_timing_unavailable'
    report['health'].append(helper.check_device(root,'final'))
    report['route_feasibility']='unresolved_histogram_and_native_collection_not_verified'
    report['status']='complete' if all(v['status']=='correctness_and_timing_complete' for v in report['methods'].values()) else 'partial'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();root=Path(args.output).resolve();root.mkdir()
    report={'status':'failed','stage':'preflight','protocol':'threshold-fixed-expression-device-cost-v1','limits':[
        'No guessed histogram API is called; source inventory alone does not validate native histogram',
        'CPU supplies exact threshold. Threshold selection is not executed or timed',
        'Collection is an explicit SIMT group-count/prefix/emit expression, not native vector compression',
        'Standalone key output includes a GM key write; do not add its time to fused collection time',
        'Not complete TopK; no full-operator speedup or DT performance prediction']}
    try:execute(root,report)
    except Exception:report['error']=traceback.format_exc();print(report['error'],file=sys.stderr)
    finally:
        report['evidence']={}
        for path in sorted(root.rglob('*')):
            if path.is_file() and (path.suffix in ('.cpp','.log','.txt') or any(s in path.name for s in ('ffts_profile','hash_dic','task_track','stars_soc.data','info.json'))):
                if not path.name.endswith(('.done','.complete')):
                    raw=path.read_bytes();report['evidence'][str(path.relative_to(root))]={'sha256':sha(raw),'base64':base64.b64encode(raw).decode()}
        (root/'primitive-return.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RUN_STATUS',report['status'],'ROUTE_FEASIBILITY',report.get('route_feasibility','not_reached'),flush=True)
    return 0 if report['status']=='complete' else 1


if __name__=='__main__':sys.exit(main())
