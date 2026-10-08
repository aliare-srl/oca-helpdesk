"""Rutas JSON para la pantalla OWL del panel. Proxy fino a services/agent_client: la lógica
y la autenticación contra el servicio viven ahí, esto solo expone esas funciones al navegador."""

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.ais_helpdesk_whatsapp.services import agent_client

_GROUP = "helpdesk_mgmt.group_helpdesk_user_own"


def _check_access():
    if not request.env.user.has_group(_GROUP):
        raise AccessError("No tenés acceso a la mesa de ayuda.")


class WhatsappDashboardController(http.Controller):
    @http.route("/ais_helpdesk_whatsapp/conversations", type="json", auth="user")
    def conversations(self, status=None, limit=200):
        _check_access()
        return agent_client.list_conversations(request.env, status=status, limit=limit)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/messages", type="json", auth="user")
    def messages(self, remote_id):
        _check_access()
        return agent_client.get_messages(request.env, remote_id)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/reply", type="json", auth="user")
    def reply(self, remote_id, text):
        _check_access()
        return agent_client.reply(request.env, remote_id, text)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/take", type="json", auth="user")
    def take(self, remote_id):
        _check_access()
        return agent_client.take(request.env, remote_id)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/return_to_ai", type="json", auth="user")
    def return_to_ai(self, remote_id):
        _check_access()
        return agent_client.return_to_ai(request.env, remote_id)

    @http.route("/ais_helpdesk_whatsapp/conversations/<int:remote_id>/close", type="json", auth="user")
    def close(self, remote_id):
        _check_access()
        return agent_client.close(request.env, remote_id)

    @http.route("/ais_helpdesk_whatsapp/conversations/start", type="json", auth="user")
    def start(self, phone, template_name, params=None, profile_name=None, helpdesk_partner_id=None):
        _check_access()
        return agent_client.start_conversation(
            request.env,
            phone=phone,
            template_name=template_name,
            params=params,
            profile_name=profile_name,
            helpdesk_partner_id=helpdesk_partner_id,
        )
