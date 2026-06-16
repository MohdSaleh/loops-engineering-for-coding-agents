#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from event_store import load_events
from common import SCHEMA_VERSION, load_json, write_json

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def empty_state():
 return {'schema_version':SCHEMA_VERSION,'projection':{'last_event_seq':0,'last_event_hash':None,'generated_at':now()},'run_id':None,'status':'IDLE','trigger':None,'vision':{'accepted_hash':None,'observed_hash':None,'changed':False},'current_goal_id':None,'current_task_id':None,'goal_checklist':[],'attempts':{},'budget':{'limits':{'turns':25,'tokens_run':200000,'tokens_task':65000,'sub_agents':3},'used':{'turns':0,'tokens_run':0,'tokens_by_task':{},'active_sub_agents':0}},'warnings':[],'waiting_for_human':[],'summary':''}
def empty_versions(): return {'schema_version':SCHEMA_VERSION,'projection':{},'sequence_counter':0,'active_goal_id':None,'versions':[]}
def goal(v,gid):
 for g in v['versions']:
  if g['goal_id']==gid:return g
 raise RuntimeError(f'unknown goal {gid}')
def reduce(events, requirements):
 s=empty_state(); v=empty_versions(); req={r['requirement_id']:dict(r) for r in requirements['requirements']}; project_complete=False
 for e in events:
  t=e['type']; p=e.get('payload',{}); gid=e.get('goal_id')
  if t=='RUN_BOOTED': s['run_id']=e['run_id'];s['status']='IN_PROGRESS';s['trigger']=p.get('trigger')
  elif t=='VISION_OBSERVED': s['vision']['observed_hash']=p.get('sha256');s['vision']['changed']=s['vision']['accepted_hash'] not in (None,p.get('sha256'))
  elif t=='VISION_ACCEPTED': s['vision']['accepted_hash']=p.get('sha256');s['vision']['changed']=False;s['goal_checklist']=p.get('goal_checklist',[])
  elif t=='GOAL_CREATED':
   project_complete=False
   prior=v['versions'][-1] if v['versions'] else None
   if prior and prior['status'] in {'IN_PROGRESS','VERIFIER_PASS','ESCALATED'}: raise RuntimeError(f"prior goal {prior['goal_id']} blocks new goal")
   g={'goal_id':gid,'prompt_id':e.get('prompt_id'),'project_id':e.get('project_id'),'goal_kind':p['goal_kind'],'parent_goal_id':p.get('parent_goal_id'),'status':'IN_PROGRESS','goal_raw':p['goal_raw'],'requirements_affected':p.get('requirements_affected',[]),'allowed_write_paths':p['allowed_write_paths'],'denied_write_paths':p.get('denied_write_paths',[]),'checklist':p['completion_conditions'],'git_sha_before':p['git_sha_before'],'git_tree_before':p['git_tree_before'],'git_sha_after':None,'git_tree_after':None,'kg_version_before':p.get('kg_version_before'),'kg_version_after':None,'stop_gate_passed':False,'files_changed':[],'started_at':e['timestamp'],'completed_at':None,'goal_outcome':None,'escalation':None}
   v['versions'].append(g);v['sequence_counter']=max(v['sequence_counter'],int(gid[1:4]));v['active_goal_id']=gid;s['current_goal_id']=gid;s['status']='IN_PROGRESS'
   for rid in g['requirements_affected']:
    if rid in req and req[rid]['status']=='OPEN': req[rid]['status']='IN_PROGRESS'; req[rid]['goal_ids']=sorted(set(req[rid].get('goal_ids',[])+[gid]))
  elif t=='TASK_STARTED': s['current_task_id']=e.get('task_id');s['attempts'].setdefault(e.get('task_id'),{'count':0,'tokens_used':0,'last_result':None})
  elif t=='MAKER_ATTEMPT_FINISHED':
   r=s['attempts'].setdefault(e.get('task_id'),{'count':0,'tokens_used':0,'last_result':None});r['count']+=1;r['tokens_used']+=int(p.get('token_cost',0));r['last_result']=p.get('result');g=goal(v,gid);g['files_changed']=sorted(set(g['files_changed'])|set(p.get('files_changed',[])))
  elif t=='VERIFICATION_PASSED': g=goal(v,gid);g['status']='VERIFIER_PASS';g['git_sha_after']=e['git_sha'];g['git_tree_after']=e['git_tree'];s['status']='VERIFYING'
  elif t=='VERIFICATION_FAILED': goal(v,gid)['status']='IN_PROGRESS';s['status']='IN_PROGRESS'
  elif t=='STOP_GATE_RECORDED':
   g=goal(v,gid);g['stop_gate_passed']=bool(p.get('passed'));s['status']='FINALIZING' if g['stop_gate_passed'] else 'IN_PROGRESS'
  elif t=='KG_PROMOTED': g=goal(v,gid);g['kg_version_after']=p['kg_version']
  elif t=='GOAL_COMPLETED':
   g=goal(v,gid)
   if g['status']!='VERIFIER_PASS' or not g['stop_gate_passed'] or not g['kg_version_after']: raise RuntimeError('completion requires verifier pass, stop gate, and promoted KG')
   g['status']='COMPLETED';g['completed_at']=e['timestamp'];g['goal_outcome']=p.get('goal_outcome');v['active_goal_id']=None;s['current_goal_id']=None;s['current_task_id']=None;s['status']='COMPLETED';s['summary']=g['goal_outcome'] or ''
   for rid in g['requirements_affected']:
    if rid in req: req[rid]['status']='VERIFIED'; req[rid]['evidence_refs']=p.get('requirement_evidence',[])
  elif t=='GOAL_ESCALATED': g=goal(v,gid);g['status']='ESCALATED';g['kg_version_after']=None;g['escalation']=p;v['active_goal_id']=gid;s['status']='ESCALATED';s['waiting_for_human'].append(p)
  elif t=='HUMAN_RESOLUTION_RECORDED':
   g=goal(v,gid);resolution=p.get('resolution');s['waiting_for_human']=[]
   if resolution=='RESUME': g['status']='IN_PROGRESS';g['escalation']=None;v['active_goal_id']=gid;s['current_goal_id']=gid;s['status']='IN_PROGRESS'
   elif resolution=='ABANDON': g['status']='ABANDONED';g['completed_at']=e['timestamp'];g['goal_outcome']=p.get('reason');g['escalation']=None;v['active_goal_id']=None;s['current_goal_id']=None;s['status']='ABANDONED'
   else: raise RuntimeError('human resolution must be RESUME or ABANDON')
  elif t=='GOAL_ABANDONED': g=goal(v,gid);g['status']='ABANDONED';g['completed_at']=e['timestamp'];v['active_goal_id']=None;s['current_goal_id']=None;s['status']='ABANDONED'
  elif t=='WARNING_RECORDED': s['warnings'].append({'timestamp':e['timestamp'],**p})
  elif t=='PROJECT_COMPLETED': project_complete=True
  elif t in {'USER_PROMPT_RECEIVED','KG_STAGE_CREATED','KG_STAGE_VALIDATED'}: pass
  else: raise RuntimeError(f'unsupported event type {t}')
  s['projection']={'last_event_seq':e['seq'],'last_event_hash':e['event_hash'],'generated_at':now()};v['projection']=dict(s['projection'])
 mandatory=[r for r in req.values() if r['priority']=='MUST']
 ready=bool(mandatory) and all(r['status']=='VERIFIED' for r in mandatory)
 pstatus={'schema_version':SCHEMA_VERSION,'project_id':requirements['project_id'],'status':'COMPLETED' if project_complete else ('READY_FOR_ACCEPTANCE' if ready else ('IN_PROGRESS' if events else 'NOT_STARTED')),'requirements':list(req.values()),'completion':{'mandatory_total':len(mandatory),'mandatory_verified':sum(r['status']=='VERIFIED' for r in mandatory),'ready_for_acceptance':ready,'user_accepted':project_complete}}
 return s,v,pstatus


def rebuild(root: Path):
 runtime=root/'.agentic/runtime';events=load_events(runtime/'LOOP-EVENTS.jsonl');requirements=load_json(root/'.agentic/policy/REQUIREMENTS.json');state,versions,project_status=reduce(events,requirements);write_json(runtime/'LOOP-STATE.json',state);write_json(runtime/'LOOP-VERSIONS.json',versions);write_json(runtime/'PROJECT-STATUS.json',project_status);return state,versions,project_status

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');a=ap.parse_args();state,_,_=rebuild(Path(a.root).resolve());print(f'rebuilt projections through event {state["projection"]["last_event_seq"]}')
if __name__=='__main__': raise SystemExit(main())
