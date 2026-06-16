#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from event_store import append_event

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--run-id',required=True);ap.add_argument('--type',required=True);ap.add_argument('--actor',required=True);ap.add_argument('--goal-id');ap.add_argument('--task-id');ap.add_argument('--prompt-id');ap.add_argument('--project-id');ap.add_argument('--git-sha');ap.add_argument('--git-tree');ap.add_argument('--payload-json',default='{}');a=ap.parse_args()
 event=append_event(Path(a.root),run_id=a.run_id,type=a.type,actor=a.actor,payload=json.loads(a.payload_json),goal_id=a.goal_id,task_id=a.task_id,prompt_id=a.prompt_id,project_id=a.project_id,git_sha=a.git_sha,git_tree=a.git_tree)
 print(json.dumps(event,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
