#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
PKG=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/'repo';root.mkdir();subprocess.run(['git','init'],cwd=root,check=True,stdout=subprocess.DEVNULL);subprocess.run(['git','config','user.email','test@example.com'],cwd=root,check=True);subprocess.run(['git','config','user.name','Test'],cwd=root,check=True);(root/'src').mkdir();(root/'src/a.txt').write_text('a\n');(root/'tests').mkdir();subprocess.run(['git','add','.'],cwd=root,check=True);subprocess.run(['git','commit','-m','base'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 subprocess.run([sys.executable,str(PKG/'install.py'),str(root)],check=True);subprocess.run(['git','add','.'],cwd=root,check=True);subprocess.run(['git','commit','-m','install'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 req=json.loads((root/'.agentic/policy/REQUIREMENTS.json').read_text());req['requirements'][0]['acceptance_conditions']=[{'type':'B','description':'src/b.txt exists'}];(root/'.agentic/policy/REQUIREMENTS.json').write_text(json.dumps(req,indent=2)+'\n')
 subprocess.run(['git','add','.agentic/policy/REQUIREMENTS.json'],cwd=root,check=True);subprocess.run(['git','commit','-m','requirements'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 g=json.loads((PKG/'examples/goal.project-task.json').read_text());g['allowed_write_paths']=['src/**','tests/**'];gp=Path(td)/'goal.json';gp.write_text(json.dumps(g))
 r=subprocess.run([sys.executable,str(root/'.agentic/scripts/agenticctl.py'),'--root',str(root),'register-goal','--goal-file',str(gp)],text=True,capture_output=True);assert r.returncode==0,r.stdout+r.stderr
 versions=json.loads((root/'.agentic/runtime/LOOP-VERSIONS.json').read_text());assert versions['active_goal_id']=='G001'
 (root/'src/b.txt').write_text('b\n');subprocess.run(['git','add','src/b.txt'],cwd=root,check=True);subprocess.run(['git','commit','-m','candidate'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 r=subprocess.run([sys.executable,str(root/'.agentic/scripts/agenticctl.py'),'--root',str(root),'verify-scope','--goal-id','G001'],text=True,capture_output=True);assert r.returncode==0,r.stdout+r.stderr
 # System path mutation must fail scope
 (root/'.agentic/policy/VISION.md').write_text('tampered\n');subprocess.run(['git','add','.agentic/policy/VISION.md'],cwd=root,check=True);subprocess.run(['git','commit','-m','bad'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 r=subprocess.run([sys.executable,str(root/'.agentic/scripts/agenticctl.py'),'--root',str(root),'verify-scope','--goal-id','G001'],text=True,capture_output=True);assert r.returncode!=0
 print('PASS: project goal scope blocks control-plane mutation')
