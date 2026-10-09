/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component, hooks } = owl;
const { useState, useRef, onWillStart, onWillUnmount, onWillPatch, onPatched } = hooks;

const DEFAULT_POLL_INTERVAL_MS = 4000;

const STATUS_PILL = {
    waiting_human: { label: "Espera a una persona", bg: "#FEF0D9", color: "#8A3B0C", border: "#F2C98A" },
    ai: { label: "Atiende la IA", bg: "#DDF1F4", color: "#0B5560", border: "#A9D8DF" },
    human: { label: "Atiende", bg: "#E1F3E8", color: "#17603B", border: "#A9D9BC" },
    closed: { label: "Cerrada", bg: "#ECE9EB", color: "#3F3A44", border: "#D2CCD3" },
};

const QUICK_REPLIES = ["Ya lo reviso", "¿Me pasás una captura?", "Quedó resuelto, gracias"];

// Orden de la lista: primero por estado (esperando > IA > persona > cerrada), y dentro de cada
// estado, de la más reciente a la más antigua.
const STATUS_ORDER = { waiting_human: 0, ai: 1, human: 2, closed: 3 };

function todayLocal() {
    const d = new Date();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${month}-${day}`;
}

function initials(name) {
    const parts = (name || "").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) {
        return "?";
    }
    return (parts[0][0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
}

export class WhatsappDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.userService = useService("user");
        this.quickReplies = QUICK_REPLIES;
        this.state = useState({
            conversations: [],
            agentDisabled: false,
            loading: true,
            error: "",
            selectedId: null,
            searchQuery: "",
            filterTab: "esperando",
            dateFrom: todayLocal(),
            dateTo: todayLocal(),
            messages: [],
            messagesLoading: false,
            messagesError: "",
            replyText: "",
            sending: false,
            actionError: "",
            actionPending: false,
            ticketInfo: null,
            now: Date.now(),
            startOpen: false,
            startPhone: "",
            startName: "",
            startTemplate: "",
            startParams: "",
            startError: "",
            startSending: false,
            startTicketId: null,
            closeOpen: false,
            closeResolution: "",
            closeError: "",
        });

        this.pollIntervalMs = DEFAULT_POLL_INTERVAL_MS;

        // Los mensajes nuevos bajan solos el scroll, salvo que se esté leyendo más arriba.
        this.messagesRef = useRef("messages");
        this.stickToBottom = true;
        this.lastScrolledId = null;
        onWillPatch(() => {
            const el = this.messagesRef.el;
            if (el) {
                this.stickToBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
            }
        });
        onPatched(() => {
            const el = this.messagesRef.el;
            if (!el) {
                this.lastScrolledId = null;
                return;
            }
            if (this.stickToBottom || this.lastScrolledId !== this.state.selectedId) {
                el.scrollTop = el.scrollHeight;
            }
            this.lastScrolledId = this.state.selectedId;
        });

        onWillStart(async () => {
            await this.loadConfig();
            await this.loadConversations();
            const params = this.props.action && this.props.action.params;
            if (params && params.conversation_id) {
                this.selectConversation(params.conversation_id);
            } else if (params && params.start_from_ticket) {
                this.openStartModal(params.start_from_ticket);
            }
            this.pollTimer = setInterval(() => this.poll(), this.pollIntervalMs);
        });

        this.clockTimer = setInterval(() => {
            this.state.now = Date.now();
        }, 30000);
        onWillUnmount(() => {
            clearInterval(this.pollTimer);
            clearInterval(this.clockTimer);
        });
    }

    async loadConfig() {
        try {
            const config = await this.rpc("/ais_helpdesk_whatsapp/config", {});
            if (config.refresh_seconds > 0) {
                this.pollIntervalMs = config.refresh_seconds * 1000;
            }
            this.state.agentDisabled = Boolean(config.agent_disabled);
        } catch (error) {
            // Se sigue con los valores por defecto si no se pudo leer la configuración.
        }
    }

    async poll() {
        await this.loadConversations({ silent: true });
        if (this.state.selectedId) {
            await this.loadMessages({ silent: true });
        }
    }

    async loadConversations({ silent = false } = {}) {
        if (!silent) {
            this.state.loading = true;
            this.state.error = "";
        }
        try {
            const conversations = await this.rpc("/ais_helpdesk_whatsapp/conversations", {});
            conversations.sort((a, b) => {
                const order = (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9);
                if (order !== 0) return order;
                return (b.last_message_at || "").localeCompare(a.last_message_at || "");
            });
            this.state.conversations = conversations;
        } catch (error) {
            if (!silent) {
                this.state.error = error.message || "No se pudo conectar con el servicio.";
            }
        } finally {
            this.state.loading = false;
        }
    }

    get byDateConversations() {
        const from = this.state.dateFrom;
        const to = this.state.dateTo;
        if (!from && !to) {
            return this.state.conversations;
        }
        return this.state.conversations.filter((c) => {
            if (!c.last_message_at) return false;
            // last_message_at viene en UTC; se compara por fecha calendario tal cual, sin pasar a
            // hora local. Cerca de la medianoche puede quedar un mensaje en el día de al lado.
            const day = c.last_message_at.slice(0, 10);
            if (from && day < from) return false;
            if (to && day > to) return false;
            return true;
        });
    }

    get esperandoCount() {
        return this.byDateConversations.filter((c) => c.status === "waiting_human").length;
    }

    get iaCount() {
        return this.byDateConversations.filter((c) => c.status === "ai").length;
    }

    get personaCount() {
        return this.byDateConversations.filter((c) => c.status === "human").length;
    }

    get cerradasCount() {
        return this.byDateConversations.filter((c) => c.status === "closed").length;
    }

    get todasCount() {
        return this.byDateConversations.length;
    }

    setFilterTab(tab) {
        this.state.filterTab = tab;
    }

    resetDateToday() {
        const today = todayLocal();
        this.state.dateFrom = today;
        this.state.dateTo = today;
    }

    get filteredConversations() {
        const byTab = this.byDateConversations.filter((c) => {
            if (this.state.filterTab === "esperando") return c.status === "waiting_human";
            if (this.state.filterTab === "ia") return c.status === "ai";
            if (this.state.filterTab === "persona") return c.status === "human";
            if (this.state.filterTab === "cerradas") return c.status === "closed";
            return true;
        });
        const query = this.state.searchQuery.trim().toLowerCase();
        if (!query) {
            return byTab;
        }
        return byTab.filter((c) => {
            const contact = c.contact || {};
            const haystack = `${contact.company || ""} ${contact.profile_name || ""} ${contact.wa_id || ""}`.toLowerCase();
            return haystack.includes(query);
        });
    }

    statusPill(status) {
        return STATUS_PILL[status] || STATUS_PILL.closed;
    }

    statusLabel(conversation) {
        if (conversation.status === "human") {
            return conversation.taken_by ? `Atiende ${conversation.taken_by}` : "Atiende una persona";
        }
        return this.statusPill(conversation.status).label;
    }

    contactLabel(conversation) {
        const contact = conversation.contact || {};
        return contact.profile_name || contact.wa_id;
    }

    initials(conversation) {
        const contact = conversation.contact || {};
        return initials(contact.profile_name || contact.company);
    }

    timeLabel(iso) {
        if (!iso) {
            return "";
        }
        return new Date(iso).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
    }

    async selectConversation(id) {
        this.state.selectedId = id;
        this.state.replyText = "";
        this.state.ticketInfo = null;
        await this.loadMessages();
        const conversation = this.selectedConversation;
        if (conversation && conversation.helpdesk_ticket_id) {
            this.loadTicketInfo(conversation.helpdesk_ticket_id);
        }
    }

    async loadTicketInfo(ticketId) {
        try {
            this.state.ticketInfo = await this.rpc(`/ais_helpdesk_whatsapp/tickets/${ticketId}`, {});
        } catch (error) {
            this.state.ticketInfo = null;
        }
    }

    async loadMessages({ silent = false } = {}) {
        const id = this.state.selectedId;
        if (!silent) {
            this.state.messagesLoading = true;
            this.state.messagesError = "";
        }
        try {
            this.state.messages = await this.rpc(`/ais_helpdesk_whatsapp/conversations/${id}/messages`, {});
        } catch (error) {
            if (!silent) {
                this.state.messagesError = error.message || "No se pudo leer la conversación.";
            }
        } finally {
            this.state.messagesLoading = false;
        }
    }

    async sendReply(text) {
        const body = (text !== undefined ? text : this.state.replyText).trim();
        const id = this.state.selectedId;
        if (!body || !id || this.state.sending) {
            return;
        }
        this.state.sending = true;
        this.state.messagesError = "";
        try {
            await this.rpc(`/ais_helpdesk_whatsapp/conversations/${id}/reply`, { text: body });
            this.state.replyText = "";
            await this.loadMessages();
        } catch (error) {
            this.state.messagesError = error.message || "No se pudo mandar la respuesta.";
        } finally {
            this.state.sending = false;
        }
    }

    sendQuickReply(text) {
        return this.sendReply(text);
    }

    onReplyKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendReply();
        }
    }

    senderClass(sender) {
        if (sender === "customer") return "customer";
        if (sender === "human") return "human";
        return "ai";
    }

    senderLabel(sender, conversation) {
        if (sender === "customer") return this.contactLabel(conversation);
        if (sender === "human") return conversation.taken_by || "Persona";
        return "IA";
    }

    mediaUrl(message) {
        return `/ais_helpdesk_whatsapp/conversations/${this.state.selectedId}/messages/${message.id}/media`;
    }

    get selectedConversation() {
        return this.state.conversations.find((c) => c.id === this.state.selectedId) || null;
    }

    get canReply() {
        return !!this.selectedConversation && this.selectedConversation.status === "human";
    }

    get canTake() {
        const status = this.selectedConversation && this.selectedConversation.status;
        return status && status !== "human" && status !== "closed";
    }

    get canReturnToAi() {
        return this.selectedConversation && this.selectedConversation.status === "human";
    }

    get canClose() {
        const status = this.selectedConversation && this.selectedConversation.status;
        return status && status !== "closed";
    }

    get pauseRemainingLabel() {
        const until = this.selectedConversation && this.selectedConversation.ai_paused_until;
        if (!until) {
            return "";
        }
        const diffMs = new Date(until).getTime() - this.state.now;
        if (diffMs <= 0) {
            return "en cualquier momento";
        }
        const totalMin = Math.round(diffMs / 60000);
        const h = Math.floor(totalMin / 60);
        const m = totalMin % 60;
        return h > 0 ? `${h} h ${m} min` : `${m} min`;
    }

    async runAction(route, extraParams = {}) {
        const id = this.state.selectedId;
        if (!id || this.state.actionPending) {
            return;
        }
        this.state.actionPending = true;
        this.state.actionError = "";
        try {
            await this.rpc(`/ais_helpdesk_whatsapp/conversations/${id}/${route}`, extraParams);
            await this.loadConversations();
            if (this.state.selectedId) {
                await this.loadMessages();
            }
        } catch (error) {
            this.state.actionError = error.message || "No se pudo completar la acción.";
        } finally {
            this.state.actionPending = false;
        }
    }

    takeConversation() {
        const ticketId = this.selectedConversation && this.selectedConversation.helpdesk_ticket_id;
        return this.runAction("take", { ticket_id: ticketId });
    }

    returnToAi() {
        const ticketId = this.selectedConversation && this.selectedConversation.helpdesk_ticket_id;
        return this.runAction("return_to_ai", { ticket_id: ticketId });
    }

    openCloseModal() {
        this.state.closeOpen = true;
        this.state.closeResolution = "";
        this.state.closeError = "";
    }

    closeCloseModal() {
        this.state.closeOpen = false;
    }

    async submitClose() {
        const resolution = this.state.closeResolution.trim();
        if (!resolution) {
            this.state.closeError = "Contá en pocas palabras cómo se resolvió, antes de cerrar.";
            return;
        }
        const id = this.state.selectedId;
        const ticketId = this.selectedConversation && this.selectedConversation.helpdesk_ticket_id;
        this.state.actionPending = true;
        this.state.closeError = "";
        try {
            await this.rpc(`/ais_helpdesk_whatsapp/conversations/${id}/close`, { resolution, ticket_id: ticketId });
            this.state.closeOpen = false;
            await this.loadConversations();
        } catch (error) {
            this.state.closeError = error.message || "No se pudo cerrar la conversación.";
        } finally {
            this.state.actionPending = false;
        }
    }

    backToList() {
        this.state.selectedId = null;
    }

    openTicket() {
        const ticketId = this.selectedConversation && this.selectedConversation.helpdesk_ticket_id;
        if (!ticketId) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "helpdesk.ticket",
            res_id: ticketId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openStartModal(prefill) {
        this.state.startOpen = true;
        this.state.startPhone = (prefill && prefill.phone) || "";
        this.state.startName = (prefill && prefill.profile_name) || "";
        this.state.startTemplate = "";
        this.state.startParams = "";
        this.state.startError = "";
        this.state.startTicketId = (prefill && prefill.ticket_id) || null;
    }

    closeStartModal() {
        this.state.startOpen = false;
    }

    async submitStart() {
        const phone = this.state.startPhone.trim();
        const templateName = this.state.startTemplate.trim();
        if (!phone || !templateName) {
            this.state.startError = "Faltan el número y la plantilla.";
            return;
        }
        this.state.startSending = true;
        this.state.startError = "";
        const params = this.state.startParams
            .split(",")
            .map((p) => p.trim())
            .filter(Boolean);
        try {
            await this.rpc("/ais_helpdesk_whatsapp/conversations/start", {
                phone,
                template_name: templateName,
                profile_name: this.state.startName.trim() || null,
                params,
                ticket_id: this.state.startTicketId,
            });
            this.state.startOpen = false;
            await this.loadConversations();
        } catch (error) {
            this.state.startError = error.message || "No se pudo iniciar la conversación.";
        } finally {
            this.state.startSending = false;
        }
    }
}

WhatsappDashboard.template = "ais_helpdesk_whatsapp.WhatsappDashboard";

registry.category("actions").add("ais_whatsapp_dashboard", WhatsappDashboard);
