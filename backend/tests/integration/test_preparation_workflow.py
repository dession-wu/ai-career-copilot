"""Regression coverage for real persistence, export review gates and upload ownership."""
from app.models.career_vault import CareerVault
from app.models.job_application import JobApplication
from app.models.user import User
from app.models.interview_question import InterviewQuestion
from app.routers.vault import processing_status


def setup_materials(db, user):
    vault = CareerVault(user_id=user.id, structured_data={"personal_info": {"name": "测试"}, "_confirmed": True}, version=1)
    job = JobApplication(user_id=user.id, company_name="公司", job_title="工程师", jd_text="Python API", status="preparing")
    db.add_all([vault, job])
    db.commit()
    db.refresh(vault)
    db.refresh(job)
    return vault, job


def test_versions_and_current_content_survive_reload(client, db_session, test_user, auth_headers):
    vault, job = setup_materials(db_session, test_user)
    for text in ["第一份草稿", "修正后的简历"]:
        response = client.post(f"/api/jobs/{job.id}/tailor/versions", headers=auth_headers, json={"content": text, "source_vault_version": vault.version, "source_jd_text": job.jd_text})
        assert response.status_code == 200, response.text
    db_session.expire_all()
    response = client.get(f"/api/jobs/{job.id}", headers=auth_headers)
    assert response.json()["tailored_resume_md"] == "修正后的简历"
    assert len(response.json()["tailored_resume_versions"]) == 2
    assert client.get(f"/api/jobs/{job.id}/export/pdf", headers=auth_headers).status_code == 409


def test_reviewed_version_must_match_current_inputs(client, db_session, test_user, auth_headers):
    vault, job = setup_materials(db_session, test_user)
    payload = {"content": "经过核对的简历", "reviewed": True, "source_vault_version": vault.version, "source_jd_text": job.jd_text}
    assert client.post(f"/api/jobs/{job.id}/tailor/versions", headers=auth_headers, json={**payload, "source_vault_version": 999}).status_code == 409
    assert client.post(f"/api/jobs/{job.id}/tailor/versions", headers=auth_headers, json=payload).status_code == 200
    vault.version += 1
    db_session.commit()
    assert client.get(f"/api/jobs/{job.id}/export/pdf", headers=auth_headers).status_code == 409


def test_export_uses_saved_reviewed_content(client, db_session, test_user, auth_headers, monkeypatch):
    vault, job = setup_materials(db_session, test_user)
    payload = {"content": "最新的已核对版本", "reviewed": True, "source_vault_version": vault.version, "source_jd_text": job.jd_text}
    assert client.post(f"/api/jobs/{job.id}/tailor/versions", headers=auth_headers, json=payload).status_code == 200
    captured = {}
    def generate(**kwargs):
        captured.update(kwargs)
        return {"success": False, "message": "PDF service unavailable"}
    monkeypatch.setattr("app.services.pdf_service.PDFService.generate_pdf", lambda self, **kwargs: generate(**kwargs))
    result = client.get(f"/api/jobs/{job.id}/export/pdf", headers=auth_headers)
    assert result.status_code == 200
    assert result.headers["content-type"].startswith("application/json")
    assert captured["resume_content"] == payload["content"]
    assert result.json()["success"] is False


def test_status_is_validated_and_persisted(client, db_session, test_user, auth_headers):
    _, job = setup_materials(db_session, test_user)
    assert client.put(f"/api/jobs/{job.id}/status", headers=auth_headers, json={"status": "unknown"}).status_code == 400
    assert client.put(f"/api/jobs/{job.id}/status", headers=auth_headers, json={"status": "applied"}).status_code == 200
    assert client.get(f"/api/jobs/{job.id}", headers=auth_headers).json()["status"] == "applied"


def test_upload_status_is_owned_and_retryable(client, db_session, test_user, auth_headers):
    import time
    vault, _ = setup_materials(db_session, test_user)
    processing_status["owned"] = {"user_id": test_user.id, "created_at": time.time(), "status": "completed", "message": "done", "vault_id": vault.id}
    processing_status["foreign"] = {"user_id": "someone-else", "created_at": time.time(), "status": "processing", "message": "busy"}
    try:
        assert client.get("/api/vault/upload-status/foreign", headers=auth_headers).status_code == 404
        for _ in range(2):
            result = client.get("/api/vault/upload-status/owned", headers=auth_headers)
            assert result.status_code == 200
            assert result.json()["vault"]["id"] == vault.id
    finally:
        processing_status.pop("owned", None)
        processing_status.pop("foreign", None)


def test_existing_interview_questions_cannot_be_read_by_other_user(client, db_session, test_user, auth_headers):
    other = User(username="anotheruser", email="other@example.com", hashed_password="not-a-login-hash")
    db_session.add(other)
    db_session.flush()
    _, job = setup_materials(db_session, other)
    db_session.add(InterviewQuestion(application_id=job.id, question_text="private question"))
    db_session.commit()
    assert client.get(f"/api/interview/jobs/{job.id}/interview-prep", headers=auth_headers).status_code == 404


def test_two_accounts_cannot_access_or_modify_each_others_materials(client, db_session, test_user, auth_headers):
    from app.services.wechat_service import resolve_user
    other = resolve_user(db_session, 'permission-app', 'permission-openid')
    vault, job = setup_materials(db_session, other)
    own_vault, own_job = setup_materials(db_session, test_user)
    original = dict(vault.structured_data)
    # Vault endpoints select by bearer identity, ignoring attempted ownership injection.
    response = client.get('/api/vault', headers=auth_headers)
    assert response.status_code == 200
    assert response.json()['id'] == own_vault.id
    assert client.put('/api/vault', headers=auth_headers, json={'user_id': other.id, 'id': vault.id, 'structured_data':{'_confirmed':True, 'personal_info':{'name':'attacker'}}}).status_code == 200
    db_session.refresh(vault)
    assert vault.structured_data == original
    attempts = [
        ('GET', f'/api/jobs/{job.id}', None),
        ('PUT', f'/api/jobs/{job.id}', {'job_title':'attacker'}),
        ('PUT', f'/api/jobs/{job.id}/status', {'status':'applied'}),
        ('GET', f'/api/jobs/{job.id}/tailor/versions', None),
        ('POST', f'/api/jobs/{job.id}/tailor/versions', {'content':'attacker','reviewed':True,'source_vault_version':vault.version,'source_jd_text':job.jd_text}),
        ('GET', f'/api/jobs/{job.id}/export/pdf', None),
        ('DELETE', f'/api/jobs/{job.id}', None),
    ]
    for method, path, payload in attempts:
        result = client.request(method, path, headers=auth_headers, json=payload)
        assert result.status_code in (403,404), (method, path, result.text)
    assert client.delete('/api/vault', headers=auth_headers).status_code == 204
    db_session.expire_all()
    assert db_session.get(CareerVault, vault.id) is not None
    untouched = db_session.get(JobApplication, job.id)
    assert untouched.job_title == '工程师'
    assert untouched.status == 'preparing'
    assert not untouched.tailored_resume_versions
