/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useEffect } from "@odoo/owl";
import { session } from "@web/session";

const NOTIF_TYPE = "helpdesk_ticket_portal_notification";

registry.category("services").add("helpdesk_portal_notifier", {
    dependencies: ["bus_service", "notification"],
    start(env, { bus_service, notification }) {

        const showNotification = (payload) => {
            const { number, name, display_name } = payload || {};
            const msg = display_name
                || [number && `#${number}`, name].filter(Boolean).join(" – ")
                || "Nuevo ticket ingresado desde el portal";

            notification.add(msg, {
                title: "Nuevo Ticket del Portal",
                type: "warning",
                sticky: true,
            });

            window.dispatchEvent(
                new CustomEvent("helpdesk_portal_new_ticket", { detail: payload || {} })
            );
        };

        bus_service.subscribe(NOTIF_TYPE, showNotification);

        // Sin addChannel() el bus no hace longpoll y las notificaciones no llegan.
        // El servidor envía con _sendone(user.partner_id) → canal (db, 'res.partner', id).
        if (session.partner_id && session.db) {
            bus_service.addChannel([session.db, "res.partner", session.partner_id]);
        }
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
