#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
PKG=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/'repo';root.mkdir();subprocess.run(['git','init'],cwd=root,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','config','user.email','test@example.com'],cwd=root,check=True);subprocess.run(['git','config','user.name','Test'],cwd=root,check=True)
 (root/'src').mkdir();(root/'src/main.py').write_text('print("ok")\n');(root/'tests').mkdir();(root/'README.md').write_text('x\n');subprocess.run(['git','add','.'],cwd=root,check=True);subprocess.run(['git','commit','-m','base'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 subprocess.run([sys.executable,str(PKG/'install.py'),str(root)],check=True)
 subprocess.run(['git','add','.'],cwd=root,check=True);subprocess.run(['git','commit','-m','install'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 r=subprocess.run([sys.executable,str(root/'.agentic/scripts/agenticctl.py'),'--root',str(root),'validate','--skip-project-checks'],text=True,capture_output=True)
 assert r.returncode==0,r.stdout+r.stderr
 ws=json.loads((root/'.agentic/config/workspace.json').read_text());assert ws['control_root']=='.agentic';assert ws['projects'][0]['root']=='.'
 print('PASS: install and workspace boundary')
