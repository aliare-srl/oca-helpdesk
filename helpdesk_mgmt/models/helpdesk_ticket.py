import logging
from datetime import timedelta

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _order = "create_date desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    @api.depends("team_id")
    def _compute_stage_id(self):
        for ticket in self:
            ticket.stage_id = ticket.team_id._get_applicable_stages()[:1]

    @api.depends("stage_id.name")
    def _compute_stage_color_index(self):
        color_map = {
            "Nuevo": 8,       "New": 8,
            "En progreso": 4, "In Progress": 4,
            "En espera": 3,   "Awaiting": 3,
            "Hecho": 10,      "Done": 10,
            "Cancelado": 1,   "Cancelled": 1,
            "Rechazado": 2,   "Rejected": 2,
        }
        for ticket in self:
            ticket.stage_color_index = color_map.get(ticket.stage_id.name, 0)

    @api.depends("stage_id.name")
    def _compute_stage_css_class(self):
        css_map = {
            "Nuevo": "bg_nuevo",
            "En progreso": "bg_progreso",
            "En espera": "bg_espera",
            "Hecho": "bg_hecho",
            "Cancelado": "bg_cancelado",
        }
        for ticket in self:
            ticket.stage_css_class = css_map.get(ticket.stage_id.name, "")

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Show always the stages without team, or stages of the default team."""
        search_domain = [
            "|",
            ("id", "in", stages.ids),
            ("team_ids", "=", False),
        ]
        default_team_id = self.default_get(["team_id"]).get("team_id")
        if default_team_id:
            search_domain = [
                "|",
                ("team_ids", "=", default_team_id),
            ] + search_domain
        return stages.search(search_domain, order=order)

    number = fields.Char(string="Ticket number", default="/", readonly=True)
    name = fields.Char(string="Title", required=True)
    description = fields.Html(sanitize_style=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned user",
        tracking=False,
        index=True,
        domain="team_id and [('share', '=', False),('id', 'in', user_ids)] or [('share', '=', False)]",  # noqa: B950
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        string="Stage",
        compute="_compute_stage_id",
        store=True,
        readonly=False,
        ondelete="restrict",
        tracking=True,
        group_expand="_read_group_stage_ids",
        copy=False,
        index=True,
        domain="['|',('team_ids', '=', team_id),('team_ids','=',False)]",
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")
    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    assigned_date = fields.Datetime()
    closed_date = fields.Datetime()
    planned_date = fields.Datetime(
        string="Fecha y Hora Prevista",
        help="Compromiso de ejecución",
        default=fields.Datetime.now,
    )
    stage_name = fields.Char(related="stage_id.name", string="Nombre de Etapa")
    stage_color_index = fields.Integer(
        string="Color de Calendario",
        compute="_compute_stage_color_index",
        store=True,
    )
    stage_css_class = fields.Char(
        string="Stage CSS Class", compute="_compute_stage_css_class"
    )
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Tags")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
        help="Channel indicates where the source of a ticket"
        "comes from (it could be a phone call, an email...)",
    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team",
        index=True,
    )
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        default="1",
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="helpdesk_ticket_ir_attachment_rel",
        column1="ticket_id",
        column2="attachment_id",
        string="Attachments",
    )
    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
    )
    sequence = fields.Integer(
        index=True,
        default=10,
        help="Gives the sequence order when displaying a list of tickets.",
    )
    active = fields.Boolean(default=True)

    fecha_limite = fields.Datetime(
        string="Fecha Límite SLA",
        compute="_compute_fecha_limite",
        store=True,
        readonly=True,
    )
    sla_target_hours = fields.Float(
        string="Horas Objetivo SLA",
        compute="_compute_fecha_limite",
        store=True,
        help="Horas laborales objetivo según categoría y prioridad, usadas "
        "para calcular fecha_limite y el % de SLA consumido.",
    )
    sla_status = fields.Selection(
        selection=[
            ("green", "\U0001F7E2 En Tiempo"),
            ("yellow", "\U0001F7E1 Próximo a Vencer"),
            ("red", "\U0001F534 Vencido"),
            ("done", "✅ Finalizado"),
        ],
        string="Estado SLA",
        store=True,
    )
    sla_yellow_sent = fields.Boolean(default=False)
    sla_red_sent = fields.Boolean(default=False)
    sla_status_at_close = fields.Selection(
        selection=[
            ("green", "\U0001F7E2 En Tiempo"),
            ("yellow", "\U0001F7E1 Próximo a Vencer"),
            ("red", "\U0001F534 Vencido"),
        ],
        string="Estado SLA al Cierre",
        copy=False,
        help="Color de SLA que tenía el ticket justo antes de cerrarse. "
        "Se fija una sola vez y no cambia aunque el ticket se reabra.",
    )
    resolution_hours = fields.Float(
        string="Horas hasta Resolución",
        compute="_compute_resolution_hours",
        store=True,
    )
    assignment_hours = fields.Float(
        string="Horas hasta Asignación",
        compute="_compute_assignment_hours",
        store=True,
    )
    portal_notification_sent = fields.Boolean(
        string="Notificación de portal enviada",
        default=False,
        copy=False,
    )
    observations = fields.Html(string="Observaciones", sanitize_style=True)

    _SLA_PRIORITY_MAP = {"0": "normal", "1": "normal", "2": "alta", "3": "urgente"}

    @api.depends("category_id", "priority", "create_date", "company_id")
    def _compute_fecha_limite(self):
        for ticket in self:
            if not ticket.create_date or not ticket.category_id:
                ticket.fecha_limite = False
                ticket.sla_target_hours = 0.0
                continue
            sla_key = self._SLA_PRIORITY_MAP.get(ticket.priority, "normal")
            config = ticket.category_id.sla_config_ids.filtered(
                lambda c, k=sla_key: c.priority == k
            )
            if not config:
                ticket.fecha_limite = False
                ticket.sla_target_hours = 0.0
                continue
            hours = config[0].hours
            calendar = ticket.company_id.helpdesk_resource_calendar_id
            if calendar:
                ticket.fecha_limite = calendar.plan_hours(
                    hours, ticket.create_date, compute_leaves=True
                )
            else:
                ticket.fecha_limite = ticket.create_date + timedelta(hours=hours)
            ticket.sla_target_hours = hours

    def _work_hours_between(self, start, end):
        """Horas laborales entre dos datetimes, según el calendario de la
        compañía. Si no hay calendario configurado, cae a horas corridas."""
        self.ensure_one()
        calendar = self.company_id.helpdesk_resource_calendar_id
        if calendar:
            return calendar.get_work_hours_count(start, end, compute_leaves=True)
        return (end - start).total_seconds() / 3600.0

    def _get_sla_hours_progress(self, at_datetime):
        """Devuelve (horas_transcurridas, horas_objetivo) según el horario
        laboral configurado, para saber qué % de SLA se consumió."""
        self.ensure_one()
        elapsed = self._work_hours_between(self.create_date, at_datetime)
        return elapsed, self.sla_target_hours

    @api.depends("closed_date", "create_date")
    def _compute_resolution_hours(self):
        for ticket in self:
            if ticket.closed_date and ticket.create_date:
                ticket.resolution_hours = ticket._work_hours_between(
                    ticket.create_date, ticket.closed_date
                )
            else:
                ticket.resolution_hours = 0.0

    @api.depends("assigned_date", "create_date")
    def _compute_assignment_hours(self):
        for ticket in self:
            if ticket.assigned_date and ticket.create_date:
                ticket.assignment_hours = ticket._work_hours_between(
                    ticket.create_date, ticket.assigned_date
                )
            else:
                ticket.assignment_hours = 0.0

    def _update_sla_status(self):
        now = fields.Datetime.now()
        for ticket in self:
            if ticket.stage_id.closed:
                vals = {"sla_status": "done"}
                if not ticket.sla_status_at_close and ticket.sla_status in (
                    "green",
                    "yellow",
                    "red",
                ):
                    vals["sla_status_at_close"] = ticket.sla_status
                ticket.with_context(skip_sla_update=True).write(vals)
                continue
            if not ticket.fecha_limite or not ticket.create_date:
                ticket.with_context(skip_sla_update=True).write({"sla_status": False})
                continue
            elapsed, total = ticket._get_sla_hours_progress(now)
            if total <= 0:
                status = "red"
            else:
                pct = elapsed / total
                if pct < 0.75:
                    status = "green"
                elif pct <= 1.0:
                    status = "yellow"
                else:
                    status = "red"
            ticket.with_context(skip_sla_update=True).write({"sla_status": status})

    @api.model
    def _cron_check_sla(self):
        now = fields.Datetime.now()
        tickets = self.sudo().search(
            [("closed", "=", False), ("fecha_limite", "!=", False)]
        )
        for ticket in tickets:
            if not ticket.create_date:
                continue
            elapsed, total = ticket._get_sla_hours_progress(now)
            if total <= 0:
                continue
            pct = elapsed / total

            if pct < 0.75:
                new_status = "green"
            elif pct <= 1.0:
                new_status = "yellow"
            else:
                new_status = "red"

            vals = {"sla_status": new_status}

            if pct >= 0.75 and not ticket.sla_yellow_sent:
                ticket.message_post(
                    body=_(
                        "⚠️ <b>Aviso SLA:</b> Este ticket está próximo a vencer "
                        "(75%% del tiempo consumido). Responsable: %s"
                    )
                    % (ticket.user_id.name or _("Sin asignar")),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=ticket.user_id.partner_id.ids if ticket.user_id else [],
                )
                vals["sla_yellow_sent"] = True

            if pct >= 1.0 and not ticket.sla_red_sent:
                ticket.message_post(
                    body=_(
                        "🚨 <b>Alerta SLA VENCIDO:</b> El ticket ha superado su plazo "
                        "límite de atención. Responsable: %s"
                    )
                    % (ticket.user_id.name or _("Sin asignar")),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=ticket.user_id.partner_id.ids if ticket.user_id else [],
                )
                if ticket.user_id and ticket.user_id.partner_id:
                    self.env["bus.bus"]._sendone(
                        ticket.user_id.partner_id,
                        "simple_notification",
                        {
                            "title": _("SLA Vencido"),
                            "message": _(
                                "El ticket %s ha superado su plazo de SLA."
                            )
                            % ticket.number,
                            "sticky": True,
                            "warning": True,
                        },
                    )
                vals["sla_red_sent"] = True

            ticket.with_context(skip_sla_update=True).write(vals)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res


    @api.model
    def get_sla_alerts_for_current_user(self):
        now = fields.Datetime.now()
        uid = self.env.user.id
        tickets = self.sudo().search([
            ("closed", "=", False),
            ("user_id", "=", uid),
            ("sla_status", "in", ["yellow", "red"]),
            ("fecha_limite", "!=", False),
        ], order="fecha_limite asc")
        result = []
        for ticket in tickets:
            total = (ticket.fecha_limite - ticket.create_date).total_seconds()
            elapsed = (now - ticket.create_date).total_seconds()
            pct = round((elapsed / total * 100), 1) if total > 0 else 100.0
            result.append({
                "id": ticket.id,
                "number": ticket.number or "",
                "name": ticket.name or "",
                "sla_status": ticket.sla_status,
                "fecha_limite": fields.Datetime.to_string(ticket.fecha_limite),
                "pct": pct,
            })
        return result

    @api.model
    def get_dashboard_data(
        self, view="open", date_from=None, date_to=None, team_id=None, category_id=None
    ):
        """Punto de entrada del panel. view='open' → tickets abiertos (foto
        actual, date_from/date_to filtran por fecha de creación). view='done'
        → tickets hechos (date_from/date_to filtran por fecha de cierre)."""
        if not self.env.user.has_group("helpdesk_mgmt.group_helpdesk_manager"):
            raise AccessError(_("No tiene permisos para ver el panel de cumplimiento."))
        team_id = int(team_id) if team_id else False
        category_id = int(category_id) if category_id else False
        if view == "done":
            return self._get_done_dashboard_data(date_from, date_to, team_id, category_id)
        return self._get_open_dashboard_data(date_from, date_to, team_id, category_id)

    def _get_open_dashboard_data(self, date_from, date_to, team_id, category_id):
        Ticket = self.sudo()
        open_domain = [("closed", "=", False)]
        if team_id:
            open_domain.append(("team_id", "=", team_id))
        if category_id:
            open_domain.append(("category_id", "=", category_id))
        if date_from:
            open_domain.append(("create_date", ">=", date_from))
        if date_to:
            open_domain.append(("create_date", "<=", date_to))

        now = fields.Datetime.now()
        open_tickets = Ticket.search(open_domain)
        waiting_hours = {
            ticket.id: ticket._work_hours_between(ticket.create_date, now)
            for ticket in open_tickets
        }

        total = len(open_tickets)
        green = len(open_tickets.filtered(lambda t: t.sla_status == "green"))
        yellow = len(open_tickets.filtered(lambda t: t.sla_status == "yellow"))
        red = len(open_tickets.filtered(lambda t: t.sla_status == "red"))
        avg_wait = round(sum(waiting_hours.values()) / total, 1) if total else 0.0

        category_breakdown = self._build_breakdown(
            open_domain, "category_id", _("Sin categoría"), "sla_status"
        )
        user_breakdown = self._build_breakdown(
            open_domain, "user_id", _("Sin asignar"), "sla_status"
        )
        partner_breakdown = self._build_breakdown(
            open_domain, "partner_id", _("Sin cliente"), "sla_status"
        )
        priority_breakdown = self._build_priority_breakdown(open_domain, "sla_status")

        top_delayed = sorted(open_tickets, key=lambda t: waiting_hours[t.id], reverse=True)[:10]
        top_delayed_data = [
            self._ranking_row(ticket, waiting_hours[ticket.id], ticket.sla_status)
            for ticket in top_delayed
        ]

        return {
            "kpis": {
                "open_count": total,
                "green": green,
                "yellow": yellow,
                "red": red,
                "avg_wait_hours": avg_wait,
            },
            "category_breakdown": category_breakdown,
            "user_breakdown": user_breakdown,
            "partner_breakdown": partner_breakdown,
            "priority_breakdown": priority_breakdown,
            "top_delayed": top_delayed_data,
        }

    def _get_done_dashboard_data(self, date_from, date_to, team_id, category_id):
        Ticket = self.sudo()
        closed_domain = [("closed", "=", True), ("closed_date", "!=", False)]
        if team_id:
            closed_domain.append(("team_id", "=", team_id))
        if category_id:
            closed_domain.append(("category_id", "=", category_id))
        if date_from:
            closed_domain.append(("closed_date", ">=", date_from))
        if date_to:
            closed_domain.append(("closed_date", "<=", date_to))

        closed_tickets = Ticket.search(closed_domain)
        total = len(closed_tickets)
        green = len(closed_tickets.filtered(lambda t: t.sla_status_at_close == "green"))
        yellow = len(closed_tickets.filtered(lambda t: t.sla_status_at_close == "yellow"))
        red = len(closed_tickets.filtered(lambda t: t.sla_status_at_close == "red"))
        avg_resolution = (
            round(sum(closed_tickets.mapped("resolution_hours")) / total, 1) if total else 0.0
        )

        category_breakdown = self._build_breakdown(
            closed_domain, "category_id", _("Sin categoría"), "sla_status_at_close", with_avg_resolution=True
        )
        user_breakdown = self._build_breakdown(
            closed_domain, "user_id", _("Sin asignar"), "sla_status_at_close", with_avg_resolution=True
        )
        partner_breakdown = self._build_breakdown(
            closed_domain, "partner_id", _("Sin cliente"), "sla_status_at_close", with_avg_resolution=True
        )
        priority_breakdown = self._build_priority_breakdown(
            closed_domain, "sla_status_at_close", with_avg_resolution=True
        )

        top_resolution = closed_tickets.sorted(key=lambda t: t.resolution_hours, reverse=True)[:10]
        top_resolution_data = [
            self._ranking_row(ticket, ticket.resolution_hours, ticket.sla_status_at_close)
            for ticket in top_resolution
        ]

        overdue_closed = closed_tickets.filtered(
            lambda t: t.sla_status_at_close == "red" and t.fecha_limite
        )
        overdue_delay = {
            ticket.id: ticket._work_hours_between(ticket.fecha_limite, ticket.closed_date)
            for ticket in overdue_closed
        }
        top_overdue = sorted(overdue_closed, key=lambda t: overdue_delay[t.id], reverse=True)[:10]
        top_overdue_data = [
            self._ranking_row(ticket, overdue_delay[ticket.id], ticket.sla_status_at_close)
            for ticket in top_overdue
        ]

        return {
            "kpis": {
                "done_count": total,
                "avg_resolution_hours": avg_resolution,
                "green": green,
                "yellow": yellow,
                "red": red,
            },
            "category_breakdown": category_breakdown,
            "user_breakdown": user_breakdown,
            "partner_breakdown": partner_breakdown,
            "priority_breakdown": priority_breakdown,
            "top_resolution": top_resolution_data,
            "top_overdue": top_overdue_data,
        }

    def _ranking_row(self, ticket, hours_value, sla_status):
        return {
            "number": ticket.number or "",
            "name": ticket.name or "",
            "category": ticket.category_id.name or _("Sin categoría"),
            "partner": ticket.partner_id.name or ticket.partner_name or _("Sin cliente"),
            "user": ticket.user_id.name or _("Sin asignar"),
            "hours": round(hours_value, 1),
            "sla_status": sla_status or False,
        }

    def _build_breakdown(
        self, domain, groupby_field, no_group_label, status_field, with_avg_resolution=False
    ):
        """Agrupado por groupby_field (Many2one): total y cuántos están
        verde/amarillo/rojo según status_field ('sla_status' para abiertos,
        'sla_status_at_close' para hechos). Si with_avg_resolution, agrega
        el tiempo promedio de resolución por grupo."""
        Ticket = self.sudo()

        names = {}
        totals = {}
        for row in Ticket.read_group(domain, ["id"], [groupby_field], lazy=False):
            key = row[groupby_field]
            gid = key[0] if key else 0
            names[gid] = key[1] if key else no_group_label
            totals[gid] = row["__count"]

        status_counts = {}
        for row in Ticket.read_group(
            domain + [(status_field, "in", ["green", "yellow", "red"])],
            [groupby_field, status_field],
            [groupby_field, status_field],
            lazy=False,
        ):
            key = row[groupby_field]
            gid = key[0] if key else 0
            names.setdefault(gid, key[1] if key else no_group_label)
            entry = status_counts.setdefault(gid, {"green": 0, "yellow": 0, "red": 0})
            entry[row[status_field]] += row["__count"]

        avg_hours = {}
        if with_avg_resolution:
            for row in Ticket.read_group(
                domain, ["resolution_hours:avg"], [groupby_field], lazy=False
            ):
                key = row[groupby_field]
                gid = key[0] if key else 0
                avg_hours[gid] = round(row["resolution_hours"] or 0.0, 1)

        result = []
        for gid, total in totals.items():
            status = status_counts.get(gid, {"green": 0, "yellow": 0, "red": 0})
            row = {
                "id": gid,
                "name": names.get(gid, no_group_label),
                "total": total,
                "green": status["green"],
                "yellow": status["yellow"],
                "red": status["red"],
            }
            if with_avg_resolution:
                row["avg_resolution_hours"] = avg_hours.get(gid, 0.0)
            result.append(row)
        result.sort(key=lambda r: r["total"], reverse=True)
        return result

    def _build_priority_breakdown(self, domain, status_field, with_avg_resolution=False):
        """Igual que _build_breakdown pero agrupado por prioridad (Selection,
        no Many2one): mantiene siempre las 4 prioridades, en orden Baja→Muy
        Alta, incluso con 0 tickets."""
        Ticket = self.sudo()
        priority_labels = dict(self._fields["priority"].selection)
        priority_order = [key for key, _label in self._fields["priority"].selection]

        totals = {
            row["priority"]: row["__count"]
            for row in Ticket.read_group(domain, ["id"], ["priority"], lazy=False)
        }

        status_counts = {}
        for row in Ticket.read_group(
            domain + [(status_field, "in", ["green", "yellow", "red"])],
            ["priority", status_field],
            ["priority", status_field],
            lazy=False,
        ):
            entry = status_counts.setdefault(row["priority"], {"green": 0, "yellow": 0, "red": 0})
            entry[row[status_field]] += row["__count"]

        avg_hours = {}
        if with_avg_resolution:
            avg_hours = {
                row["priority"]: round(row["resolution_hours"] or 0.0, 1)
                for row in Ticket.read_group(
                    domain, ["resolution_hours:avg"], ["priority"], lazy=False
                )
            }

        result = []
        for key in priority_order:
            status = status_counts.get(key, {"green": 0, "yellow": 0, "red": 0})
            row = {
                "id": key,
                "name": priority_labels.get(key, key),
                "total": totals.get(key, 0),
                "green": status["green"],
                "yellow": status["yellow"],
                "red": status["red"],
            }
            if with_avg_resolution:
                row["avg_resolution_hours"] = avg_hours.get(key, 0.0)
            result.append(row)
        return result

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    def _creation_subtype(self):
        return self.env.ref("helpdesk_mgmt.hlp_tck_created")

    def _get_parent_cc_email(self):
        self.ensure_one()
        parent = self.partner_id.parent_id if self.partner_id else False
        return parent.email if parent and parent.email else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number", "/") == "/":
                vals["number"] = self._prepare_ticket_number(vals)
            if vals.get("user_id") and not vals.get("assigned_date"):
                vals["assigned_date"] = fields.Datetime.now()
            if vals.get("team_id"):
                team = self.env["helpdesk.ticket.team"].browse([vals["team_id"]])
                if team.company_id:
                    vals["company_id"] = team.company_id.id
        tickets = super().create(vals_list)
        tickets.with_context(skip_sla_update=True)._update_sla_status()
        if self.env.context.get("helpdesk_from_portal"):
            tickets._notify_new_ticket_bus()
        assign_template = self.env.ref(
            "helpdesk_mgmt.assigned_ticket_template",
            raise_if_not_found=False,
        )
        if assign_template:
            for ticket in tickets:
                if (
                    ticket.user_id
                    and ticket.user_id.partner_id.email
                    and ticket.user_id.id != ticket.create_uid.id
                ):
                    assign_template.send_mail(
                        ticket.id,
                        force_send=True,
                        email_values={
                            "email_to": ticket.user_id.partner_id.email,
                            "recipient_ids": [],
                        },
                    )
        return tickets

    def _notify_new_ticket_bus(self):
        group = self.env.ref("helpdesk_mgmt.group_helpdesk_user", raise_if_not_found=False)
        if not group:
            return
        for ticket in self:
            partner_name = ticket.partner_id.name or ticket.partner_name or ""
            payload = {
                "id": ticket.id,
                "number": ticket.number or "",
                "name": ticket.name or "",
                "partner": partner_name,
                "display_name": "[%s] %s – %s" % (
                    ticket.number or "?",
                    ticket.name or "",
                    partner_name,
                ),
            }
            for user in group.users:
                if not user.partner_id or not user.active:
                    continue
                _logger.info(
                    "[helpdesk] bus notify → usuario=%s ticket=%s partner=%s",
                    user.login, ticket.number, partner_name,
                )
                self.env["bus.bus"]._sendone(
                    user.partner_id,
                    "helpdesk_ticket_portal_notification",
                    payload,
                )

    @api.model
    def current_user_is_helpdesk(self):
        """
        Devuelve True si el usuario actual pertenece al grupo helpdesk_user.
        Usado por el JS para decidir si iniciar el polling.
        """
        group = self.env.ref(
            "helpdesk_mgmt.group_helpdesk_user", raise_if_not_found=False
        )
        return bool(group and self.env.user in group.users)

    @api.model
    def get_new_portal_tickets_for_notification(self):
        """
        Polling endpoint: devuelve tickets nuevos del portal creados
        en los últimos 90 segundos que aún no fueron notificados.
        Solo funciona para usuarios con permiso helpdesk_user.
        """
        group = self.env.ref(
            "helpdesk_mgmt.group_helpdesk_user", raise_if_not_found=False
        )
        if not group or self.env.user not in group.users:
            return []

        cutoff = fields.Datetime.now() - timedelta(seconds=90)

        portal_group = self.env.ref('base.group_portal')
        portal_user_ids = portal_group.users.ids

        web_channel = self.env.ref(
            "helpdesk_mgmt.helpdesk_ticket_channel_web", raise_if_not_found=False
        )

        domain = [
            ("create_date", ">=", cutoff),
            ("portal_notification_sent", "=", False),
            ("create_uid", "in", portal_user_ids),
        ]
        if web_channel:
            domain.append(("channel_id", "=", web_channel.id))

        tickets = self.search(domain)

        result = []
        for ticket in tickets:
            result.append({
                "id": ticket.id,
                "number": ticket.number or "",
                "name": ticket.name or "",
                "partner": ticket.partner_id.name or ticket.partner_name or "",
                "display_name": "[%s] %s – %s" % (
                    ticket.number or "?",
                    ticket.name or "",
                    ticket.partner_id.name or ticket.partner_name or "",
                ),
            })

        if result:
            tickets.write({"portal_notification_sent": True})

        return result

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        old_user_ids = {}
        if "user_id" in vals:
            for ticket in self:
                old_user_ids[ticket.id] = ticket.user_id.id

        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.closed:
                    vals["closed_date"] = now
            if vals.get("user_id"):
                vals["assigned_date"] = now
        result = super().write(vals)

        if "user_id" in vals and vals.get("user_id"):
            assign_template = self.env.ref(
                "helpdesk_mgmt.assigned_ticket_template",
                raise_if_not_found=False,
            )
            if assign_template:
                for ticket in self:
                    if old_user_ids.get(ticket.id) != ticket.user_id.id:
                        assign_template.send_mail(
                            ticket.id,
                            force_send=True,
                            email_values={
                                "email_to": ticket.user_id.partner_id.email,
                                "recipient_ids": [],
                            },
                        )

        if not self.env.context.get("skip_sla_update"):
            sla_triggers = {"stage_id", "category_id", "priority"}
            if any(f in vals for f in sla_triggers):
                self.with_context(skip_sla_update=True)._update_sla_status()
        return result

    def unlink(self):
        raise UserError(
            "Los tickets no pueden eliminarse. "
            "Si desea dar de baja un ticket, utilice la opción Archivar."
        )

    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/ticket/%s" % (item.id)
        return res

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        ticket = self[0]
        if "stage_id" in tracking and ticket.stage_id.mail_template_id:
            options = {
                # Need to set mass_mail so that the email will always be sent
                "composition_mode": "mass_mail",
                "auto_delete_message": True,
                "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                    "mail.mt_note"
                ),
                "email_layout_xmlid": "mail.mail_notification_light",
            }
            # Si el partner es sucursal, agregar la empresa madre como destinatario adicional
            parent = ticket.partner_id.parent_id if ticket.partner_id else False
            if parent and parent.email:
                options["partner_ids"] = [(4, parent.id)]
            res["stage_id"] = (ticket.stage_id.mail_template_id, options)
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        ticket = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)

        return ticket

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(partner_ids)
        return super().message_update(msg, update_vals=update_vals)

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id:
                    partner = ticket.partner_id
                    if partner.parent_id and partner.email:
                        # Usar email directo para evitar que Odoo enrute al commercial_partner
                        ticket._message_add_suggested_recipient(
                            recipients,
                            email=partner.email,
                            reason=_("Customer"),
                        )
                    else:
                        ticket._message_add_suggested_recipient(
                            recipients, partner=partner, reason=_("Customer")
                        )
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(
                        recipients,
                        email=ticket.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            return recipients
        return recipients

    def _notify_get_reply_to(
        self, default=None, records=None, company=None, doc_names=None
    ):
        """Override to set alias of tasks to their team if any."""
        aliases = (
            self.sudo()
            .mapped("team_id")
            ._notify_get_reply_to(
                default=default, records=None, company=company, doc_names=None
            )
        )
        res = {ticket.id: aliases.get(ticket.team_id.id) for ticket in self}
        leftover = self.filtered(lambda rec: not rec.team_id)
        if leftover:
            res.update(
                super(HelpdeskTicket, leftover)._notify_get_reply_to(
                    default=default, records=None, company=company, doc_names=doc_names
                )
            )
        return res
