"""Cliente HTTP contra la API del servicio AgenteIA-MesadeAyuda-Odoo (el "panel").

El servicio es el dueño de las conversaciones: este módulo solo muestra lo que la API
le entrega y dispara las acciones a través de ella. No hay nada de esto en el XML-RPC
del Helpdesk: es una API HTTP aparte, protegida por una clave compartida (X-Panel-Key).
"""

import logging

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TIMEOUT = 10


def _config(env):
    params = env["ir.config_parameter"].sudo()
    base_url = (params.get_param("ais_helpdesk_whatsapp.service_url") or "").rstrip("/")
    api_key = params.get_param("ais_helpdesk_whatsapp.panel_api_key") or ""
    if not base_url or not api_key:
        raise UserError(
            _("Falta configurar la URL del servicio o la clave de la API en Ajustes > Mesa de Ayuda WhatsApp.")
        )
    return base_url, api_key


def _request(env, method, path, json_body=None, params=None):
    base_url, api_key = _config(env)
    url = f"{base_url}{path}"
    try:
        response = requests.request(
            method, url, json=json_body, params=params, headers={"X-Panel-Key": api_key}, timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        _logger.warning("Error llamando a %s: %s", url, exc)
        raise UserError(_("No se pudo conectar con el servicio de WhatsApp: %s") % exc) from exc

    if response.status_code == 401:
        raise UserError(_("La clave de la API configurada es inválida."))
    if response.status_code == 404:
        raise UserError(_("No se encontró la conversación en el servicio."))
    if response.status_code >= 400:
        raise UserError(
            _("El servicio de WhatsApp devolvió un error (%(code)s): %(detail)s")
            % {"code": response.status_code, "detail": response.text[:300]}
        )
    return response.json() if response.content else {}


def list_conversations(env, status=None, limit=200):
    params = {"limit": limit}
    if status:
        params["status"] = status
    return _request(env, "GET", "/api/conversations", params=params).get("conversations", [])


def get_messages(env, remote_id):
    return _request(env, "GET", f"/api/conversations/{remote_id}/messages").get("messages", [])


def get_message_media(env, remote_id, message_id):
    """Devuelve (content_type, contenido) del adjunto real de un mensaje. No usa _request: esa
    función siempre espera JSON, y esto es el archivo en bruto (ej. la imagen del cliente)."""
    base_url, api_key = _config(env)
    url = f"{base_url}/api/conversations/{remote_id}/messages/{message_id}/media"
    try:
        response = requests.get(url, headers={"X-Panel-Key": api_key}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        _logger.warning("Error llamando a %s: %s", url, exc)
        raise UserError(_("No se pudo conectar con el servicio de WhatsApp: %s") % exc) from exc
    if response.status_code != 200:
        raise UserError(_("No se encontró el adjunto en el servicio."))
    return response.headers.get("Content-Type", "application/octet-stream"), response.content


def reply(env, remote_id, text):
    return _request(env, "POST", f"/api/conversations/{remote_id}/reply", json_body={"text": text})


def take(env, remote_id, taken_by=None):
    body = {"taken_by": taken_by} if taken_by else None
    return _request(env, "POST", f"/api/conversations/{remote_id}/take", json_body=body)


def return_to_ai(env, remote_id):
    return _request(env, "POST", f"/api/conversations/{remote_id}/return_to_ai")


def close(env, remote_id):
    return _request(env, "POST", f"/api/conversations/{remote_id}/close")


def start_conversation(
    env, phone, template_name, params=None, profile_name=None, helpdesk_partner_id=None, helpdesk_ticket_id=None
):
    body = {"phone": phone, "template_name": template_name, "params": params or []}
    if profile_name:
        body["profile_name"] = profile_name
    if helpdesk_partner_id:
        body["helpdesk_partner_id"] = helpdesk_partner_id
    if helpdesk_ticket_id:
        body["helpdesk_ticket_id"] = helpdesk_ticket_id
    return _request(env, "POST", "/api/conversations/start", json_body=body)
