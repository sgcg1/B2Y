"""Step 2 only: untouched target source, public CPU gate, guarded BMM verification."""
import argparse
import base64
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
HERE=Path(__file__).resolve().parent
SHA='4409536e1f0dba8dca7141d6aee6fc6677afa9ce'
BRANCH='codex/topk-select-ascend950-42'


def main():
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid())
    root=Path('/home/y00937463')/('topk-42-step2-r1-'+stamp);root.mkdir()
    report={'step':2,'status':'failed','source_sha':SHA,'branch':BRANCH,'commands':[],
            'environment':{'python':sys.version,'executable':sys.executable},'next_step_allowed':False}
    def command(args,label,cwd=None,env=None):
        with (root/(label+'.log')).open('w') as log:
            r=subprocess.run(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        report['commands'].append({'label':label,'argv':args,'exit_code':r.returncode})
        return r.returncode
    try:
        identity=json.loads((HERE/'identity.json').read_text())
        for name,digest in identity.items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
        report['identity']=identity
        for package in ('torch','torch-npu','tilelang','tileops','pytest','PyYAML'):
            try:report['environment'][package]=importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:report['environment'][package]='not_installed'
        bundle=root/'target.bundle'
        bundle.write_bytes(b''.join(f.read_bytes() for f in sorted(HERE.glob('target.bundle.part*'))))
        assert hashlib.sha256(bundle.read_bytes()).hexdigest()=='b4654cc0350f995ba401992373434c011ae207d2dc8ee439534ad0176d8625c8'
        source=root/'TileOPs'
        assert command(['git','clone','--branch',BRANCH,str(bundle),str(source)],'clone')==0
        actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip();assert actual==SHA
        # Keep the delivery target explicit; never push to the target repository here.
        assert command(['git','remote','set-url','origin','https://github.com/sgcg1/TileOPs.git'],'remote',source)==0
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TORCH_DEVICE_BACKEND_AUTOLOAD='0')
        if command([sys.executable,'scripts/ci/ascend950.py','--phase','cpu','--output',str(root/'cpu')],'cpu',source,env):
            report['status']='blocked_cpu_check_failed';return 1
        cpu=json.loads((root/'cpu/receipt.json').read_text());assert cpu['status']=='passed'
        report['cpu_receipt']=cpu
        guard=Path(os.environ.get('TILEOPS_NPU_GUARD','/usr/local/libexec/ascend-npu/npu_guard.py'))
        mounts=Path('/proc/self/mountinfo').read_text();(root/'mountinfo.txt').write_text(mounts)
        # Fail closed: an ordinary directory/private flock is not host reservation evidence.
        shared_mount=any(len(line.split())>4 and line.split()[4]=='/run/lock/ascend-npu' for line in mounts.splitlines())
        report['guard_preflight']={'path':str(guard),'exists':guard.is_file(),'shared_lock_mount_present':shared_mount,
            'note':'Mount presence is necessary here, not proof of canonical site certification; guard still validates ownership/processes.'}
        if not guard.is_file() or not shared_mount:
            report['status']='blocked_host_guard_not_available';return 1
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('TORCH_DEVICE_BACKEND_AUTOLOAD',None)
        args=[sys.executable,'scripts/benchmark_ascend.py','--owner','JotaroSSR/topk-step2-'+stamp,
              '--run-dir',str(root/'bmm'),'--guard',str(guard),'--op','BmmFwdOp','--verify-only']
        rc=command(args,'bmm',source,env)
        if (root/'bmm/receipt.json').exists():report['bmm_receipt']=json.loads((root/'bmm/receipt.json').read_text())
        report['status']='cpu_and_bmm_passed_environment_acceptance_pending' if rc==0 and report.get('bmm_receipt',{}).get('status')=='passed' else 'blocked_bmm_verification_failed'
        # PR/CANN9.3 remains a development environment, not the maintainer canonical lock.
        return 0 if report['status']=='cpu_and_bmm_passed_environment_acceptance_pending' else 1
    except Exception:
        report['error']=traceback.format_exc();return 1
    finally:
        report['evidence']={}
        for path in sorted(root.rglob('*')):
            if path.is_file() and source_not_code(path,root) and path.suffix in ('.log','.json','.xml','.txt'):
                raw=path.read_bytes();report['evidence'][str(path.relative_to(root))]={'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
        output=HERE.parents[1]/'AAA_Results'/('topk-42-step2-r1-'+stamp+'.json');output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('STATUS',report['status']);print('UPLOAD_RESULT',output);print('RAW_DIRECTORY',root)
        subprocess.run([sys.executable,str(HERE/'pack.py'),str(output)],check=False)


def source_not_code(path,root):return path.relative_to(root).parts[0]!='TileOPs'


if __name__=='__main__':sys.exit(main())
