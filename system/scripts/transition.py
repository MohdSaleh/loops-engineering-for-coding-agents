#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess
from pathlib import Path
from common import load_json
from event_store import append_event
from rebuild_projections import rebuild

def emit(root,run,typ,actor,gid,payload,sha=None,tree=None):
    event=append_event(root,run_id=run,type=typ,actor=actor,payload=payload,goal_id=gid,git_sha=sha,git_tree=tree)
    rebuild(root)
    return event

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('complete-goal');c.add_argument('--goal-id',required=True);c.add_argument('--outcome',required=True)
    e=sub.add_parser('escalate');e.add_argument('--goal-id',required=True);e.add_argument('--code',required=True);e.add_argument('--reason',required=True)
    rs=sub.add_parser('resolve');rs.add_argument('--goal-id',required=True);rs.add_argument('--resolution',required=True,choices=['RESUME','ABANDON']);rs.add_argument('--reason',default='human resolution')
    sub.add_parser('accept-project')
    a=ap.parse_args();root=Path(a.root).resolve();state=load_json(root/'.agentic/runtime/LOOP-STATE.json');versions=load_json(root/'.agentic/runtime/LOOP-VERSIONS.json');run=state['run_id'] or 'manual'
    if a.cmd in {'complete-goal','escalate','resolve'}:
        g=next(x for x in versions['versions'] if x['goal_id']==a.goal_id)
    if a.cmd=='escalate':
        emit(root,run,'GOAL_ESCALATED','orchestrator',a.goal_id,{'escalation_code':a.code,'reason':a.reason})
    elif a.cmd=='complete-goal':
        if g['status']!='VERIFIER_PASS' or not g.get('stop_gate_passed') or not g.get('kg_version_after'):
            raise SystemExit('goal requires verifier pass, stop gate, and promoted KG')
        result=subprocess.run(['python3',str(root/'.agentic/scripts/validate_system.py'),'--root',str(root)],check=False)
        if result.returncode:return result.returncode
        emit(root,run,'GOAL_COMPLETED','orchestrator',a.goal_id,{'goal_outcome':a.outcome,'requirement_evidence':[{'goal_id':a.goal_id,'git_tree':g['git_tree_after']}]},g['git_sha_after'],g['git_tree_after'])
    elif a.cmd=='resolve':
        emit(root,run,'HUMAN_RESOLUTION_RECORDED','human',a.goal_id,{'resolution':a.resolution,'reason':a.reason})
    elif a.cmd=='accept-project':
        ps=load_json(root/'.agentic/runtime/PROJECT-STATUS.json')
        if not ps['completion']['ready_for_acceptance']:raise SystemExit('project is not ready for acceptance')
        emit(root,run,'PROJECT_COMPLETED','human','G000',{'accepted':True})
    return 0
if __name__=='__main__':raise SystemExit(main())
