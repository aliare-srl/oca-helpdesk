from datetime import datetime, timezone

from odoo import api, fields, models
from odoo.tools import html_escape

from odoo.addons.ais_helpdesk_whatsapp.services import agent_client

STATUS_SELECTION = [
    ("ai", "Atiende la IA"),
    ("waiting_human", "Esperando a un humano"),
    ("human", "Atiende un humano"),
    ("closed", "Cerrada"),
]

_SENDER_LABEL = {"customer": "Cliente", "ai": "IA", "human": "Persona"}


class WhatsappConversation(models.Model):
    """Copia liviana de una conversación. La fuente real es el servicio; esto es solo para mostrarla en Odoo."""

    _name = "ais.whatsapp.conversation"
    _description = "Conversación de WhatsApp"
    _inherit = ["mail.thread"]
    _order = "is_urgent desc, last_message_at desc"

    remote_id = fields.Integer(string="Id en el servicio", required=True, index=True)
    status = fields.Selection(STATUS_SELECTION, required=True, default="ai", tracking=True)
    is_urgent = fields.Boolean(string="Urgente")
    escalation_category = fields.Char(string="Motivo de escalamiento")
    escalation_reason = fields.Text(string="Detalle")
    wa_id = fields.Char(string="WhatsApp")
    contact_name = fields.Char(string="Contacto")
    company_name = fields.Char(string="Empresa")
    verified = fields.Boolean(string="Contacto verificado")
    helpdesk_ticket_remote_id = fields.Integer(string="Id del ticket")
    ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Ticket", compute="_compute_ticket_id", store=True
    )
    last_message_at = fields.Datetime(string="Último mensaje")
    created_at_remote = fields.Datetime(string="Creada")
    last_synced_message_id = fields.Integer(default=0)

    _sql_constraints = [
        ("remote_id_uniq", "unique(remote_id)", "Ya existe una conversación con ese id del servicio."),
    ]

    @api.depends("helpdesk_ticket_remote_id")
    def _compute_ticket_id(self):
        Ticket = self.env["helpdesk.ticket"]
        for record in self:
            record.ticket_id = (
                Ticket.browse(record.helpdesk_ticket_remote_id) if record.helpdesk_ticket_remote_id else False
            )

    @staticmethod
    def _parse_remote_datetime(value):
        # El servicio manda ISO 8601 en UTC ("...T...+00:00"); Odoo 15 guarda datetimes naive en UTC.
        if not value:
            return False
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    @api.model
    def _vals_from_remote(self, data):
        contact = data.get("contact") or {}
        return {
            "remote_id": data["id"],
            "status": data.get("status") or "ai",
            "is_urgent": bool(data.get("is_urgent")),
            "escalation_category": data.get("escalation_category") or "",
            "escalation_reason": data.get("escalation_reason") or "",
            "wa_id": contact.get("wa_id") or "",
            "contact_name": contact.get("profile_name") or "",
            "company_name": contact.get("company") or "",
            "verified": bool(contact.get("verified")),
            "helpdesk_ticket_remote_id": data.get("helpdesk_ticket_id") or 0,
            "last_message_at": self._parse_remote_datetime(data.get("last_message_at")),
            "created_at_remote": self._parse_remote_datetime(data.get("created_at")),
        }

    @api.model
    def sync_list(self, status=None):
        """Trae la lista del servicio y actualiza (o crea) la copia local. No toca los mensajes."""
        remote_items = agent_client.list_conversations(self.env, status=status)
        existing = {c.remote_id: c for c in self.search([("remote_id", "in", [d["id"] for d in remote_items])])}
        for data in remote_items:
            vals = self._vals_from_remote(data)
            record = existing.get(data["id"])
            if record:
                record.write(vals)
            else:
                self.create(vals)
        return True

    def action_refresh(self):
        """Trae de nuevo esta conversación puntual (estado, urgencia, etc.) y sus mensajes nuevos."""
        self.ensure_one()
        remote = agent_client.list_conversations(self.env)
        data = next((d for d in remote if d["id"] == self.remote_id), None)
        if data:
            self.write(self._vals_from_remote(data))
        self._sync_messages()

    def _sync_messages(self):
        self.ensure_one()
        messages = agent_client.get_messages(self.env, self.remote_id)
        new_last = self.last_synced_message_id
        for message in messages:
            if message["id"] <= self.last_synced_message_id:
                continue
            label = _SENDER_LABEL.get(message.get("sender"), message.get("sender"))
            raw_body = message.get("body") or ("[adjunto]" if message.get("has_media") else "")
            safe_body = html_escape(raw_body).replace("\n", "<br/>")
            self.message_post(body=f"<b>{label}</b> ({(message.get('timestamp') or '')[:16]}): {safe_body}")
            new_last = max(new_last, message["id"])
        if new_last != self.last_synced_message_id:
            self.last_synced_message_id = new_last

    def action_take(self):
        self.ensure_one()
        agent_client.take(self.env, self.remote_id, taken_by=self.env.user.name)
        self.action_refresh()

    def action_return_to_ai(self):
        self.ensure_one()
        agent_client.return_to_ai(self.env, self.remote_id)
        self.action_refresh()

    def action_close(self):
        self.ensure_one()
        agent_client.close(self.env, self.remote_id)
        self.action_refresh()

    def action_open_reply_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ais.whatsapp.reply.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_conversation_id": self.id},
        }

    @api.model
    def cron_sync_list(self):
        params = self.env["ir.config_parameter"].sudo()
        if not params.get_param("ais_helpdesk_whatsapp.service_url") or not params.get_param(
            "ais_helpdesk_whatsapp.panel_api_key"
        ):
            return  # Todavía no se configuró el servicio: no ensuciar el log cada 2 minutos.
        self.sync_list()
