"""Read-only backend evidence. Names/snippets are clues, never performance proof."""
import hashlib
import inspect
from pathlib import Path
import re


def collect(T,tilelang):
    keywords=('hist','sort','merge','scan','cumsum','prefix','compress','gather','shuffle','ballot','popc','reduce','fragment','simdvf','simtvf')
    exported={}
    for name in dir(T):
        if name.startswith('_') or not any(word in name.lower() for word in keywords):continue
        obj=getattr(T,name)
        try:signature=str(inspect.signature(obj)) if callable(obj) else type(obj).__name__
        except Exception:signature='unavailable'
        exported[name]={'signature':signature,'doc':(inspect.getdoc(obj) or '')[:400]}
    package=Path(tilelang.__file__).resolve().parent
    roots=[package/'ascend',package/'language',package/'src/ascend',package/'src/op',
           package/'src/tl_templates/ascend',Path('/home/y00937463/tilelang/src/ascend'),Path('/home/y00937463/tilelang/src/op')]
    pattern=re.compile(r'Histograms|\bvhist\b|\bhistogram\b|\bhistograms\b|compress|gather_mask|sort32|merge_sort',re.I)
    matches=[];seen=set();scanned=0;bytes_read=0;truncated=False
    for root in roots:
        if not root.exists():continue
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix not in ('.py','.cc','.cpp','.h','.hpp'):continue
            absolute=str(path.resolve())
            if absolute in seen:continue
            seen.add(absolute)
            if scanned>=1200 or bytes_read>32*1024*1024:truncated=True;break
            if path.stat().st_size>2*1024*1024:continue
            raw=path.read_bytes();scanned+=1;bytes_read+=len(raw)
            hits=[{'line':i+1,'text':line[:300]} for i,line in enumerate(raw.decode('utf-8',errors='replace').splitlines()) if pattern.search(line)]
            if hits and len(matches)<100:matches.append({'path':absolute,'sha256':hashlib.sha256(raw).hexdigest(),'hits':hits[:12],'hits_truncated':len(hits)>12})
            elif hits:truncated=True
    return {'exports':exported,'roots':[{'path':str(p),'exists':p.exists()} for p in roots],
            'source_files_scanned':scanned,'bytes_read':bytes_read,'matches':matches,'truncated':truncated,
            'histogram_device_test':'not_exercised_no_verified_callable_signature',
            'interpretation':'Discovery evidence only. Absence from names is not proof of hardware incapability; no unverified function was invoked.'}
