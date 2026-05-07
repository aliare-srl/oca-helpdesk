/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { useEffect } from "@odoo/owl";

// ---------------------------------------------------------------------------
// 1. Servicio global: escucha el bus y reenvía el payload como CustomEvent.
//    No muestra nada por sí solo — la notificación la muestra el ListController
//    solo cuando el usuario tiene la vista helpdesk abierta.
// ---------------------------------------------------------------------------
const helpdeskBusListenerService = {
    dependencies: ["bus_service"],
    start(env, { bus_service }) {
        bus_service.subscribe("new_helpdesk_ticket", (payload) => {
            window.dispatchEvent(
                new CustomEvent("helpdesk_new_ticket_received", { detail: payload || {} })
            );
        });
    },
};

registry.category("services").add("helpdesk_bus_listener", helpdeskBusListenerService);

// ---------------------------------------------------------------------------
// 2. Patch de ListController:
//    - Solo actúa cuando el modelo activo es helpdesk.ticket.
//    - Muestra una notificación STICKY (no desaparece sola).
//    - Recarga la grilla para que aparezca el nuevo ticket.
// ---------------------------------------------------------------------------
patch(ListController.prototype, "helpdesk_mgmt.bus_list_reload", {
    setup() {
        this._super();
        const notification = useService("notification");
        const model = this.model;

        useEffect(
            () => {
                // Salir si no es la vista de helpdesk
                if (!model || model.resModel !== "helpdesk.ticket") {
                    return;
                }

                const handler = (evt) => {
                    const { number, name, partner } = evt.detail || {};
                    const title = "🎫 Nuevo ticket del portal";
                    const lines = [number && `#${number}`, name, partner && `(${partner})`]
                        .filter(Boolean)
                        .join(" – ");

                    notification.add(lines || "Nuevo ticket ingresado desde el portal", {
                        title,
                        type: "warning",
                        sticky: true,        // no desaparece hasta que el usuario la cierre
                    });

                    // Recargar la grilla para que el ticket aparezca sin F5
                    model.load();
                };

                window.addEventListener("helpdesk_new_ticket_received", handler);
                return () => window.removeEventListener("helpdesk_new_ticket_received", handler);
            },
            () => []  // sin dependencias: se monta una vez y se desmonta con el componente
        );
    },
});
