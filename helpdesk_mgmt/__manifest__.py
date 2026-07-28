# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Management",
    "summary": """
        Helpdesk""",
    "version": "15.0.4.7.1",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "AdaptiveCity, "
    "Tecnativa, "
    "ForgeFlow, "
    "C2i Change 2 Improve, "
    "Domatix, "
    "Factor Libre, "
    "SDi Soluciones, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/helpdesk",
    "depends": ["mail", "portal", "resource"],
    "data": [
        "data/helpdesk_data.xml",
        "data/helpdesk_stage_colors.xml",
        "data/helpdesk_sla_cron.xml",
        "security/helpdesk_security.xml",
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/helpdesk_ticket_templates.xml",
        "views/helpdesk_ticket_menu.xml",
        "views/helpdesk_ticket_team_views.xml",
        "views/helpdesk_ticket_stage_views.xml",
        "views/helpdesk_ticket_category_views.xml",
        "views/helpdesk_ticket_channel_views.xml",
        "views/helpdesk_ticket_tag_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/helpdesk_dashboard_views.xml",
    ],
    "demo": ["demo/helpdesk_demo.xml"],
    "assets": {
        "web.assets_backend": [
            "helpdesk_mgmt/static/src/css/helpdesk_styles.css",
            "helpdesk_mgmt/static/src/css/helpdesk_dashboard.css",
            "helpdesk_mgmt/static/src/js/helpdesk_tab_fix.js",
            "helpdesk_mgmt/static/src/js/helpdesk_list_tab_add.js",
            "helpdesk_mgmt/static/src/js/helpdesk_list_save_reload.js",
            "helpdesk_mgmt/static/src/js/helpdesk_sla_notifications.js",
            "helpdesk_mgmt/static/src/js/notification_handler.js",
            "helpdesk_mgmt/static/src/js/helpdesk_dashboard/helpdesk_dashboard.js",
        ],
        "web.assets_qweb": [
            "helpdesk_mgmt/static/src/xml/helpdesk_dashboard.xml",
        ],
        "web.assets_frontend": [
            "helpdesk_mgmt/static/src/js/new_ticket.js",
            "helpdesk_mgmt/static/src/js/portal_ticket_deflection.js",
        ],
    },
    "development_status": "Beta",
    "application": True,
    "installable": True,
}
