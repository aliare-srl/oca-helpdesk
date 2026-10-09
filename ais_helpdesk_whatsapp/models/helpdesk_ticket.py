from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    whatsapp_conversation_remote_id = fields.Integer(
        string="Id de la conversación de WhatsApp",
        help="Lo escribe el servicio al crear el ticket, para no depender del sync cada 2 minutos.",
    )
    whatsapp_conversation_count = fields.Integer(compute="_compute_whatsapp_conversation_count")

    def _fallback_conversation_remote_id(self):
        """Tickets creados antes de que existiera whatsapp_conversation_remote_id: buscar en la copia local."""
        conversation = self.env["ais.whatsapp.conversation"].search(
            [("ticket_id", "=", self.id)], order="last_message_at desc", limit=1
        )
        return conversation.remote_id if conversation else False

    def _compute_whatsapp_conversation_count(self):
        for ticket in self:
            ticket.whatsapp_conversation_count = 1 if (
                ticket.whatsapp_conversation_remote_id or ticket._fallback_conversation_remote_id()
            ) else 0

    def action_open_whatsapp_conversation(self):
        self.ensure_one()
        conversation_id = self.whatsapp_conversation_remote_id or self._fallback_conversation_remote_id()
        return {
            "type": "ir.actions.client",
            "tag": "ais_whatsapp_dashboard",
            "name": "Conversaciones de WhatsApp",
            "params": {"conversation_id": conversation_id},
        }
