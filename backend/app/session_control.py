"""Persist revocations on D-mounted private storage. No raw tokens are stored."""
import hashlib
import os
import sqlite3
import time
from pathlib import Path
from fastapi.responses import JSONResponse

ROOT=Path(os.environ.get('MODEL_DATA_DIR','/app/private'))
ROOT.mkdir(parents=True,exist_ok=True)
DB=ROOT/'sessions.sqlite'
with sqlite3.connect(DB) as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS revoked(id TEXT PRIMARY KEY,expires REAL NOT NULL)')

def identity(token,payload):
    return hashlib.sha256(str(payload.get('sid') or token).encode()).hexdigest()

def is_revoked(token,payload):
    with sqlite3.connect(DB) as conn:
        return conn.execute('SELECT 1 FROM revoked WHERE id=? AND expires>?',(identity(token,payload),time.time())).fetchone() is not None

def install(app,prefix,decode):
    @app.middleware('http')
    async def session_logout(request,call_next):
        if request.method=='POST' and request.url.path==prefix+'/auth/logout':
            token=request.headers.get('authorization','').removeprefix('Bearer ')
            payload=decode(token)
            if not payload:return JSONResponse({'detail':'请重新登录。'},status_code=401)
            with sqlite3.connect(DB) as conn:
                conn.execute('DELETE FROM revoked WHERE expires<?',(time.time(),))
                conn.execute('INSERT OR REPLACE INTO revoked VALUES(?,?)',(identity(token,payload),time.time()+90*86400))
            return JSONResponse({'message':'已退出登录。'},headers={'Cache-Control':'no-store'})
        return await call_next(request)
