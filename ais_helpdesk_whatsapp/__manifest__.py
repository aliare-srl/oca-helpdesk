{
    "name": "Mesa de Ayuda - WhatsApp",
    "version": "15.0.2.6.0",
    "category": "Helpdesk",
    "summary": "Ver y atender desde Odoo las conversaciones de WhatsApp del agente de IA",
    "author": "Aliare SRL",
    "website": "https://aliare.com.ar",
    "license": "LGPL-3",
    "depends": ["helpdesk_mgmt"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/whatsapp_conversation_views.xml",
        "views/helpdesk_ticket_views.xml",
        "wizards/whatsapp_reply_wizard_views.xml",
        "wizards/whatsapp_start_wizard_views.xml",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ais_helpdesk_whatsapp/static/src/js/whatsapp_dashboard.js",
            "ais_helpdesk_whatsapp/static/src/scss/whatsapp_dashboard.scss",
        ],
        "web.assets_qweb": [
            "ais_helpdesk_whatsapp/static/src/xml/whatsapp_dashboard.xml",
        ],
    },
    "installable": True,
    "application": False,
}
