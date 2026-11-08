from unittest.mock import patch
import pytest
from fastapi import HTTPException
from app.services.wechat_service import exchange_code, resolve_user
from app.config import Settings

def test_identity_isolation(db_session):
    a = resolve_user(db_session, 'app', 'openid')
    assert resolve_user(db_session, 'app', 'openid').id == a.id
    assert resolve_user(db_session, 'other', 'openid').id != a.id
    assert resolve_user(db_session, 'app', 'other').id != a.id

@pytest.mark.parametrize('payload,status', [({'errcode':40029},401), ({},502), ({'openid':'x','session_key':'secret'},200)])
def test_exchange(payload,status):
    settings = Settings(SECRET_KEY='test', WECHAT_APP_ID='app', WECHAT_APP_SECRET='secret')
    with patch('app.services.wechat_service.requests.get') as get:
        get.return_value.json.return_value = payload
        if status == 200:
            assert exchange_code('code', settings) == 'x'
        else:
            with pytest.raises(HTTPException) as error: exchange_code('code', settings)
            assert error.value.status_code == status

def test_missing_configuration():
    with pytest.raises(HTTPException) as error:
        exchange_code('code', Settings(SECRET_KEY='test', WECHAT_APP_ID='', WECHAT_APP_SECRET=''))
    assert error.value.status_code == 503

@pytest.mark.parametrize('code', ['', ' ', 'x y', 'x'*513, 123, None])
def test_invalid_payload(client, code):
    assert client.post('/api/auth/wechat', json={'code':code}).status_code == 422

def test_timeout():
    import requests
    with patch('app.services.wechat_service.requests.get', side_effect=requests.Timeout('private')):
        with pytest.raises(HTTPException) as error:
            exchange_code('code', Settings(SECRET_KEY='test', WECHAT_APP_ID='app', WECHAT_APP_SECRET='secret'))
        assert error.value.status_code == 504
        assert 'private' not in str(error.value.detail)

def test_login_and_me(client, monkeypatch):
    monkeypatch.setattr('app.routers.auth.exchange_code', lambda code, settings: 'stable-openid')
    monkeypatch.setattr('app.routers.auth.get_settings', lambda: Settings(SECRET_KEY='test', WECHAT_APP_ID='app'))
    token = client.post('/api/auth/wechat', json={'code':'fresh'}).json()['access_token']
    response = client.get('/api/auth/me', headers={'Authorization':f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json()['email'].endswith('@example.com')

def test_unique_race_recovery(db_session, monkeypatch):
    from app.models.user import User
    from app.models.wechat_identity import WechatIdentity
    winner = resolve_user(db_session, 'race-app', 'race-openid')
    initial_count = db_session.query(User).count()
    original_query = db_session.query
    count = 0
    def query(model):
        nonlocal count
        result = original_query(model)
        if model is WechatIdentity:
            count += 1
            if count == 1:
                from unittest.mock import Mock
                hidden = Mock()
                hidden.filter_by.return_value.first.return_value = None
                return hidden
        return result
    monkeypatch.setattr(db_session, 'query', query)
    assert resolve_user(db_session, 'race-app', 'race-openid').id == winner.id
    assert db_session.query(User).count() == initial_count


def test_wechat_password_login_is_rejected(client, db_session):
    user = resolve_user(db_session, 'password-app', 'password-openid')
    response = client.post('/api/auth/login', data={'username':user.username, 'password':'arbitrary-password'})
    assert response.status_code == 401



def test_exchange_does_not_log_credentials(caplog):
    import logging
    import requests
    settings = Settings(SECRET_KEY='test', WECHAT_APP_ID='public-app', WECHAT_APP_SECRET='private-wechat-secret')
    with caplog.at_level(logging.INFO):
        with patch('app.services.wechat_service.requests.get') as get:
            get.return_value.json.return_value = {'openid':'identity', 'session_key':'private-session-key'}
            assert exchange_code('private-login-code', settings) == 'identity'
            assert get.call_args.kwargs['timeout'] == 10.0
        with patch('app.services.wechat_service.requests.get', side_effect=requests.ConnectionError('private-wechat-secret private-login-code')):
            with pytest.raises(HTTPException) as error:
                exchange_code('private-login-code', settings)
            assert error.value.status_code == 502
            assert 'private' not in error.value.detail
    assert 'private-wechat-secret' not in caplog.text
    assert 'private-login-code' not in caplog.text
    assert 'private-session-key' not in caplog.text
