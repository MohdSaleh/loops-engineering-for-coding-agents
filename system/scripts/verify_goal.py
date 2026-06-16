#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, operator, re, subprocess
from pathlib import Path
from common import load_json, load_workspace, project_by_id, git
from event_store import append_event
from rebuild_projections import rebuild

OPS={'>=':operator.ge,'<=':operator.le,'==':operator.eq,'>':operator.gt,'<':operator.lt}
def hash_file(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--goal-id',required=True);ap.add_argument('--type-d-approvals');a=ap.parse_args();root=Path(a.root).resolve();runtime=root/'.agentic/runtime';versions=load_json(runtime/'LOOP-VERSIONS.json');state=load_json(runtime/'LOOP-STATE.json');g=next(x for x in versions['versions'] if x['goal_id']==a.goal_id);ws=load_workspace(root);project=project_by_id(ws,g['project_id']);cwd=(root/project['command_cwd']).resolve();run=state['run_id'] or 'manual'
 scope=subprocess.run(['python3',str(root/'.agentic/scripts/verify_scope.py'),'--root',str(root),'--goal-id',a.goal_id],check=False)
 if scope.returncode:return scope.returncode
 approvals=load_json(Path(a.type_d_approvals)) if a.type_d_approvals else {};results=[];refs=[];all_pass=True;evdir=runtime/'evidence'/a.goal_id;evdir.mkdir(parents=True,exist_ok=True)
 for c in g['checklist']:
  typ=c['type'];passed=False;detail='';output=''
  if typ=='A':
   r=subprocess.run(c['command'],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False);output=r.stdout or '';passed=r.returncode==c['expected_exit_code'];detail=f'exit={r.returncode}, expected={c["expected_exit_code"]}'
  elif typ=='B':
   path=(cwd/c['path']).resolve();expected=c['expected_state'];actual='exists' if path.exists() else 'absent'
   if isinstance(expected,str):passed=actual==expected
   elif isinstance(expected,dict) and 'sha256' in expected:passed=path.is_file() and hash_file(path)==expected['sha256']
   detail=f'actual={actual}, expected={expected}'
  elif typ=='C':
   r=subprocess.run(c['command'],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False);output=r.stdout or '';m=re.search(c['metric_regex'],output);value=float(m.group(1)) if m else None;passed=r.returncode==0 and value is not None and OPS[c['operator']](value,float(c['threshold']));detail=f'value={value}, condition={c["operator"]}{c["threshold"]}'
  else:
   record=approvals.get(c['condition_id'],{});passed=record.get('passed') is True;detail=record.get('evidence','missing independent Type D approval')
  log=evdir/f"{c['condition_id']}.log";log.write_text(detail+'\n'+output,encoding='utf-8');refs.append({'path':str(log.relative_to(root)),'sha256':hash_file(log)});results.append({'condition_id':c['condition_id'],'status':'PASS' if passed else 'FAIL','detail':detail});all_pass=all_pass and passed
 sha=git(root,'rev-parse','HEAD');tree=git(root,'rev-parse','HEAD^{tree}');typ='VERIFICATION_PASSED' if all_pass else 'VERIFICATION_FAILED';append_event(root,run_id=run,type=typ,actor='verifier',payload={'results':results},goal_id=a.goal_id,project_id=g['project_id'],git_sha=sha,git_tree=tree,evidence_refs=refs);rebuild(root);print(json.dumps(results,indent=2));return 0 if all_pass else 1
if __name__=='__main__':raise SystemExit(main())
