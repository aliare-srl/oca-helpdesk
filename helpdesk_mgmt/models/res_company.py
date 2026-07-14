# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    helpdesk_mgmt_portal_select_team = fields.Boolean(
        string="Select team in Helpdesk portal"
    )
    helpdesk_mgmt_portal_team_id_required = fields.Boolean(
        string="Required Team field in Helpdesk portal",
        default=True,
    )
    helpdesk_mgmt_portal_category_id_required = fields.Boolean(
        string="Required Category field in Helpdesk portal",
        default=True,
    )

    def _default_helpdesk_resource_calendar(self):
        return self.env.ref(
            "helpdesk_mgmt.helpdesk_default_resource_calendar", raise_if_not_found=False
        )

    helpdesk_resource_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        string="Horario Laboral Mesa de Ayuda",
        default=_default_helpdesk_resource_calendar,
        help="Días y horas laborales usados para calcular los vencimientos de SLA "
        "y los tiempos de resolución de Helpdesk.",
    )
