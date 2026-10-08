from odoo import fields, models

from odoo.addons.ais_helpdesk_whatsapp.services import agent_client


class WhatsappStartWizard(models.TransientModel):
    _name = "ais.whatsapp.start.wizard"
    _description = "Iniciar una conversación de WhatsApp"

    phone = fields.Char(string="WhatsApp (con código de país, solo números)", required=True)
    profile_name = fields.Char(string="Nombre")
    template_name = fields.Char(string="Plantilla aprobada por Meta", required=True)
    params = fields.Char(
        string="Parámetros de la plantilla",
        help="Separados por coma, en el orden que los espera la plantilla. Vacío si no tiene.",
    )
    partner_id = fields.Many2one("res.partner", string="Contacto de Odoo (opcional)")

    def action_send(self):
        self.ensure_one()
        params_list = [p.strip() for p in (self.params or "").split(",") if p.strip()]
        agent_client.start_conversation(
            self.env,
            phone=self.phone,
            template_name=self.template_name,
            params=params_list,
            profile_name=self.profile_name,
            helpdesk_partner_id=self.partner_id.id if self.partner_id else None,
        )
        self.env["ais.whatsapp.conversation"].sync_list()
        return {"type": "ir.actions.act_window_close"}
