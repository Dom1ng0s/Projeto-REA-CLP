"""
Sprint 5 — Moderação e Painel Admin.
Auth via make_token fixture (Supabase JWT).
Tests that depend on Supabase triggers (report/rating status changes) are skipped.
"""
import uuid

import pytest

from src.extensions.database import db
from src.models.models import REA, REAReport, UserRole, REA_STATUS_REVIEW

REAS_URL             = "/api/reas/"
DENUNCIAS_URL        = "/api/denuncias/"
ADMIN_REVISAO_URL    = "/api/admin/revisao"
ADMIN_ESTATISTICAS_URL = "/api/admin/estatisticas"

_REA_BASE = {
    "title":           "REA Sprint 5",
    "description":     "Material para testes de moderacao.",
    "resource_url":    "https://s5.com/rea",
    "license":         "CC BY 4.0",
    "format":          "text",
    "subject_area":    "Educacao",
    "education_level": "ensino_fundamental",
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _submit_rea(client, token, overrides=None):
    data = {**_REA_BASE, **(overrides or {})}
    r = client.post(REAS_URL, json=data, headers=_auth(token))
    return r.get_json()["data"]


def _denunciar(client, token, rea_id, reason="inappropriate", detail=None):
    body = {"rea_id": rea_id, "reason": reason}
    if detail:
        body["detail"] = detail
    return client.post(DENUNCIAS_URL, json=body, headers=_auth(token))


def _make_admin_token(app, make_token):
    """Mints a token for a new UUID, inserts a UserRole(role='admin') row."""
    user_id = str(uuid.uuid4())
    with app.app_context():
        db.session.add(UserRole(user_id=uuid.UUID(user_id), role="admin"))
        db.session.commit()
    return make_token(user_id)


def _force_review_status(app, rea_id: str, report_count: int = 3):
    """Directly sets a REA to blocked_review (simulates the Supabase trigger)."""
    with app.app_context():
        rea = db.session.get(REA, uuid.UUID(rea_id))
        rea.status = REA_STATUS_REVIEW
        rea.report_count = report_count
        db.session.commit()


def _fazer_n_denuncias(client, make_token, rea_id, n):
    for _ in range(n):
        token = make_token()
        _denunciar(client, token, rea_id)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Decorador @admin_required
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_required_sem_token(client):
    r = client.get(ADMIN_REVISAO_URL)
    assert r.status_code == 401


def test_admin_required_usuario_comum_recebe_403(client, make_token):
    token = make_token()
    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token))
    assert r.status_code == 403
    assert "administradores" in r.get_json()["message"].lower()


def test_admin_required_admin_acessa_com_sucesso(client, app, make_token):
    token = _make_admin_token(app, make_token)
    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token))
    assert r.status_code == 200


def test_admin_required_token_invalido(client):
    r = client.get(ADMIN_REVISAO_URL, headers=_auth("token.invalido.aqui"))
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 2. POST /api/denuncias/
# ═══════════════════════════════════════════════════════════════════════════════

def test_denuncia_success(client, make_token):
    token_a = make_token()
    token_b = make_token()
    rea = _submit_rea(client, token_a)

    r = _denunciar(client, token_b, rea["id"], reason="broken_link", detail="Retorna 404")
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["rea_id"] == rea["id"]
    assert "report_count" in data   # value updated by Supabase trigger in production


def test_denuncia_sem_token_retorna_401(client, make_token):
    token = make_token()
    rea = _submit_rea(client, token)
    r = client.post(DENUNCIAS_URL, json={"rea_id": rea["id"], "reason": "spam"})
    assert r.status_code == 401


def test_denuncia_rea_inexistente_retorna_404(client, make_token):
    token = make_token()
    r = _denunciar(client, token, "00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_denuncia_motivo_invalido_retorna_400(client, make_token):
    token_a = make_token()
    token_b = make_token()
    rea = _submit_rea(client, token_a)
    r = _denunciar(client, token_b, rea["id"], reason="motivo_inventado")
    assert r.status_code == 400


def test_denuncia_campos_obrigatorios_ausentes(client, make_token):
    token = make_token()
    r = client.post(DENUNCIAS_URL, json={}, headers=_auth(token))
    assert r.status_code == 400


def test_denuncia_duplicada_mesmo_usuario_retorna_400(client, make_token):
    token_a = make_token()
    token_b = make_token()
    rea = _submit_rea(client, token_a)
    _denunciar(client, token_b, rea["id"])
    r = _denunciar(client, token_b, rea["id"])
    assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Gatilhos — dependem de triggers Supabase (skipped no DB local)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="Requer trigger recompute_rea_reports do Supabase")
def test_terceira_denuncia_aciona_sob_revisao(client, make_token):
    pass


@pytest.mark.skip(reason="Requer trigger recompute_rea_reports do Supabase")
def test_rea_sob_revisao_some_da_listagem(client, make_token):
    pass


@pytest.mark.skip(reason="Requer trigger recompute_rea_rating do Supabase")
def test_nota_baixa_oculta_rea(client, make_token):
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# 4. GET /api/admin/revisao
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_listar_revisao_vazio(client, app, make_token):
    token = _make_admin_token(app, make_token)
    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token))
    assert r.status_code == 200
    assert r.get_json()["data"] == []


def test_admin_listar_revisao_retorna_rea_em_revisao(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)

    _fazer_n_denuncias(client, make_token, rea["id"], n=2)
    _force_review_status(app, rea["id"], report_count=2)

    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token_admin))
    assert r.status_code == 200
    items = r.get_json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == rea["id"]
    assert items[0]["status"] == "blocked_review"


def test_admin_listar_revisao_nao_inclui_ativo(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    _submit_rea(client, token_user)  # status = active

    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token_admin))
    assert r.get_json()["data"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 5. POST /api/admin/aprovar/<id>
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_aprovar_restaura_para_ativo(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)
    _force_review_status(app, rea["id"])

    r = client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "active"


def test_admin_aprovar_rea_volta_para_busca(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)
    _force_review_status(app, rea["id"])

    client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))

    r = client.get(REAS_URL)
    ids = [item["id"] for item in r.get_json()["data"]["items"]]
    assert rea["id"] in ids


def test_admin_aprovar_marca_denuncias_como_dismissed(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, make_token, rea["id"], n=2)
    _force_review_status(app, rea["id"], report_count=2)

    client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))

    with app.app_context():
        reports = db.session.execute(
            db.select(REAReport).where(REAReport.rea_id == uuid.UUID(rea["id"]))
        ).scalars().all()
        assert all(rep.state == "dismissed" for rep in reports)
        assert all(rep.resolved_at is not None for rep in reports)


def test_admin_aprovar_rea_nao_sob_revisao_retorna_400(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)   # status = active

    r = client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))
    assert r.status_code == 400


def test_admin_aprovar_rea_inexistente_retorna_404(client, app, make_token):
    token = _make_admin_token(app, make_token)
    r = client.post(
        "/api/admin/aprovar/00000000-0000-0000-0000-000000000000",
        headers=_auth(token),
    )
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 6. POST /api/admin/remover/<id>
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_remover_rea_success(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)

    r = client.post(f"/api/admin/remover/{rea['id']}", headers=_auth(token_admin))
    assert r.status_code == 200
    assert r.get_json()["data"]["removido"] is True

    with app.app_context():
        assert db.session.get(REA, uuid.UUID(rea["id"])) is None


def test_admin_remover_cascade_apaga_reports(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, make_token, rea["id"], n=2)

    client.post(f"/api/admin/remover/{rea['id']}", headers=_auth(token_admin))

    with app.app_context():
        count = db.session.execute(
            db.select(db.func.count(REAReport.id)).where(
                REAReport.rea_id == uuid.UUID(rea["id"])
            )
        ).scalar_one()
        assert count == 0


def test_admin_remover_rea_inexistente_retorna_404(client, app, make_token):
    token = _make_admin_token(app, make_token)
    r = client.post(
        "/api/admin/remover/00000000-0000-0000-0000-000000000000",
        headers=_auth(token),
    )
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GET /api/admin/estatisticas
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_estatisticas_estrutura(client, app, make_token):
    token = _make_admin_token(app, make_token)
    r = client.get(ADMIN_ESTATISTICAS_URL, headers=_auth(token))
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert {"usuarios", "reas", "moderacao"} <= data.keys()
    assert "total" in data["reas"]
    assert "ativos" in data["reas"]
    assert "ocultos_automaticamente" in data["reas"]
    assert "sob_revisao" in data["reas"]
    assert "total_avaliacoes" in data["moderacao"]
    assert "total_denuncias" in data["moderacao"]
    assert "com_interacao" in data["usuarios"]


def test_admin_estatisticas_contagens_corretas(client, app, make_token):
    token_admin = _make_admin_token(app, make_token)
    token_user  = make_token()
    _submit_rea(client, token_user)
    _submit_rea(client, token_user, {"title": "REA 2", "resource_url": "https://s5.com/rea2"})

    r = client.get(ADMIN_ESTATISTICAS_URL, headers=_auth(token_admin))
    data = r.get_json()["data"]

    assert data["reas"]["total"] == 2
    assert data["reas"]["ativos"] == 2
    assert data["reas"]["ocultos_automaticamente"] == 0
    assert data["reas"]["sob_revisao"] == 0
    assert data["moderacao"]["total_avaliacoes"] == 0
    assert data["moderacao"]["total_denuncias"] == 0
