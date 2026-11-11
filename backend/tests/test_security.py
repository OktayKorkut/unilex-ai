from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_access_token,
    hash_password,
    verify_password,
    verify_password_reset_token,
)


class TestPasswordHashing:
    def test_hash_is_not_the_plain_password(self):
        assert hash_password("gizli-sifre") != "gizli-sifre"

    def test_correct_password_verifies(self):
        hashed = hash_password("gizli-sifre")
        assert verify_password("gizli-sifre", hashed) is True

    def test_wrong_password_is_rejected(self):
        hashed = hash_password("gizli-sifre")
        assert verify_password("yanlis-sifre", hashed) is False

    def test_same_password_gets_different_hashes(self):
        # Her hash kendi rastgele salt'ını taşır
        assert hash_password("ayni") != hash_password("ayni")

    def test_unicode_password_roundtrip(self):
        hashed = hash_password("şifreÇığ123")
        assert verify_password("şifreÇığ123", hashed) is True
        assert verify_password("sifreCig123", hashed) is False


class TestAccessToken:
    def test_roundtrip_keeps_claims(self):
        token = create_access_token({"sub": "42", "email": "a@b.com"})
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["email"] == "a@b.com"

    def test_token_has_expiry_in_the_future(self):
        payload = decode_access_token(create_access_token({"sub": "1"}))
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_tampered_token_is_rejected(self):
        token = create_access_token({"sub": "1"})
        assert decode_access_token(token[:-2] + "xx") is None

    def test_garbage_is_rejected(self):
        assert decode_access_token("bu-bir-token-degil") is None

    def test_token_signed_with_another_key_is_rejected(self):
        forged = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "baska-bir-anahtar",
            algorithm=settings.ALGORITHM,
        )
        assert decode_access_token(forged) is None

    def test_expired_token_is_rejected(self, monkeypatch):
        monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
        assert decode_access_token(create_access_token({"sub": "1"})) is None


class TestPasswordResetToken:
    def test_roundtrip_returns_user_id(self):
        assert verify_password_reset_token(create_password_reset_token(7)) == 7

    def test_access_token_cannot_reset_a_password(self):
        # Erişim token'ı "pwd_reset" tipini taşımaz, şifre sıfırlamada geçersizdir
        assert verify_password_reset_token(create_access_token({"sub": "7"})) is None

    def test_expired_reset_token_is_rejected(self, monkeypatch):
        monkeypatch.setattr(settings, "RESET_TOKEN_EXPIRE_MINUTES", -1)
        assert verify_password_reset_token(create_password_reset_token(7)) is None

    def test_garbage_is_rejected(self):
        assert verify_password_reset_token("sacma") is None
