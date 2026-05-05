/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from "@web/views/list/list_controller";

// ─── PATCH 1: TAB en último campo ────────────────────────────────────────────
patch(ListRenderer.prototype, "helpdesk_mgmt.list_tab_add", {
    onCellKeydownEditMode(hotkey, cell, group, record) {
        if (
            hotkey !== "tab" ||
            !this.tableRef.el ||
            !this.tableRef.el.classList.contains("o_helpdesk_aliare") ||
            this.findNextFocusableOnRow(cell.parentElement, cell)
        ) {
            return this._super(...arguments);
        }

        // Captura ANTES del async para que sirva como referencia post-reload+add
        const initialRowCount = this.tableRef.el.querySelectorAll(
            "tbody tr.o_data_row"
        ).length;

        (async () => {
            // 1. Guardar el registro actual; abortar si falla validación
            const saved = await record.save();
            if (!saved) return;

            // 2. Recargar lista desde servidor → aplica default_order="create_date desc"
            await this.props.list.load();

            // 3. Crear nueva fila vacía en top (record ya está clean, no hay doble-guardado)
            this.add({ group });

            // 4. Foco en "name" de la nueva fila (la que aumentó el conteo)
            let attempts = 0;
            const focusNameField = () => {
                if (!this.tableRef.el) return;
                const allRows = this.tableRef.el.querySelectorAll("tbody tr.o_data_row");
                if (allRows.length > initialRowCount) {
                    const inp = allRows[0].querySelector(
                        '.o_field_widget[name="name"] input'
                    );
                    if (inp) {
                        inp.focus();
                        inp.select();
                        return;
                    }
                }
                if (++attempts < 30) setTimeout(focusNameField, 50);
            };
            setTimeout(focusNameField, 50);
        })();

        return true;
    },
});

// ─── PATCH 2: Botón "Guardar" ────────────────────────────────────────────────
patch(ListController.prototype, "helpdesk_mgmt.list_reload_on_save", {
    async saveRecord() {
        const result = await this._super(...arguments);
        if (result && this.el && this.el.querySelector("table.o_helpdesk_aliare")) {
            await this.model.root.load();
        }
        return result;
    },
});
