"""Offline integration test: local bare Git remote, no GitCode/network access."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('one_upload',Path(__file__).with_name('upload.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class UploadTest(unittest.TestCase):
    def test_serial_push_and_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'work';root.mkdir();remote=Path(temp)/'remote.git'
            def run(*args,cwd=root):
                return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.STDOUT,text=True).strip()
            run('init','--bare',str(remote));run('init','-b','main')
            run('config','user.name','Offline Test');run('config','user.email','offline@example.invalid')
            (root/'README').write_text('seed');run('add','README');run('commit','-m','seed')
            run('remote','add','origin',str(remote));run('push','-u','origin','main')
            folder=root/'AAA_Results';folder.mkdir()
            for i in (1,2,3):
                chunk=folder/('report%d-part-0001.txt'%i);chunk.write_bytes(b'YWJj')
                manifest=folder/('report%d-parts-manifest.json'%i)
                manifest.write_text(json.dumps({'files':[{'parts':[{'name':chunk.name,'bytes':4,'sha256':hashlib.sha256(b'YWJj').hexdigest()}]}]}))
                log=folder/('topk-step6-compare-console-20261105T12000%dZ-123-r%d.log'%(i,i))
                log.write_text('UPLOAD_MANIFEST /home/user/B2Y/AAA_Results/'+manifest.name+'\n')
                os.utime(log,(i,i))
            self.assertEqual(len(module.select_files(root)),9)
            original_git=module.git
            def local_git(*args,**kwargs):
                if args==('remote','get-url','origin'):return 'https://gitcode.com/JotaroSSR/B2Y.git'
                return original_git(*args,**kwargs)
            with patch.object(module,'ROOT',root),patch.object(module,'git',local_git),patch.object(sys,'argv',['upload.py','--upload']):
                # First failure leaves exactly one committed file; resume must push it first.
                fired=[False]
                def interrupted(*args,**kwargs):
                    if 'push' in args and not fired[0]:
                        fired[0]=True;raise RuntimeError('Simulated transport disconnect')
                    return local_git(*args,**kwargs)
                with patch.object(module,'git',interrupted):
                    with self.assertRaises(RuntimeError):module.main()
                module.main()
                commits=run('rev-list','--reverse','HEAD').splitlines()
                self.assertEqual(len(commits),10)
                for commit in commits[1:]:
                    self.assertEqual(len(run('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()),1)
                self.assertEqual(run('rev-parse','HEAD'),run('rev-parse','main',cwd=remote))
                module.main();self.assertEqual(len(run('rev-list','HEAD').splitlines()),10)


if __name__=='__main__':unittest.main()
