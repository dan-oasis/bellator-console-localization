from pathlib import Path
import hashlib,json,re,struct,sys,unittest,zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from managed import Managed,resource_read,baml_read,STRING_TYPES,sread,U32
class PayloadTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=json.loads((ROOT/'package/manifest.json').read_text(encoding='utf-8'))
  cls.mapping=json.loads((ROOT/'locales/en.json').read_text(encoding='utf-8'))
 def test_checksums(self):
  for row in self.manifest['files']:
   for lang in ['ru','en']:
    p=ROOT/'package/payload'/lang/row['relative']
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row[lang])
 def test_rebuild_is_exact(self):
  for row in self.manifest['files']:
   ru=(ROOT/'package/payload/ru'/row['relative']).read_bytes()
   rebuilt,_=Managed(ru).patch(self.mapping)
   self.assertEqual(rebuilt,(ROOT/'package/payload/en'/row['relative']).read_bytes())
 def test_no_russian_in_visible_english_baml_or_used_literals(self):
  for row in self.manifest['files']:
   m=Managed((ROOT/'package/payload/en'/row['relative']).read_bytes())
   used={U32(m.b,p) for at,p,n in m.instructions() if m.b[at]==0x72}
   for off,s in m.us():
    if (0x70000000|off) in used:self.assertIsNone(re.search('[А-Яа-яЁё]',s),s)
   for _,r in m.roots():
    for name,value,*_ in resource_read(r)[1]:
     if not name.endswith('.baml'):continue
     for pos,t,d in baml_read(value):
      if t in STRING_TYPES:
       s,_=sread(d,STRING_TYPES[t]);self.assertIsNone(re.search('[А-Яа-яЁё]',s),s)
 def test_only_selected_string_operands_change_in_methods(self):
  for row in self.manifest['files']:
   ru=Managed((ROOT/'package/payload/ru'/row['relative']).read_bytes())
   en=Managed((ROOT/'package/payload/en'/row['relative']).read_bytes())
   self.assertEqual(list(ru.methods()),list(en.methods()))
   allowed=set()
   for at,p,n in ru.instructions():
    if ru.b[at]==0x72 and ru.b[p:p+4]!=en.b[p:p+4]:allowed.update(range(p,p+4))
   for co,size in ru.methods():
    for p in range(co,co+size):
     if ru.b[p]!=en.b[p]:self.assertIn(p,allowed)
 def test_os_lookup_strings_and_call_structure_preserved(self):
  row=next(x for x in self.manifest['files'] if x['relative'].endswith('.exe'))
  ru=Managed((ROOT/'package/payload/ru'/row['relative']).read_bytes());en=Managed((ROOT/'package/payload/en'/row['relative']).read_bytes())
  rs=dict(ru.us());es=dict(en.us())
  for at,p,n in ru.instructions():
   if ru.b[at]!=0x72:continue
   token=U32(ru.b,p);text=rs[token&0xffffff]
   if re.search('[\u4e00-\u9fff]',text):
    self.assertEqual(token,U32(en.b,p))
    self.assertEqual(text,es[token&0xffffff])
 def test_format_placeholders_preserved(self):
  for ru,en in self.mapping.items():
   self.assertEqual(sorted(re.findall(r'\{[^{}]+\}',ru)),sorted(re.findall(r'\{[^{}]+\}',en)),ru)
 def test_zip_and_manifest_payloads(self):
  with zipfile.ZipFile(ROOT/'dist/BellatorConsole_1.1.5_RU_EN.zip') as z:
   self.assertIsNone(z.testzip());prefix='BellatorConsole_1.1.5_RU_EN/'
   for row in self.manifest['files']:
    for lang in ['ru','en']:
     content=z.read(prefix+'payload/'+lang+'/'+row['relative'])
     self.assertEqual(hashlib.sha256(content).hexdigest(),row[lang])
   self.assertIn(prefix+'Install.cmd',z.namelist())
   self.assertIn(prefix+'Restore.cmd',z.namelist())
 def test_powershell_utf8_bom(self):
  self.assertTrue((ROOT/'package/Install.ps1').read_bytes().startswith(b'\xef\xbb\xbf'))
if __name__=='__main__':unittest.main()
