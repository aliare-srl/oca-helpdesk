from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ais_whatsapp_agent_disabled = fields.Boolean(
        string="Desactivar el agente de IA",
        config_parameter="ais_helpdesk_whatsapp.agent_disabled",
        help="Si se marca, ninguna conversación nueva la contesta la IA: pasan directo a esperar "
        "a una persona, avisándole al cliente. No afecta a las conversaciones que ya está "
        "atendiendo una persona.",
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
    ais_whatsapp_inactivity_close_minutes = fields.Integer(
        string="Minutos de inactividad del cliente para cerrar solo",
        config_parameter="ais_helpdesk_whatsapp.inactivity_close_minutes",
        default=30,
        help="Si el cliente no vuelve a escribir en este tiempo, se cierra la conversación y el "
        "ticket solos, avisándole. 0 desactiva el cierre automático.",
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
