from odoo import fields, models

from odoo.addons.ais_helpdesk_whatsapp.services import agent_client


class WhatsappReplyWizard(models.TransientModel):
    _name = "ais.whatsapp.reply.wizard"
    _description = "Responder una conversación de WhatsApp"

    conversation_id = fields.Many2one("ais.whatsapp.conversation", required=True)
    text = fields.Text(string="Respuesta", required=True)

    def action_send(self):
        self.ensure_one()
        agent_client.reply(self.env, self.conversation_id.remote_id, self.text)
        self.conversation_id.action_refresh()
        return {"type": "ir.actions.act_window_close"}
