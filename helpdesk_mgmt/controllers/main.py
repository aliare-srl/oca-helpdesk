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
        return http.request.render(
            "helpdesk_mgmt.portal_create_ticket",
            {
                "categories": categories,
                "teams": self._get_teams(),
                "email": email,
                "name": name,
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
        vals = {
            "company_id": company.id,
            "category_id": category.id,
            "description": plaintext2html(raw_description) if raw_description else False,
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env.ref(
                "helpdesk_mgmt.helpdesk_ticket_channel_web", False
            ).id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
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
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
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
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'en', 'de', 'del', 'al', 'que', 'por', 'para', 'con',
            'sin', 'a', 'y', 'o', 'es', 'se', 'lo', 'su',
            'the', 'an', 'is', 'are', 'of', 'in', 'to', 'for', 'and',
        }
        words = [w for w in subject.lower().split() if len(w) > 2 and w not in STOPWORDS]
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

        tickets = request.env['helpdesk.ticket'].sudo().search(domain, limit=5)
        ticket_results = [
            {
                'id': t.id,
                'name': t.name,
                'number': t.number,
                'stage': t.stage_id.name,
                'url': '/my/ticket/%d' % t.id,
            }
            for t in tickets
        ]

        slide_results = []
        if request.env['ir.model'].sudo().search([('model', '=', 'slide.slide')], limit=1):
            if len(name_conds) == 1:
                slide_domain = list(name_conds)
            else:
                slide_domain = ['|'] * (len(name_conds) - 1) + name_conds
            slide_domain += [('is_published', '=', True)]
            slides = request.env['slide.slide'].sudo().search(slide_domain, limit=3)
            slide_results = [
                {'id': s.id, 'name': s.name, 'url': s.website_url}
                for s in slides
            ]

        return {'tickets': ticket_results, 'slides': slide_results}
