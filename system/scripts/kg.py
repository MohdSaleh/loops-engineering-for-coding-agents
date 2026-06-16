#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, os, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
import jsonschema
from common import load_json, load_workspace, project_by_id, path_matches, sha256_file, git, write_json
from event_store import append_event
from rebuild_projections import rebuild

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def excluded(ws,path): return any(path_matches(path,p) for p in ws['kg_exclude'])
def prov(path,sha,tree,filehash=None,start=None,end=None,extractor='universal-file',confidence=1.0): return {'extractor':extractor,'extractor_version':'3.0','source_path':path,'start_line':start,'end_line':end,'file_sha256':filehash,'git_sha':sha,'git_tree':tree,'generated_at':now(),'confidence':confidence}
def eid(kind,*parts): return kind+':'+hashlib.sha256('|'.join(parts).encode()).hexdigest()[:24]
def extract(root,project,sha,tree):
 ws=load_workspace(root);tracked=[x for x in git(root,'ls-tree','-r','--name-only',sha).splitlines() if x];nodes=[];edges=[];project_node=f"project:{project['project_id']}";nodes.append({'id':project_node,'type':'Project','name':project['project_id'],'project_id':project['project_id'],'attributes':{'root':project['root']},'provenance':prov(None,sha,tree)})
 for rel in tracked:
  if excluded(ws,rel): continue
  blob=subprocess.run(['git','show',f'{sha}:{rel}'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
  if blob.returncode!=0: continue
  data=blob.stdout
  fh=hashlib.sha256(data).hexdigest();fid='file:'+rel;kind='Test' if any(rel==t or rel.startswith(t.rstrip('/')+'/') for t in project['test_roots']) else 'File';nodes.append({'id':fid,'type':kind,'name':Path(rel).name,'project_id':project['project_id'],'attributes':{},'provenance':prov(rel,sha,tree,fh)});edges.append({'id':eid('contains',project_node,fid),'type':'CONTAINS','from':project_node,'to':fid,'project_id':project['project_id'],'attributes':{},'provenance':prov(rel,sha,tree,fh)})
  try:text=data.decode('utf-8')
  except UnicodeDecodeError:continue
  if rel.endswith('.py'):
   try:
    mod=ast.parse(text)
    for n in ast.walk(mod):
     if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
      typ='Class' if isinstance(n,ast.ClassDef) else 'Function';sid=f"symbol:{rel}:{n.name}:{n.lineno}";nodes.append({'id':sid,'type':typ,'name':n.name,'project_id':project['project_id'],'attributes':{},'provenance':prov(rel,sha,tree,fh,n.lineno,getattr(n,'end_lineno',n.lineno),'python-ast',1.0)});edges.append({'id':eid('defines',fid,sid),'type':'DEFINES','from':fid,'to':sid,'project_id':project['project_id'],'attributes':{},'provenance':prov(rel,sha,tree,fh,n.lineno,getattr(n,'end_lineno',n.lineno),'python-ast',1.0)})
   except SyntaxError: pass
  elif rel.endswith(('.js','.jsx','.ts','.tsx')):
   pattern=re.compile(r'(?m)^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)')
   for m in pattern.finditer(text):
    line=text[:m.start()].count('\n')+1;name=m.group(1);typ='Class' if 'class' in m.group(0) else 'Function';sid=f"symbol:{rel}:{name}:{line}";nodes.append({'id':sid,'type':typ,'name':name,'project_id':project['project_id'],'attributes':{'parser':'conservative-regex'},'provenance':prov(rel,sha,tree,fh,line,line,'js-ts-conservative',0.65)});edges.append({'id':eid('defines',fid,sid),'type':'DEFINES','from':fid,'to':sid,'project_id':project['project_id'],'attributes':{},'provenance':prov(rel,sha,tree,fh,line,line,'js-ts-conservative',0.65)})
 return nodes,edges

def validate_bundle(root,bundle):
 manifest=load_json(bundle/'manifest.json');jsonschema.validate(manifest,load_json(root/'.agentic/schemas/kg-manifest.schema.json'));nodes=[json.loads(x) for x in (bundle/'nodes.jsonl').read_text().splitlines() if x];edges=[json.loads(x) for x in (bundle/'edges.jsonl').read_text().splitlines() if x];ns=set()
 for n in nodes:jsonschema.validate(n,load_json(root/'.agentic/schemas/kg-node.schema.json'));ns.add(n['id'])
 for e in edges:jsonschema.validate(e,load_json(root/'.agentic/schemas/kg-edge.schema.json'));assert e['from'] in ns and e['to'] in ns
 assert len(nodes)==manifest['counts']['nodes'] and len(edges)==manifest['counts']['edges']
 for name,rec in manifest['artifacts'].items():
  fp=bundle/rec['path'];assert fp.is_file() and sha256_file(fp)==rec['sha256']
 return manifest

def emit(root,run,typ,gid,payload,sha,tree):
 return append_event(root,run_id=run,type=typ,actor='kg_builder',payload=payload,goal_id=gid,git_sha=sha,git_tree=tree)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');sub=ap.add_subparsers(dest='cmd',required=True);b=sub.add_parser('build');b.add_argument('--goal-id',required=True);p=sub.add_parser('promote');p.add_argument('--goal-id',required=True);a=ap.parse_args();root=Path(a.root).resolve();runtime=root/'.agentic/runtime';versions=load_json(runtime/'LOOP-VERSIONS.json');state=load_json(runtime/'LOOP-STATE.json');g=next(x for x in versions['versions'] if x['goal_id']==a.goal_id);ws=load_workspace(root);project=project_by_id(ws,g['project_id']);run=state['run_id'] or 'manual'
 if g['status']!='VERIFIER_PASS' or not g.get('stop_gate_passed'): raise SystemExit('KG build/promote requires VERIFIER_PASS and passed stop gate')
 if a.cmd=='build':
  manifests=list((root/'.agentic/knowledge/manifests').glob('kg-*.json'));n=max([int(x.stem.split('-')[1]) for x in manifests] or [0])+1;kg=f'kg-{n:06d}';bundle=root/'.agentic/knowledge/staging'/run
  if bundle.exists():shutil.rmtree(bundle)
  (bundle/'projections').mkdir(parents=True);nodes,edges=extract(root,project,g['git_sha_after'],g['git_tree_after']);(bundle/'nodes.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in nodes));(bundle/'edges.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in edges));(bundle/'projections/INDEX.md').write_text(f'# Knowledge Graph {kg}\n\nNodes: {len(nodes)}  \nEdges: {len(edges)}\n');
  artifacts={k:{'path':v,'sha256':sha256_file(bundle/v)} for k,v in {'nodes':'nodes.jsonl','edges':'edges.jsonl','projections':'projections/INDEX.md'}.items()};manifest={'schema_version':'3.0','kg_version':kg,'status':'STAGING','goal_id':g['goal_id'],'project_id':g['project_id'],'git_sha':g['git_sha_after'],'git_tree':g['git_tree_after'],'generated_at':now(),'extractors':[{'name':'universal-file','version':'3.0'},{'name':'python-ast','version':'stdlib'},{'name':'js-ts-conservative','version':'3.0'}],'counts':{'nodes':len(nodes),'edges':len(edges)},'artifacts':artifacts};write_json(bundle/'manifest.json',manifest);validate_bundle(root,bundle);emit(root,run,'KG_STAGE_CREATED',g['goal_id'],{'kg_version':kg},g['git_sha_after'],g['git_tree_after']);emit(root,run,'KG_STAGE_VALIDATED',g['goal_id'],{'kg_version':kg,'passed':True},g['git_sha_after'],g['git_tree_after']);print(kg)
 else:
  bundle=root/'.agentic/knowledge/staging'/run;manifest=validate_bundle(root,bundle);kg=manifest['kg_version'];release=root/'.agentic/knowledge/releases'/kg
  if release.exists():raise SystemExit('release already exists')
  manifest['status']='PROMOTED';write_json(bundle/'manifest.json',manifest);os.replace(bundle,release);write_json(root/'.agentic/knowledge/manifests'/f'{kg}.json',manifest);current=root/'.agentic/knowledge/current';
  if current.is_symlink() or current.exists(): current.unlink()
  current.symlink_to(Path('releases')/kg);emit(root,run,'KG_PROMOTED',g['goal_id'],{'kg_version':kg},g['git_sha_after'],g['git_tree_after']);rebuild(root);print(kg)
if __name__=='__main__': raise SystemExit(main())
