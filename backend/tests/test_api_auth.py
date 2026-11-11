"""
Kimlik doğrulama, yetkilendirme ve hesap yönetimi uçtan uca testleri
(gerçek FastAPI uygulaması + geçici SQLite).
"""

import pytest

from app.api.routers import auth as auth_router
from app.core.security import create_access_token, create_password_reset_token
from app.db.models import ChatSession, Message, University, User

PREFIX = "/api/v1"
PASSWORD = "dogru-sifre-123"


def _register(client, email="ogrenci@ornek.com", password=PASSWORD, name="Ayşe Öğrenci"):
    return client.post(f"{PREFIX}/auth/register", json={"email": email, "password": password, "full_name": name})


def _login(client, email="ogrenci@ornek.com", password=PASSWORD):
    return client.post(f"{PREFIX}/auth/login", json={"email": email, "password": password})


def _auth_headers(client, email="ogrenci@ornek.com"):
    assert _register(client, email=email).status_code == 201
    token = _login(client, email=email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestRegisterAndLogin:
    def test_register_then_login_returns_a_working_token(self, client):
        assert _register(client).status_code == 201
        response = _login(client)
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"

        me = client.get(f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {body['access_token']}"})
        assert me.status_code == 200
        assert me.json()["email"] == "ogrenci@ornek.com"

    def test_password_is_stored_hashed(self, client, db):
        _register(client)
        user = db.query(User).filter(User.email == "ogrenci@ornek.com").one()
        assert user.hashed_password != PASSWORD
        assert user.hashed_password.startswith("$2")  # bcrypt

    def test_duplicate_email_is_rejected(self, client):
        assert _register(client).status_code == 201
        assert _register(client).status_code == 400

    def test_invalid_email_is_rejected(self, client):
        assert _register(client, email="bu-bir-eposta-degil").status_code == 422

    def test_wrong_password_and_unknown_user_look_identical(self, client):
        _register(client)
        wrong_password = _login(client, password="yanlis")
        unknown_user = _login(client, email="yok@ornek.com")
        assert wrong_password.status_code == unknown_user.status_code == 401
        assert wrong_password.json() == unknown_user.json()  # kullanıcı varlığı sızmaz


class TestProtectedRoutes:
    def test_missing_token_is_rejected(self, client):
        assert client.get(f"{PREFIX}/users/me").status_code in (401, 403)

    def test_invalid_token_is_rejected(self, client):
        response = client.get(f"{PREFIX}/users/me", headers={"Authorization": "Bearer sacma"})
        assert response.status_code == 401

    def test_valid_token_of_a_deleted_user_is_rejected(self, client):
        token = create_access_token({"sub": "99999"})
        response = client.get(f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_regular_user_cannot_use_admin_routes(self, client):
        headers = _auth_headers(client)
        assert client.get(f"{PREFIX}/admin/stats", headers=headers).status_code == 403
        assert client.get(f"{PREFIX}/admin/users", headers=headers).status_code == 403

    def test_anonymous_cannot_use_admin_routes(self, client):
        assert client.get(f"{PREFIX}/admin/stats").status_code in (401, 403)


class TestPasswordReset:
    def test_forgot_password_does_not_reveal_whether_the_email_exists(self, client, monkeypatch):
        sent = []

        async def fake_send(to_email, full_name, token):
            sent.append(to_email)

        monkeypatch.setattr(auth_router, "send_password_reset_email", fake_send)
        _register(client)

        known = client.post(f"{PREFIX}/auth/forgot-password", json={"email": "ogrenci@ornek.com"})
        unknown = client.post(f"{PREFIX}/auth/forgot-password", json={"email": "yok@ornek.com"})

        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()
        assert sent == ["ogrenci@ornek.com"]  # e-posta yalnızca kayıtlı adrese gider

    def test_reset_token_changes_the_password(self, client, db):
        _register(client)
        user_id = db.query(User).one().id
        token = create_password_reset_token(user_id)

        response = client.post(f"{PREFIX}/auth/reset-password", json={"token": token, "new_password": "yeni-sifre-456"})

        assert response.status_code == 200
        assert _login(client, password="yeni-sifre-456").status_code == 200
        assert _login(client, password=PASSWORD).status_code == 401

    def test_invalid_reset_token_is_rejected(self, client):
        response = client.post(f"{PREFIX}/auth/reset-password", json={"token": "sacma", "new_password": "yeni-sifre-456"})
        assert response.status_code == 401

    def test_access_token_cannot_be_used_to_reset_a_password(self, client, db):
        _register(client)
        user_id = db.query(User).one().id
        access = create_access_token({"sub": str(user_id)})

        response = client.post(f"{PREFIX}/auth/reset-password", json={"token": access, "new_password": "yeni-sifre-456"})

        assert response.status_code == 401
        assert _login(client).status_code == 200  # eski şifre hâlâ geçerli

    def test_too_short_new_password_is_rejected(self, client, db):
        _register(client)
        token = create_password_reset_token(db.query(User).one().id)
        response = client.post(f"{PREFIX}/auth/reset-password", json={"token": token, "new_password": "123"})
        assert response.status_code == 422


class TestAccountDeletion:
    def test_deleting_the_account_removes_user_sessions_and_messages(self, client, db):
        headers = _auth_headers(client)
        user = db.query(User).one()
        uni = University(name="Test Üni", slug="test", mevzuat_url="https://ornek.edu.tr")
        db.add(uni)
        db.commit()
        session = ChatSession(user_id=user.id, university_id=uni.id, title="Sohbet")
        db.add(session)
        db.commit()
        db.add_all([
            Message(session_id=session.id, role="user", content="soru"),
            Message(session_id=session.id, role="assistant", content="yanıt"),
        ])
        db.commit()

        assert client.delete(f"{PREFIX}/users/me", headers=headers).status_code == 204

        db.expire_all()
        assert db.query(User).count() == 0
        assert db.query(ChatSession).count() == 0
        assert db.query(Message).count() == 0

    def test_token_stops_working_after_account_deletion(self, client):
        headers = _auth_headers(client)
        client.delete(f"{PREFIX}/users/me", headers=headers)
        assert client.get(f"{PREFIX}/users/me", headers=headers).status_code == 401

    def test_deleting_one_account_does_not_touch_another_users_data(self, client, db):
        headers_a = _auth_headers(client, "a@ornek.com")
        _auth_headers(client, "b@ornek.com")
        user_b = db.query(User).filter(User.email == "b@ornek.com").one()
        session_b = ChatSession(user_id=user_b.id, title="B'nin sohbeti")
        db.add(session_b)
        db.commit()

        client.delete(f"{PREFIX}/users/me", headers=headers_a)

        db.expire_all()
        assert db.query(User).filter(User.email == "b@ornek.com").count() == 1
        assert db.query(ChatSession).filter(ChatSession.user_id == user_b.id).count() == 1
