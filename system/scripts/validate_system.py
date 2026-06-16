#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
import jsonschema
from common import AgenticError, load_json, load_workspace, project_by_id, git, path_matches, is_protected, classify_path, sha256_file
from event_store import load_events
from rebuild_projections import reduce

def validate_json(path,schema): jsonschema.validate(load_json(path),load_json(schema))
def stable(v):
 c=json.loads(json.dumps(v));c.get('projection',{}).pop('generated_at',None);return c

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--skip-project-checks',action='store_true');a=ap.parse_args();root=Path(a.root).resolve()
 try:
  print('GROUP A: control-plane and workspace boundary')
  for p in ['AGENTS.md','.agentic/config/workspace.json','.agentic/policy/VISION.md','.agentic/policy/PROJECT-SPEC.md','.agentic/policy/REQUIREMENTS.json','.agentic/runtime/LOOP-EVENTS.jsonl']:
   if not (root/p).exists(): raise AgenticError(f'missing {p}')
  validate_json(root/'.agentic/config/workspace.json',root/'.agentic/schemas/workspace.schema.json');validate_json(root/'.agentic/policy/REQUIREMENTS.json',root/'.agentic/schemas/requirements.schema.json');ws=load_workspace(root)
  if ws['control_root']!='.agentic': raise AgenticError('v3 embedded profile requires control_root=.agentic')
  for project in ws['projects']:
   if not (root/project['root']).exists(): raise AgenticError(f"project root missing: {project['root']}")
  print('PASS: Group A')
  print('GROUP B: event chain and deterministic projections')
  events=load_events(root/'.agentic/runtime/LOOP-EVENTS.jsonl')
  for event in events: jsonschema.validate(event,load_json(root/'.agentic/schemas/event.schema.json'))
  req=load_json(root/'.agentic/policy/REQUIREMENTS.json');s,v,p=reduce(events,req)
  actual_s=load_json(root/'.agentic/runtime/LOOP-STATE.json');actual_v=load_json(root/'.agentic/runtime/LOOP-VERSIONS.json');actual_p=load_json(root/'.agentic/runtime/PROJECT-STATUS.json')
  if stable(s)!=stable(actual_s) or stable(v)!=stable(actual_v) or p!=actual_p: raise AgenticError('runtime projections are stale or manually edited')
  validate_json(root/'.agentic/runtime/LOOP-STATE.json',root/'.agentic/schemas/state.schema.json');validate_json(root/'.agentic/runtime/LOOP-VERSIONS.json',root/'.agentic/schemas/versions.schema.json');validate_json(root/'.agentic/runtime/PROJECT-STATUS.json',root/'.agentic/schemas/project-status.schema.json')
  print('PASS: Group B')
  print('GROUP C: active-goal scope and candidate integrity')
  active=v.get('active_goal_id')
  if active:
   g=next(x for x in v['versions'] if x['goal_id']==active)
   if g['status']=='VERIFIER_PASS':
    if git(root,'rev-parse','HEAD')!=g['git_sha_after'] or git(root,'rev-parse','HEAD^{tree}')!=g['git_tree_after']:raise AgenticError('HEAD differs from verifier-approved candidate')
   changed=[x for x in git(root,'diff','--name-only',g['git_sha_before'],'HEAD').splitlines() if x]
   for path in changed:
    if is_protected(ws,path): raise AgenticError(f'active candidate changed protected path {path}')
    if any(path_matches(path,d) for d in g['denied_write_paths']): raise AgenticError(f'active candidate changed denied path {path}')
    if not any(path_matches(path,pat) for pat in g['allowed_write_paths']): raise AgenticError(f'active candidate changed out-of-scope path {path}')
    if g['goal_kind']!='SYSTEM_MAINTENANCE' and classify_path(ws,path)['class'] in {'CONTROL_PLANE','RUNTIME_STATE','KNOWLEDGE_GENERATED'}: raise AgenticError(f'project goal changed system path {path}')
  for row in git(root,'status','--porcelain','--untracked-files=all').splitlines():
   path=row[3:].strip().split(' -> ')[-1]
   if classify_path(ws,path)['class']=='PROJECT':raise AgenticError(f'uncommitted project path present: {path}')
  print('PASS: Group C')
  print('GROUP D: project deterministic checks')
  if not a.skip_project_checks:
   cfg=load_json(root/'.agentic/config/loop-validation.json')
   for project in ws['projects']:
    profile=cfg['profiles'][project['validation_profile']]
    cwd=(root/project['command_cwd']).resolve()
    for check in profile['checks']:
     r=subprocess.run(check['command'],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=check.get('timeout_seconds',300),check=False)
     log=root/'.agentic/runtime/validation-logs'/project['project_id'];log.mkdir(parents=True,exist_ok=True);(log/f"{check['name']}.log").write_text(r.stdout or '')
     if r.returncode!=check.get('expected_exit_code',0) and check.get('required',True): raise AgenticError(f"project check {check['name']} failed: exit {r.returncode}")
  print('PASS: Group D')
  print('GROUP E: knowledge graph integrity')
  completed=[x for x in v['versions'] if x['status']=='COMPLETED']
  check_goal=None
  if active:
   ag=next(x for x in v['versions'] if x['goal_id']==active)
   if ag.get('kg_version_after'):check_goal=ag
  elif completed:check_goal=completed[-1]
  if check_goal:
   kg=check_goal['kg_version_after'];manifest=load_json(root/'.agentic/knowledge/manifests'/f'{kg}.json')
   jsonschema.validate(manifest,load_json(root/'.agentic/schemas/kg-manifest.schema.json'))
   if manifest['git_tree']!=check_goal['git_tree_after'] or manifest['status']!='PROMOTED':raise AgenticError('KG does not match verified candidate')
   bundle=root/'.agentic/knowledge/releases'/kg
   for rec in manifest['artifacts'].values():
    if sha256_file(bundle/rec['path'])!=rec['sha256']:raise AgenticError('KG artifact hash mismatch')
  print('PASS: Group E')
  print('GROUP F: project-completion invariant')
  if p['status']=='COMPLETED' and not (p['completion']['ready_for_acceptance'] and p['completion']['user_accepted']): raise AgenticError('project completed without verified mandatory requirements and user acceptance')
  print('PASS: Group F');print('ALL VALIDATIONS PASSED');return 0
 except Exception as exc:
  print(f'VALIDATION FAILED: {exc}',file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
