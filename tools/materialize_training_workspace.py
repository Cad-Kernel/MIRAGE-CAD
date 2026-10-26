"""Create a configured inspection workspace without changing archived source snapshots."""
import argparse,json,shutil
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshot',choices=['run_source','development_source'],default='run_source');p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
 repo=Path(__file__).resolve().parents[1];src=repo/'training/source_snapshots'/a.snapshot/'src';dst=a.destination.resolve()
 if dst.exists():raise SystemExit('Destination must not exist; no silent resume or overwrite')
 shutil.copytree(src,dst)
 replacements={'__RUN_SOURCE_ROOT__':str(dst),'__RUN_ROOT__':str(dst.parent),'__REPO_ROOT__':str(repo),'__DEV_ROOT__':str(repo),
 '__EVIDENCE_SOURCE_ROOT__':str(repo/'evidence'),'__USER_HOME__':str(Path.home()),'__LOCAL_WORKSPACE__':str(dst.parent),'__TEMP_RUN_ROOT__':str(dst.parent/'tmp')}
 for f in dst.rglob('*'):
  if not f.is_file():continue
  try:text=f.read_text(encoding='utf-8')
  except UnicodeDecodeError:continue
  for old,new in replacements.items():text=text.replace(old,new)
  f.write_text(text,encoding='utf-8')
 print(json.dumps({'workspace':str(dst),'training_started':False,'warning':'Historical guards refer to original hashes and original layout. Configure data/runtime and review the source mapping; this command does not authorize a new experiment.'},indent=2))
if __name__=='__main__':main()
