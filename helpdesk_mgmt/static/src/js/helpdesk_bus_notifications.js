/** @odoo-module **/
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useEffect } from "@odoo/owl";

// Servicio que escucha el canal bus "new_helpdesk_ticket"
// y dispara un CustomEvent en window para que el ListController lo capture.
const helpdeskBusListenerService = {
    dependencies: ["bus_service"],
    start(env, { bus_service }) {
        bus_service.subscribe("new_helpdesk_ticket", () => {
            window.dispatchEvent(new CustomEvent("helpdesk_new_ticket_received"));
        });
    },
};

registry.category("services").add("helpdesk_bus_listener", helpdeskBusListenerService);

// Cuando el usuario tiene abierta la lista de helpdesk.ticket,
// recarga la grilla al recibir el evento de nuevo ticket.
patch(ListController.prototype, "helpdesk_mgmt.bus_list_reload", {
    setup() {
        this._super();
        const model = this.model;
        useEffect(
            () => {
                if (!model || model.resModel !== "helpdesk.ticket") {
                    return;
                }
                const handler = () => model.load();
                window.addEventListener("helpdesk_new_ticket_received", handler);
                return () => window.removeEventListener("helpdesk_new_ticket_received", handler);
            },
            () => []
        );
    },
});
