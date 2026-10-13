from odoo import fields, models


class SupportPlan(models.Model):
    """Plan de soporte que se le asigna a la empresa cliente. Se administra desde Helpdesk > Configuración."""

    _name = "ais.support.plan"
    _description = "Plan de soporte"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    observations = fields.Text(string="Observaciones", help="Qué incluye el plan.")

    _sql_constraints = [("name_uniq", "unique(name)", "Ya existe un plan con ese nombre.")]
