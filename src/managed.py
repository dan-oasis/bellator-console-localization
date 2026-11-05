"""Read and patch Bellator 1.1.5 resources without executing the binaries.

Only BAML values and ldstr string references may change. Method instruction
layout and the metadata tables are preserved. Python 3.10+, standard library.
"""
import struct
U32=lambda b,o:struct.unpack_from('<I',b,o)[0]
U16=lambda b,o:struct.unpack_from('<H',b,o)[0]
P32=lambda n:struct.pack('<I',n)
def vread(b,p):
 n=0;s=0
 while True:
  x=b[p];p+=1;n|=(x&127)<<s;s+=7
  if x<128:return n,p
  if s>35:raise ValueError('Invalid variable integer')
def vwrite(n):
 out=bytearray()
 while n>=128:out.append((n&127)|128);n>>=7
 out.append(n);return bytes(out)
def cread(b,p):
 x=b[p];p+=1
 if x<128:return x,p
 if x<192:return ((x&63)<<8)|b[p],p+1
 return ((x&31)<<24)|(b[p]<<16)|(b[p+1]<<8)|b[p+2],p+3
def cwrite(n):
 if n<128:return bytes([n])
 if n<16384:return bytes([128|(n>>8),n&255])
 return bytes([192|(n>>24),(n>>16)&255,(n>>8)&255,n&255])
def sread(b,p,encoding='utf-8'):
 n,p=vread(b,p);return b[p:p+n].decode(encoding),p+n
def swrite(s):
 v=s.encode('utf-8');return vwrite(len(v))+v
FIX={1:6,2:0,3:3,4:0,7:2,8:0,9:2,10:0,11:2,12:0,13:2,14:0,26:0,33:4,34:4,35:6,37:4,39:9,40:9,41:0,42:0,43:0,44:2,45:4,46:2,48:3,49:0,50:2,51:2,53:8,54:4,55:3,56:4}
VAR={5,6,15,16,17,18,19,20,21,22,23,24,25,27,28,29,30,31,32,36,38,47,52}
STRING_TYPES={5:2,16:0,17:0,25:0,32:2,36:2,52:0}
def baml_read(b):
 p=4+U32(b,0)+12;records=[]
 while p<len(b):
  start=p;t=b[p];p+=1
  if t in FIX:end=p+FIX[t]
  elif t in VAR:size,q=vread(b,p);end=p+size;p=q
  else:raise ValueError(('BAML record',start,t))
  assert p<=end<=len(b)
  records.append((start,t,b[p:end]));p=end
 assert records[-1][1]==2
 return records
def baml_record(t,d):
 if t in VAR:
  size=len(d)+1
  while len(d)+len(vwrite(size))!=size:size=len(d)+len(vwrite(size))
  return bytes([t])+vwrite(size)+d
 return bytes([t])+d

def baml_patch(b,mapping):
 records=baml_read(b);new=[];count=0
 for pos,t,d in records:
  if t in STRING_TYPES:
   so=STRING_TYPES[t];s,end=sread(d,so)
   if s in mapping:
    d=d[:so]+swrite(mapping[s])+d[end:];count+=1
  new.append([pos,t,d])
 offsets={};p=records[0][0]
 for pos,t,d in new:offsets[pos]=p;p+=len(baml_record(t,d))
 offsets[len(b)]=p
 for i,(pos,t,d) in enumerate(new):
  if t!=37:continue
  end=pos+5+U32(d,0);assert end in offsets
  new[i][2]=P32(offsets[end]-(offsets[pos]+5))
  j=i+1;keys=[]
  while records[j][1] in [38,39,55,50]:
   if records[j][1] in [38,39]:keys.append(j)
   j+=1
  base=records[j][0];assert records[j][1]==3 or (not keys and base==end)
  for k in keys:
   kd=bytearray(new[k][2]);off=2 if new[k][1]==38 else 3;target=base+U32(kd,off)
   assert target in offsets
   struct.pack_into('<I',kd,off,offsets[target]-offsets[base]);new[k][2]=bytes(kd)
 result=b[:records[0][0]]+b''.join(baml_record(t,d) for _,t,d in new)
 baml_validate(result)
 return result,count

def baml_validate(b):
 rs=baml_read(b);bounds={x[0] for x in rs}|{len(b)}
 for i,(pos,t,d) in enumerate(rs):
  if t!=37:continue
  end=pos+5+U32(d,0);assert end in bounds
  j=i+1;keys=[]
  while rs[j][1] in [38,39,55,50]:
   if rs[j][1] in [38,39]:keys.append(rs[j])
   j+=1
  base=rs[j][0]
  for _,kt,kd in keys:assert base+U32(kd,2 if kt==38 else 3) in bounds and base+U32(kd,2 if kt==38 else 3)<end

def resource_read(r):
 assert U32(r,0)==0xbeefcace
 p=12+U32(r,8);ver,n,nt=struct.unpack_from('<III',r,p);p+=12;assert ver==2
 for _ in range(nt):_,p=sread(r,p)
 p=(p+7)&~7;p+=n*4;positions=struct.unpack_from('<'+'I'*n,r,p);p+=n*4;ds=U32(r,p);ns=p+4;entries=[]
 for pos in positions:
  name,end=sread(r,ns+pos,'utf-16-le');dp=U32(r,end);kind,q=vread(r,ds+dp)
  if kind not in [32,33]:raise ValueError(('Unsupported resource type',kind))
  size=U32(r,q);entries.append((name,r[q+4:q+4+size],end,dp,kind))
 return ds,entries

def resource_patch(r,mapping):
 ds,entries=resource_read(r);header=bytearray(r[:ds]);data=bytearray();count=0
 for name,value,entry,dp,kind in sorted(entries,key=lambda x:x[3]):
  if name.endswith('.baml'):value,n=baml_patch(value,mapping);count+=n
  struct.pack_into('<I',header,entry,len(data));data+=vwrite(kind)+P32(len(value))+value
 return bytes(header+data),count

ONE={x:0 for x in list(range(0,0x0e))+list(range(0x14,0x1f))+[0x25,0x26,0x2a]+list(range(0x46,0x6f))+[0x76,0x7a]+list(range(0x82,0x8c))+[0x8e]+list(range(0x90,0xa3))+list(range(0xb3,0xbb))+[0xc3]+list(range(0xd1,0xdd))+[0xdf,0xe0]}
for x in range(0x0e,0x14):ONE[x]=1
for x in [0x1f]+list(range(0x2b,0x38))+[0xde]:ONE[x]=1
for x in [0x20,0x22,0x27,0x28,0x29]+list(range(0x38,0x45))+list(range(0x6f,0x76))+[0x79]+list(range(0x7b,0x82))+[0x8c,0x8d,0x8f,0xa3,0xa4,0xa5,0xc2,0xc6,0xd0,0xdd]:ONE[x]=4
for x in [0x21,0x23]:ONE[x]=8
ONE[0x45]='switch'
TWO={x:0 for x in [0,1,2,3,4,5,0xf,0x11,0x13,0x14,0x17,0x18,0x1a,0x1d]}
for x in [6,7,0x15,0x16,0x1c]:TWO[x]=4
for x in range(9,0xf):TWO[x]=2
TWO[0x12]=1;TWO[0x19]=1

class Managed:
 def __init__(self,b):
  self.b=b;self.pe=U32(b,60);self.opt=self.pe+24;self.sec=self.opt+U16(b,self.pe+20);self.dd=self.opt+(112 if U16(b,self.opt)==0x20b else 96);self.sections=[]
  for i in range(U16(b,self.pe+6)):
   o=self.sec+40*i;vs,va,sz,raw=struct.unpack_from('<IIII',b,o+8);self.sections.append((vs,va,sz,raw));assert raw+sz<=len(b)
  self.cli=self.rva(U32(b,self.dd+14*8));self.md=self.rva(U32(b,self.cli+8));self.mdsize=U32(b,self.cli+12);self.streams={};self.stream_entries={}
  p=self.md+16+U32(b,self.md+12);p=(p+3)&~3;cnt=U16(b,p+2);p+=4
  for _ in range(cnt):
   entry=p;off,size=struct.unpack_from('<II',b,p);p+=8;end=b.index(0,p);name=b[p:end].decode();p=(end+4)&~3
   assert off+size<=self.mdsize;self.streams[name]=(self.md+off,size);self.stream_entries[name]=entry-self.md
  self.ro=self.rva(U32(b,self.cli+24));self.rsize=U32(b,self.cli+28)
 def rva(self,x):
  for vs,va,sz,raw in self.sections:
   if va<=x<va+max(vs,sz):return raw+x-va
  raise ValueError(('Unmapped RVA',x))
 def us(self):
  b=self.b;start,size=self.streams['#US'];p=start+1
  while p<start+size:
   off=p-start;n,p=cread(b,p)
   if not n:continue
   yield off,b[p:p+n-1].decode('utf-16-le');p+=n
 def roots(self):
  p=0;b=self.b[self.ro:self.ro+self.rsize]
  while p<len(b):
   if p+4>len(b):
    assert not any(b[p:]);break
   n=U32(b,p)
   if not n:p+=4;continue
   assert p+4+n<=len(b)
   yield p,b[p+4:p+4+n]
   p=(p+4+n+7)&~7
 def methods(self):
  b=self.b;tab,_=self.streams['#~'];valid=struct.unpack_from('<Q',b,tab+8)[0];heap=b[tab+6];p=tab+24;rows={}
  for i in range(64):
   if valid&(1<<i):rows[i]=U32(b,p);p+=4
  idx=lambda t:4 if rows.get(t,0)>=65536 else 2
  coded=lambda ts,bits:4 if max(rows.get(t,0) for t in ts)>=(1<<(16-bits)) else 2
  sh=4 if heap&1 else 2;gh=4 if heap&2 else 2;bh=4 if heap&4 else 2
  sizes={0:2+sh+3*gh,1:coded([0,26,35,1],2)+2*sh,2:4+2*sh+coded([2,1,27],2)+idx(4)+idx(6),3:idx(4),4:2+sh+bh,5:idx(6),6:8+sh+bh+idx(8)}
  for i in range(6):p+=rows.get(i,0)*sizes[i]
  for i in range(rows.get(6,0)):
   rv=U32(b,p+i*sizes[6])
   if not rv:continue
   mo=self.rva(rv);first=b[mo]
   if first&3==2:co=mo+1;size=first>>2
   elif first&3==3:co=mo+(U16(b,mo)>>12)*4;size=U32(b,mo+4)
   else:raise ValueError(('Invalid method header',mo))
   yield co,size
 def instructions(self):
  b=self.b
  for co,size in self.methods():
   p=co
   while p<co+size:
    at=p;op=b[p];p+=1
    if op==0xfe:op=b[p];p+=1;n=TWO.get(op)
    else:n=ONE.get(op)
    assert n is not None,('IL opcode',hex(at),hex(op))
    if n=='switch':n=4+4*U32(b,p)
    yield at,p,n
    p+=n
   assert p==co+size
 def patch(self,mapping):
  b=self.b;out=bytearray(b[:max(raw+sz for vs,va,sz,raw in self.sections)]);roots=list(self.roots());baml_count=0
  # Root offsets remain stable because English resources fit within RU slots.
  for i,(off,r) in enumerate(roots):
   ds,entries=resource_read(r)
   if not entries:continue
   nr,n=resource_patch(r,mapping);baml_count+=n
   limit=roots[i+1][0] if i+1<len(roots) else self.rsize
   assert off+4+len(nr)<=limit,('English resource exceeds source slot',off,len(nr),limit)
   out[self.ro+off:self.ro+limit]=P32(len(nr))+nr+bytes(limit-off-4-len(nr))
  us,usz=self.streams['#US'];new_us=bytearray(b[us:us+usz]);tokens={}
  for off,s in self.us():
   if s not in mapping:continue
   v=mapping[s].encode('utf-16-le');no=len(new_us)
   units=struct.unpack('<'+'H'*(len(v)//2),v);special=int(any(x>>8 or (x&255) in [0x27,0x2d,0x7f] or 1<=(x&255)<=8 or 0xe<=(x&255)<=0x1f for x in units))
   new_us+=cwrite(len(v)+1)+v+bytes([special]);tokens[0x70000000|off]=0x70000000|no
  changes=[]
  for at,p,n in self.instructions():
   if b[at]==0x72 and U32(b,p) in tokens:
    old=U32(b,p);struct.pack_into('<I',out,p,tokens[old]);changes.append(p)
  metadata=bytearray(b[self.md:self.md+self.mdsize]);metadata+=bytes((-len(metadata))%4)
  struct.pack_into('<II',metadata,self.stream_entries['#US'],len(metadata),len(new_us));metadata+=new_us
  out+=bytes((-len(out))%8);mdfile=len(out);out+=metadata
  last=self.sec+(U16(b,self.pe+6)-1)*40;vs,va,rawsz,raw=struct.unpack_from('<IIII',b,last+8)
  struct.pack_into('<II',out,self.cli+8,va+mdfile-raw,len(metadata));newvs=len(out)-raw
  fa=U32(b,self.opt+36);sa=U32(b,self.opt+32);newraw=(newvs+fa-1)//fa*fa;out+=bytes(raw+newraw-len(out))
  struct.pack_into('<I',out,last+8,newvs);struct.pack_into('<I',out,last+16,newraw);struct.pack_into('<I',out,last+36,0x40000040)
  struct.pack_into('<I',out,self.opt+56,(va+newvs+sa-1)//sa*sa);struct.pack_into('<I',out,self.opt+8,U32(b,self.opt+8)+newraw-rawsz)
  struct.pack_into('<II',out,self.dd+4*8,0,0);struct.pack_into('<I',out,self.opt+64,0);assert U32(b,self.cli+36)==0
  # Reopen the output and validate metadata, BAML, method integrity, and tokens.
  check=Managed(bytes(out));allowed={p+j for p in changes for j in range(4)}
  for co,sz in self.methods():
   for i in range(co,co+sz):assert b[i]==out[i] or i in allowed
  for name in ['#~','#Strings','#GUID','#Blob']:
   a,sz=self.streams[name];c,cs=check.streams[name];assert sz==cs and b[a:a+sz]==out[c:c+cs]
  for _,r in check.roots():
   for name,value,*_ in resource_read(r)[1]:
    if name.endswith('.baml'):baml_validate(value)
  valid_us={0x70000000|off:s for off,s in check.us()}
  for at,p,n in check.instructions():
   if out[at]==0x72:assert U32(out,p) in valid_us
  return bytes(out),{'baml_values_changed':baml_count,'string_references_changed':len(changes),'methods_verified':len(list(self.methods()))}
