odoo.define('helpdesk_mgmt.portal_notifier', function (require) {
    'use strict';

    var AbstractService = require('web.AbstractService');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var ListController = require('web.ListController');

    // Servicio de polling: verifica cada 30 segundos si hay tickets
    // nuevos ingresados desde el portal que no fueron notificados todavía.
    // Solo corre si el usuario logueado pertenece al grupo helpdesk_user.
    var HelpdeskPortalNotifier = AbstractService.extend({
        name: 'helpdesk_portal_notifier',

        start: function () {
            var self = this;

            rpc.query({
                model: 'helpdesk.ticket',
                method: 'current_user_is_helpdesk',
                args: [],
            }).then(function (isHelpdeskUser) {
                if (!isHelpdeskUser) {
                    return;
                }
                self._intervalId = setInterval(function () {
                    self._poll();
                }, 30000);
            }).catch(function (err) {
                console.error('[helpdesk] No se pudo verificar permisos:', err);
            });
        },

        _poll: function () {
            var self = this;
            rpc.query({
                model: 'helpdesk.ticket',
                method: 'get_new_portal_tickets_for_notification',
                args: [],
            }).then(function (tickets) {
                if (!tickets || !tickets.length) {
                    return;
                }
                tickets.forEach(function (payload) {
                    self._showNotification(payload);
                });
            }).catch(function (err) {
                console.error('[helpdesk] Error en polling:', err);
            });
        },

        _showNotification: function (payload) {
            var number = payload.number || '';
            var name = payload.name || '';
            var partner = payload.partner || '';
            var msg = payload.display_name
                || [
                    number && ('#' + number),
                    name,
                    partner && ('(' + partner + ')')
                  ].filter(Boolean).join(' – ')
                || 'Nuevo ticket ingresado desde el portal';

            // sticky: true — la notificación NO desaparece sola.
            // El operador debe cerrarla manualmente con la X.
            this.displayNotification({
                title: '🎫 Nuevo Ticket del Portal',
                message: msg,
                type: 'warning',
                sticky: true,
            });

            // Señal para que el ListController recargue la grilla
            // si el usuario tiene abierta la vista de tickets.
            window.dispatchEvent(
                new CustomEvent('helpdesk_portal_new_ticket', { detail: payload })
            );
        },

        destroy: function () {
            if (this._intervalId) {
                clearInterval(this._intervalId);
            }
            this._super.apply(this, arguments);
        },
    });

    core.serviceRegistry.add('helpdesk_portal_notifier', HelpdeskPortalNotifier);

    // Patch del ListController para recargar la grilla cuando
    // llega una notificación de ticket nuevo del portal.
    ListController.include({
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.modelName !== 'helpdesk.ticket') {
                    return;
                }
                self._helpdeskPortalHandler = function () {
                    self.reload();
                };
                window.addEventListener(
                    'helpdesk_portal_new_ticket',
                    self._helpdeskPortalHandler
                );
            });
        },

        destroy: function () {
            if (this._helpdeskPortalHandler) {
                window.removeEventListener(
                    'helpdesk_portal_new_ticket',
                    this._helpdeskPortalHandler
                );
            }
            this._super.apply(this, arguments);
        },
    });

    return HelpdeskPortalNotifier;
});
