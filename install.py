#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, uuid
from pathlib import Path

def detect_project(root: Path):
 source=[p for p in ['src','app','lib','packages','services'] if (root/p).exists()] or ['src']
 tests=[p for p in ['tests','test','__tests__','e2e'] if (root/p).exists()] or ['tests']
 docs=[p for p in ['docs'] if (root/p).exists()] or ['docs']; assets=[p for p in ['public','assets','static'] if (root/p).exists()] or ['public']
 configs=[p for p in ['package.json','pyproject.toml','requirements.txt','go.mod','Cargo.toml','pom.xml','tsconfig.json'] if (root/p).exists()]
 checks=[]
 if (root/'package.json').exists():
  try:
   pkg=json.loads((root/'package.json').read_text());scripts=pkg.get('scripts',{})
   for name in ['test','typecheck','lint','build']:
    if name in scripts: checks.append({'name':name,'command':['npm','run',name],'required':True,'expected_exit_code':0,'timeout_seconds':600,'gates':['comprehensive'] if name=='build' else ['fast','comprehensive']})
  except Exception: pass
 if (root/'pyproject.toml').exists() or (root/'requirements.txt').exists():
  checks.append({'name':'python-compile','command':['python3','-m','compileall','-q',*source],'required':True,'expected_exit_code':0,'timeout_seconds':300,'gates':['fast','comprehensive']})
  if (root/'tests').exists(): checks.append({'name':'pytest','command':['python3','-m','pytest','-q'],'required':True,'expected_exit_code':0,'timeout_seconds':600,'gates':['fast','comprehensive']})
 if not checks: checks=[{'name':'git-diff-check','command':['git','diff','--check'],'required':True,'expected_exit_code':0,'timeout_seconds':60,'gates':['fast','comprehensive']}]
 return source,tests,docs,assets,configs,checks

def copy_if_missing(src,dst,force=False):
 if dst.exists() and not force:return
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('target');ap.add_argument('--force',action='store_true');ap.add_argument('--init-git',action='store_true');a=ap.parse_args();pkg=Path(__file__).resolve().parent;root=Path(a.target).resolve();root.mkdir(parents=True,exist_ok=True)
 created_git=False
 if not (root/'.git').exists():
  if a.init_git:
   subprocess.run(['git','init'],cwd=root,check=True);created_git=True
  else: raise SystemExit('target must be a Git repository; pass --init-git to initialize')
 control=root/'.agentic'
 copy_if_missing(pkg/'system/templates/AGENTS.md',root/'AGENTS.md',a.force)
 for src in (pkg/'system/protocol').glob('*'):copy_if_missing(src,control/'protocol'/src.name,a.force)
 for src in (pkg/'system/scripts').glob('*'):
  if src.is_file(): copy_if_missing(src,control/'scripts'/src.name,a.force)
 for src in (pkg/'system/schemas').glob('*'):
  if src.is_file(): copy_if_missing(src,control/'schemas'/src.name,a.force)
 for name in ['VISION.md','PROJECT-SPEC.md','REQUIREMENTS.json']:
  copy_if_missing(pkg/'system/templates'/name,control/'policy'/name,a.force)
 source,tests,docs,assets,configs,checks=detect_project(root)
 ws=json.loads((pkg/'system/templates/workspace.json').read_text());ws['workspace_id']=root.name+'-'+uuid.uuid4().hex[:8];p=ws['projects'][0];p.update({'source_roots':source,'test_roots':tests,'documentation_roots':docs,'asset_roots':assets,'config_files':configs})
 (control/'config').mkdir(parents=True,exist_ok=True)
 if not (control/'config/workspace.json').exists() or a.force:(control/'config/workspace.json').write_text(json.dumps(ws,indent=2)+'\n')
 val={'schema_version':'3.0','profiles':{'default':{'checks':checks}}}
 if not (control/'config/loop-validation.json').exists() or a.force:(control/'config/loop-validation.json').write_text(json.dumps(val,indent=2)+'\n')
 runtime=control/'runtime';runtime.mkdir(parents=True,exist_ok=True);(runtime/'LOOP-EVENTS.jsonl').touch(exist_ok=True)
 for d in ['evidence','errors','packets','validation-logs','locks']: (runtime/d).mkdir(exist_ok=True)
 (runtime/'.gitignore').write_text('*\n!.gitignore\n',encoding='utf-8')
 for d in ['knowledge/staging','knowledge/releases','knowledge/manifests','skills']: (control/d).mkdir(parents=True,exist_ok=True)
 subprocess.run(['python3',str(control/'scripts/rebuild_projections.py'),'--root',str(root)],check=True)
 (control/'scripts/.gitignore').write_text('__pycache__/\n*.pyc\n',encoding='utf-8')
 cache=control/'scripts/__pycache__'
 if cache.exists(): shutil.rmtree(cache)
 if created_git:
  subprocess.run(['git','config','user.name','Loop Engineering'],cwd=root,check=True)
  subprocess.run(['git','config','user.email','loop-engineering@local'],cwd=root,check=True)
  subprocess.run(['git','add','AGENTS.md','.agentic'],cwd=root,check=True)
  subprocess.run(['git','commit','-m','chore: initialize Loop Engineering v3.0'],cwd=root,check=True)
 else:
  probe=subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if probe.returncode!=0: print('WARNING: repository has no baseline commit; create one before registering a goal')
 print(f'Installed Loop Engineering v3.0 into {root}')
 print('Next: edit .agentic/policy/PROJECT-SPEC.md and REQUIREMENTS.json, then run:')
 print('  python3 .agentic/scripts/agenticctl.py --root . validate')
 return 0
if __name__=='__main__': raise SystemExit(main())
