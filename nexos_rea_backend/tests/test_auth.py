REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"

VALID_USER = {"name": "João", "email": "joao@teste.com", "password": "senha123"}


def _register(client, data=None):
    return client.post(REGISTER_URL, json=data or VALID_USER)


def _login(client, email=VALID_USER["email"], password=VALID_USER["password"]):
    return client.post(LOGIN_URL, json={"email": email, "password": password})


def _token(client):
    _register(client)
    r = _login(client)
    return r.get_json()["data"]["access_token"]


# --- Register ---

def test_register_success(client):
    r = _register(client)
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["email"] == VALID_USER["email"]
    assert data["role"] == "usuario"
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 400
    assert "já cadastrado" in r.get_json()["message"]


def test_register_missing_name(client):
    r = _register(client, {"email": "x@x.com", "password": "123456"})
    assert r.status_code == 400


def test_register_invalid_email(client):
    r = _register(client, {"name": "X", "email": "nao-e-email", "password": "123456"})
    assert r.status_code == 400
    assert "inválido" in r.get_json()["message"]


def test_register_short_password(client):
    r = _register(client, {"name": "X", "email": "x@x.com", "password": "123"})
    assert r.status_code == 400
    assert "senha" in r.get_json()["message"].lower()


# --- Login ---

def test_login_success(client):
    _register(client)
    r = _login(client)
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert "access_token" in data
    assert data["user"]["email"] == VALID_USER["email"]


def test_login_wrong_password(client):
    _register(client)
    r = _login(client, password="senha_errada")
    assert r.status_code == 401
    assert "inválidas" in r.get_json()["message"]


def test_login_unknown_email(client):
    r = _login(client, email="naoexiste@teste.com")
    assert r.status_code == 401


def test_login_missing_fields(client):
    r = client.post(LOGIN_URL, json={})
    assert r.status_code == 401


# --- Me ---

def test_me_authenticated(client):
    token = _token(client)
    r = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.get_json()["data"]["email"] == VALID_USER["email"]


def test_me_without_token(client):
    r = client.get(ME_URL)
    assert r.status_code == 401


def test_me_invalid_token(client):
    r = client.get(ME_URL, headers={"Authorization": "Bearer token.invalido.aqui"})
    assert r.status_code == 422
