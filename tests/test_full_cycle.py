#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
PKG=Path(__file__).resolve().parents[1]
def run(cmd,cwd=None):
 r=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
 if r.returncode: raise AssertionError(r.stdout)
 return r.stdout
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/"repo"; root.mkdir(); run(["git","init","-q"],root); run(["git","config","user.email","test@example.com"],root); run(["git","config","user.name","Test"],root)
 (root/"src").mkdir(); (root/"tests").mkdir(); (root/"src/main.py").write_text("def health():\n    return 'ok'\n"); run(["git","add","."],root); run(["git","commit","-qm","base"],root)
 run([sys.executable,str(PKG/"install.py"),str(root)]); run(["git","add","."],root); run(["git","commit","-qm","install"],root)
 req=json.loads((root/".agentic/policy/REQUIREMENTS.json").read_text()); req["requirements"][0]["acceptance_conditions"]=[{"type":"B","description":"health test exists"}]; (root/".agentic/policy/REQUIREMENTS.json").write_text(json.dumps(req,indent=2)+"\n"); run(["git","add",".agentic/policy/REQUIREMENTS.json"],root); run(["git","commit","-qm","requirements"],root)
 g=json.loads((PKG/"examples/goal.project-task.json").read_text()); g["allowed_write_paths"]=["src/**","tests/**"]; g["completion_conditions"]=[{"condition_id":"C1","type":"A","description":"compile succeeds","command":["python3","-m","compileall","-q","src"],"expected_exit_code":0}]; gp=Path(td)/"goal.json"; gp.write_text(json.dumps(g))
 scripts=root/".agentic/scripts"; run([sys.executable,str(scripts/"register_goal.py"),"--root",str(root),"--goal-file",str(gp)])
 (root/"tests/test_health.py").write_text("from src.main import health\n\ndef test_health(): assert health()=='ok'\n"); run(["git","add","tests/test_health.py"],root); run(["git","commit","-qm","candidate"],root)
 run([sys.executable,str(scripts/"verify_goal.py"),"--root",str(root),"--goal-id","G001"]); run([sys.executable,str(scripts/"stop_gate.py"),"--root",str(root),"--goal-id","G001"])
 run([sys.executable,str(scripts/"kg.py"),"--root",str(root),"build","--goal-id","G001"]); run([sys.executable,str(scripts/"kg.py"),"--root",str(root),"promote","--goal-id","G001"])
 run([sys.executable,str(scripts/"transition.py"),"--root",str(root),"complete-goal","--goal-id","G001","--outcome","Health behavior verified"]); run([sys.executable,str(scripts/"transition.py"),"--root",str(root),"accept-project"])
 run([sys.executable,str(scripts/"validate_system.py"),"--root",str(root)]); ps=json.loads((root/".agentic/runtime/PROJECT-STATUS.json").read_text()); assert ps["status"]=="COMPLETED"
 print("PASS: complete user goal → scope → verify → KG → goal → project lifecycle")
