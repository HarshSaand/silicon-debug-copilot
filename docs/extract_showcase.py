from pathlib import Path
import argparse, json, hashlib, sys
p=argparse.ArgumentParser();p.add_argument('--source', type=Path, required=True);a=p.parse_args()
S=a.source.resolve(); D=Path(__file__).resolve().parent; R=D.parent
D.mkdir(exist_ok=True)
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def source(rel):return {'path':rel,'sha256':digest(S/rel)}
def write(data):
 import subprocess
 data['dataset_url']='https://github.com/HarshSaand/silicon-debug-copilot/blob/main/evals/frozen_benchmark.jsonl'
 data['source_code_commit']=subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip()
 data['extractor_sha256']=digest(Path(__file__))
 data['sources']=sources
 data['source_repository']='https://github.com/HarshSaand/'+R.name
 data['extraction']='python docs/extract_showcase.py --source /path/to/reproduced/project'
 (D/'output-example.json').write_text(json.dumps(data,indent=2,ensure_ascii=False,default=str)+'\n')
sys.path.insert(0,str(R/'src'));from silicon_debug.parsers import parse_log
from silicon_debug.workflow import TriageWorkflow
f='evals/frozen_benchmark.jsonl';cases=[json.loads(l) for l in (S/f).read_text().splitlines()];case=next(x for x in cases if x['category']=='pcie_link' and x['answerable']);text='\n'.join(f"2026-01-01T00:00:00.{line['timestamp_offset_ms']:03d} [{line.get('severity','ERROR')}] {line['message']}" for line in case['lines']);report=TriageWorkflow().run(parse_log(text,case['case_id']));out=report.model_dump(mode='json');sources=[source(f)]
write(dict(title='Silicon Debug Copilot',subtitle='A supported log signature with cited evidence',eyebrow='ACTUAL WORKFLOW OUTPUT · SYNTHETIC INPUT',context=case['case_id']+' · local deterministic triage · no corrective actions executed',blocks=[['INPUT LOG',text],['CLASSIFICATION',json.dumps(out['classification'],ensure_ascii=False)],['READ-ONLY NEXT CHECK',json.dumps(out['next_diagnostics'],ensure_ascii=False)[:900]]],raw=dict(case=case,report=out),note='The supplied incident is a synthetic regression fixture. This demonstrates actual parsing, evidence references and read-only triage, not confirmed physical silicon diagnosis or a trained language model.',input='Timestamped synthetic PCIe log fixture',output='Supported signature, evidence IDs and read-only next diagnostic'))
