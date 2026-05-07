/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useEffect } from "@odoo/owl";

const NOTIF_TYPE = "helpdesk_ticket_portal_notification";

// ---------------------------------------------------------------------------
// SERVICIO: escucha el bus y muestra la alerta en CUALQUIER vista del backend.
// La notificación es sticky → el usuario debe cerrarla manualmente.
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

            // Alerta sticky: el usuario debe cerrarla con la X
            notification.add(msg, {
                title: "Nuevo Ticket del Portal",
                type: "warning",
                sticky: true,
            });

            // Señal para que el ListController (si está abierto) recargue la grilla
            window.dispatchEvent(
                new CustomEvent("helpdesk_portal_ticket", { detail: payload || {} })
            );
        };

        // Suscripción directa al tipo específico (OWL bus_service v15)
        bus_service.subscribe(NOTIF_TYPE, showAndDispatch);

        // Cobertura adicional: evento genérico 'notification' del bus (filtrado por tipo)
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
// LIST CONTROLLER: cuando la vista helpdesk.ticket está abierta,
// recarga la grilla al recibir la señal (sin mostrar otra notificación).
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
