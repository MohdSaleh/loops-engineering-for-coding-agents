from __future__ import annotations
import fcntl, hashlib, json, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from common import SCHEMA_VERSION

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def canonical_event_hash(event: dict[str,Any]) -> str:
    body={k:v for k,v in event.items() if k!='event_hash'}
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()

def load_events(path: Path) -> list[dict[str,Any]]:
    result=[]; previous=None
    if not path.exists(): return result
    for line_no,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        event=json.loads(line)
        if event.get('seq')!=len(result)+1: raise RuntimeError(f'event sequence invalid at line {line_no}')
        if event.get('prev_event_hash')!=previous: raise RuntimeError(f'event previous hash invalid at line {line_no}')
        actual=canonical_event_hash(event)
        if event.get('event_hash')!=actual: raise RuntimeError(f'event hash invalid at line {line_no}')
        previous=actual; result.append(event)
    return result

def append_event(root: Path, *, run_id: str, type: str, actor: str, payload: dict[str,Any], goal_id: str|None=None, task_id: str|None=None, prompt_id: str|None=None, project_id: str|None=None, git_sha: str|None=None, git_tree: str|None=None, evidence_refs: list[dict[str,str]]|None=None) -> dict[str,Any]:
    root=root.resolve(); runtime=root/'.agentic/runtime'; runtime.mkdir(parents=True,exist_ok=True)
    path=runtime/'LOOP-EVENTS.jsonl'; lock_path=runtime/'locks/event-log.lock'; lock_path.parent.mkdir(parents=True,exist_ok=True)
    with lock_path.open('a+',encoding='utf-8') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        events=load_events(path); previous=events[-1]['event_hash'] if events else None
        event={'schema_version':SCHEMA_VERSION,'seq':len(events)+1,'event_id':str(uuid.uuid4()),'timestamp':utc_now(),'run_id':run_id,'goal_id':goal_id,'task_id':task_id,'prompt_id':prompt_id,'project_id':project_id,'type':type,'actor':actor,'git_sha':git_sha,'git_tree':git_tree,'payload':payload,'evidence_refs':evidence_refs or [],'prev_event_hash':previous}
        event['event_hash']=canonical_event_hash(event)
        with path.open('a',encoding='utf-8') as handle:
            handle.write(json.dumps(event,sort_keys=True,separators=(',',':'))+'\n');handle.flush();os.fsync(handle.fileno())
        fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
    return event
