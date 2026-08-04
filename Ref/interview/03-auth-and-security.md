# Lesson 3 — Auth and Security

## What this lesson covers

- Password hashing and validation
- JWT access tokens vs opaque refresh tokens
- Refresh-token rotation
- Login rate limiting
- Account management

## Password hashing

File: `backend/app/auth.py`

```python
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

Why bcrypt? It is adaptive: you can increase work factor as CPUs get faster. Storing plain passwords is disqualifying in any interview.

## Password validation

File: `backend/app/auth.py`

Rules:
- ≥ 8 characters
- uppercase, lowercase, number, special character

This is enforced at registration and password reset.

## JWT access tokens

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(user_id: str) -> str:
    return _create_jwt_token(
        user_id, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
```

Access tokens are short-lived (15 minutes). They are used for every authenticated request and WebSocket connection.

## Opaque refresh tokens

```python
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_refresh_token(user_id: str, db: Session) -> str:
    token_value = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(token=token_value, user_id=user_id, expires_at=expires_at)
    db.add(rt)
    db.commit()
    return token_value
```

Refresh tokens are stored in the database, not encoded JWTs. This lets you revoke them.

## Refresh-token rotation

```python
def rotate_refresh_token(refresh_token: str, db: Session):
    # Find old token, unrevoked, not expired
    # Revoke it
    # Issue new access + refresh tokens
    rt.revoked_at = now
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id, db)
```

Rotation means every refresh invalidates the previous refresh token. If a stolen token is used twice, the second attempt fails — a strong signal of token theft.

## Rate limiting

```python
_login_attempts: dict[str, list[datetime]] = {}
_login_lockouts: dict[str, datetime] = {}

def check_rate_limit(identifier: str) -> tuple[bool, int]:
    # 5 failed attempts per 15 minutes → 15-minute lockout
```

Uses in-memory dictionaries. Good for a portfolio project; production would use Redis with a sliding window.

## WebSocket auth

WebSocket connections cannot set custom headers easily, so the JWT is passed as a query parameter:

```python
token = ws.query_params.get("token")
user = authenticate_ws_token(token, db)
```

This is standard for WebSocket; the token is still short-lived and HTTPS/WSS protects it in transit.

## Why this matters in an interview

You can say:

> "I use bcrypt for password hashing, short-lived JWT access tokens (15 minutes), and opaque refresh tokens stored in the database with rotation. If a refresh token is reused after rotation, it is rejected. I also enforce a password policy and rate-limit login attempts to slow brute-force attacks."

## Common trap

**"Why not just use a long-lived JWT?"**

Strong answer: long-lived JWTs cannot be revoked. If leaked, an attacker has access until expiry. Opaque refresh tokens can be revoked in the database, and rotation limits the window of abuse.

## Self-check

1. Why is bcrypt used instead of SHA-256 for passwords?
2. What is the difference between an access token and a refresh token?
3. What is refresh-token rotation and why is it useful?
4. How are WebSocket connections authenticated?
5. What is the rate-limiting policy?

## Code map

| Concept | File |
|---|---|
| Hashing + validation | `backend/app/auth.py` |
| JWT creation/decode | `backend/app/auth.py` |
| Refresh token DB model | `backend/app/models_db.py` |
| Rate limiting | `backend/app/auth.py` |
| Auth REST routes | `backend/app/routers/auth.py` |
| WebSocket auth | `backend/app/ws/queue.py`, `backend/app/ws/duel.py` |
