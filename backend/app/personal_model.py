"""Private per-user model credentials; never fall back to a server key."""
import hashlib
import os
import sqlite3
from contextlib import contextmanager, closing
from contextvars import ContextVar
from pathlib import Path
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.auth import get_current_user as get_current_active_user
from app.database import SessionLocal
from app.services.auth_service import AuthService

ROOT=Path(os.environ.get('MODEL_DATA_DIR','/app/private'))
ROOT.mkdir(parents=True,exist_ok=True)
path=ROOT/'model-encryption.key'
if not path.exists():
    with path.open('xb') as stream:stream.write(Fernet.generate_key())
    path.chmod(0o600)
BOX=Fernet(path.read_bytes())
with closing(sqlite3.connect(ROOT/'models.sqlite')) as conn, conn:
    conn.execute('CREATE TABLE IF NOT EXISTS configs(user_id TEXT PRIMARY KEY,provider TEXT NOT NULL,key TEXT NOT NULL)')
CURRENT=ContextVar('novel_model_user',default=None)
router=APIRouter()

def config(user_id):
    with closing(sqlite3.connect(ROOT/'models.sqlite')) as conn, conn:
        return conn.execute('SELECT provider,key FROM configs WHERE user_id=?',(user_id,)).fetchone()

class ModelConfig(BaseModel):
    provider:str=Field(pattern='^(bailian|deepseek|openai)$')
    key:str=Field(min_length=1,max_length=512)

@router.get('/model-settings')
def get_model(current=Depends(get_current_active_user)):
    value=config(current.id)
    return {**access_status(current.id), 'configured':bool(value),'provider':value[0] if value else 'bailian'}

@router.put('/model-settings')
def save_model(body:ModelConfig,current=Depends(get_current_active_user)):
    if not body.key.strip():raise HTTPException(422,'请输入有效的 Key')
    try:
        from langchain_openai import ChatOpenAI
        options=provider_options(body.provider,body.key.strip())
        client=ChatOpenAI(**options,timeout=20,max_retries=0,max_tokens=8,
            extra_body={'enable_thinking':False} if body.provider=='bailian' else {})
        result=client.invoke('Reply OK')
        if not str(result.content).strip():raise ValueError('empty')
    except Exception:
        raise HTTPException(422,'个人 Key 验证失败，请检查地域、余额和模型权限。不会消耗平台免费次数。')
    with closing(sqlite3.connect(ROOT/'models.sqlite')) as conn, conn:
        conn.execute('INSERT OR REPLACE INTO configs VALUES(?,?,?)',(current.id,body.provider,BOX.encrypt(body.key.strip().encode()).decode()))
    return {'configured':True,'provider':body.provider}

@router.delete('/model-settings')
def delete_model(current=Depends(get_current_active_user)):
    with closing(sqlite3.connect(ROOT/'models.sqlite')) as conn, conn:conn.execute('DELETE FROM configs WHERE user_id=?',(current.id,))
    return {'configured':False}

def personal_config():
    user_id=CURRENT.get()
    value=config(user_id) if user_id is not None else None
    if not value:raise HTTPException(409,'请先在设置中配置自己的 API Key。')
    provider,encrypted=value
    return user_id,provider,BOX.decrypt(encrypted.encode()).decode(),hashlib.sha256(encrypted.encode()).hexdigest()

def install(app):
    app.include_router(router,prefix='/api',tags=['personal model'])
    @app.middleware('http')
    async def model_scope(request,call_next):
        user_id=None
        token=request.headers.get('authorization','')
        if token.startswith('Bearer '):
            with SessionLocal() as session:
                service=AuthService(session)
                name=service.verify_token(token[7:])
                current=service.get_user_by_username(name) if name else None
                if current:user_id=current.id
        scope=CURRENT.set(user_id)
        operation={'id':request.headers.get('Idempotency-Key') or __import__('uuid').uuid4().hex,
                   'fingerprint':hashlib.sha256((request.method+request.url.path+'?'+request.url.query).encode()+await request.body()).hexdigest(),
                   'reserved':False,'valid':False,'user':user_id}
        op_scope=OPERATION.set(operation)
        try:
            response=await call_next(request)
            original=response.body_iterator
            async def finish():
                stream_user=CURRENT.set(user_id)
                stream_op=OPERATION.set(operation)
                try:
                    async for chunk in original: yield chunk
                finally:
                    settle(operation, response.status_code < 400 and operation['valid'] and not operation.get('failed'))
                    OPERATION.reset(stream_op)
                    CURRENT.reset(stream_user)
            response.body_iterator=finish()
            return response
        except AccessDenied as error:
            from starlette.responses import JSONResponse
            settle(operation,False)
            return JSONResponse({'detail':error.detail,'code':error.code},status_code=error.status)
        except Exception:
            settle(operation,False)
            raise
        finally:
            OPERATION.reset(op_scope)
            CURRENT.reset(scope)

def llm_options():
    user_id=CURRENT.get()
    if user_id is None: raise AccessDenied(401,'authentication_required','请先登录后使用 AI。')
    value=config(user_id)
    if value:
        provider,encrypted=value
        key=BOX.decrypt(encrypted.encode()).decode()
        return provider_options(provider,key)
    key=platform_key()
    if not key: raise AccessDenied(503,'platform_unconfigured','平台 AI 尚未配置，请稍后重试或配置个人 Key。')
    reserve(OPERATION.get())
    return provider_options('bailian',key)


def provider_options(provider,key):
    return {'api_key':key,'model': 'qwen3.7-flash' if provider=='bailian' else ('deepseek-chat' if provider=='deepseek' else 'gpt-4o-mini'),
            'base_url':'https://dashscope.aliyuncs.com/compatible-mode/v1' if provider=='bailian' else ('https://api.deepseek.com' if provider=='deepseek' else 'https://api.openai.com/v1')}

class AccessDenied(HTTPException):
    def __init__(self,status,code,detail):
        super().__init__(status,detail)
        self.status=status
        self.code=code

OPERATION=ContextVar('career_llm_operation',default=None)

def platform_key():
    key=os.environ.get('BAILIAN_API_KEY','').strip()
    if key:return key
    filename=os.environ.get('BAILIAN_API_KEY_FILE','')
    if not filename and os.name=='nt':
        default=Path(r'E:\podnotes\podnotes-server\config\ops-secrets\bailian-secret.bin')
        if default.is_file():filename=str(default)
    if not filename:return ''
    if os.name!='nt':raise AccessDenied(503,'platform_unconfigured','DPAPI 密钥文件仅支持 Windows，容器请注入 BAILIAN_API_KEY。')
    import ctypes
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_=[('length',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_char))]
    raw=Path(filename).read_bytes()
    buf=ctypes.create_string_buffer(raw)
    source=Blob(len(raw),ctypes.cast(buf,ctypes.POINTER(ctypes.c_char)))
    output=Blob()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(output)):
        raise AccessDenied(503,'platform_unconfigured','平台密钥文件无法解密。')
    try:return ctypes.string_at(output.data,output.length).decode().strip()
    finally:ctypes.windll.kernel32.LocalFree(output.data)

@contextmanager
def ledger():
    conn=sqlite3.connect(ROOT/'usage.sqlite',timeout=30)
    conn.execute('CREATE TABLE IF NOT EXISTS operations(owner TEXT,id TEXT,fingerprint TEXT,state TEXT,pid INTEGER,PRIMARY KEY(owner,id))')
    try:
        with conn: yield conn
    finally:conn.close()

def access_status(user_id):
    with ledger() as conn:
        used=conn.execute("SELECT count(*) FROM operations WHERE owner=? AND state='succeeded'",(str(user_id),)).fetchone()[0]
        pending=conn.execute("SELECT count(*) FROM operations WHERE owner=? AND state='running'",(str(user_id),)).fetchone()[0]
    return {'model':'qwen3.7-flash','free_limit':3,'free_used':used,'free_reserved':pending,'free_remaining':max(0,3-used-pending),'platform_configured':bool(os.environ.get('BAILIAN_API_KEY') or os.environ.get('BAILIAN_API_KEY_FILE') or (os.name=='nt' and Path(r'E:\podnotes\podnotes-server\config\ops-secrets\bailian-secret.bin').is_file()))}

def reserve(op):
    if not op or op['user'] is None:raise AccessDenied(401,'authentication_required','请登录后使用 AI。')
    if op['reserved']:return
    owner=str(op['user'])
    with ledger() as conn:
        conn.execute('BEGIN IMMEDIATE')
        rows=conn.execute("SELECT owner,id,pid FROM operations WHERE state='running'").fetchall()
        for old_owner,old_id,pid in rows:
            try:os.kill(pid,0)
            except ProcessLookupError:conn.execute("UPDATE operations SET state='failed' WHERE owner=? AND id=?",(old_owner,old_id))
            except PermissionError:pass
        row=conn.execute('SELECT fingerprint,state FROM operations WHERE owner=? AND id=?',(owner,op['id'])).fetchone()
        if row:
            if row[0]!=op['fingerprint']:raise AccessDenied(409,'idempotency_conflict','操作 ID 与请求不匹配。')
            if row[1]!='failed':raise AccessDenied(409,'operation_exists','该 AI 操作已处理或处理中，请查看已有结果。')
        count=conn.execute("SELECT count(*) FROM operations WHERE owner=? AND state IN ('running','succeeded')",(owner,)).fetchone()[0]
        if count>=3:raise AccessDenied(409,'personal_key_required','累计 3 次免费 AI 已用完或处理中，请在设置中配置个人百炼 Key。')
        conn.execute('INSERT OR REPLACE INTO operations VALUES(?,?,?,?,?)',(owner,op['id'],op['fingerprint'],'running',os.getpid()))
    op['reserved']=True

def settle(op,success):
    if not op['reserved']:return
    with ledger() as conn:conn.execute("UPDATE operations SET state=? WHERE owner=? AND id=? AND state='running'",('succeeded' if success else 'failed',str(op['user']),op['id']))

class TrackedClient:
    def __init__(self,client):self.client=client;self.operation=OPERATION.get()
    def invoke(self,*args,**kwargs):
        if self.operation:self.operation['failed']=False
        response=self.client.invoke(*args,**kwargs)
        if self.operation and str(getattr(response,'content','')).strip():self.operation['valid']=True
        return response
    def __getattr__(self,name):return getattr(self.client,name)


def mark_failed():
    operation=OPERATION.get()
    if operation:operation['failed']=True
