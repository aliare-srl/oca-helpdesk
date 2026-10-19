from odoo import _, api, fields, models

from ..services import agent_client


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ais_whatsapp_agent_disabled = fields.Boolean(
        string="Desactivar el agente de IA",
        config_parameter="ais_helpdesk_whatsapp.agent_disabled",
        help="Si se marca, ninguna conversación nueva la contesta la IA: pasan directo a esperar "
        "a una persona, avisándole al cliente. No afecta a las conversaciones que ya está "
        "atendiendo una persona.",
    )
    ais_whatsapp_budget_usd = fields.Float(
        string="Tope de gasto mensual de IA (USD)",
        config_parameter="ais_helpdesk_whatsapp.budget_usd",
        help="Si el gasto estimado de IA del mes llega a este monto, el agente se desactiva solo: las "
        "conversaciones nuevas esperan a una persona. Se reactiva el día 1 o al subir el monto. "
        "0 = sin tope.",
    )
    ais_whatsapp_month_usage = fields.Char(
        string="Gasto de IA del mes",
        readonly=True,
        help="Costo estimado (según los precios cargados en el servicio), no la factura del proveedor.",
    )
    ais_whatsapp_quota_category_ids = fields.Many2many(
        "helpdesk.ticket.category",
        "ais_whatsapp_settings_quota_category_rel",
        "settings_id",
        "category_id",
        string="Categorías de consultas (cuentan para el tope)",
        help="Solo los tickets de estas categorías (por ejemplo consultas, reclamos y errores de Odoo) cuentan "
        "para el tope de tickets por mes de cada empresa. Los tickets de consulta que crea la IA van con la "
        "primera de la lista (la de menor id). Si queda vacía, no se asigna categoría y cuentan todos.",
    )
    ais_whatsapp_urgent_category_ids = fields.Many2many(
        "helpdesk.ticket.category",
        "ais_whatsapp_settings_urgent_category_rel",
        "settings_id",
        "category_id",
        string="Categorías de urgencias",
        help="Categorías con las que se clasifican las urgencias. No cuentan para el tope. Los tickets de "
        "urgencia que crea la IA van con la primera de la lista (la de menor id).",
    )
    ais_whatsapp_service_url = fields.Char(
        string="URL del servicio de WhatsApp",
        config_parameter="ais_helpdesk_whatsapp.service_url",
        help="URL base del servicio AgenteIA-MesadeAyuda-Odoo, sin la barra final "
        "(ej. https://mesaayuda.mochipa.com.ar).",
    )
    ais_whatsapp_panel_api_key = fields.Char(
        string="Clave de la API (X-Panel-Key)",
        config_parameter="ais_helpdesk_whatsapp.panel_api_key",
    )
    ais_whatsapp_ai_user_id = fields.Many2one(
        "res.users",
        string="Usuario de la IA",
        config_parameter="ais_helpdesk_whatsapp.ai_user_id",
        help="A nombre de quién queda asignado un ticket mientras lo atiende la IA (al tomar una "
        "conversación pasa al usuario que la tomó; al devolverla, vuelve a este).",
    )
    ais_whatsapp_requirement_category_id = fields.Many2one(
        "helpdesk.ticket.category",
        string="Categoría de nuevos requerimientos",
        config_parameter="ais_helpdesk_whatsapp.requirement_category_id",
        help="Categoría con la que la IA registra lo que el cliente pide y Odoo no hace (nuevos "
        "requerimientos). No cuenta para el tope mensual y el ticket queda abierto para su evaluación.",
    )
    ais_whatsapp_requirement_user_id = fields.Many2one(
        "res.users",
        string="Responsable de nuevos requerimientos",
        config_parameter="ais_helpdesk_whatsapp.requirement_user_id",
        help="Usuario de desarrollo al que se asignan los tickets de nuevos requerimientos que registra la IA.",
    )
    ais_whatsapp_inactivity_close_minutes = fields.Integer(
        string="Minutos de inactividad del cliente para cerrar solo",
        config_parameter="ais_helpdesk_whatsapp.inactivity_close_minutes",
        default=30,
        help="Si el cliente no vuelve a escribir en este tiempo, se cierra la conversación y el "
        "ticket solos, avisándole. 0 desactiva el cierre automático.",
    )
    ais_whatsapp_inactivity_unattended_text = fields.Char(
        string="Mensaje al cerrar por falta de atención",
        config_parameter="ais_helpdesk_whatsapp.inactivity_unattended_text",
        default="Le pedimos disculpas, en este momento no podemos atenderlo. Por favor, intente más tarde.",
        help="Se manda al cerrar solas las conversaciones a las que nadie le respondió (no las atiende la IA y "
        "ninguna persona le escribió después de su último mensaje). Las urgencias nunca se cierran solas.",
    )
    ais_whatsapp_refresh_seconds = fields.Integer(
        string="Segundos entre actualizaciones de la pantalla",
        config_parameter="ais_helpdesk_whatsapp.refresh_seconds",
        default=4,
        help="Cada cuánto se refresca sola la lista de conversaciones y el chat abierto.",
    )
    ais_whatsapp_waiting_human_alert_minutes = fields.Integer(
        string="Minutos entre avisos de conversaciones esperando",
        config_parameter="ais_helpdesk_whatsapp.waiting_human_alert_minutes",
        default=15,
        help="Mientras haya conversaciones esperando a una persona, se avisa por mail al equipo "
        "cada este tiempo (se repite solo si la cola no se vació). 0 desactiva el aviso.",
    )
    ais_whatsapp_waiting_human_team_id = fields.Many2one(
        "helpdesk.ticket.team",
        string="Equipo para avisos de conversaciones esperando",
        config_parameter="ais_helpdesk_whatsapp.waiting_human_team_id",
        help="El aviso se manda por mail y WhatsApp a cada miembro de este equipo (con el mail o "
        "el móvil cargado en su contacto), menos el usuario de la IA. El WhatsApp necesita además "
        "una plantilla aprobada por Meta configurada en el servicio.",
    )

    ais_whatsapp_wait_notice_1_enabled = fields.Boolean(
        string="Aviso 1: operadores ocupados",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_1_enabled",
        help="Se manda a los clientes que esperan a una persona. No se manda si el aviso 2 está activo.",
    )
    ais_whatsapp_wait_notice_1_text = fields.Char(
        string="Texto del aviso 1",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_1_text",
        default="Estimado cliente, en este momento todos nuestros operadores se encuentran ocupados. "
        "En cuanto uno de ellos esté disponible, te atenderemos a la brevedad. "
        "Muchas gracias por tu paciencia.",
    )
    ais_whatsapp_wait_notice_1_minutes = fields.Integer(
        string="Minutos entre avisos 1",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_1_minutes",
        default=5,
        help="El primero sale al cumplirse este tiempo de espera; luego se repite cada este tiempo.",
    )
    ais_whatsapp_wait_notice_2_enabled = fields.Boolean(
        string="Aviso 2: demora",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_2_enabled",
        help="Se manda a los clientes que esperan a una persona. Si está activo, tiene prioridad y el aviso 1 no se manda.",
    )
    ais_whatsapp_wait_notice_2_text = fields.Char(
        string="Texto del aviso 2",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_2_text",
        default="Estimado cliente, debido a la alta demanda de consultas, actualmente tenemos una demora "
        "aproximada de 30 minutos en la atención.\n\nEn cuanto un operador esté disponible, atenderemos "
        "tu consulta a la brevedad.\n\nAgradecemos tu paciencia y comprensión.",
    )
    ais_whatsapp_wait_notice_2_minutes = fields.Integer(
        string="Minutos entre avisos 2",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_2_minutes",
        default=10,
        help="El primero sale al cumplirse este tiempo de espera; luego se repite cada este tiempo.",
    )
    ais_whatsapp_wait_notice_max = fields.Integer(
        string="Máximo de avisos por conversación",
        config_parameter="ais_helpdesk_whatsapp.wait_notice_max",
        default=3,
        help="Cuántos avisos de espera recibe como máximo el cliente en cada espera (vale para los dos avisos). "
        "0 = sin límite. Vuelve a contar si la conversación deja de esperar y vuelve a esperar.",
    )

    # Many2many no se guarda solo en un parámetro del sistema: se guardan los ids separados por coma.
    _CATEGORY_PARAMS = {
        "ais_whatsapp_quota_category_ids": "ais_helpdesk_whatsapp.quota_category_ids",
        "ais_whatsapp_urgent_category_ids": "ais_helpdesk_whatsapp.urgent_category_ids",
    }

    @api.model
    def get_values(self):
        res = super().get_values()
        # Un campo calculado no llega al abrir Ajustes (Odoo no lo manda en el onchange inicial): se carga acá.
        usage = agent_client.get_usage(self.env)
        res["ais_whatsapp_month_usage"] = _("No disponible") if usage is None else "USD %.2f" % usage["spent"]
        params = self.env["ir.config_parameter"].sudo()
        for field, key in self._CATEGORY_PARAMS.items():
            ids = [int(i) for i in (params.get_param(key) or "").split(",") if i.strip().isdigit()]
            res[field] = [(6, 0, ids)]
        return res

    def set_values(self):
        super().set_values()
        params = self.env["ir.config_parameter"].sudo()
        for field, key in self._CATEGORY_PARAMS.items():
            params.set_param(key, ",".join(str(i) for i in sorted(self[field].ids)) or False)

