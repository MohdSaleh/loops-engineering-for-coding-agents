from __future__ import annotations
import fnmatch, hashlib, json, os, subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "3.0"

class AgenticError(RuntimeError): pass

def load_json(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: raise AgenticError(f"cannot load JSON {path}: {exc}") from exc

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=False)+"\n", encoding="utf-8")
    os.replace(temp, path)

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def git(root: Path, *args: str) -> str:
    p=subprocess.run(["git",*args],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode: raise AgenticError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()

def normalize_rel(path: str) -> str:
    value=path.replace('\\','/')
    while value.startswith('./'):
        value=value[2:]
    value=value.rstrip('/') if value not in ('', '.') else value
    return value or '.'

def path_matches(path: str, pattern: str) -> bool:
    path=normalize_rel(path); pattern=normalize_rel(pattern)
    if pattern == '**': return True
    if pattern.endswith('/**'):
        base=pattern[:-3].rstrip('/')
        return path == base or path.startswith(base+'/')
    return fnmatch.fnmatchcase(path, pattern)

def load_workspace(root: Path) -> dict[str,Any]:
    p=root/'.agentic/config/workspace.json'
    if not p.is_file(): raise AgenticError(f"workspace manifest missing: {p}")
    return load_json(p)

def project_by_id(workspace: dict[str,Any], project_id: str) -> dict[str,Any]:
    for p in workspace['projects']:
        if p['project_id']==project_id: return p
    raise AgenticError(f"unknown project_id {project_id}")

def classify_path(workspace: dict[str,Any], path: str) -> dict[str,Any]:
    rel=normalize_rel(path)
    if any(path_matches(rel,p) for p in workspace.get('generated_paths',[])):
        return {'pattern':'<generated>','class':'BUILD_OUTPUT','write_roles':['build_tool']}
    for rule in workspace['ownership']:
        if path_matches(rel, rule['pattern']): return rule
    return {'pattern':'<none>','class':'UNCLASSIFIED','write_roles':[]}

def is_protected(workspace: dict[str,Any], path: str) -> bool:
    return any(path_matches(path,p) for p in workspace.get('protected_paths',[]))

def allowed_for_role(workspace: dict[str,Any], path: str, role: str) -> bool:
    return not is_protected(workspace,path) and role in classify_path(workspace,path).get('write_roles',[])
