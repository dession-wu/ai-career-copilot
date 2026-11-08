import os,sys,tempfile,types,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('work/career-test-deps').resolve()))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
class DB:
 def __enter__(self):return self
 def __exit__(self,*args):pass
class Auth:
 def __init__(self,db):pass
 def verify_token(self,t):return t
 def get_user_by_username(self,n):return types.SimpleNamespace(id=n)
with tempfile.TemporaryDirectory() as d:
 os.environ['MODEL_DATA_DIR']=d;os.environ['BAILIAN_API_KEY']='test-placeholder-not-real'
 for name,attrs in [('app.auth',{'get_current_user':lambda:types.SimpleNamespace(id='u')}),('app.database',{'SessionLocal':DB}),('app.services.auth_service',{'AuthService':Auth})]:
  mod=types.ModuleType(name);mod.__dict__.update(attrs);sys.modules[name]=mod
 spec=importlib.util.spec_from_file_location('career_model',str(Path(__file__).resolve().parents[1]/'backend/app/personal_model.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 app=FastAPI();m.install(app)
 class MockClient:
  def invoke(self,*a,**kw):return types.SimpleNamespace(content='valid')
 @app.post('/ai')
 def ai():
  m.llm_options();client=m.TrackedClient(MockClient());client.invoke('one');client.invoke('two');return {'ok':True}
 @app.post('/failed')
 def failed():
  m.llm_options();m.TrackedClient(MockClient()).invoke('one');m.mark_failed();return {'fallback':True}
 from starlette.responses import StreamingResponse
 @app.post('/stream')
 def stream():
  async def generate():
   m.llm_options();m.TrackedClient(MockClient()).invoke('one');yield 'data: result\n\n'
  return StreamingResponse(generate(),media_type='text/event-stream')
 with TestClient(app) as client:
  headers={'Authorization':'Bearer u','Idempotency-Key':'first'}
  assert client.post('/ai',headers=headers).status_code==200
  assert m.access_status('u')['free_used']==1
  assert client.post('/ai',headers=headers).status_code==409
  headers['Idempotency-Key']='failed';assert client.post('/failed',headers=headers).status_code==200
  assert m.access_status('u')['free_used']==1
  headers['Idempotency-Key']='stream';assert client.post('/stream',headers=headers).status_code==200
  assert m.access_status('u')['free_used']==2
  headers['Idempotency-Key']='third';assert client.post('/ai',headers=headers).status_code==200
  headers['Idempotency-Key']='fourth';assert client.post('/ai',headers=headers).status_code==409
  assert client.post('/ai').status_code==401
  class VerifyClient:
   def __init__(self,**kw):assert kw['model']=='qwen3.7-flash';assert kw['extra_body']=={'enable_thinking':False}
   def invoke(self,*a):return types.SimpleNamespace(content='OK')
  with patch('langchain_openai.ChatOpenAI',VerifyClient):
   assert client.put('/api/model-settings',json={'provider':'bailian','key':'test-personal'}).status_code==200
  assert 'test-personal' not in client.get('/api/model-settings').text
  headers['Idempotency-Key']='personal';assert client.post('/ai',headers=headers).status_code==200
  assert m.access_status('u')['free_used']==3
 print('PASS FastAPI: multi-call single charge; idempotency; business failure refund; streaming context; cap; anonymous; personal verification/priority/no key echo')
