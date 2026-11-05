"""Build English payloads from the supplied Russian revision 5 payloads."""
from pathlib import Path
import hashlib,json
from managed import Managed
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'斗战者控制台.dll':'8262619c2b5150b31ec1c1e72b5d30bc9ffa187c4a842088dbc09485e44d0cc7','ApplyIcc/ApplyIcc.exe':'135095ecfe92531a0fd282cd52cd9bce2682c49485f54a78bbe1cfc2bf565dd8'}
def main():
 mapping=json.loads((ROOT/'locales/en.json').read_text());reports={}
 for relative,expected in EXPECTED.items():
  source=ROOT/'package/payload/ru'/relative;b=source.read_bytes();assert hashlib.sha256(b).hexdigest()==expected,'Unexpected RU payload'
  patched,report=Managed(b).patch(mapping);target=ROOT/'package/payload/en'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(patched)
  report.update(source_sha256=expected,english_sha256=hashlib.sha256(patched).hexdigest(),runtime_tested=False);reports[relative]=report
 (ROOT/'docs/build-report.json').write_text(json.dumps(reports,indent=2)+'\n',newline='\n');print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
