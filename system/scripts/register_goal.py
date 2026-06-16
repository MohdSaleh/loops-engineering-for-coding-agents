#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, uuid
from pathlib import Path
import jsonschema
from common import load_json, load_workspace, project_by_id, path_matches, git
from event_store import append_event
from rebuild_projections import rebuild

def emit(root, run, typ, actor, payload, **ids):
 return append_event(root,run_id=run,type=typ,actor=actor,payload=payload,**ids)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--goal-file',required=True);ap.add_argument('--run-id');a=ap.parse_args();root=Path(a.root).resolve();goal=load_json(Path(a.goal_file));jsonschema.validate(goal,load_json(root/'.agentic/schemas/goal.schema.json'));ws=load_workspace(root);project_by_id(ws,goal['project_id'])
 if goal['status']!='READY': raise SystemExit('only READY goal contracts may be registered')
 versions=load_json(root/'.agentic/runtime/LOOP-VERSIONS.json');prior=versions['versions'][-1] if versions['versions'] else None
 if prior and prior['status'] in {'IN_PROGRESS','VERIFIER_PASS','ESCALATED'}: raise SystemExit(f"prior goal {prior['goal_id']} is {prior['status']} and blocks a new goal")
 if goal['goal_kind']=='SYSTEM_MAINTENANCE' and not goal['system_change_authorized']: raise SystemExit('SYSTEM_MAINTENANCE requires system_change_authorized=true')
 if goal['goal_kind']!='SYSTEM_MAINTENANCE' and goal['system_change_authorized']: raise SystemExit('ordinary project goals cannot authorize system changes')
 for pat in goal['allowed_write_paths']+goal['denied_write_paths']:
  if Path(pat).is_absolute() or '..' in Path(pat).parts: raise SystemExit(f'path patterns must be relative and non-traversing: {pat}')
 if goal['goal_kind']!='SYSTEM_MAINTENANCE':
  for pat in goal['allowed_write_paths']:
   if pat=='**' or pat=='AGENTS.md' or pat.startswith('.agentic'): raise SystemExit(f'project goal has unsafe allowed path {pat}')
 for pat in goal['allowed_write_paths']:
  if any(path_matches(pat,x) or path_matches(x,pat) for x in ws['protected_paths']): raise SystemExit(f'allowed path overlaps protected path: {pat}')
 req=load_json(root/'.agentic/policy/REQUIREMENTS.json');known={r['requirement_id'] for r in req['requirements']};missing=set(goal['requirements_affected'])-known
 if missing: raise SystemExit(f'unknown requirements: {sorted(missing)}')
 vision=(root/'.agentic/policy/VISION.md').read_text();
 for c in goal['completion_conditions']:
  typ=c['type']
  if typ=='A' and (not c.get('command') or 'expected_exit_code' not in c): raise SystemExit(f"TYPE A requires command and expected_exit_code: {c['condition_id']}")
  if typ=='B' and (not c.get('path') or 'expected_state' not in c): raise SystemExit(f"TYPE B requires path and expected_state: {c['condition_id']}")
  if typ=='C' and (not c.get('command') or not c.get('metric_regex') or c.get('operator') is None or c.get('threshold') is None): raise SystemExit(f"TYPE C requires command, metric_regex, operator, and threshold: {c['condition_id']}")
  if typ=='D' and c['description'] not in vision: raise SystemExit(f"TYPE D criterion is not pre-approved verbatim: {c['description']}")
 seq=versions.get('sequence_counter',0)+1;gid=f'G{seq:03d}';run=a.run_id or str(uuid.uuid4());sha=git(root,'rev-parse','HEAD');tree=git(root,'rev-parse','HEAD^{tree}');vision_hash=hashlib.sha256(vision.encode()).hexdigest()
 state=load_json(root/'.agentic/runtime/LOOP-STATE.json')
 if state['vision'].get('accepted_hash') not in (None,vision_hash): raise SystemExit('VISION changed since accepted goal; resolve before creating a new goal')
 emit(root,run,'RUN_BOOTED','orchestrator',{'trigger':{'type':'TRIGGER-GOAL','source':'user_prompt'}})
 emit(root,run,'VISION_OBSERVED','orchestrator',{'sha256':vision_hash})
 if state['vision'].get('accepted_hash') is None: emit(root,run,'VISION_ACCEPTED','orchestrator',{'sha256':vision_hash,'goal_checklist':goal['completion_conditions']})
 emit(root,run,'USER_PROMPT_RECEIVED','human',{'goal_raw':goal['goal_raw']},prompt_id=goal['prompt_id'],project_id=goal['project_id'])
 payload={**goal,'git_sha_before':sha,'git_tree_before':tree,'parent_goal_id':prior['goal_id'] if prior else None,'vision_hash_at_start':vision_hash}
 emit(root,run,'GOAL_CREATED','orchestrator',payload,goal_id=gid,prompt_id=goal['prompt_id'],project_id=goal['project_id'],git_sha=sha,git_tree=tree)
 rebuild(root);print(gid)
if __name__=='__main__': raise SystemExit(main())
