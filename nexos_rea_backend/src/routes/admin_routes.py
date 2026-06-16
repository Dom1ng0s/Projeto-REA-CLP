from flask import Blueprint

from src.services import admin_service
from src.utils.decorators import admin_required
from src.utils.responses import error, success

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/revisao")
@admin_required
def listar_sob_revisao():
    """
    GET /api/admin/revisao
    Lista todos os REAs com status "Sob Revisão", com suas denúncias detalhadas.
    """
    resultado = admin_service.listar_sob_revisao()
    return success(data=resultado)


@admin_bp.post("/aprovar/<string:rea_id>")
@admin_required
def aprovar_rea(rea_id: str):
    """
    POST /api/admin/aprovar/<rea_id>
    Julga o conteúdo como adequado: restaura para ATIVO e fecha as denúncias.
    """
    try:
        resultado = admin_service.aprovar_rea(rea_id)
        return success(data=resultado, message="REA aprovado e restaurado ao catalogo.")
    except LookupError as e:
        return error(str(e), 404)
    except ValueError as e:
        return error(str(e), 400)


@admin_bp.post("/remover/<string:rea_id>")
@admin_required
def remover_rea(rea_id: str):
    """
    POST /api/admin/remover/<rea_id>
    Julga o conteúdo como inadequado e o remove definitivamente do catálogo.
    Ação irreversível — CASCADE remove avaliações, denúncias e itens de coleção.
    """
    try:
        resultado = admin_service.remover_rea(rea_id)
        return success(data=resultado, message="REA removido definitivamente do catalogo.")
    except LookupError as e:
        return error(str(e), 404)


@admin_bp.get("/estatisticas")
@admin_required
def obter_estatisticas():
    """
    GET /api/admin/estatisticas
    Retorna métricas agregadas do sistema para o dashboard do administrador.
    """
    resultado = admin_service.obter_estatisticas()
    return success(data=resultado)
