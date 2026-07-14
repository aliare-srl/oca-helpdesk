# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """- Asigna el horario laboral por defecto a las compañías que no tengan
    uno configurado.
    - Recalcula fecha_limite, sla_target_hours, resolution_hours y
    assignment_hours de todos los tickets: la lógica de cálculo pasó de
    horas corridas a horas laborales, así que no alcanza con que Odoo
    recompute solo columnas nuevas, hay que forzar el recálculo de las
    que ya existían.
    - Recalcula el semáforo SLA de los tickets abiertos y reconstruye
    sla_status_at_close de los tickets ya cerrados con la nueva lógica.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    default_calendar = env.ref(
        "helpdesk_mgmt.helpdesk_default_resource_calendar", raise_if_not_found=False
    )
    if default_calendar:
        companies = env["res.company"].search([("helpdesk_resource_calendar_id", "=", False)])
        if companies:
            companies.write({"helpdesk_resource_calendar_id": default_calendar.id})

    Ticket = env["helpdesk.ticket"]
    tickets = Ticket.with_context(active_test=False).search([])
    if not tickets:
        return

    tickets._compute_fecha_limite()
    tickets._compute_resolution_hours()
    tickets._compute_assignment_hours()
    tickets.flush(
        ["fecha_limite", "sla_target_hours", "resolution_hours", "assignment_hours"]
    )

    open_tickets = tickets.filtered(lambda t: not t.closed)
    open_tickets._update_sla_status()

    closed_tickets = tickets.filtered(lambda t: t.closed)
    for ticket in closed_tickets:
        total = ticket.sla_target_hours
        if not total:
            continue
        pct = ticket.resolution_hours / total
        if pct > 1.0:
            status = "red"
        elif pct >= 0.75:
            status = "yellow"
        else:
            status = "green"
        ticket.sla_status_at_close = status
    tickets.flush(["sla_status", "sla_status_at_close"])

    _logger.info(
        "helpdesk_mgmt 15.0.4.7.0: recalculados %s tickets con horario laboral",
        len(tickets),
    )
