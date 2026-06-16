#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import load_json, load_workspace, project_by_id, git, write_json

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--goal-id',required=True);ap.add_argument('--candidate',action='store_true');a=ap.parse_args();root=Path(a.root).resolve();ws=load_workspace(root);versions=load_json(root/'.agentic/runtime/LOOP-VERSIONS.json');g=next(x for x in versions['versions'] if x['goal_id']==a.goal_id);p=project_by_id(ws,g['project_id']);packets=root/'.agentic/runtime/packets';packets.mkdir(parents=True,exist_ok=True)
 if not a.candidate:
  packet={'schema_version':'3.0','goal_id':g['goal_id'],'project_id':g['project_id'],'project_root':p['root'],'goal_raw':g['goal_raw'],'task':{'task_id':'T001','description':g['goal_raw']},'allowed_write_paths':g['allowed_write_paths'],'denied_write_paths':g['denied_write_paths'],'completion_conditions':g['checklist'],'baseline_git_sha':g['git_sha_before'],'baseline_git_tree':g['git_tree_before'],'context_files':['.agentic/policy/PROJECT-SPEC.md','.agentic/policy/REQUIREMENTS.json','.agentic/policy/VISION.md']};write_json(packets/f'{g["goal_id"]}-maker.json',packet)
 else:
  sha=git(root,'rev-parse','HEAD');tree=git(root,'rev-parse','HEAD^{tree}');packet={'schema_version':'3.0','goal_id':g['goal_id'],'project_id':g['project_id'],'project_root':p['root'],'completion_conditions':g['checklist'],'allowed_write_paths':g['allowed_write_paths'],'denied_write_paths':g['denied_write_paths'],'baseline_git_sha':g['git_sha_before'],'baseline_git_tree':g['git_tree_before'],'candidate_git_sha':sha,'candidate_git_tree':tree,'forbidden_context':['.agentic/runtime/LOOP-EVENTS.jsonl','.agentic/runtime/LOOP-STATE.json','maker packet','maker summaries','maker session logs']};write_json(packets/f'{g["goal_id"]}-verifier.json',packet)
 print(packet)
if __name__=='__main__': raise SystemExit(main())
