"""Generate the manifest, bilingual installer package and SHA-256 sums."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=[]
 for relative,original,previous in [
  ('斗战者控制台.dll','d9c1ebcb43315d46319c24b7c11fc0facad54d4d4737305dce72f53d6b6a43a2',['eb3d846296d96d701d162d1d5bacffc062023b1e17f41135086f9e050a5cfdd5','f7d6d391700891a6dcf17fbbe85f40b19fff114da404d883e5d0981fa34b86fb','eca13a8430aa4e05c27a98f5ba9f8d866e377c91f57adb0bb94a012879639e39','bbd616d8364ea718dcde53e07b1106e111a72375276d7669e92e248ca7ba6191']),
  ('ApplyIcc/ApplyIcc.exe','a9ca6c36c36e92c7467b8cffb5c155e68895fa1983d77fd52e5d3a24fe52d7d5',[])]:
  row={'relative':relative,'original':original,'previous':previous}
  for lang in ['ru','en']:row[lang]=digest(ROOT/'package/payload'/lang/relative)
  files.append(row)
 (ROOT/'package/manifest.json').write_text(json.dumps({'version':'1.1.5-localization.6','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 ps=ROOT/'package/Install.ps1';text=ps.read_text(encoding='utf-8-sig');ps.write_text(text,encoding='utf-8-sig',newline='\n')
 for action in ['Install','Restore']:
  cmd=f'@echo off\r\npowershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Install.ps1" -Action {action}\r\nset "result=%ERRORLEVEL%"\r\necho.\r\npause\r\nexit /b %result%\r\n'
  (ROOT/'package'/f'{action}.cmd').write_bytes(cmd.encode('ascii'))
 for name in ['README.md','README.ru.md']:(ROOT/'package'/name).write_bytes((ROOT/name).read_bytes())
 sums=''.join(digest(p)+'  '+p.relative_to(ROOT/'package').as_posix()+'\n' for p in sorted((ROOT/'package').rglob('*'),key=lambda p:p.relative_to(ROOT/'package').as_posix()) if p.is_file() and p.name!='SHA256SUMS')
 (ROOT/'package/SHA256SUMS').write_text(sums,encoding='utf-8',newline='\n')
 (ROOT/'dist').mkdir(exist_ok=True)
 archive=ROOT/'dist/BellatorConsole_1.1.5_RU_EN.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted((ROOT/'package').rglob('*'),key=lambda p:p.relative_to(ROOT/'package').as_posix()):
   if p.is_file():
    info=zipfile.ZipInfo('BellatorConsole_1.1.5_RU_EN/'+p.relative_to(ROOT/'package').as_posix(),date_time=(2026,1,1,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes(),compresslevel=9)
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None
 (ROOT/'dist/SHA256SUMS').write_text(digest(archive)+'  '+archive.name+'\n',encoding='utf-8',newline='\n')
 print(archive.name,archive.stat().st_size,'bytes',digest(archive))
if __name__=='__main__':main()
