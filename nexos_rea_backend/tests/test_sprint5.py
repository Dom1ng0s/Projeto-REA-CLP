"""
Sprint 5 — Moderação e Painel Admin
Cobre: moderacao_service (gatilhos), denuncia_routes e admin_routes.
"""
import uuid

import pytest

from src.extensions.database import db
from src.models.models import REA, Report, RoleEnum, StatusREAEnum, User

# ── URLs ──────────────────────────────────────────────────────────────────────
REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REAS_URL = "/api/reas/"
DENUNCIAS_URL = "/api/denuncias/"
ADMIN_REVISAO_URL = "/api/admin/revisao"
ADMIN_ESTATISTICAS_URL = "/api/admin/estatisticas"

# ── Dados fixos ───────────────────────────────────────────────────────────────
_ADMIN_DATA = {"name": "Admin", "email": "admin@nexos.com", "password": "adminpass123"}
_USER_A = {"name": "Alice", "email": "alice@s5.com", "password": "senha123"}
_USER_B = {"name": "Bruno", "email": "bruno@s5.com", "password": "senha123"}
_USER_C = {"name": "Carlos", "email": "carlos@s5.com", "password": "senha123"}

_REA_BASE = {
    "title": "REA Sprint 5",
    "description": "Material para testes de moderacao.",
    "url": "https://s5.com/rea",
    "license": "CC BY 4.0",
    "resource_type": "article",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register_and_login(client, user):
    client.post(REGISTER_URL, json=user)
    r = client.post(LOGIN_URL, json={"email": user["email"], "password": user["password"]})
    return r.get_json()["data"]["access_token"]


def _make_admin(client, user_data=None):
    """Registra usuário e promove a admin via acesso direto ao banco."""
    data = user_data or _ADMIN_DATA
    client.post(REGISTER_URL, json=data)
    with client.application.app_context():
        u = db.session.execute(
            db.select(User).where(User.email == data["email"])
        ).scalar_one()
        u.role = RoleEnum.admin
        db.session.commit()
    r = client.post(LOGIN_URL, json={"email": data["email"], "password": data["password"]})
    return r.get_json()["data"]["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _submit_rea(client, token, overrides=None):
    data = {**_REA_BASE, **(overrides or {})}
    r = client.post(REAS_URL, json=data, headers=_auth(token))
    return r.get_json()["data"]


def _denunciar(client, token, rea_id, reason="conteudo_inapropriado", detail=None):
    body = {"rea_id": rea_id, "reason": reason}
    if detail:
        body["detail"] = detail
    return client.post(DENUNCIAS_URL, json=body, headers=_auth(token))


def _avaliar(client, token, rea_id, score):
    return client.post(
        f"{REAS_URL}{rea_id}/avaliacoes",
        json={"score": score},
        headers=_auth(token),
    )


def _fazer_n_denuncias(client, rea_id, n, offset=0):
    """Cria n usuários únicos (via offset) e cada um denuncia o REA."""
    for i in range(offset, offset + n):
        user = {
            "name": f"Denunciante{i}",
            "email": f"denunciante{i}@s5.com",
            "password": "senha123",
        }
        token = _register_and_login(client, user)
        _denunciar(client, token, rea_id)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Decorador @admin_required
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_required_sem_token(client):
    r = client.get(ADMIN_REVISAO_URL)
    assert r.status_code == 401


def test_admin_required_usuario_comum_recebe_403(client):
    token = _register_and_login(client, _USER_A)
    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token))
    assert r.status_code == 403
    assert "administradores" in r.get_json()["message"].lower()


def test_admin_required_admin_acessa_com_sucesso(client):
    token = _make_admin(client)
    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token))
    assert r.status_code == 200


def test_admin_required_token_invalido(client):
    r = client.get(ADMIN_REVISAO_URL, headers=_auth("token.invalido.aqui"))
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 2. POST /api/denuncias/ — caminho feliz e validações
# ═══════════════════════════════════════════════════════════════════════════════

def test_denuncia_success(client):
    token_a = _register_and_login(client, _USER_A)
    token_b = _register_and_login(client, _USER_B)
    rea = _submit_rea(client, token_a)

    r = _denunciar(client, token_b, rea["id"], reason="link_quebrado", detail="Retorna 404")
    assert r.status_code == 201
    data = r.get_json()["data"]
    assert data["rea_id"] == rea["id"]
    assert data["report_count"] == 1
    assert data["status"] == "ativo"


def test_denuncia_sem_token_retorna_401(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token)
    r = client.post(DENUNCIAS_URL, json={"rea_id": rea["id"], "reason": "spam"})
    assert r.status_code == 401


def test_denuncia_rea_inexistente_retorna_404(client):
    token = _register_and_login(client, _USER_A)
    r = _denunciar(client, token, "00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_denuncia_motivo_invalido_retorna_400(client):
    token_a = _register_and_login(client, _USER_A)
    token_b = _register_and_login(client, _USER_B)
    rea = _submit_rea(client, token_a)
    r = _denunciar(client, token_b, rea["id"], reason="motivo_inventado")
    assert r.status_code == 400


def test_denuncia_campos_obrigatorios_ausentes(client):
    token = _register_and_login(client, _USER_A)
    r = client.post(DENUNCIAS_URL, json={}, headers=_auth(token))
    assert r.status_code == 400


def test_denuncia_duplicada_mesmo_usuario_retorna_400(client):
    token_a = _register_and_login(client, _USER_A)
    token_b = _register_and_login(client, _USER_B)
    rea = _submit_rea(client, token_a)
    _denunciar(client, token_b, rea["id"])
    r = _denunciar(client, token_b, rea["id"])
    assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Gatilho de denúncias — 3 denúncias → SOB_REVISAO
# ═══════════════════════════════════════════════════════════════════════════════

def test_duas_denuncias_nao_alteram_status(client):
    token_a = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_a)
    _fazer_n_denuncias(client, rea["id"], n=2)

    r = client.get(f"{REAS_URL}{rea['id']}")
    assert r.status_code == 200


def test_terceira_denuncia_aciona_sob_revisao(client):
    token_a = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_a)
    _fazer_n_denuncias(client, rea["id"], n=2)

    # Terceira denúncia dispara o gatilho
    token_c = _register_and_login(client, _USER_C)
    r = _denunciar(client, token_c, rea["id"])
    assert r.status_code == 201
    assert r.get_json()["data"]["status"] == "sob_revisao"
    assert r.get_json()["data"]["report_count"] == 3


def test_rea_sob_revisao_some_da_listagem(client):
    token_a = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_a)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = client.get(REAS_URL)
    ids = [item["id"] for item in r.get_json()["data"]["items"]]
    assert rea["id"] not in ids


def test_rea_sob_revisao_nao_acessivel_por_id(client):
    token_a = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_a)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = client.get(f"{REAS_URL}{rea['id']}")
    assert r.status_code == 404


def test_denuncias_adicionais_apos_sob_revisao_sao_registradas(client, app):
    """Denúncias em REA já sob revisão devem ser persistidas para rastreabilidade."""
    token_a = _register_and_login(client, _USER_A)
    token_extra = _register_and_login(client, _USER_B)
    rea = _submit_rea(client, token_a)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = _denunciar(client, token_extra, rea["id"])
    assert r.status_code == 201

    with app.app_context():
        count = db.session.execute(
            db.select(db.func.count(Report.id)).where(
                Report.rea_id == uuid.UUID(rea["id"])
            )
        ).scalar_one()
        assert count == 4


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Gatilho de qualidade — avg_rating < 2.0
# ═══════════════════════════════════════════════════════════════════════════════

def test_nota_1_oculta_rea_da_listagem(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token)

    r = _avaliar(client, token, rea["id"], score=1)
    assert r.status_code == 201

    r = client.get(REAS_URL)
    ids = [item["id"] for item in r.get_json()["data"]["items"]]
    assert rea["id"] not in ids


def test_nota_1_oculta_rea_por_id(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token)
    _avaliar(client, token, rea["id"], score=1)

    r = client.get(f"{REAS_URL}{rea['id']}")
    assert r.status_code == 404


def test_nota_exatamente_2_nao_oculta(client):
    """avg == 2.0 não deve ocultar: condição é avg < 2.0, não avg <= 2.0."""
    token = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token)
    _avaliar(client, token, rea["id"], score=2)

    r = client.get(f"{REAS_URL}{rea['id']}")
    assert r.status_code == 200


def test_nota_alta_nao_oculta(client):
    token = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token)
    _avaliar(client, token, rea["id"], score=5)

    r = client.get(f"{REAS_URL}{rea['id']}")
    assert r.status_code == 200


def test_gatilho_nota_nao_afeta_sob_revisao(app, client):
    """Gatilho de qualidade não deve sobrescrever o status SOB_REVISAO."""
    from src.services import moderacao_service

    token_a = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_a)

    with app.app_context():
        rea_obj = db.session.get(REA, uuid.UUID(rea["id"]))
        rea_obj.status = StatusREAEnum.sob_revisao
        rea_obj.avg_rating = 1.0
        rea_obj.rating_count = 1
        changed = moderacao_service.aplicar_gatilho_avaliacao(rea_obj)
        assert changed is False
        assert rea_obj.status == StatusREAEnum.sob_revisao


def test_gatilho_nota_sem_avaliacoes_nao_oculta(app, client):
    """rating_count == 0 não deve acionar o gatilho mesmo com avg == 0.0."""
    from src.services import moderacao_service

    token_a = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_a)

    with app.app_context():
        rea_obj = db.session.get(REA, uuid.UUID(rea["id"]))
        assert rea_obj.rating_count == 0
        assert rea_obj.avg_rating == 0.0
        changed = moderacao_service.aplicar_gatilho_avaliacao(rea_obj)
        assert changed is False
        assert rea_obj.status == StatusREAEnum.ativo


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GET /api/admin/revisao
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_listar_revisao_vazio(client):
    token = _make_admin(client)
    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token))
    assert r.status_code == 200
    assert r.get_json()["data"] == []


def test_admin_listar_revisao_retorna_rea_e_denuncias(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token_admin))
    assert r.status_code == 200
    items = r.get_json()["data"]
    assert len(items) == 1
    item = items[0]
    assert item["id"] == rea["id"]
    assert item["status"] == "sob_revisao"
    assert item["report_count"] == 3
    assert len(item["denuncias"]) == 3


def test_admin_listar_revisao_nao_inclui_ativo(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    _submit_rea(client, token_user)  # REA ativo, sem denúncias

    r = client.get(ADMIN_REVISAO_URL, headers=_auth(token_admin))
    assert r.get_json()["data"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 6. POST /api/admin/aprovar/<id>
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_aprovar_restaura_para_ativo(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "ativo"


def test_admin_aprovar_rea_volta_para_busca(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))

    r = client.get(REAS_URL)
    ids = [item["id"] for item in r.get_json()["data"]["items"]]
    assert rea["id"] in ids


def test_admin_aprovar_marca_denuncias_como_revisadas(client, app):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))

    with app.app_context():
        reports = db.session.execute(
            db.select(Report).where(Report.rea_id == uuid.UUID(rea["id"]))
        ).scalars().all()
        assert all(rep.reviewed for rep in reports)
        assert all(rep.reviewed_at is not None for rep in reports)


def test_admin_aprovar_rea_nao_sob_revisao_retorna_400(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)  # status = ativo

    r = client.post(f"/api/admin/aprovar/{rea['id']}", headers=_auth(token_admin))
    assert r.status_code == 400


def test_admin_aprovar_rea_inexistente_retorna_404(client):
    token = _make_admin(client)
    r = client.post(
        "/api/admin/aprovar/00000000-0000-0000-0000-000000000000",
        headers=_auth(token),
    )
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 7. POST /api/admin/remover/<id>
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_remover_rea_success(client, app):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = client.post(f"/api/admin/remover/{rea['id']}", headers=_auth(token_admin))
    assert r.status_code == 200
    assert r.get_json()["data"]["removido"] is True

    with app.app_context():
        assert db.session.get(REA, uuid.UUID(rea["id"])) is None


def test_admin_remover_cascade_apaga_reports(client, app):
    """Remoção do REA deve apagar todas as denúncias via CASCADE."""
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    client.post(f"/api/admin/remover/{rea['id']}", headers=_auth(token_admin))

    with app.app_context():
        count = db.session.execute(
            db.select(db.func.count(Report.id)).where(
                Report.rea_id == uuid.UUID(rea["id"])
            )
        ).scalar_one()
        assert count == 0


def test_admin_remover_rea_inexistente_retorna_404(client):
    token = _make_admin(client)
    r = client.post(
        "/api/admin/remover/00000000-0000-0000-0000-000000000000",
        headers=_auth(token),
    )
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GET /api/admin/estatisticas
# ═══════════════════════════════════════════════════════════════════════════════

def test_admin_estatisticas_estrutura_completa(client):
    token = _make_admin(client)
    r = client.get(ADMIN_ESTATISTICAS_URL, headers=_auth(token))
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert {"usuarios", "reas", "moderacao"} <= data.keys()
    assert "total" in data["usuarios"]
    assert "taxa_engajamento_pct" in data["usuarios"]
    assert "total" in data["reas"]
    assert "ativos" in data["reas"]
    assert "ocultos_automaticamente" in data["reas"]
    assert "sob_revisao" in data["reas"]
    assert "total_avaliacoes" in data["moderacao"]
    assert "total_denuncias" in data["moderacao"]


def test_admin_estatisticas_contagens_corretas(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    _submit_rea(client, token_user)
    _submit_rea(client, token_user, {"title": "REA 2", "url": "https://s5.com/rea2"})

    r = client.get(ADMIN_ESTATISTICAS_URL, headers=_auth(token_admin))
    data = r.get_json()["data"]

    assert data["usuarios"]["total"] == 2  # admin + user_a
    assert data["reas"]["total"] == 2
    assert data["reas"]["ativos"] == 2
    assert data["reas"]["ocultos_automaticamente"] == 0
    assert data["reas"]["sob_revisao"] == 0
    assert data["moderacao"]["total_avaliacoes"] == 0
    assert data["moderacao"]["total_denuncias"] == 0


def test_admin_estatisticas_sob_revisao_contabilizado(client):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _fazer_n_denuncias(client, rea["id"], n=3)

    r = client.get(ADMIN_ESTATISTICAS_URL, headers=_auth(token_admin))
    data = r.get_json()["data"]

    assert data["reas"]["sob_revisao"] == 1
    assert data["reas"]["ativos"] == 0
    assert data["moderacao"]["total_denuncias"] == 3


def test_admin_estatisticas_oculto_contabilizado(client, app):
    token_admin = _make_admin(client)
    token_user = _register_and_login(client, _USER_A)
    rea = _submit_rea(client, token_user)
    _avaliar(client, token_user, rea["id"], score=1)  # avg=1.0 → OCULTO

    r = client.get(ADMIN_ESTATISTICAS_URL, headers=_auth(token_admin))
    data = r.get_json()["data"]

    assert data["reas"]["ocultos_automaticamente"] == 1
    assert data["reas"]["ativos"] == 0
    assert data["moderacao"]["total_avaliacoes"] == 1
