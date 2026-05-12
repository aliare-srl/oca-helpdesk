odoo.define('helpdesk_mgmt.portal_deflection', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.HelpdeskDeflection = publicWidget.Widget.extend({
        selector: "form[action='/submitted/ticket']",
        events: {
            'focusout #ticket_subject': '_onSubjectFocusOut',
        },

        _onSubjectFocusOut: function (ev) {
            var subject = $(ev.currentTarget).val().trim();
            if (subject.length < 3) {
                return;
            }
            var self = this;
            ajax.jsonRpc('/helpdesk/suggest_solutions', 'call', {subject: subject})
                .then(function (result) {
                    self._renderSuggestions(result);
                })
                .catch(function (err) {
                    console.error('[helpdesk] Error al obtener sugerencias:', err);
                });
        },

        _renderSuggestions: function (result) {
            var $panel = $('#helpdesk_suggestions_panel');
            var $empty = $('#helpdesk_suggestions_empty');
            var hasTickets = result.tickets && result.tickets.length > 0;
            var hasSlides = result.slides && result.slides.length > 0;

            if (!hasTickets && !hasSlides) {
                $panel.find('.card').remove();
                $empty.show();
                return;
            }

            $empty.hide();

            var html = '<div class="card border-info shadow-sm">'
                + '<div class="card-header bg-info text-white py-2">'
                + '<strong>💡 ¿Ya existe una solución?</strong>'
                + '</div><div class="card-body p-3">';

            if (hasTickets) {
                html += '<p class="mb-1 font-weight-bold">🎫 Tickets similares:</p>'
                    + '<ul class="list-unstyled mb-3">';
                result.tickets.forEach(function (t) {
                    html += '<li class="mb-1"><a href="#" class="helpdesk-suggestion-link text-info"'
                        + ' data-url="' + t.url + '">'
                        + '🎫 [' + t.number + '] ' + t.name
                        + ' <small class="text-muted">(' + t.stage + ')</small></a></li>';
                });
                html += '</ul>';
            }

            if (hasSlides) {
                html += '<p class="mb-1 font-weight-bold">📚 Cursos sugeridos:</p>'
                    + '<ul class="list-unstyled">';
                result.slides.forEach(function (s) {
                    html += '<li class="mb-1"><a href="#" class="helpdesk-suggestion-link text-info"'
                        + ' data-url="' + s.url + '">📚 ' + s.name + '</a></li>';
                });
                html += '</ul>';
            }

            html += '</div></div>';
            $panel.find('.card').remove();
            $panel.append(html);

            $panel.find('.helpdesk-suggestion-link').on('click', function (e) {
                e.preventDefault();
                var url = $(this).data('url');
                window.open(url, '_blank');
            });
        },
    });
});
