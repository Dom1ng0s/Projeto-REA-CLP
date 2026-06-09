import pytest

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REAS_URL = "/api/reas/"
RECOMENDACOES_URL = "/api/recomendacoes/"

_USER_A = {"name": "Ana", "email": "ana@s4.com", "password": "senha123"}
_USER_B = {"name": "Bruno", "email": "bruno@s4.com", "password": "senha123"}

_TAG_PYTHON = 1
_TAG_ALGEBRA = 2

_REA_PYTHON = {
    "title": "Python para Todos",
    "description": "Curso introdutório de Python.",
    "url": "https://s4.com/python",
    "license": "CC BY 4.0",
    "resource_type": "course",
}
_REA_ALGEBRA = {
    "title": "Álgebra Linear Aplicada",
    "description": "Material completo de álgebra linear.",
    "url": "https://s4.com/algebra",
    "license": "CC BY-SA 4.0",
    "resource_type": "ebook",
}


# --- helpers ---

def _register_and_login(client, user):
    client.post(REGISTER_URL, json=user)
    r = client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.get_json()["data"]["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _submit(client, token, rea):
    return client.post(REAS_URL, json=rea, headers=_auth(token)).get_json()["data"]


def _tag_rea(client, token, rea_id, tag_ids):
    return client.post(f"{REAS_URL}{rea_id}/tags", json={"tag_ids": tag_ids}, headers=_auth(token))


def _set_interests(client, token, interesses):
    return client.put("/api/perfil/interesses", json={"interesses": interesses}, headers=_auth(token))


# --- Avaliações ---

def test_avaliar_rea_success(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 5}, headers=_auth(token))
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["score"] == 5
    assert data["avg_rating"] == 5.0


def test_avaliar_rea_score_invalido(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 6}, headers=_auth(token))
    assert r.status_code == 400


def test_avaliar_rea_atualiza_media(client):
    token_a = _register_and_login(client, _USER_A)
    token_b = _register_and_login(client, _USER_B)
    rea = _submit(client, token_a, _REA_PYTHON)
    client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 4}, headers=_auth(token_a))
    r = client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 2}, headers=_auth(token_b))
    assert r.status_code == 201
    assert r.get_json()["data"]["avg_rating"] == 3.0
    assert r.get_json()["data"]["rating_count"] == 2


# --- Visualização ---

def test_registrar_visualizacao(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/visualizacao", headers=_auth(token))
    assert r.status_code == 200


def test_visualizacao_sem_token(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/visualizacao")
    assert r.status_code == 401


# --- Classificação de REAs por tags ---

def test_classificar_rea_success(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    client.post("/api/perfil/interesses", json={"interesses": [{"tag_id": _TAG_PYTHON, "weight": 1.0}]})

    from src.extensions.database import db
    from src.models.models import Tag
    with client.application.app_context():
        if not db.session.get(Tag, _TAG_PYTHON):
            db.session.add(Tag(id=_TAG_PYTHON, name="Python", slug="python"))
            db.session.commit()

    r = _tag_rea(client, token, rea["id"], [_TAG_PYTHON])
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert any(t["tag_id"] == _TAG_PYTHON for t in data["tags"])


def test_classificar_rea_tag_inexistente(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    r = _tag_rea(client, token, rea["id"], [9999])
    assert r.status_code == 404


def test_classificar_rea_sem_tags(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)
    r = _tag_rea(client, token, rea["id"], [])
    assert r.status_code == 400


# --- Recálculo de pesos ---

def test_peso_aumenta_ao_adicionar_colecao(client):
    from src.extensions.database import db
    from src.models.models import Tag, UserTagInterest

    token = _register_and_login(client, _USER_A)
    rea = _submit(client, token, _REA_PYTHON)

    with client.application.app_context():
        if not db.session.get(Tag, _TAG_PYTHON):
            db.session.add(Tag(id=_TAG_PYTHON, name="Python", slug="python"))
            db.session.commit()

    _tag_rea(client, token, rea["id"], [_TAG_PYTHON])

    col = client.post("/api/colecoes/", json={"name": "Minha Coleção"}, headers=_auth(token)).get_json()["data"]
    client.post(f"/api/colecoes/{col['id']}/items", json={"rea_id": rea["id"]}, headers=_auth(token))

    token_resp = client.post(LOGIN_URL, json={"email": _USER_A["email"], "password": _USER_A["password"]})
    user_id = token_resp.get_json()["data"]["user"]["id"]

    with client.application.app_context():
        import uuid
        interest = db.session.get(UserTagInterest, (uuid.UUID(user_id), _TAG_PYTHON))
        assert interest is not None
        assert interest.weight > 1.0


# --- Motor de recomendação ---

def test_recomendacoes_sem_perfil_retorna_lista(client):
    token = _register_and_login(client, _USER_A)
    r = client.get(RECOMENDACOES_URL, headers=_auth(token))
    assert r.status_code == 200
    assert isinstance(r.get_json()["data"], list)


def test_recomendacoes_sem_token(client):
    r = client.get(RECOMENDACOES_URL)
    assert r.status_code == 401


def test_recomendacoes_com_perfil_retorna_score(client):
    from src.extensions.database import db
    from src.models.models import Tag

    token = _register_and_login(client, _USER_A)

    with client.application.app_context():
        for tid, name, slug in [(_TAG_PYTHON, "Python", "python"), (_TAG_ALGEBRA, "Álgebra", "algebra")]:
            if not db.session.get(Tag, tid):
                db.session.add(Tag(id=tid, name=name, slug=slug))
        db.session.commit()

    rea_py = _submit(client, token, _REA_PYTHON)
    rea_al = _submit(client, token, _REA_ALGEBRA)
    _tag_rea(client, token, rea_py["id"], [_TAG_PYTHON])
    _tag_rea(client, token, rea_al["id"], [_TAG_ALGEBRA])

    _set_interests(client, token, [
        {"tag_id": _TAG_PYTHON, "weight": 5.0},
        {"tag_id": _TAG_ALGEBRA, "weight": 1.0},
    ])

    r = client.get(RECOMENDACOES_URL, headers=_auth(token))
    assert r.status_code == 200
    items = r.get_json()["data"]
    assert len(items) >= 2
    assert "relevance_score" in items[0]
    assert items[0]["relevance_score"] >= items[1]["relevance_score"]
    assert items[0]["title"] == _REA_PYTHON["title"]
