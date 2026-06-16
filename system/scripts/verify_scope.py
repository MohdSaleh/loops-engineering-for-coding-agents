#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from common import load_json, load_workspace, path_matches, is_protected, classify_path, git

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--goal-id',required=True);ap.add_argument('--candidate',default='HEAD');a=ap.parse_args();root=Path(a.root).resolve();ws=load_workspace(root);versions=load_json(root/'.agentic/runtime/LOOP-VERSIONS.json');g=next(x for x in versions['versions'] if x['goal_id']==a.goal_id);changed=[x for x in git(root,'diff','--name-only',g['git_sha_before'],a.candidate).splitlines() if x.strip()];errors=[]
 for path in changed:
  if is_protected(ws,path): errors.append(f'protected path changed: {path}');continue
  if any(path_matches(path,d) for d in g['denied_write_paths']): errors.append(f'denied path changed: {path}');continue
  if not any(path_matches(path,p) for p in g['allowed_write_paths']): errors.append(f'outside goal scope: {path}');continue
  cls=classify_path(ws,path)['class']
  if g['goal_kind']!='SYSTEM_MAINTENANCE' and cls in {'CONTROL_PLANE','RUNTIME_STATE','KNOWLEDGE_GENERATED'}: errors.append(f'project goal changed system-owned path: {path} ({cls})')
 status=git(root,'status','--porcelain','--untracked-files=all').splitlines()
 for row in status:
  path=row[3:].strip()
  if ' -> ' in path:path=path.split(' -> ',1)[1]
  cls=classify_path(ws,path)['class']
  if cls=='PROJECT':errors.append(f'uncommitted project path present: {path}')
 if errors:
  print('\n'.join('FAIL: '+e for e in errors));return 1
 print(f'PASS: {len(changed)} changed paths are within {g["goal_id"]} scope');return 0
if __name__=='__main__': raise SystemExit(main())
