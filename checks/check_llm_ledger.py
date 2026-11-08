import os,sys,tempfile,types,importlib.util,concurrent.futures
from pathlib import Path
with tempfile.TemporaryDirectory() as d:
 os.environ['MODEL_DATA_DIR']=d
 for name,attrs in [('app.auth',{'get_current_user':lambda:None}),('app.database',{'SessionLocal':None}),('app.services.auth_service',{'AuthService':None})]:
  m=types.ModuleType(name);m.__dict__.update(attrs);sys.modules[name]=m
 spec=importlib.util.spec_from_file_location('career_model',str(Path(__file__).resolve().parents[1]/'backend/app/personal_model.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def op(i,user='u'):return {'id':str(i),'fingerprint':'f','reserved':False,'valid':False,'user':user}
 def attempt(i):
  o=op(i)
  try:m.reserve(o);return o
  except m.AccessDenied:return None
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(attempt,range(8)))
 reserved=[o for o in results if o];assert len(reserved)==3
 assert m.access_status('u')['free_remaining']==0
 m.settle(reserved[0],False);assert m.access_status('u')['free_remaining']==1
 another=op('replacement');m.reserve(another);m.settle(another,True)
 assert m.access_status('u')['free_used']==1
 assert m.access_status('other')['free_remaining']==3
 try:m.reserve(op('replacement'));raise AssertionError('duplicate admitted')
 except m.AccessDenied as e:assert e.status==409
 try:m.llm_options();raise AssertionError('anonymous admitted')
 except m.AccessDenied as e:assert e.status==401
 print('PASS: concurrent cap, failure release, success charge, user isolation, duplicate rejection, anonymous denial')
