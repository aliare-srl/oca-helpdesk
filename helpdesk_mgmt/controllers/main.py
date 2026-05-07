import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class HelpdeskTicketController(http.Controller):
    @http.route("/ticket/close", type="http", auth="user")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""
        values = {}
        for field_name, field_value in kw.items():
            if field_name.endswith("_id"):
                values[field_name] = int(field_value)
            else:
                values[field_name] = field_value
        ticket = (
            http.request.env["helpdesk.ticket"]
            .sudo()
            .search([("id", "=", values["ticket_id"])])
        )
        stage = http.request.env["helpdesk.ticket.stage"].browse(values.get("stage_id"))
        if stage.close_from_portal:  # protect against invalid target stage request
            ticket.stage_id = values.get("stage_id")

        return werkzeug.utils.redirect("/my/ticket/" + str(ticket.id))

    def _get_teams(self):
        return (
            http.request.env["helpdesk.ticket.team"]
            .with_company(request.env.company.id)
            .search([("active", "=", True), ("show_in_portal", "=", True)])
            if http.request.env.user.company_id.helpdesk_mgmt_portal_select_team
            else False
        )

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        session_info = http.request.env["ir.http"].session_info()
        company = request.env.company
        category_model = http.request.env["helpdesk.ticket.category"]
        categories = category_model.with_company(company.id).search(
            [("active", "=", True)]
        )
        email = http.request.env.user.email
        name = http.request.env.user.name
        company = request.env.company
        commercial_partner = request.env.user.partner_id.commercial_partner_id
        branches = commercial_partner.child_ids.filtered(lambda c: c.active)
        return http.request.render(
            "helpdesk_mgmt.portal_create_ticket",
            {
                "categories": categories,
                "teams": self._get_teams(),
                "email": email,
                "name": name,
                "branches": branches,
                "ticket_team_id_required": (
                    company.helpdesk_mgmt_portal_team_id_required
                ),
                "ticket_category_id_required": (
                    company.helpdesk_mgmt_portal_category_id_required
                ),
                "max_upload_size": session_info["max_file_upload_size"],
            },
        )

    def _prepare_submit_ticket_vals(self, **kw):
        category = http.request.env["helpdesk.ticket.category"].browse(
            int(kw.get("category"))
        )
        company = category.company_id or http.request.env.company
        raw_description = (kw.get("description") or "").strip()
        branch_id = kw.get("branch_id")
        if branch_id:
            partner = http.request.env["res.partner"].sudo().browse(int(branch_id))
            if not partner.exists():
                partner = request.env.user.partner_id
        else:
            partner = request.env.user.partner_id
        vals = {
            "company_id": company.id,
            "category_id": category.id,
            "description": plaintext2html(raw_description) if raw_description else False,
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env.ref(
                "helpdesk_mgmt.helpdesk_ticket_channel_web", False
            ).id,
            "partner_id": partner.id,
            "partner_name": partner.name,
            "partner_email": partner.email,
        }
        team = http.request.env["helpdesk.ticket.team"]
        if company.helpdesk_mgmt_portal_select_team and kw.get("team"):
            team = (
                http.request.env["helpdesk.ticket.team"]
                .sudo()
                .search(
                    [("id", "=", int(kw.get("team"))), ("show_in_portal", "=", True)]
                )
            )
            vals["team_id"] = team.id
        # Need to set stage_id so that the _track_template() method is called
        # and the mail is sent automatically if applicable
        vals["stage_id"] = team._get_applicable_stages()[:1].id
        return vals

    @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        vals = self._prepare_submit_ticket_vals(**kw)
        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        subscriber_ids = list({request.env.user.partner_id.id, vals.get("partner_id", 0)} - {0})
        new_ticket.message_subscribe(partner_ids=subscriber_ids)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "helpdesk.ticket",
                            "res_id": new_ticket.id,
                        }
                    )
        return werkzeug.utils.redirect("/my/ticket/%s" % new_ticket.id)

    @http.route('/helpdesk/suggest_solutions', type='json', auth='user', website=True)
    def suggest_solutions(self, subject='', **kw):
        STOPWORDS = {
            # Artículos
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            # Preposiciones
            'a', 'al', 'ante', 'bajo', 'con', 'contra', 'de', 'del',
            'desde', 'durante', 'en', 'entre', 'hacia', 'hasta',
            'mediante', 'para', 'por', 'sin', 'sobre', 'tras',
            # Conjunciones
            'e', 'ni', 'o', 'u', 'y', 'aunque', 'como', 'cuando',
            'mas', 'pero', 'porque', 'pues', 'que', 'si', 'sino', 'ya',
            # Pronombres y determinantes
            'ese', 'esa', 'eso', 'este', 'esta', 'esto',
            'le', 'les', 'lo', 'me', 'mi', 'mis', 'nos',
            'se', 'su', 'sus', 'te', 'tu', 'tus', 'vos', 'yo',
            # Verbos auxiliares / cópulas
            'es', 'son', 'fue', 'ser', 'hay', 'ha', 'han', 'he',
            'hemos', 'sido', 'tiene', 'tienen',
            # Adverbios comunes
            'así', 'aquí', 'bien', 'mal', 'más', 'muy', 'no', 'sí',
            'también', 'hoy', 'ayer',
            # Inglés básico
            'and', 'are', 'for', 'from', 'in', 'is', 'not',
            'of', 'or', 'that', 'the', 'this', 'to', 'with',
        }

        CLOSED_STAGES = {
            'hecho', 'resuelto', 'cerrado', 'finalizado', 'completado',
            'done', 'resolved', 'closed', 'completed',
        }

        words = [
            w for w in subject.lower().split()
            if len(w) >= 3 and w not in STOPWORDS
        ]
        if not words:
            return {'tickets': [], 'slides': []}

        partner_id = request.env.user.partner_id.id

        name_conds = [('name', 'ilike', w) for w in words]
        if len(name_conds) == 1:
            word_domain = list(name_conds)
        else:
            word_domain = ['|'] * (len(name_conds) - 1) + name_conds

        domain = ['&', '|',
                  ('partner_id', '=', partner_id),
                  ('partner_id', '=', False)] + word_domain

        candidates = request.env['helpdesk.ticket'].sudo().search(domain, limit=50)

        def score_ticket(t):
            name_lower = t.name.lower()
            keyword_score = sum(1 for w in words if w in name_lower)
            stage_lower = (t.stage_id.name or '').lower()
            stage_bonus = 2 if any(k in stage_lower for k in CLOSED_STAGES) else 0
            return keyword_score + stage_bonus

        scored = sorted(
            [(t, score_ticket(t)) for t in candidates],
            key=lambda x: x[1],
            reverse=True,
        )

        ticket_results = [
            {
                'id': t.id,
                'name': t.name,
                'number': t.number,
                'stage': t.stage_id.name,
                'url': '/my/ticket/%d' % t.id,
            }
            for t, score in scored[:5]
            if score > 0
        ]

        slide_results = []
        if request.env['ir.model'].sudo().search([('model', '=', 'slide.slide')], limit=1):
            if len(name_conds) == 1:
                slide_domain = list(name_conds)
            else:
                slide_domain = ['|'] * (len(name_conds) - 1) + name_conds
            slide_domain += [('is_published', '=', True)]
            slides = request.env['slide.slide'].sudo().search(slide_domain, limit=20)

            def score_slide(s):
                name_lower = s.name.lower()
                return sum(1 for w in words if w in name_lower)

            scored_slides = sorted(
                [(s, score_slide(s)) for s in slides],
                key=lambda x: x[1],
                reverse=True,
            )
            slide_results = [
                {'id': s.id, 'name': s.name, 'url': s.website_url}
                for s, score in scored_slides[:5]
                if score > 0
            ]

        return {'tickets': ticket_results, 'slides': slide_results}
