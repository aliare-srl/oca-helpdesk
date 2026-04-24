from odoo import api, fields, models


class HelpdeskTicketStage(models.Model):
    _name = "helpdesk.ticket.stage"
    _description = "Helpdesk Ticket Stage"
    _order = "sequence, id"

    name = fields.Char(string="Stage Name", required=True, translate=True)
    description = fields.Html(translate=True, sanitize_style=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean()
    closed = fields.Boolean()
    close_from_portal = fields.Boolean(
        help="Display button in portal ticket form to allow closing ticket "
        "with this stage as target."
    )
    mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template",
        domain=[("model", "=", "helpdesk.ticket")],
        help="If set an email will be sent to the "
        "customer when the ticket"
        "reaches this step.",
    )
    color = fields.Integer(string="Color Index")
    fold = fields.Boolean(
        string="Folded in Kanban",
        help="This stage is folded in the kanban view "
        "when there are no records in that stage "
        "to display.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    team_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.team",
        string="Helpdesk Teams",
        help="Specific team that uses this stage. If it is empty all teams could uses",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    @api.model
    def _set_default_stage_colors(self):
        """Fuerza los colores de calendario en cada etapa.
        Busca por nombre (ES e EN) para ser robusto frente a etapas
        que no tengan XML IDs registrados en ir.model.data.
        """
        color_by_name = {
            "Nuevo": 2,
            "New": 2,
            "En progreso": 4,
            "In Progress": 4,
            "En espera": 3,
            "Awaiting": 3,
            "Hecho": 10,
            "Done": 10,
            "Cancelado": 1,
            "Cancelled": 1,
            "Rechazado": 2,
            "Rejected": 2,
        }
        for name, color in color_by_name.items():
            self.search([("name", "=", name)]).write({"color": color})

    @api.onchange("closed")
    def _onchange_closed(self):
        if not self.closed:
            self.close_from_portal = False
