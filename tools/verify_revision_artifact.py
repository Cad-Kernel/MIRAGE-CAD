"""Model-free integrity and raw-result checks for the distributed review artifact."""
import argparse,hashlib,json,re
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root.resolve()
 manifest=root/'evidence/bundle_manifest.jsonl';count=0;total=0
 for line in manifest.read_text(encoding='utf-8').splitlines():
  item=json.loads(line);f=root/item['path'];assert f.is_file(),item['path'];h=hashlib.sha256()
  with f.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
  assert f.stat().st_size==item['bytes'] and h.hexdigest()==item['sha256'],item['path'];count+=1;total+=f.stat().st_size
 checks=[]
 r1=root/'evidence/cpu_audits/review01_native_results_v1'
 for f in sorted(r1.glob('*execution_rows.jsonl')):
  rows=[json.loads(x) for x in f.read_text().splitlines() if x.strip()];assert len(rows)==500
  checks.append({'source':f.relative_to(root).as_posix(),'rows':len(rows),'build':sum(bool(x.get('build_ok')) for x in rows)})
 for pattern,n in [('review_03_fullstack_replications/result/*paired_cases.jsonl',2500),('review_04_exposure_policy/result/paired_cases_*.jsonl',2500)]:
  for f in sorted((root/'evidence').glob(pattern)):
   rows=[json.loads(x) for x in f.read_text().splitlines() if x.strip()];assert len(rows)==n and len({x['sample_id'] for x in rows})==n
   arms={}
   for arm in rows[0]['arms']:
    gates=[x['arms'][arm].get('native_gate',x['arms'][arm].get('execution')) for x in rows]
    arms[arm]={'build':sum(bool(x['build_ok']) for x in gates),'export':sum(bool(x['step_export_ok']) for x in gates)}
   checks.append({'source':f.relative_to(root).as_posix(),'rows':n,'arms':arms})
 print(json.dumps({'status':'PASS','files_verified':count,'bytes_verified':total,'raw_row_checks':checks,'model_training_inference_or_CAD_execution':False},indent=2))
if __name__=='__main__':main()
