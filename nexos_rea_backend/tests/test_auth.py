"""
Tests for the jwt_required decorator (Sprint A: auth migrated to Supabase JWT).
Uses POST /api/reas/ as the protected endpoint under test.
"""
import time

import jwt as pyjwt
import pytest

from tests.conftest import _TEST_JWT_SECRET

REAS_URL = "/api/reas/"

_VALID_REA = {
    "title": "REA de Teste Auth",
    "resource_url": "https://auth-test.com/rea",
    "license": "cc_by",
    "format": "video",
    "subject_area": "Computacao",
    "education_level": "medio",
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _expired_token() -> str:
    now = int(time.time())
    payload = {
        "sub":  "00000000-0000-0000-0000-000000000001",
        "aud":  "authenticated",
        "role": "authenticated",
        "iat":  now - 7200,
        "exp":  now - 3600,
    }
    return pyjwt.encode(payload, _TEST_JWT_SECRET, algorithm="HS256")


# --- jwt_required guard ---

def test_no_token_returns_401(client):
    r = client.post(REAS_URL, json=_VALID_REA)
    assert r.status_code == 401
    assert "ausente" in r.get_json()["message"].lower()


def test_malformed_token_returns_422(client):
    r = client.post(REAS_URL, json=_VALID_REA, headers=_auth("token.invalido.aqui"))
    assert r.status_code == 422
    assert "invalido" in r.get_json()["message"].lower()


def test_expired_token_returns_401(client):
    r = client.post(REAS_URL, json=_VALID_REA, headers=_auth(_expired_token()))
    assert r.status_code == 401
    assert "expirado" in r.get_json()["message"].lower()


def test_valid_token_passes_auth(client, make_token):
    token = make_token()
    r = client.post(REAS_URL, json=_VALID_REA, headers=_auth(token))
    # Auth passed — business logic ran and returned 201
    assert r.status_code == 201


def test_wrong_secret_returns_422(client):
    payload = {
        "sub":  "00000000-0000-0000-0000-000000000002",
        "aud":  "authenticated",
        "role": "authenticated",
        "iat":  int(time.time()),
        "exp":  int(time.time()) + 3600,
    }
    bad_token = pyjwt.encode(payload, "wrong-secret-entirely", algorithm="HS256")
    r = client.post(REAS_URL, json=_VALID_REA, headers=_auth(bad_token))
    assert r.status_code == 422
