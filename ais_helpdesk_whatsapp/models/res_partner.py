from datetime import datetime

import pytz

from odoo import api, fields, models

TZ_NAME = "America/Argentina/Buenos_Aires"
ODOO_VERSIONS = [(f"{v}.0", f"{v}.0") for v in range(11, 20)]


class ResPartner(models.Model):
    _inherit = "res.partner"

    ais_odoo_version = fields.Selection(ODOO_VERSIONS, string="Versión de Odoo instalada")
    ais_support_plan_id = fields.Many2one("ais.support.plan", string="Plan de soporte")
    ais_plan_observations = fields.Text(
        related="ais_support_plan_id.observations", string="Qué incluye el plan", readonly=True
    )
    ais_tickets_per_month = fields.Integer(
        string="Tickets por mes", help="Cantidad de tickets de atención por mes. 0 = ilimitado."
    )
    ais_tickets_used_month = fields.Integer(
        string="Tickets resueltos este mes", compute="_compute_ais_tickets_used_month"
    )
    ais_tickets_summary = fields.Char(string="Tickets del mes", compute="_compute_ais_tickets_used_month")

    @api.depends("ais_tickets_per_month")
    def _compute_ais_tickets_used_month(self):
        """Tickets de la empresa y de todos sus contactos, creados en el mes y ya resueltos (los
        cancelados o rechazados no cuentan), de la categoría de consultas si está configurada."""
        local_now = datetime.now(pytz.timezone(TZ_NAME))
        month_start = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start = month_start.astimezone(pytz.utc).replace(tzinfo=None)
        not_counted = [
            stage.id
            for xmlid in ("helpdesk_mgmt.helpdesk_ticket_stage_cancelled", "helpdesk_mgmt.helpdesk_ticket_stage_rejected")
            for stage in [self.env.ref(xmlid, raise_if_not_found=False)]
            if stage
        ]
        Ticket = self.env["helpdesk.ticket"].sudo()
        # Si hay una categoría de consultas configurada (Ajustes de Mesa de Ayuda), solo cuentan esos tickets.
        category = self.env["ir.config_parameter"].sudo().get_param("ais_helpdesk_whatsapp.quota_category_id")
        category_domain = [("category_id", "=", int(category))] if category and category.isdigit() else []
        for partner in self:
            used = 0
            if partner.is_company and partner.id:
                used = Ticket.search_count(
                    [
                        ("partner_id", "child_of", partner.id),
                        ("create_date", ">=", month_start),
                        ("stage_id.closed", "=", True),
                        ("stage_id", "not in", not_counted),
                    ]
                    + category_domain
                )
            partner.ais_tickets_used_month = used
            limit = partner.ais_tickets_per_month
            partner.ais_tickets_summary = f"{used} de {limit}" if limit > 0 else f"{used} (ilimitado)"
