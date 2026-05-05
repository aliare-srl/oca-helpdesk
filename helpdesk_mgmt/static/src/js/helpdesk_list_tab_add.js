/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

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

        // add() llama internamente a addNewRecord() que ya guarda el record actual
        this.add({ group });

        let attempts = 0;
        const focusNameField = () => {
            if (!this.tableRef.el) return;
            const selectedRow = this.tableRef.el.querySelector(
                "tbody tr.o_data_row.o_selected_row"
            );
            if (selectedRow) {
                const inp = selectedRow.querySelector(
                    '.o_field_widget[name="name"] input'
                );
                if (inp) {
                    inp.focus();
                    inp.select();
                    return;
                }
            }
            if (++attempts < 20) setTimeout(focusNameField, 50);
        };
        setTimeout(focusNameField, 150);

        return true;
    },
});
