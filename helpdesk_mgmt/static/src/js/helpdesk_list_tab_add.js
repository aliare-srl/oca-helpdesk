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

        if (record && typeof record.save === "function") {
            const saved = await record.save();
            if (!saved) return false;
        } else {
            const activeEl = document.activeElement;
            if (activeEl) activeEl.blur();
        }

        // Reload entre save y add: reordena por create_date desc antes de agregar la fila nueva
        await this.props.list.load();
        this.props.list.model.notify();

        this.add({ group });

        let attempts = 0;
        const focusNewRow = () => {
            const table = this.tableRef.el;
            if (!table) return;
            const allRows = table.querySelectorAll("tbody tr.o_data_row");
            const selectedRow = table.querySelector(
                "tbody tr.o_data_row.o_selected_row"
            );
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
