REAS_URL = "/api/reas/"

_VALID_REA = {
    "title":           "Introducao ao Python",
    "description":     "Curso gratuito para iniciantes com exercicios.",
    "resource_url":    "https://exemplo.com/python",
    "license":         "CC BY 4.0",
    "format":          "video",
    "subject_area":    "Computacao",
    "education_level": "ensino_medio",
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _submit(client, token, data=None):
    return client.post(REAS_URL, json=data or _VALID_REA, headers=_auth(token))


# --- Listagem ---

def test_list_reas_empty(client):
    r = client.get(REAS_URL)
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["items"] == []
    assert data["pagination"]["total"] == 0


def test_list_reas_with_results(client, make_token):
    token = make_token()
    _submit(client, token)
    r = client.get(REAS_URL)
    assert r.status_code == 200
    assert r.get_json()["data"]["pagination"]["total"] == 1


def test_search_by_title(client, make_token):
    token = make_token()
    _submit(client, token)
    _submit(client, token, {**_VALID_REA, "title": "Algebra Linear", "resource_url": "https://x.com/2"})
    r = client.get(f"{REAS_URL}?q=python")
    assert r.status_code == 200
    items = r.get_json()["data"]["items"]
    assert len(items) == 1
    assert "Python" in items[0]["title"]


def test_search_no_results(client):
    r = client.get(f"{REAS_URL}?q=termoqueNaoExiste")
    assert r.status_code == 200
    assert r.get_json()["data"]["pagination"]["total"] == 0


def test_pagination(client, make_token):
    token = make_token()
    for i in range(5):
        _submit(client, token, {**_VALID_REA, "title": f"REA {i}", "resource_url": f"https://x.com/{i}"})
    r = client.get(f"{REAS_URL}?page=1&per_page=3")
    data = r.get_json()["data"]
    assert len(data["items"]) == 3
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["pages"] == 2


# --- Filtros de catálogo (Sprint E) ---

def test_filter_by_format(client, make_token):
    token = make_token()
    _submit(client, token)                        # format = "video"
    _submit(client, token, {**_VALID_REA, "format": "audio", "resource_url": "https://x.com/audio"})
    r = client.get(f"{REAS_URL}?format=video")
    items = r.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["format"] == "video"


def test_filter_by_education_level(client, make_token):
    token = make_token()
    _submit(client, token)                        # education_level = "ensino_medio"
    _submit(client, token, {**_VALID_REA, "education_level": "superior", "resource_url": "https://x.com/sup"})
    r = client.get(f"{REAS_URL}?education_level=ensino_medio")
    items = r.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["education_level"] == "ensino_medio"


def test_filter_by_language(client, make_token):
    token = make_token()
    _submit(client, token)                        # language defaults to "pt_br"
    _submit(client, token, {**_VALID_REA, "language": "en", "resource_url": "https://x.com/en"})
    r = client.get(f"{REAS_URL}?language=pt_br")
    items = r.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["language"] == "pt_br"


def test_filter_by_subject_area(client, make_token):
    token = make_token()
    _submit(client, token)                        # subject_area = "Computacao"
    _submit(client, token, {**_VALID_REA, "subject_area": "Matematica", "resource_url": "https://x.com/mat"})
    r = client.get(f"{REAS_URL}?subject_area=Computacao")
    items = r.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["subject_area"] == "Computacao"


def test_invalid_min_rating_returns_400(client):
    r = client.get(f"{REAS_URL}?min_rating=naoEnumero")
    assert r.status_code == 400


# --- Detalhe ---

def test_get_rea_by_id(client, make_token):
    token = make_token()
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

def test_submit_rea_success(client, make_token):
    token = make_token()
    r = _submit(client, token)
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["title"] == _VALID_REA["title"]
    assert data["rating_avg"] == 0.0
    assert data["format"] == "video"


def test_submit_rea_without_token(client):
    r = client.post(REAS_URL, json=_VALID_REA)
    assert r.status_code == 401


def test_submit_rea_missing_title(client, make_token):
    token = make_token()
    r = _submit(client, token, {**_VALID_REA, "title": ""})
    assert r.status_code == 400


def test_submit_rea_invalid_format(client, make_token):
    token = make_token()
    r = _submit(client, token, {**_VALID_REA, "format": "tipo_invalido"})
    assert r.status_code == 400
    assert "Formato invalido" in r.get_json()["message"]


def test_submit_rea_missing_required_fields(client, make_token):
    token = make_token()
    # missing subject_area and education_level
    r = _submit(client, token, {
        "title": "REA Incompleto",
        "resource_url": "https://x.com/incompleto",
        "license": "CC BY 4.0",
        "format": "video",
    })
    assert r.status_code == 400


def test_submit_rea_duplicate_url(client, make_token):
    token = make_token()
    _submit(client, token)
    r = _submit(client, token)
    assert r.status_code == 400
    assert "URL" in r.get_json()["message"]
