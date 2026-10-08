/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component, hooks } = owl;
const { useState, onWillStart } = hooks;

const STATUS_LABEL = {
    ai: "Atiende la IA",
    waiting_human: "Esperando a un humano",
    human: "Atiende un humano",
    closed: "Cerrada",
};

// Primero las que esperan o están con una persona, después la IA, al final las cerradas.
const STATUS_ORDER = { waiting_human: 0, human: 1, ai: 2, closed: 3 };

export class WhatsappDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({ conversations: [], loading: true, error: "", selectedId: null });
        onWillStart(() => this.loadConversations());
    }

    async loadConversations() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const conversations = await this.rpc("/ais_helpdesk_whatsapp/conversations", {});
            conversations.sort((a, b) => {
                if (a.is_urgent !== b.is_urgent) return a.is_urgent ? -1 : 1;
                const order = STATUS_ORDER[a.status] - STATUS_ORDER[b.status];
                if (order !== 0) return order;
                return (b.last_message_at || "").localeCompare(a.last_message_at || "");
            });
            this.state.conversations = conversations;
        } catch (error) {
            this.state.error = error.message || "No se pudo conectar con el servicio.";
        } finally {
            this.state.loading = false;
        }
    }

    statusLabel(status) {
        return STATUS_LABEL[status] || status;
    }

    contactLabel(conversation) {
        const contact = conversation.contact || {};
        return contact.company || contact.profile_name || contact.wa_id;
    }

    selectConversation(id) {
        this.state.selectedId = id;
    }

    get selectedConversation() {
        return this.state.conversations.find((c) => c.id === this.state.selectedId) || null;
    }
}

WhatsappDashboard.template = "ais_helpdesk_whatsapp.WhatsappDashboard";

registry.category("actions").add("ais_whatsapp_dashboard", WhatsappDashboard);
