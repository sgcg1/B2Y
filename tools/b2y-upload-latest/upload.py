"""Plan the latest result batch; optionally commit and push exactly one file at a time."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]


def git(*args, capture=True):
    result=subprocess.run(['git',*args],cwd=ROOT,text=True,
        stdout=subprocess.PIPE if capture else None,stderr=subprocess.PIPE if capture else None,timeout=180)
    if result.returncode:
        raise RuntimeError('Git command failed: '+args[0]+'\n'+(result.stderr or 'See terminal output'))
    return result.stdout.strip() if capture else ''


def select_files(root):
    folder=(root/'AAA_Results').resolve()
    logs=list(folder.glob('*.log'))
    if not logs:raise ValueError('No result logs in AAA_Results')
    latest=max(logs,key=lambda f:(f.stat().st_mtime_ns,f.name))
    match=re.fullmatch(r'(topk-step6-compare-console)-[0-9TZ]+-(\d+)-r[123]\.log',latest.name)
    if match:
        logs=sorted(folder.glob(match[1]+'-*-'+match[2]+'-r[123].log'))
        if len(logs)!=3:raise ValueError('Latest step6 batch has not finished all three process logs; wait until the test ends')
    else:logs=[latest]
    selected=set(logs)
    for log in logs:
        refs=re.findall(r'^UPLOAD_(?:RESULT|MANIFEST|PART):?\s+(.+?)\s*$',log.read_text(encoding='utf-8',errors='replace'),re.M)
        paths=[]
        for name in refs:
            path=folder/Path(name).name
            if path.parent.resolve()!=folder or not path.is_file():raise ValueError('Missing result file: '+path.name)
            paths.append(path)
        # Manifest+all shards are sufficient; avoid redundant potentially oversized raw JSON.
        manifests=[f for f in paths if f.name.endswith('-manifest.json')]
        if manifests:
            for manifest in manifests:
                data=json.loads(manifest.read_text(encoding='utf-8'))
                for entry in data['files']:
                    for part in entry['parts']:
                        if Path(part['name']).name!=part['name']:raise ValueError('Invalid shard name')
                        path=folder/part['name'];raw=path.read_bytes()
                        if len(raw)!=part['bytes'] or hashlib.sha256(raw).hexdigest()!=part['sha256']:raise ValueError('Shard checksum failed: '+path.name)
                        selected.add(path)
                selected.add(manifest)
        else:
            selected.update(f for f in paths if f.suffix=='.json')
    files=sorted(selected,key=lambda f:(f.suffix=='.log',f.name))
    if len(files)==len(logs):raise ValueError('Latest logs contain no result references; refusing to guess a batch')
    for f in files:
        if f.stat().st_size>9*1024*1024:raise ValueError('File exceeds conservative GitCode limit; split it first: '+f.name)
    return [f.relative_to(root.resolve()).as_posix() for f in files]


def synchronize(selected):
    git('fetch','origin','main',capture=False)
    remote=git('rev-parse','origin/main');head=git('rev-parse','HEAD')
    if remote==head:return
    ahead=git('rev-list','--reverse','origin/main..HEAD').splitlines()
    if ahead:
        # Resume only the single-file commit produced by this tool after a failed push.
        if len(ahead)!=1 or not git('log','-1','--format=%s').startswith('b2y-result-one: '):
            raise ValueError('Local branch contains other unpublished commits; upload script will not push them')
        changed=git('diff-tree','--no-commit-id','--name-only','-r',head).splitlines()
        if len(changed)!=1 or changed[0] not in selected:raise ValueError('Pending commit is outside this result batch')
        status=subprocess.run(['git','merge-base','--is-ancestor',remote,head],cwd=ROOT)
        if status.returncode:raise ValueError('Remote advanced while a local result commit is pending; resolve divergence before resuming; no force push')
        git('-c','http.version=HTTP/1.1','push','origin','HEAD:main',capture=False)
        git('fetch','origin','main',capture=False)
    git('merge','--ff-only','origin/main',capture=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upload',action='store_true',help='Without this flag only print the batch; no git changes/network')
    args=parser.parse_args()
    files=select_files(ROOT)
    print('LATEST_BATCH_FILES',len(files),flush=True)
    for f in files:print(f,flush=True)
    if not args.upload:
        print('Plan only. Add --upload after the test has finished to send these files one at a time.');return 0
    if git('branch','--show-current')!='main':raise ValueError('B2Y checkout must be on main')
    if git('diff','--cached','--name-only'):raise ValueError('Index contains staged changes; preserve/finish them first')
    url=git('remote','get-url','origin')
    parsed=urlsplit(url)
    https=parsed.scheme=='https' and parsed.hostname=='github.com' and parsed.path.rstrip('/').removesuffix('.git')=='/sgcg1/B2Y' and not parsed.username and not parsed.password
    ssh=url in ('git@github.com:sgcg1/B2Y.git','git@github.com:sgcg1/B2Y')
    if not (https or ssh):raise ValueError('Expected sgcg1/B2Y GitHub remote, without an embedded token')
    synchronize(files)
    for index,name in enumerate(files,1):
        synchronize(files)
        if not git('status','--porcelain','--',name):
            print('ALREADY_UPLOADED',name,flush=True);continue
        git('add','--',name)
        if git('diff','--cached','--name-only').splitlines()!=[name]:raise ValueError('Index is not restricted to the current file; stopped')
        git('-c','user.name=JotaroSSR','-c','user.email=1224862686@qq.com','commit','-m','b2y-result-one: '+name,capture=False)
        print('PUSH_ONE',index,'/',len(files),name,flush=True)
        git('-c','http.version=HTTP/1.1','push','origin','HEAD:main',capture=False)
        git('fetch','origin','main',capture=False)
        if git('rev-parse','HEAD')!=git('rev-parse','origin/main'):raise ValueError('Remote changed unexpectedly; stopped before next file')
    print('BATCH_UPLOAD_COMPLETE',flush=True);return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,RuntimeError,subprocess.TimeoutExpired,OSError) as exc:
        print('STOPPED:',exc,file=sys.stderr);sys.exit(1)
