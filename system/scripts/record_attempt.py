#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import load_json
from event_store import append_event
from rebuild_projections import rebuild

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--goal-id',required=True);ap.add_argument('--task-id',required=True);ap.add_argument('--result',required=True,choices=['PASS','FAIL','BLOCKED']);ap.add_argument('--files-json',default='[]');ap.add_argument('--token-cost',type=int,default=0);ap.add_argument('--strategy-id');a=ap.parse_args();root=Path(a.root).resolve();state=load_json(root/'.agentic/runtime/LOOP-STATE.json');run=state['run_id'] or 'manual';append_event(root,run_id=run,type='TASK_STARTED',actor='orchestrator',payload={},goal_id=a.goal_id,task_id=a.task_id);append_event(root,run_id=run,type='MAKER_ATTEMPT_FINISHED',actor='maker',payload={'result':a.result,'files_changed':json.loads(a.files_json),'token_cost':a.token_cost,'strategy_id':a.strategy_id},goal_id=a.goal_id,task_id=a.task_id);rebuild(root);return 0
if __name__=='__main__':raise SystemExit(main())
