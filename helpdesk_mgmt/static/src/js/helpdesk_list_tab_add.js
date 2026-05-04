/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, "helpdesk_mgmt.list_tab_add", {
    async onCellKeydownEditMode(hotkey, cell, group, record) {
        if (
            hotkey !== "tab" ||
            !this.tableRef.el ||
            !this.tableRef.el.classList.contains("o_helpdesk_aliare") ||
            this.findNextFocusableOnRow(cell.parentElement, cell)
        ) {
            return this._super(...arguments);
        }

        // 1. Guardar el record actual antes de agregar uno nuevo
        if (record && typeof record.save === "function") {
            const saved = await record.save();
            if (!saved) return false;
        } else {
            // Fallback: blur del campo activo para disparar el guardado del campo
            const activeEl = document.activeElement;
            if (activeEl) activeEl.blur();
        }

        // 2. Agregar nueva fila (editable="top" la pone arriba)
        this.add({ group });

        // 3. Esperar a que OWL re-renderice y la nueva fila aparezca PRIMERA y SELECCIONADA
        let attempts = 0;
        const focusNewRow = () => {
            const table = this.tableRef.el;
            if (!table) return;
            const allRows = table.querySelectorAll("tbody tr.o_data_row");
            const selectedRow = table.querySelector(
                "tbody tr.o_data_row.o_selected_row"
            );
            // La nueva fila debe ser la primera Y estar seleccionada
            if (selectedRow && allRows.length && selectedRow === allRows[0]) {
                const inp = selectedRow.querySelector(
                    '.o_field_widget[name="name"] input'
                );
                if (inp) {
                    inp.focus();
                    inp.select();
                    return;
                }
            }
            if (++attempts < 30) {
                setTimeout(focusNewRow, 50);
            }
        };
        setTimeout(focusNewRow, 50);

        return true;
    },
});
