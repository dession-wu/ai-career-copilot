import secrets
import uuid
import requests
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.services.auth_service import pwd_context
from app.models.wechat_identity import WechatIdentity

def exchange_code(code, settings):
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        raise HTTPException(503, '微信登录尚未配置')
    try:
        response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
            'appid': settings.WECHAT_APP_ID, 'secret': settings.WECHAT_APP_SECRET,
            'js_code': code, 'grant_type': 'authorization_code'}, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout:
        raise HTTPException(504, '微信认证服务超时') from None
    except (requests.RequestException, ValueError):
        raise HTTPException(502, '微信认证服务响应异常') from None
    if not isinstance(payload, dict):
        raise HTTPException(502, '微信认证服务响应异常')
    if payload.get('errcode'):
        raise HTTPException(401 if payload['errcode'] in (40029, 40163, 40226) else 502, '微信登录失败，请重新获取登录凭证')
    openid = payload.get('openid')
    if not isinstance(openid, str) or not openid or len(openid) > 128:
        raise HTTPException(502, '微信认证服务响应异常')
    return openid

def resolve_user(db, app_id, openid):
    def existing():
        return db.query(WechatIdentity).filter_by(app_id=app_id, openid=openid).first()
    identity = existing()
    if identity:
        return db.get(User, identity.user_id)
    ident = uuid.uuid4().hex
    user = User(username='wx_' + ident, email='wx_' + ident + '@example.com', hashed_password=pwd_context.hash(secrets.token_urlsafe(32)))
    try:
        with db.begin_nested():
            db.add(user)
            db.flush()
            db.add(WechatIdentity(app_id=app_id, openid=openid, user_id=user.id))
            db.flush()
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        # The failed savepoint has already rolled back both new records.
        identity = existing()
        if identity:
            return db.get(User, identity.user_id)
        raise



