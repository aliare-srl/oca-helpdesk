from odoo import fields, models


class HelpdeskSlaConfig(models.Model):
    _name = "helpdesk.sla.config"
    _description = "Configuración SLA por Categoría"
    _order = "priority"

    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Categoría",
        required=True,
        ondelete="cascade",
    )
    priority = fields.Selection(
        selection=[
            ("0", "Baja"),
            ("1", "Media"),
            ("2", "Alta"),
            ("3", "Muy Alta"),
        ],
        string="Prioridad",
        required=True,
    )
    hours = fields.Float(string="Horas límite", required=True, default=72.0)
