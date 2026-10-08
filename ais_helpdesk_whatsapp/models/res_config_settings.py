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
