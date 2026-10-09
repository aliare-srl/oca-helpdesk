"""Rutas JSON para la pantalla OWL del panel. Proxy fino a services/agent_client: la lógica
y la autenticación contra el servicio viven ahí, esto solo expone esas funciones al navegador."""

import logging

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import html_escape

from odoo.addons.ais_helpdesk_whatsapp.services import agent_client

_GROUP = "helpdesk_mgmt.group_helpdesk_user"
_logger = logging.getLogger(__name__)


def _check_access():
    if not request.env.user.has_group(_GROUP):
        raise AccessError("No tenés acceso a la mesa de ayuda.")


def _config_param(key, default=""):
    return request.env["ir.config_parameter"].sudo().get_param(key) or default


def _reassign_ticket(ticket_id, user_id):
    # La conversación en el servicio ya se actualizó antes de llamar a esto: si tocar el ticket
    # falla (ej. el usuario asignado no tiene email y Odoo no puede notificarlo), no hay que
    # devolver error, la acción principal ya funcionó. Queda solo en el log para revisar.
    if not ticket_id or not user_id:
        return
    try:
        request.env["helpdesk.ticket"].browse(int(ticket_id)).user_id = int(user_id)
    except Exception:  # noqa: BLE001
        _logger.exception("No se pudo reasignar el ticket %s al usuario %s", ticket_id, user_id)


def _close_ticket_with_resolution(ticket_id, resolution):
    if not ticket_id:
        return
    try:
        ticket = request.env["helpdesk.ticket"].browse(int(ticket_id))
        if not ticket.exists():
            return
        stage = request.env["helpdesk.ticket.stage"].search([("name", "=", "Hecho")], limit=1)
        vals = {"stage_id": stage.id} if stage else {}
        if resolution:
            safe = html_escape(resolution).replace("\n", "<br/>")
            # ticket.description es un Markup: sumarle un string plano lo escapa (markupsafe lo
            # trata como texto no confiable). Se pasa a str primero para armar HTML real.
            vals["description"] = f"{str(ticket.description or '')}<p><b>Resolución:</b> {safe}</p>"
        if vals:
            ticket.write(vals)
    except Exception:  # noqa: BLE001
        _logger.exception("No se pudo cerrar el ticket %s con la resolución", ticket_id)


class WhatsappDashboardController(http.Controller):
    @http.route("/ais_helpdesk_whatsapp/config", type="json", auth="user")
    def config(self):
        _check_access()
        refresh_seconds = _config_param("ais_helpdesk_whatsapp.refresh_seconds", "4")
        return {
            "refresh_seconds": int(refresh_seconds) if refresh_seconds.isdigit() else 4,
            "agent_disabled": _config_param("ais_helpdesk_whatsapp.agent_disabled") == "True",
        }

    @http.route("/ais_helpdesk_whatsapp/conversations", type="json", auth="user")
    def conversations(self, status=None, limit=200):
        _check_access()
        return agent_client.list_conversations(request.env, status=status, limit=limit)

    @http.route("/ais_helpdesk_whatsapp/messages/search", type="json", auth="user")
    def search_messages(self, q):
        _check_access()
        return agent_client.search_messages(request.env, q)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/messages", type="json", auth="user")
    def messages(self, remote_id):
        _check_access()
        return agent_client.get_messages(request.env, remote_id)

    @http.route(
        "/ais_helpdesk_whatsapp/conversations/<int:remote_id>/messages/<int:message_id>/media",
        type="http",
        auth="user",
    )
    def message_media(self, remote_id, message_id):
        _check_access()
        content_type, content = agent_client.get_message_media(request.env, remote_id, message_id)
        return request.make_response(content, headers=[("Content-Type", content_type)])

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/reply", type="json", auth="user")
    def reply(self, remote_id, text):
        _check_access()
        return agent_client.reply(request.env, remote_id, text)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/take", type="json", auth="user")
    def take(self, remote_id, ticket_id=None):
        _check_access()
        result = agent_client.take(request.env, remote_id, taken_by=request.env.user.name)
        _reassign_ticket(ticket_id, request.env.user.id)
        return result

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/return_to_ai", type="json", auth="user")
    def return_to_ai(self, remote_id, ticket_id=None):
        _check_access()
        result = agent_client.return_to_ai(request.env, remote_id)
        _reassign_ticket(ticket_id, _config_param("ais_helpdesk_whatsapp.ai_user_id"))
        return result

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/close", type="json", auth="user")
    def close(self, remote_id, resolution=None, ticket_id=None):
        _check_access()
        result = agent_client.close(request.env, remote_id)
        _close_ticket_with_resolution(ticket_id, resolution)
        return result

    @http.route("/ais_helpdesk_whatsapp/tickets/<int:ticket_id>", type="json", auth="user")
    def ticket_info(self, ticket_id):
        _check_access()
        ticket = request.env["helpdesk.ticket"].browse(ticket_id)
        if not ticket.exists():
            return False
        return {
            "id": ticket.id,
            "number": ticket.number,
            "name": ticket.name,
            "stage": ticket.stage_id.name,
        }

    @http.route("/ais_helpdesk_whatsapp/conversations/start", type="json", auth="user")
    def start(self, phone, template_name, params=None, profile_name=None, helpdesk_partner_id=None, ticket_id=None):
        _check_access()
        result = agent_client.start_conversation(
            request.env,
            phone=phone,
            template_name=template_name,
            params=params,
            profile_name=profile_name,
            helpdesk_partner_id=helpdesk_partner_id,
            helpdesk_ticket_id=ticket_id,
        )
        if ticket_id:
            try:
                ticket = request.env["helpdesk.ticket"].browse(int(ticket_id))
                conversation = (result or {}).get("conversation") or {}
                if ticket.exists() and not ticket.whatsapp_conversation_remote_id and conversation.get("id"):
                    ticket.whatsapp_conversation_remote_id = conversation["id"]
            except Exception:  # noqa: BLE001
                _logger.exception("No se pudo vincular el ticket %s a la conversación nueva", ticket_id)
        return result
