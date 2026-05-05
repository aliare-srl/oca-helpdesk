odoo.define('helpdesk_mgmt.sla_notifications', function (require) {
    'use strict';

    var ListController = require('web.ListController');
    var rpc = require('web.rpc');

    ListController.include({
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (
                    self.modelName === 'helpdesk.ticket' &&
                    !sessionStorage.getItem('helpdesk_sla_notified')
                ) {
                    self._checkSlaAlerts();
                }
            });
        },

        _checkSlaAlerts: function () {
            var self = this;
            rpc.query({
                model: 'helpdesk.ticket',
                method: 'get_sla_alerts_for_current_user',
                args: [],
            }).then(function (tickets) {
                tickets.forEach(function (ticket) {
                    var isRed = ticket.sla_status === 'red';
                    var fechaLocal = self._utcToLocal(ticket.fecha_limite);
                    self.displayNotification({
                        type: isRed ? 'danger' : 'warning',
                        title: isRed ? '🔴 SLA Vencido' : '🟡 SLA Próximo a Vencer',
                        message: (
                            (isRed ? '🔴' : '🟡') + ' #' + ticket.number +
                            ' — ' + ticket.name +
                            '\nConsumo: ' + ticket.pct + '% | Límite: ' + fechaLocal
                        ),
                        sticky: isRed,
                        buttons: [{
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
                        }],
                    });
                });
                sessionStorage.setItem('helpdesk_sla_notified', '1');
            }).catch(function (err) {
                console.error('[helpdesk_mgmt] Error al obtener alertas SLA:', err);
                sessionStorage.setItem('helpdesk_sla_notified', '1');
            });
        },

        _utcToLocal: function (utcString) {
            if (!utcString) return '';
            // El servidor devuelve "YYYY-MM-DD HH:MM:SS" en UTC
            var d = new Date(utcString.replace(' ', 'T') + 'Z');
            return d.toLocaleString();
        },
    });

    return ListController;
});
