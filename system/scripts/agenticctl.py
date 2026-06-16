#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

def run(script,args):return subprocess.call([sys.executable,str(Path(__file__).with_name(script)),*args])
def main():
    ap=argparse.ArgumentParser(prog='agenticctl');ap.add_argument('--root',default='.')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('rebuild')
    v=sub.add_parser('validate');v.add_argument('--skip-project-checks',action='store_true')
    g=sub.add_parser('register-goal');g.add_argument('--goal-file',required=True);g.add_argument('--run-id')
    mp=sub.add_parser('maker-packet');mp.add_argument('--goal-id',required=True)
    vp=sub.add_parser('verifier-packet');vp.add_argument('--goal-id',required=True)
    sc=sub.add_parser('verify-scope');sc.add_argument('--goal-id',required=True);sc.add_argument('--candidate',default='HEAD')
    dv=sub.add_parser('verify');dv.add_argument('--goal-id',required=True);dv.add_argument('--type-d-approvals')
    sg=sub.add_parser('stop-gate');sg.add_argument('--goal-id',required=True)
    ra=sub.add_parser('record-attempt');ra.add_argument('--goal-id',required=True);ra.add_argument('--task-id',required=True);ra.add_argument('--result',required=True,choices=['PASS','FAIL','BLOCKED']);ra.add_argument('--files-json',default='[]');ra.add_argument('--token-cost',default='0')
    kb=sub.add_parser('kg-build');kb.add_argument('--goal-id',required=True)
    kp=sub.add_parser('kg-promote');kp.add_argument('--goal-id',required=True)
    cg=sub.add_parser('complete-goal');cg.add_argument('--goal-id',required=True);cg.add_argument('--outcome',required=True)
    es=sub.add_parser('escalate');es.add_argument('--goal-id',required=True);es.add_argument('--code',required=True);es.add_argument('--reason',required=True)
    rs=sub.add_parser('resolve');rs.add_argument('--goal-id',required=True);rs.add_argument('--resolution',required=True,choices=['RESUME','ABANDON']);rs.add_argument('--reason',default='human resolution')
    sub.add_parser('accept-project')
    a=ap.parse_args();base=['--root',a.root]
    if a.cmd=='rebuild':return run('rebuild_projections.py',base)
    if a.cmd=='validate':return run('validate_system.py',base+(['--skip-project-checks'] if a.skip_project_checks else []))
    if a.cmd=='register-goal':return run('register_goal.py',base+['--goal-file',a.goal_file]+(['--run-id',a.run_id] if a.run_id else []))
    if a.cmd=='maker-packet':return run('build_packets.py',base+['--goal-id',a.goal_id])
    if a.cmd=='verifier-packet':return run('build_packets.py',base+['--goal-id',a.goal_id,'--candidate'])
    if a.cmd=='verify-scope':return run('verify_scope.py',base+['--goal-id',a.goal_id,'--candidate',a.candidate])
    if a.cmd=='verify':return run('verify_goal.py',base+['--goal-id',a.goal_id]+(['--type-d-approvals',a.type_d_approvals] if a.type_d_approvals else []))
    if a.cmd=='stop-gate':return run('stop_gate.py',base+['--goal-id',a.goal_id])
    if a.cmd=='record-attempt':return run('record_attempt.py',base+['--goal-id',a.goal_id,'--task-id',a.task_id,'--result',a.result,'--files-json',a.files_json,'--token-cost',str(a.token_cost)])
    if a.cmd in {'kg-build','kg-promote'}:return run('kg.py',base+[a.cmd.split('-')[1],'--goal-id',a.goal_id])
    if a.cmd in {'complete-goal','escalate','resolve'}:
        args=base+[a.cmd,'--goal-id',a.goal_id]
        if a.cmd=='complete-goal':args+=['--outcome',a.outcome]
        elif a.cmd=='escalate':args+=['--code',a.code,'--reason',a.reason]
        else:args+=['--resolution',a.resolution,'--reason',a.reason]
        return run('transition.py',args)
    if a.cmd=='accept-project':return run('transition.py',base+['accept-project'])
    return 2
if __name__=='__main__':raise SystemExit(main())
