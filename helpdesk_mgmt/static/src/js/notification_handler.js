/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useEffect } from "@odoo/owl";
import { session } from "@web/session";

const NOTIF_TYPE = "helpdesk_ticket_portal_notification";

// ---------------------------------------------------------------------------
// SERVICIO GLOBAL
//
// Problema raíz: bus_service.subscribe() registra el handler pero NO activa
// el polling. Para que el bus haga longpoll/WebSocket en tiempo real, hay que
// llamar a addChannel(), que inicia la conexión.
//
// Solución: suscribir al canal del partner del usuario actual. Ese es
// exactamente el canal al que el servidor envía con _sendone(user.partner_id).
// ---------------------------------------------------------------------------
registry.category("services").add("helpdesk_portal_notifier", {
    dependencies: ["bus_service", "notification"],
    start(env, { bus_service, notification }) {

        const showAndDispatch = (payload) => {
            console.log("[helpdesk] Notificación recibida!", payload);

            const { display_name, number, name } = payload || {};
            const msg = display_name
                || [number && `#${number}`, name].filter(Boolean).join(" – ")
                || "Nuevo ticket ingresado desde el portal";

            notification.add(msg, {
                title: "Nuevo Ticket del Portal",
                type: "warning",
                sticky: true,         // no desaparece sola — el usuario la cierra con X
            });

            window.dispatchEvent(
                new CustomEvent("helpdesk_portal_ticket", { detail: payload || {} })
            );
        };

        // 1. Registrar handler para nuestro tipo
        bus_service.subscribe(NOTIF_TYPE, showAndDispatch);

        // 2. ACTIVAR el polling suscribiendo el canal del partner del usuario.
        //    Sin esto, el bus no hace longpoll y los mensajes llegan solo al
        //    reconectar la sesión.
        //    El servidor envía con: bus.bus._sendone(user.partner_id, ...)
        //    que internamente usa el canal (dbname, 'res.partner', partner_id).
        if (session.partner_id && session.db) {
            bus_service.addChannel([session.db, "res.partner", session.partner_id]);
        }

        // 3. Cobertura adicional: evento genérico del bus (filtrado por tipo)
        if (typeof bus_service.addEventListener === "function") {
            bus_service.addEventListener("notification", (evt) => {
                const list = Array.isArray(evt.detail) ? evt.detail : [evt.detail];
                list.forEach((notif) => {
                    const type = notif.type || (notif.message && notif.message.type);
                    if (type === NOTIF_TYPE) {
                        showAndDispatch(notif.payload || notif.message || notif);
                    }
                });
            });
        }
    },
});

// ---------------------------------------------------------------------------
// LIST CONTROLLER
// Si el usuario tiene la vista helpdesk.ticket abierta, recarga la grilla
// cuando llega la señal (la notificación ya la mostró el servicio de arriba).
// ---------------------------------------------------------------------------
patch(ListController.prototype, "helpdesk_mgmt.portal_grid_reload", {
    setup() {
        this._super();
        const model = this.model;

        useEffect(
            () => {
                if (!model || model.resModel !== "helpdesk.ticket") {
                    return;
                }
                const handler = () => model.load();
                window.addEventListener("helpdesk_portal_ticket", handler);
                return () => window.removeEventListener("helpdesk_portal_ticket", handler);
            },
            () => []
        );
    },
});
