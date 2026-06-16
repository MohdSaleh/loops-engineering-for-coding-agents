#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from common import load_json, load_workspace, project_by_id
from event_store import append_event
from rebuild_projections import rebuild

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--goal-id',required=True);a=ap.parse_args();root=Path(a.root).resolve();runtime=root/'.agentic/runtime';state=load_json(runtime/'LOOP-STATE.json');versions=load_json(runtime/'LOOP-VERSIONS.json');g=next(x for x in versions['versions'] if x['goal_id']==a.goal_id)
    if g['status']!='VERIFIER_PASS':raise SystemExit('stop gate requires VERIFIER_PASS')
    ws=load_workspace(root);project=project_by_id(ws,g['project_id']);cfg=load_json(root/'.agentic/config/loop-validation.json');profile=cfg['profiles'][project['validation_profile']];cwd=(root/project['command_cwd']).resolve();logs=runtime/'validation-logs'/project['project_id'];logs.mkdir(parents=True,exist_ok=True);results=[];passed=True;refs=[]
    for check in profile['checks']:
        gates=check.get('gates',['fast','comprehensive'])
        if 'fast' not in gates:continue
        r=subprocess.run(check['command'],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=min(int(check.get('timeout_seconds',60)),60),check=False);output=r.stdout or '';log=logs/f"stop-{check['name']}.log";log.write_text(output,encoding='utf-8');refs.append({'path':str(log.relative_to(root)),'sha256':hashlib.sha256(log.read_bytes()).hexdigest()});ok=r.returncode==check.get('expected_exit_code',0);results.append({'name':check['name'],'exit_code':r.returncode,'passed':ok});passed=passed and (ok or not check.get('required',True))
    append_event(root,run_id=state['run_id'] or 'manual',type='STOP_GATE_RECORDED',actor='validator',payload={'passed':passed,'checks':results},goal_id=a.goal_id,project_id=g['project_id'],git_sha=g['git_sha_after'],git_tree=g['git_tree_after'],evidence_refs=refs);rebuild(root);print(json.dumps(results,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
