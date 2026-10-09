from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

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
