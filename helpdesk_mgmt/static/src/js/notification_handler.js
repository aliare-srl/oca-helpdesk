/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useEffect } from "@odoo/owl";

registry.category("services").add("helpdesk_portal_notifier", {
    dependencies: ["rpc", "notification"],
    async start(env, { rpc, notification }) {

        // Verificar primero si el usuario tiene permisos de helpdesk.
        // Si no los tiene, no iniciamos el polling — no tiene sentido
        // consultar ni mostrar notificaciones a usuarios sin acceso.
        let isHelpdeskUser = false;
        try {
            isHelpdeskUser = await rpc("/web/dataset/call_kw", {
                model: "helpdesk.ticket",
                method: "current_user_is_helpdesk",
                args: [],
                kwargs: {},
            });
        } catch (e) {
            console.error("[helpdesk] No se pudo verificar permisos:", e);
            return {};
        }

        if (!isHelpdeskUser) {
            return {};
        }

        const showNotification = (payload) => {
            const { number, name, partner, display_name } = payload || {};
            const msg = display_name
                || [number && `#${number}`, name, partner && `(${partner})`]
                    .filter(Boolean).join(" – ")
                || "Nuevo ticket ingresado desde el portal";

            // sticky: true es CRÍTICO — la notificación no desaparece sola.
            // El operador debe cerrarla manualmente haciendo click en la X.
            notification.add(msg, {
                title: "🎫 Nuevo Ticket del Portal",
                type: "warning",
                sticky: true,
            });

            window.dispatchEvent(
                new CustomEvent("helpdesk_portal_new_ticket", { detail: payload || {} })
            );
        };

        const poll = async () => {
            try {
                const tickets = await rpc("/web/dataset/call_kw", {
                    model: "helpdesk.ticket",
                    method: "get_new_portal_tickets_for_notification",
                    args: [],
                    kwargs: {},
                });
                if (tickets && tickets.length) {
                    tickets.forEach(showNotification);
                }
            } catch (e) {
                console.error("[helpdesk] Error en polling:", e);
            }
        };

        const intervalId = setInterval(poll, 30000);

        return {
            destroy() {
                clearInterval(intervalId);
            },
        };
    },
});

patch(ListController.prototype, "helpdesk_mgmt.portal_ticket_grid_reload", {
    setup() {
        this._super();
        const model = this.model;

        useEffect(
            () => {
                if (!model || model.resModel !== "helpdesk.ticket") {
                    return;
                }
                const handler = () => model.load();
                window.addEventListener("helpdesk_portal_new_ticket", handler);
                return () => window.removeEventListener("helpdesk_portal_new_ticket", handler);
            },
            () => []
        );
    },
});
