"""
Sprint 4 — Avaliações, Visualizações, Tags e Recomendações.
Auth via make_token fixture (Supabase JWT); all DB triggers skipped.
"""
import pytest

REAS_URL          = "/api/reas/"
RECOMENDACOES_URL = "/api/recomendacoes/"

_REA_PYTHON = {
    "title":           "Python para Todos",
    "description":     "Curso introdutorio de Python.",
    "resource_url":    "https://s4.com/python",
    "license":         "CC BY 4.0",
    "format":          "video",
    "subject_area":    "Computacao",
    "education_level": "ensino_medio",
}
_REA_ALGEBRA = {
    "title":           "Algebra Linear Aplicada",
    "description":     "Material completo de algebra linear.",
    "resource_url":    "https://s4.com/algebra",
    "license":         "CC BY-SA 4.0",
    "format":          "text",
    "subject_area":    "Matematica",
    "education_level": "superior",
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _submit(client, token, rea):
    return client.post(REAS_URL, json=rea, headers=_auth(token)).get_json()["data"]


def _tag_rea(client, token, rea_id, tags: list[str]):
    return client.post(f"{REAS_URL}{rea_id}/tags", json={"tags": tags}, headers=_auth(token))


# --- Avaliações ---

def test_avaliar_rea_success(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 5}, headers=_auth(token))
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["rating"] == 5
    assert "rating_avg" in data
    assert "rating_count" in data


def test_avaliar_rea_score_invalido(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 6}, headers=_auth(token))
    assert r.status_code == 400


def test_avaliar_rea_score_zero_invalido(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/avaliacoes", json={"score": 0}, headers=_auth(token))
    assert r.status_code == 400


@pytest.mark.skip(reason="Requer trigger recompute_rea_rating do Supabase — nao disponivel no DB local")
def test_avaliar_rea_atualiza_media(client, make_token):
    pass


# --- Visualização ---

def test_registrar_visualizacao(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/visualizacao", headers=_auth(token))
    assert r.status_code == 200


def test_visualizacao_sem_token(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = client.post(f"{REAS_URL}{rea['id']}/visualizacao")
    assert r.status_code == 401


# --- Classificação de REAs por tags (string labels) ---

def test_classificar_rea_success(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = _tag_rea(client, token, rea["id"], ["python", "programacao"])
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert set(data["tags"]) >= {"python", "programacao"}


def test_classificar_rea_sem_tags_retorna_400(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    r = _tag_rea(client, token, rea["id"], [])
    assert r.status_code == 400


def test_classificar_rea_acumula_tags(client, make_token):
    token = make_token()
    rea = _submit(client, token, _REA_PYTHON)
    _tag_rea(client, token, rea["id"], ["python"])
    _tag_rea(client, token, rea["id"], ["programacao"])
    r = client.get(f"{REAS_URL}{rea['id']}")
    tags = r.get_json()["data"]["tags"]
    assert "python" in tags
    assert "programacao" in tags


# --- Motor de recomendação ---

def test_recomendacoes_sem_perfil_retorna_lista(client, make_token):
    token = make_token()
    r = client.get(RECOMENDACOES_URL, headers=_auth(token))
    assert r.status_code == 200
    assert isinstance(r.get_json()["data"], list)


def test_recomendacoes_sem_token_retorna_401(client):
    r = client.get(RECOMENDACOES_URL)
    assert r.status_code == 401


def test_recomendacoes_retorna_campo_relevance_score(client, make_token):
    token = make_token()
    _submit(client, token, _REA_PYTHON)
    r = client.get(RECOMENDACOES_URL, headers=_auth(token))
    assert r.status_code == 200
    items = r.get_json()["data"]
    assert len(items) >= 1
    assert "relevance_score" in items[0]
    assert "resource_url" in items[0]
    assert "rating_avg" in items[0]
