# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Reconstruye sla_status_at_close para tickets ya cerrados, a partir de
    fecha_limite y closed_date (ya existentes), para que el panel de
    Cumplimiento tenga historial desde el día uno.

    resolution_hours/assignment_hours son computed+store: Odoo los recalcula
    solos para los registros existentes al agregar la columna, no requieren
    backfill manual acá.
    """
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE helpdesk_ticket t
        SET sla_status_at_close = CASE
            WHEN (
                EXTRACT(EPOCH FROM (t.closed_date - t.create_date))
                / EXTRACT(EPOCH FROM (t.fecha_limite - t.create_date))
            ) > 1.0 THEN 'red'
            WHEN (
                EXTRACT(EPOCH FROM (t.closed_date - t.create_date))
                / EXTRACT(EPOCH FROM (t.fecha_limite - t.create_date))
            ) >= 0.75 THEN 'yellow'
            ELSE 'green'
        END
        WHERE t.closed_date IS NOT NULL
          AND t.fecha_limite IS NOT NULL
          AND t.fecha_limite > t.create_date
          AND t.sla_status_at_close IS NULL
        """,
    )
