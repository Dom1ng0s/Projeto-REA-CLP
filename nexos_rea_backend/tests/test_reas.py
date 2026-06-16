REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REAS_URL = "/api/reas/"

_VALID_USER = {"name": "Ana", "email": "ana@teste.com", "password": "senha123"}

_VALID_REA = {
    "title": "Introdução ao Python",
    "description": "Curso gratuito para iniciantes com exercícios.",
    "url": "https://exemplo.com/python",
    "license": "CC BY 4.0",
    "resource_type": "course",
}


def _token(client):
    client.post(REGISTER_URL, json=_VALID_USER)
    r = client.post(LOGIN_URL, json={"email": _VALID_USER["email"], "password": _VALID_USER["password"]})
    return r.get_json()["data"]["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _submit(client, token, data=None):
    return client.post(REAS_URL, json=data or _VALID_REA, headers=_auth(token))


# --- Listagem e busca ---

def test_list_reas_empty(client):
    r = client.get(REAS_URL)
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["items"] == []
    assert data["pagination"]["total"] == 0


def test_list_reas_with_results(client):
    token = _token(client)
    _submit(client, token)
    r = client.get(REAS_URL)
    assert r.status_code == 200
    assert r.get_json()["data"]["pagination"]["total"] == 1


def test_search_by_title(client):
    token = _token(client)
    _submit(client, token)
    _submit(client, token, {**_VALID_REA, "title": "Álgebra Linear", "url": "https://x.com/2"})
    r = client.get(f"{REAS_URL}?q=python")
    assert r.status_code == 200
    items = r.get_json()["data"]["items"]
    assert len(items) == 1
    assert "Python" in items[0]["title"]


def test_search_no_results(client):
    r = client.get(f"{REAS_URL}?q=termoqueNaoExiste")
    assert r.status_code == 200
    assert r.get_json()["data"]["pagination"]["total"] == 0


def test_pagination(client):
    token = _token(client)
    for i in range(5):
        _submit(client, token, {**_VALID_REA, "title": f"REA {i}", "url": f"https://x.com/{i}"})
    r = client.get(f"{REAS_URL}?page=1&per_page=3")
    data = r.get_json()["data"]
    assert len(data["items"]) == 3
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["pages"] == 2


# --- Detalhe ---

def test_get_rea_by_id(client):
    token = _token(client)
    created = _submit(client, token).get_json()["data"]
    r = client.get(f"{REAS_URL}{created['id']}")
    assert r.status_code == 200
    assert r.get_json()["data"]["id"] == created["id"]


def test_get_rea_not_found(client):
    r = client.get(f"{REAS_URL}00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_get_rea_invalid_id(client):
    r = client.get(f"{REAS_URL}id-invalido")
    assert r.status_code == 404


# --- Submissão ---

def test_submit_rea_success(client):
    token = _token(client)
    r = _submit(client, token)
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["title"] == _VALID_REA["title"]
    assert data["avg_rating"] == 0.0


def test_submit_rea_without_token(client):
    r = client.post(REAS_URL, json=_VALID_REA)
    assert r.status_code == 401


def test_submit_rea_missing_title(client):
    token = _token(client)
    r = _submit(client, token, {**_VALID_REA, "title": ""})
    assert r.status_code == 400


def test_submit_rea_invalid_type(client):
    token = _token(client)
    r = _submit(client, token, {**_VALID_REA, "resource_type": "tipo_invalido"})
    assert r.status_code == 400
    assert "Tipo invalido" in r.get_json()["message"]


def test_submit_rea_duplicate_url(client):
    token = _token(client)
    _submit(client, token)
    r = _submit(client, token)
    assert r.status_code == 400
    assert "URL" in r.get_json()["message"]
