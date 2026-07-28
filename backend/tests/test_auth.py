import time
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from jose import jwt

from app.auth import ALGORITHM, SECRET_KEY
from app.main import app

client = TestClient(app)


def _unique(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_register_and_login():
    username = _unique("auth")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data

    res = client.post(
        "/auth/login",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 200
    login_data = res.json()
    assert "access_token" in login_data


def test_login_invalid_password():
    username = _unique("badpass")
    res = client.post("/auth/register", json={"username": username, "password": "StrongPass1!"})
    assert res.status_code == 201
    res = client.post(
        "/auth/login",
        json={"username": username, "password": "WrongPass1!"},
    )
    assert res.status_code == 401


def test_weak_password_rejected():
    username = _unique("weak")
    # Too short triggers Pydantic validation
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "weak"},
    )
    assert res.status_code == 422

    # Long enough but missing complexity
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "password1234"},
    )
    assert res.status_code == 400


def test_refresh_token_rotation():
    username = _unique("refresh")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    refresh = res.json()["refresh_token"]

    res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    refresh_data = res.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data

    # Old refresh token should be invalid
    res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 401


def test_rate_limit_lockout():
    username = _unique("ratelimit")
    res = client.post("/auth/register", json={"username": username, "password": "StrongPass1!"})
    assert res.status_code == 201

    final_status = None
    for _ in range(6):
        res = client.post(
            "/auth/login",
            json={"username": username, "password": "WrongPass1!"},
        )
        final_status = res.status_code

    # After 6 failed attempts, should be rate limited
    assert final_status == 429


def test_password_reset_flow():
    username = _unique("reset")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201

    res = client.post("/auth/password-reset-request", json={"username": username})
    assert res.status_code == 200
    token = res.json()["token"]

    res = client.post(
        "/auth/password-reset",
        json={"token": token, "new_password": "NewStrongPass2!"},
    )
    assert res.status_code == 200

    res = client.post(
        "/auth/login", json={"username": username, "password": "NewStrongPass2!"}
    )
    assert res.status_code == 200


def test_duplicate_username_rejected():
    username = _unique("dup")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201

    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 409


def test_account_deletion_requires_password():
    username = _unique("delete")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    access = res.json()["access_token"]

    res = client.request(
        "DELETE",
        "/auth/me",
        headers={"Authorization": f"Bearer {access}"},
        json={"password": "WrongPass1!"},
    )
    assert res.status_code == 401

    res = client.request(
        "DELETE",
        "/auth/me",
        headers={"Authorization": f"Bearer {access}"},
        json={"password": "StrongPass1!"},
    )
    assert res.status_code == 200

    res = client.post(
        "/auth/login", json={"username": username, "password": "StrongPass1!"}
    )
    assert res.status_code == 401


def test_change_password():
    username = _unique("change")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    access = res.json()["access_token"]

    res = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {access}"},
        json={"current_password": "StrongPass1!", "new_password": "NewStrongPass2!"},
    )
    assert res.status_code == 200

    res = client.post(
        "/auth/login", json={"username": username, "password": "NewStrongPass2!"}
    )
    assert res.status_code == 200


def test_logout_all_revokes_refresh():
    username = _unique("logoutall")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    access = res.json()["access_token"]
    refresh = res.json()["refresh_token"]

    res = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert res.status_code == 200

    res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 401


def test_access_token_expiry_short():
    username = _unique("access")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    access = res.json()["access_token"]
    payload = jwt.get_unverified_claims(access)
    assert "exp" in payload
    assert 0 < payload["exp"] - time.time() <= 20 * 60


def test_refresh_token_expiry_long():
    from app.database import SessionLocal
    from app.models_db import RefreshToken

    username = _unique("refresh_exp")
    res = client.post(
        "/auth/register",
        json={"username": username, "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    refresh = res.json()["refresh_token"]
    db = SessionLocal()
    try:
        token_record = db.query(RefreshToken).filter(RefreshToken.token == refresh).first()
        assert token_record is not None
        assert token_record.expires_at is not None
        ttl = (token_record.expires_at - datetime.utcnow()).total_seconds()
        assert 6 * 24 * 60 * 60 < ttl <= 8 * 24 * 60 * 60
    finally:
        db.close()
