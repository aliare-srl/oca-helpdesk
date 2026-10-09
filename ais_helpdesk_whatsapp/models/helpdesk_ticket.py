from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    whatsapp_conversation_count = fields.Integer(compute="_compute_whatsapp_conversation_count")

    def _compute_whatsapp_conversation_count(self):
        Conv = self.env["ais.whatsapp.conversation"]
        for ticket in self:
            ticket.whatsapp_conversation_count = Conv.search_count([("ticket_id", "=", ticket.id)])

    def action_open_whatsapp_conversation(self):
        self.ensure_one()
        conversation = self.env["ais.whatsapp.conversation"].search(
            [("ticket_id", "=", self.id)], order="last_message_at desc", limit=1
        )
        return {
            "type": "ir.actions.client",
            "tag": "ais_whatsapp_dashboard",
            "name": "Conversaciones de WhatsApp",
            "params": {"conversation_id": conversation.remote_id if conversation else False},
        }
