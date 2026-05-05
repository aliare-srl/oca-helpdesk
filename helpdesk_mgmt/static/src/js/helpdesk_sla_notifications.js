odoo.define('helpdesk_mgmt.sla_notifications', function (require) {
    'use strict';

    var ListController = require('web.ListController');
    var rpc = require('web.rpc');

    var SESSION_KEY = 'helpdesk_sla_notified';

    ListController.include({

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self._helpdeskIsSlaView()) {
                    self._helpdeskShowSlaNotifications();
                }
            });
        },

        _helpdeskIsSlaView: function () {
            return this.modelName === 'helpdesk.ticket';
        },

        _helpdeskShowSlaNotifications: function () {
            var self = this;

            if (sessionStorage.getItem(SESSION_KEY)) {
                return;
            }

            rpc.query({
                model: 'helpdesk.ticket',
                method: 'get_sla_alerts_for_current_user',
                args: [],
            }).then(function (tickets) {
                if (!tickets || tickets.length === 0) {
                    sessionStorage.setItem(SESSION_KEY, '1');
                    return;
                }

                tickets.forEach(function (ticket) {
                    var isRed = ticket.sla_status === 'red';
                    var icon = isRed ? '🚨' : '⚠️';
                    var title = isRed ? 'SLA Vencido' : 'SLA Próximo a Vencer';
                    var message = icon + ' [' + ticket.number + '] ' + ticket.name
                        + ' — ' + ticket.pct + '% del tiempo consumido.'
                        + ' Vence: ' + self._helpdeskFormatDate(ticket.fecha_limite);

                    self.displayNotification({
                        title: title,
                        message: message,
                        type: isRed ? 'danger' : 'warning',
                        sticky: isRed,
                        buttons: [
                            {
                                name: 'Ver ticket',
                                primary: true,
                                onClick: function () {
                                    self.do_action({
                                        type: 'ir.actions.act_window',
                                        res_model: 'helpdesk.ticket',
                                        res_id: ticket.id,
                                        views: [[false, 'form']],
                                        target: 'current',
                                    });
                                },
                            },
                        ],
                    });
                });

                sessionStorage.setItem(SESSION_KEY, '1');

            }).catch(function (err) {
                console.error('[helpdesk_mgmt] Error al obtener alertas SLA:', err);
            });
        },

        _helpdeskFormatDate: function (dateStr) {
            if (!dateStr) return '';
            try {
                var d = new Date(dateStr.replace(' ', 'T') + 'Z');
                var pad = function (n) { return String(n).padStart(2, '0'); };
                return pad(d.getDate()) + '/' + pad(d.getMonth() + 1) + '/' + d.getFullYear()
                    + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
            } catch (e) {
                return dateStr;
            }
        },
    });
});
